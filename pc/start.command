#!/bin/bash
# macOS launcher: double-click in Finder, or run "bash start.command" in Terminal.
cd "$(dirname "$0")" || exit 1

fail() {
  echo
  echo "$1"
  read -r -p "Enter 키를 누르면 닫습니다." _
  exit 1
}

usable() {
  "$1" -c 'import sys,tkinter;sys.exit(sys.version_info<(3,10) or tkinter.TkVersion<8.6)' >/dev/null 2>&1
}

if [ ! -x .venv/bin/python ]; then
  python=
  for candidate in python3.12 python3.11 python3.10 python3 \
      /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 \
      /opt/homebrew/bin/python3.12 /usr/local/bin/python3.12; do
    if command -v "$candidate" >/dev/null 2>&1 && usable "$candidate"; then python=$candidate;break;fi
  done
  if [ -z "$python" ]; then
    open 'https://www.python.org/downloads/macos/' 2>/dev/null
    fail "Python 3.10~3.12와 Tkinter가 필요합니다. python.org에서 Python 3.12 macOS 설치 파일을 받아 설치한 뒤 다시 실행해 주세요.
Homebrew Python을 쓴다면 brew install python-tk@3.12 도 설치해 주세요."
  fi
  "$python" -m venv --clear .venv || fail "가상 환경을 만들지 못했습니다. 이 폴더에 쓰기 권한이 있는지 확인해 주세요."
fi
.venv/bin/python -m pip install -r requirements.txt || fail "라이브러리 설치에 실패했습니다. 위 오류와 인터넷 연결을 확인해 주세요."
.venv/bin/python desktop.py || fail "프로그램이 오류로 종료됐습니다. 위 오류를 확인해 주세요."
