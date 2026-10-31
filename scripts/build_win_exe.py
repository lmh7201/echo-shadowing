"""Build release/echo-pc.exe, a single-file Windows app with Python and dependencies inside.
Usage: py -3.12 scripts/build_win_exe.py  (set ECHO_VERSION=v1.3.0 so the exe can update itself from GitHub Releases)"""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
RELEASE=ROOT/'release'

def main():
    for name in ('win','win-build','win-venv'):shutil.rmtree(RELEASE/name,ignore_errors=True)
    subprocess.run([sys.executable,'-m','venv',str(RELEASE/'win-venv')],check=True)
    python=str(RELEASE/'win-venv'/'Scripts'/'python.exe')
    subprocess.run([python,'-m','pip','install','-q','-r',str(ROOT/'pc'/'requirements.txt'),'pyinstaller==6.22.3'],check=True)
    subprocess.run([python,'-m','PyInstaller','--noconfirm','--distpath',str(RELEASE/'win'),'--workpath',str(RELEASE/'win-build'),str(ROOT/'scripts'/'echo-pc-win.spec')],check=True)
    output=RELEASE/'echo-pc.exe';shutil.copy2(RELEASE/'win'/'echo-pc.exe',output)
    print(output)

if __name__=='__main__':main()
