Echo PC — PC에서 만들고 모바일에서 연습하기

Windows 시작하기
1. python.org에서 Python 3.12 64비트를 설치합니다. 이미 있다면 생략합니다.
2. 다운로드한 ZIP을 쓰기 가능한 폴더에 모두 압축 해제합니다.
3. start.cmd를 두 번 클릭합니다. 첫 실행은 필요한 라이브러리를 설치합니다.
4. 음성 선택 → large-v3(정확도 우선) 또는 turbo(속도 우선) → 언어 ja(일본어)를 선택합니다.
   파일이 없다면 '팟캐스트에서 음성 받기'를 누르세요.
   애플 팟캐스트 공유 링크 또는 공개 RSS 입력 → 에피소드 불러오기 → 회차 선택 → 음성 받기.
   YUYU 방송 링크가 기본으로 준비되어 있고, 마지막으로 연 방송은 다음 실행에도 기억합니다.
   제목으로 회차를 검색할 수 있습니다. 다운로드가 끝나면 생성 화면에 자동 선택됩니다.
5. 먼저 '앞 30초 시험'으로 확인한 후 '전체 음성'으로 생성합니다.
6. 결과 폴더 열기 → practice.echo.zip을 휴대폰으로 전송합니다.
7. 이 저장소 README.md에 안내된 웹페이지에서 '연습 파일 열기'를 누릅니다.
   압축을 풀지 말고 practice.echo.zip을 그대로 선택합니다.

저장 형식
- practice.echo.zip: 원본 음성 + 스크립트 + 단어 시간, 한 번에 불러오기.
- transcript.echo.json: 단어 시간을 보존한 자막. 원본 음성을 먼저 선택한 뒤 이 파일을 가져와도 됩니다.
- transcript.srt: 다른 자막 프로그램용. 단어 시간은 없습니다.
- 원본 음성이 180MB보다 크면 ZIP 생성을 건너뛰고 JSON과 SRT만 저장합니다.
- 결과는 프로그램의 results 하위에 새 폴더로 저장되며 원본을 덮어쓰지 않습니다.
- 받은 팟캐스트 원본은 downloads 폴더에 저장됩니다. 이미 받은 동일 회차는 재사용합니다.
- 공개 RSS에 배포된 원본 형식 그대로 받습니다. MP3 외에 M4A 등이 제공될 수 있습니다.
- 유료 구독자 전용/로그인 필요 에피소드는 지원하지 않습니다.

실행 조건
- API 키나 유료 서비스 없이 기기 내에서 처리합니다. 첫 모델 다운로드에는 인터넷과 수 GB 디스크가 필요합니다.
- CPU는 별도 GPU 없이 실행되지만 긴 음성에서 오래 걸립니다. large-v3는 넉넉한 메모리가 필요합니다.
- cuda는 호환 NVIDIA GPU와 CUDA/cuDNN을 직접 구성한 경우에만 선택합니다. 기본은 cpu이며, Mac은 cpu만 지원합니다.
- 모델은 models 폴더에 저장되어 다음에 재사용됩니다. 최초 다운로드 때 진행 표시가 잠시 멈춰 보일 수 있습니다.
- 일본어 단어 경계와 시간은 AI 추정치이며 정확한 정답 자막을 보장하지 않습니다.
- 모바일에서 새로고침하면 현재 연습은 사라집니다. 저장 파일은 보관해주세요.

macOS 시작하기
Apple Silicon Mac은 Python 설치가 필요 없는 Mac 앱을 권장합니다. macOS 14 이상이 필요합니다.
릴리스 페이지에서 echo-pc-mac-arm64.zip을 받아 압축을 풀고 Echo PC 앱을 실행하세요.
처음 열 때 경고가 나오면 아래 3번과 같이 [그래도 열기]를 누릅니다.

Intel Mac이거나 Python으로 직접 실행하려면 아래 순서를 따릅니다. Intel Mac은 macOS 13 이상이 필요합니다.
1. python.org에서 Python 3.12 macOS 설치 파일을 받아 설치합니다.
   Homebrew Python을 쓴다면 brew install python-tk@3.12 로 Tkinter도 설치합니다.
2. 다운로드한 ZIP을 쓰기 가능한 폴더에 모두 압축 해제합니다.
3. start.command를 두 번 클릭합니다. 터미널 창이 열리고, 첫 실행은 필요한 라이브러리를 설치합니다.
   'Apple이 확인할 수 없습니다'라는 경고가 나오면 [완료]를 누른 뒤
   시스템 설정 → 개인정보 보호 및 보안 → 아래쪽의 [그래도 열기]를 누르고 다시 실행합니다.
   경고 없이 실행하려면 터미널에서 이 폴더로 이동한 뒤 bash start.command 를 입력해도 됩니다.
   터미널이 다운로드 폴더 등에 접근하려고 한다는 창이 나오면 허용합니다.
4. 이후 사용법은 Windows 시작하기의 4번부터와 같습니다. 실행 장치는 cpu만 지원합니다.

Linux
Python 3.10 이상과 Tkinter가 필요합니다. 터미널에서 이 폴더로 이동한 뒤:
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python desktop.py

CLI 예시
python transcribe.py "podcast.mp3" --model large-v3 --language ja --device cpu --seconds 30 --output "result-preview"
전체 음성은 --seconds 30을 생략하세요. --output은 아직 없는 새 폴더를 지정합니다.

사용 라이브러리: faster-whisper (MIT) https://github.com/SYSTRAN/faster-whisper
