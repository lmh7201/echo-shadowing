# Echo · 쉐도잉 스튜디오

[웹 앱 열기](https://lmh7201.github.io/echo-shadowing/) · [PC 도구 다운로드](https://github.com/lmh7201/echo-shadowing/releases/latest)

팟캐스트 음성으로 스크립트를 만들고, 소리에 맞춰 문장과 단어를 따라 연습하는 도구입니다.

## 사용하는 방법

### PC에서 자막 만들기 → 모바일에서 연습하기

1. 웹페이지의 다운로드 링크 또는 이 저장소 **Releases**에서 PC 도구를 받아 실행합니다.
   - **Windows**: `echo-pc.exe` 하나를 받아 실행합니다. Python은 필요하지 않습니다. 처음 실행할 때 'Windows의 PC 보호' 창이 나오면 **추가 정보 → 실행**을 누릅니다.
   - **Apple Silicon Mac**: `echo-pc-mac-arm64.zip`의 압축을 풀고 **Echo PC** 앱을 실행합니다. Python은 필요하지 않습니다. 처음 열 때 'Apple이 확인할 수 없습니다'라는 경고가 나오면 **시스템 설정 → 개인정보 보호 및 보안**에서 **그래도 열기**를 누릅니다.
   - **Intel Mac**: `echo-pc.zip`의 `start.command`를 실행합니다. Python 3.12가 필요하며, 자세한 내용은 [pc/README.txt](pc/README.txt)를 참고합니다.
   - Windows exe와 Mac 앱은 실행할 때마다 GitHub Releases에서 새 버전을 확인합니다. 새 버전이 있으면 물어본 뒤 내려받아 스스로 교체하고 다시 시작합니다. **업데이트 확인** 버튼으로 직접 확인할 수도 있습니다. Python 소스 ZIP은 자동 업데이트하지 않습니다.
2. **팟캐스트에서 음성 받기**에서 Apple Podcasts 공유 링크 또는 공개 RSS를 넣고 회차를 선택합니다.
3. Large-v3 또는 Turbo와 음성 언어를 선택합니다. 먼저 앞 30초를 시험한 뒤 전체 음성을 처리합니다.
4. 결과 폴더의 `음성 제목_날짜시각.echo.zip`(예: `第12回_1101_1530.echo.zip`, 제목 앞 30자 + 월일_시분)을 휴대폰으로 옮깁니다. 만들 때마다 이름이 달라 직접 바꿀 필요가 없습니다.
5. 모바일 웹페이지에서 **연습 파일 열기**로 ZIP을 그대로 선택합니다.

음성, 스크립트, 단어 시간이 함께 복원됩니다. 모바일에서는 AI를 다시 실행할 필요가 없습니다.

### 웹에서 바로 만들기

음성 파일 → 언어·모델 선택 → 스크립트 만들기 순서로 사용합니다. 브라우저에서 Small/Base/Tiny 모델을 실행합니다. PC 도구는 이보다 큰 Large-v3/Turbo 모델을 지원합니다.

## 지원 기능

- 문장·단어 하이라이트와 클릭해서 구간 이동
- 문장 반복, 따라 말할 시간, 속도 조절, 스크립트 가리기
- `.echo.zip` 저장·가져오기: 음성과 단어 시간을 한 번에 이동
- `.echo.json` 저장·가져오기: 단어 시간 유지, 음성은 별도 선택
- SRT/VTT 가져오기와 SRT 저장: 문장 시간만 지원
- PC에서 공개 팟캐스트 검색·다운로드, 마지막 방송 기억

## GitHub Pages 배포

저장소의 **Settings → Pages → Build and deployment → Source**를 **GitHub Actions**로 선택합니다. `main` 브랜치의 변경을 올리면 Pages 워크플로가 검사와 PC 도구 패키징을 거쳐 `web/`을 배포합니다. 배포가 끝난 주소는 **Settings → Pages** 또는 **Actions**에서 확인할 수 있습니다.

`v1.0.0`처럼 `v`로 시작하는 태그를 올리면 PC 도구 소스 ZIP을 GitHub Release로 게시합니다. 같은 Release에 GitHub Actions의 Windows 환경에서 빌드한 단일 실행 파일(`echo-pc.exe`)과 macOS 환경에서 빌드한 Mac 앱(`echo-pc-mac-arm64.zip`)도 함께 올립니다. 두 앱 모두 코드 서명 인증서로 서명하지 않았으므로 처음 실행할 때 경고가 나옵니다. 저장소와 Pages의 공개 범위는 GitHub 설정을 따릅니다. 앱 자체에는 로그인 기능이 없습니다.

빌드할 때 `ECHO_VERSION` 환경 변수의 태그가 exe와 Mac 앱 안에 들어가고, 앱은 이 값을 `releases/latest`의 `tag_name`과 비교해 더 큰 버전만 내려받습니다. 내려받은 파일은 GitHub가 알려주는 SHA-256과 대조한 뒤에만 교체합니다. 자동 업데이트는 최신 Release에 해당 플랫폼 파일이 올라간 뒤부터 동작하므로, 워크플로의 Windows·macOS 작업이 모두 끝날 때까지 기다리세요. `ECHO_VERSION` 없이 로컬에서 빌드한 앱은 버전이 `v0.0.0`이라 자동 업데이트를 하지 않습니다.

## 로컬 실행과 검사

```sh
python scripts/package_pc.py
python -m http.server 8765 --directory web
```

브라우저에서 `http://localhost:8765`를 엽니다. 음성 인식은 모듈과 Web Worker를 사용하므로 HTML 파일을 직접 더블클릭하는 대신 HTTP로 실행합니다.

```sh
npm test
python -m unittest discover -s pc -p 'test_*.py'
```

PC 도구의 추가 실행 방법은 [pc/README.txt](pc/README.txt)를 참고하세요.

## 저장과 실행 조건

- 음성 인식은 기기에서 처리합니다. 모델 다운로드에는 인터넷과 디스크 공간이 필요합니다.
- PC 모델은 `pc/models/`, 팟캐스트 원본은 `pc/downloads/`, 결과는 `pc/results/`에 저장합니다. 이 폴더들은 Git에서 제외합니다.
- Windows `echo-pc.exe`는 모델·원본·결과를 `%LOCALAPPDATA%\Echo PC\`에, Mac 앱은 `~/Library/Application Support/Echo PC/`에 저장합니다. 앱의 **결과 폴더 열기**로 바로 열 수 있습니다.
- 자동 업데이트는 새 파일을 같은 폴더의 `updates/`에 내려받은 뒤 실행 중인 exe 또는 앱을 교체합니다. 교체 직전 버전은 `echo-pc.old.exe` 또는 숨김 폴더 `.Echo PC.app.old`로 남았다가 다음 실행 때 지워집니다. exe나 앱이 있는 폴더에 쓸 수 없으면 업데이트에 실패하고 내려받은 파일 위치를 알려줍니다.
- CPU로 실행할 수 있습니다. CUDA는 호환 NVIDIA GPU와 cuBLAS·cuDNN을 별도로 구성한 경우에 사용합니다.
- macOS는 CPU로 실행합니다. Apple Silicon Mac은 macOS 14 이상, Intel Mac은 macOS 13 이상이 필요합니다.
- 원본 음성이 180MB를 넘으면 연습 ZIP 대신 JSON 자막과 원본 음성을 별도로 옮깁니다.
- 새로고침하면 현재 연습은 사라집니다. 연습 파일을 보관하세요.
- 음성 인식 내용, 일본어 단어 경계, 시간은 AI 추정치입니다.
- 공개 RSS의 원본 다운로드를 지원합니다. 유료·로그인 전용 에피소드는 지원하지 않습니다.
- 저장소의 `web/demo.wav`는 합성 예제입니다. 실제 팟캐스트 음원과 생성한 개인 자막은 포함하지 않습니다.

## 구성과 외부 라이브러리

- `web/`: HTML/CSS/JavaScript 웹 앱
- `pc/`: Python/Tkinter PC 도구
- `pc/updater.py`: exe·Mac 앱의 자동 업데이트(GitHub Releases 확인, 다운로드 검증, 교체 후 재시작)
- `pc/icons/`: 앱 아이콘(`icon.ico` Windows, `icon.icns` macOS, `icon.png` 창 아이콘). `py -3.12 scripts/make_icon.py`로 다시 그립니다(Pillow와 Georgia Italic 필요)
- `scripts/package_pc.py`: 정해진 PC 소스만 ZIP으로 패키징
- `scripts/build_win_exe.py`, `scripts/echo-pc-win.spec`: PyInstaller로 Python이 포함된 단일 `echo-pc.exe`를 빌드. Windows에서 `py -3.12 scripts/build_win_exe.py`로 실행
- `scripts/build_mac_app.sh`, `scripts/echo-pc-mac.spec`: PyInstaller로 Python이 포함된 Mac 앱을 빌드. Apple Silicon Mac에서 `scripts/build_mac_app.sh python3.12`로 실행
- Transformers.js: 브라우저 음성 인식, CDN에서 로드
- faster-whisper: PC 음성 인식, 첫 실행 시 설치
- fflate 0.8.2: ZIP 처리, 라이선스는 `web/vendor/fflate-LICENSE.txt`

웹에서는 Google Fonts와 jsDelivr/Hugging Face에 연결합니다. 음성이나 자막을 저장소에 자동 업로드하는 기능은 없습니다.
