"""Self-update for the frozen Windows exe and Mac app: GitHub Releases is the only source."""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
from urllib.parse import urlparse
import uuid
from podcasts import request,read_small,DownloadCancelled

REPO='lmh7201/echo-shadowing'
LATEST=f'https://api.github.com/repos/{REPO}/releases/latest'
MAC=sys.platform=='darwin'
ASSET='echo-pc-mac-arm64.zip' if MAC else 'echo-pc.exe'
FROZEN=getattr(sys,'frozen',False)
MAX_ASSET=1024*1024*1024


def read_version():
    """The build bakes the release tag into echo-version.txt; a source checkout runs as 'dev'."""
    try:return (Path(sys._MEIPASS)/'echo-version.txt').read_text('utf8').strip() or 'dev'
    except (AttributeError,OSError):return 'dev'


def parse_version(text):
    found=re.fullmatch(r'\s*v?(\d+)\.(\d+)(?:\.(\d+))?\s*',text or '')
    return tuple(int(n or 0) for n in found.groups()) if found else None


VERSION=read_version()
# Local builds without ECHO_VERSION are 0.0.0: never replace them with a release.
ENABLED=FROZEN and parse_version(VERSION) not in (None,(0,0,0))


@dataclass(frozen=True)
class Release:
    tag:str
    url:str
    size:int
    sha256:str=''


def latest(current=None):
    """This platform's asset of the newest published release, or None when nothing is newer."""
    installed=parse_version(current or VERSION)
    if installed is None:return None
    data=json.loads(read_small(LATEST,1024*1024))
    tag=str(data.get('tag_name',''))
    asset=next((a for a in data.get('assets',[]) if a.get('name')==ASSET),None)
    if asset is None or (parse_version(tag) or (0,0,0))<=installed:return None
    url=str(asset.get('browser_download_url',''))
    if urlparse(url).hostname!='github.com':raise ValueError('업데이트 주소가 GitHub가 아닙니다.')
    digest=str(asset.get('digest',''))
    return Release(tag,url,int(asset.get('size') or 0),digest[7:] if digest.startswith('sha256:') else '')


def download(release,folder,progress=lambda current,total:None,cancel=None):
    """Fetch the asset into folder, checking the size and the SHA-256 GitHub reports."""
    cancel=cancel or threading.Event()
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    target=folder/ASSET;partial=folder/f'.echo-{uuid.uuid4().hex}.part'
    digest=hashlib.sha256();received=0
    try:
        with request(release.url) as response:
            total=int(response.headers.get('Content-Length','0') or 0) or release.size
            if total>MAX_ASSET:raise ValueError('업데이트 파일이 너무 큽니다.')
            with partial.open('xb') as out:
                while True:
                    if cancel.is_set():raise DownloadCancelled()
                    block=response.read(256*1024)
                    if not block:break
                    received+=len(block)
                    if received>MAX_ASSET:raise ValueError('업데이트 파일이 너무 큽니다.')
                    digest.update(block);out.write(block);progress(received,total)
        if not received or (release.size and received!=release.size):raise ValueError('업데이트 다운로드가 끝나지 않았습니다. 다시 시도해 주세요.')
        if release.sha256 and digest.hexdigest()!=release.sha256:raise ValueError('받은 업데이트 파일이 손상됐습니다. 다시 시도해 주세요.')
        partial.replace(target)
        return target
    finally:
        partial.unlink(missing_ok=True)


def aside(path):
    """Where the previous and the staged copy of the running app live during a swap."""
    if path.suffix=='.app':return path.with_name(f'.{path.name}.old'),path.with_name(f'.{path.name}.new')
    return path.with_name(f'{path.stem}.old{path.suffix}'),path.with_name(f'{path.stem}.new{path.suffix}')


def swap_windows(exe,new):
    """Windows lets a running exe be renamed but not overwritten: move it aside, then the new one into place."""
    old,staged=aside(exe)
    shutil.copyfile(new,staged)  # fails first when the exe's folder is read-only, before the exe is touched
    old.unlink(missing_ok=True)
    exe.rename(old)
    try:staged.rename(exe)
    except OSError:
        old.rename(exe);raise
    return old


def swap_mac(app,new_app):
    """Stage the new bundle beside the running one, then rename both so the swap is atomic."""
    old,staged=aside(app)
    shutil.rmtree(staged,ignore_errors=True);shutil.move(str(new_app),str(staged))
    shutil.rmtree(old,ignore_errors=True)
    app.rename(old)
    try:staged.rename(app)
    except OSError:
        old.rename(app);raise
    return old


def running_app():
    here=Path(sys.executable).resolve()
    if not MAC:return here
    app=here.parents[2] if len(here.parents)>2 else here
    if app.suffix!='.app':raise ValueError('앱 번들 위치를 찾지 못해 자동 업데이트를 할 수 없습니다.')
    return app


def launch_env():
    """A one-file exe hands its unpacked folder to children through _PYI_*/_MEIPASS2; the new exe must unpack itself."""
    return {k:v for k,v in os.environ.items() if not k.startswith('_PYI_') and k!='_MEIPASS2'}


def install(path):
    """Replace the running app with the downloaded one and launch it; the caller quits afterwards."""
    path=Path(path);app=running_app()
    if MAC:
        extract=path.parent/f'extract-{uuid.uuid4().hex}'
        subprocess.run(['ditto','-x','-k',str(path),str(extract)],check=True,capture_output=True)  # zipfile drops symlinks and modes
        new_app=next(extract.glob('*.app'),None)
        if new_app is None or not (new_app/'Contents'/'MacOS').is_dir():raise ValueError('업데이트 파일 안에 앱이 없습니다.')
        swap_mac(app,new_app)
        shutil.rmtree(extract,ignore_errors=True);path.unlink(missing_ok=True)
        subprocess.Popen(['open','-n',str(app)],env=launch_env())
    else:
        swap_windows(app,path)
        path.unlink(missing_ok=True)
        subprocess.Popen([str(app)],cwd=str(app.parent),env=launch_env())


def cleanup(folder):
    """Drop what the last update left: the previous app (its process may still be exiting) and partial downloads."""
    if not FROZEN:return
    def job():
        shutil.rmtree(folder,ignore_errors=True)
        try:pending=list(aside(running_app()))
        except ValueError:return
        for _ in range(10):
            remaining=[]
            for p in pending:
                try:
                    if p.is_dir():shutil.rmtree(p)
                    elif p.exists():p.unlink()
                except OSError:remaining.append(p)
            pending=remaining
            if not pending:return
            time.sleep(1)
    threading.Thread(target=job,daemon=True).start()
