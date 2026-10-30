"""Public Apple Podcasts / RSS discovery and original-audio download."""
from dataclasses import dataclass
from datetime import timezone
from email.utils import parsedate_to_datetime
import hashlib
import html
import json
from pathlib import Path
import re
import threading
from urllib.parse import urlparse,unquote
from urllib.request import Request,urlopen
import uuid
import xml.etree.ElementTree as ET

DEFAULT_URL='https://podcasts.apple.com/kr/podcast/id1480155677'
MAX_FEED=20*1024*1024
MAX_AUDIO=2*1024*1024*1024


@dataclass(frozen=True)
class Episode:
    title:str
    url:str
    date:str=''
    duration:str=''
    mime:str=''


def http_url(url):
    url=url.strip();p=urlparse(url)
    if p.scheme not in ('https','http') or not p.hostname or p.username or p.password:
        raise ValueError('애플 팟캐스트 공유 링크나 공개 RSS의 http(s) 주소를 입력해 주세요.')
    return url


def request(url):
    return urlopen(Request(http_url(url),headers={'User-Agent':'EchoPC/1.1 (public podcast reader)','Accept':'*/*'}),timeout=30)


def read_small(url,limit=MAX_FEED):
    with request(url) as response:
        data=response.read(limit+1)
    if len(data)>limit:
        raise ValueError('방송 목록이 너무 큽니다.')
    return data


def resolve_feed(url):
    url=http_url(url);p=urlparse(url)
    if p.hostname.lower() in ('podcasts.apple.com','itunes.apple.com'):
        found=re.search(r'/id(\d+)(?:/|$)',p.path)
        if not found:
            raise ValueError('방송 공유 링크에 id로 시작하는 방송 번호가 필요합니다.')
        data=json.loads(read_small('https://itunes.apple.com/lookup?id='+found[1]+'&entity=podcast',1024*1024))
        feed=next((r.get('feedUrl') for r in data.get('results',[]) if r.get('feedUrl')),None)
        if not feed:
            raise ValueError('공개 RSS를 찾지 못했습니다. 방송 제작자의 RSS 주소를 입력해 주세요.')
        return http_url(feed)
    return url


def local(tag):
    return tag.rsplit('}',1)[-1]


def child_text(element,name):
    child=next((c for c in element if local(c.tag)==name),None)
    return ''.join(child.itertext()).strip() if child is not None else ''


def parse_feed(data):
    if len(data)>MAX_FEED or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('지원하지 않는 RSS 형식입니다.')
    try:root=ET.fromstring(data)
    except ET.ParseError as e:
        raise ValueError('RSS를 읽을 수 없습니다. 웹사이트 주소 대신 애플 팟캐스트 링크나 RSS를 입력해 주세요.') from e
    channel=next((c for c in root if local(c.tag)=='channel'),root)
    title=html.unescape(child_text(channel,'title')) or '팟캐스트'
    episodes=[];seen=set()
    for entry in channel:
        if local(entry.tag) not in ('item','entry'):continue
        enclosure=next((c for c in entry if local(c.tag)=='enclosure' or (local(c.tag)=='link' and c.get('rel')=='enclosure')),None)
        if enclosure is None:continue
        raw=enclosure.get('url') or enclosure.get('href') or ''
        try:url=http_url(raw)
        except ValueError:continue
        mime=enclosure.get('type','')
        if mime and not (mime.startswith('audio/') or mime in ('application/octet-stream','video/mp4')):continue
        if url in seen:continue
        seen.add(url)
        name=html.unescape(child_text(entry,'title')) or f'에피소드 {len(episodes)+1}'
        date=child_text(entry,'pubDate') or child_text(entry,'published')
        try:date=parsedate_to_datetime(date).astimezone(timezone.utc).strftime('%Y-%m-%d')
        except (ValueError,TypeError,AttributeError):date=date[:32]
        episodes.append(Episode(name,url,date,child_text(entry,'duration'),mime))
        if len(episodes)>=5000:break
    if not episodes:raise ValueError('공개 음성 파일이 있는 에피소드를 찾지 못했습니다.')
    return title,episodes


def load_podcast(url):
    feed=resolve_feed(url)
    title,episodes=parse_feed(read_small(feed))
    return title,episodes,feed


class DownloadCancelled(Exception):pass


def download_episode(episode,folder,progress=lambda current,total:None,cancel=None):
    cancel=cancel or threading.Event()
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    suffix=Path(unquote(urlparse(episode.url).path)).suffix.lower()
    if suffix not in ('.mp3','.m4a','.wav','.ogg','.flac','.aac','.mp4','.opus'):
        suffix={'audio/mp4':'.m4a','audio/x-m4a':'.m4a','audio/ogg':'.ogg','audio/wav':'.wav','audio/flac':'.flac'}.get(episode.mime,'.mp3')
    title=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',episode.title).strip(' .')[:90] or 'episode'
    digest=hashlib.sha256(episode.url.encode()).hexdigest()[:10]
    target=folder/f'podcast-{title}-{digest}{suffix}'
    if target.is_file() and target.stat().st_size:
        progress(target.stat().st_size,target.stat().st_size);return target
    partial=folder/f'.echo-{uuid.uuid4().hex}.part'
    try:
        if cancel.is_set():raise DownloadCancelled()
        with request(episode.url) as response:
            content_type=response.headers.get('Content-Type','').lower()
            if 'text/html' in content_type or 'application/json' in content_type:
                raise ValueError('음성 대신 웹페이지가 반환됐습니다. 공개 음원인지 확인해 주세요.')
            total=int(response.headers.get('Content-Length','0') or 0)
            if total>MAX_AUDIO:raise ValueError('2GB 이하의 음원만 다운로드할 수 있습니다.')
            received=0
            with partial.open('xb') as out:
                while True:
                    if cancel.is_set():raise DownloadCancelled()
                    block=response.read(256*1024)
                    if not block:break
                    received+=len(block)
                    if received>MAX_AUDIO:raise ValueError('2GB 이하의 음원만 다운로드할 수 있습니다.')
                    out.write(block);progress(received,total)
        if cancel.is_set():raise DownloadCancelled()
        if not received or (total and total!=received):raise ValueError('음성 다운로드가 끝나지 않았습니다. 다시 시도해 주세요.')
        partial.replace(target)
        return target
    finally:
        partial.unlink(missing_ok=True)
