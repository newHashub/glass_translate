# 🪟 GlassTranslate

<div align="center">

[简体中文](../README.md) • [English](README_EN.md) • [日本語](README_JA.md) • **한국어**

![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D4?logo=windows)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**투명한 번역 유리: 외국어 위에 올려두면 원문 자리에 번역문이 표시됩니다.**

<a href="assets/GlassTranslate-Promo.mp4">
  <img src="assets/preview.gif" alt="GlassTranslate 데모" width="860" />
</a>

[▶️ 데모 영상 보기 (46초, 중국어 자막)](assets/GlassTranslate-Promo.mp4)

</div>

GlassTranslate는 Windows용 실시간 화면 번역 도구입니다. 테두리 없는 투명한 뷰파인더를 외국어 위로 옮기면 원문 위에 번역문이 겹쳐 표시되며, 팝업이 화면을 가리지 않습니다. 외국어 웹페이지와 문서, 번역되지 않은 게임, 자막 없는 영상을 볼 때 유용합니다.

## 기능

- **제자리 번역**: 각 줄의 위치를 인식하고 주변 배경색을 가져와 원문 위에 번역문을 그립니다.
- **자유로운 이동**: 창 안을 좌클릭 드래그하면 이동, 가장자리를 끌면 크기 조절, 휠로 커서 중심 확대/축소. 손을 떼면 바로 다시 인식합니다.
- **영역 선택 번역**: `Alt + S`를 누르고 스크린샷처럼 영역을 드래그하면 뷰파인더가 그 영역에 맞춰 번역합니다.
- **언어 자동 감지**: 설치된 영어·일본어·중국어·한국어 OCR 중에서 자동으로 고릅니다. 영어가 섞인 한국어·일본어도 인식합니다.
- **API 키 불필요**: 기본으로 유도(Youdao) 웹 채널을 사용합니다. DeepSeek, OpenAI 또는 로컬 Ollama도 연결할 수 있습니다.
- **빠른 속도**: Windows 내장 OCR을 로컬에서 사용합니다. 같은 문장으로 다시 돌아오면 네트워크 대신 캐시를 사용합니다.

> 번역 채널은 중국어에 맞춰져 있습니다. 한국어로도 번역할 수 있지만 주 대상은 중국어입니다.

## 다운로드 및 사용

1. [Releases](https://github.com/newHashub/glass_translate/releases)를 열고 최신 `GlassTranslate-vX.Y.Z-Windows-x64.zip`을 내려받습니다(릴리스 아래쪽 Assets에 있습니다).
2. 원하는 위치에 압축을 풀고, 안에 있는 `GlassTranslate` 폴더를 열어 `GlassTranslate.exe`를 더블클릭합니다.
3. 뷰파인더를 외국어 위로 드래그합니다. `Alt + R`로 언제든 마우스 위치에 표시하거나 숨길 수 있습니다.

압축을 푼 폴더 구성:

```
GlassTranslate/
├── GlassTranslate.exe      ← 더블클릭해 실행
├── 创建桌面快捷方式.vbs     ← "바탕화면 바로가기 만들기": 더블클릭하면 아이콘 생성
├── 使用说明.txt             ← 사용 안내(중국어)
└── _internal/              ← 실행에 필요한 파일. exe와 같은 곳에 두세요
```

> 저장소 페이지의 소스 코드(Code → Download ZIP)는 개발자용이라 바로 실행되지 않습니다. Releases의 ZIP을 내려받으세요.

Python은 필요 없습니다. 한국어나 일본어를 인식하려면 해당 OCR 언어 팩이 필요합니다. [자주 묻는 질문](#자주-묻는-질문)을 참고하세요.

## 단축키와 조작

| 조작 | 동작 |
| :--- | :--- |
| `Alt + R` | 마우스 위치에 뷰파인더 표시/숨기기 |
| `Alt + S` | 영역 선택 번역: 영역을 드래그하면 번역. `Esc` 또는 우클릭으로 취소 |
| 창 안에서 좌클릭 드래그 | 뷰파인더 이동 |
| 가장자리/모서리 드래그 | 크기 조절 |
| 창 안에서 휠 | 커서 중심 확대/축소(메뉴에서 끌 수 있음) |
| 창 안/트레이 아이콘 우클릭 | 설정 메뉴 열기 |
| 트레이 아이콘 클릭 | 뷰파인더 표시/숨기기 |

두 단축키 모두 우클릭 메뉴의 **⌨️ 唤出快捷键**(호출 단축키)에서 바꿀 수 있으며 바로 적용됩니다.

## 설정 메뉴

창 안이나 트레이 아이콘을 우클릭하면 다음을 설정할 수 있습니다.

- **번역 언어**: 자주 쓰는 12가지 프리셋(자동/영/일/한/프/독/러/스페인어 → 중국어, 중국어 → 영/일/한, 자동 → 영어) 또는 "사용자 지정"에서 자유롭게 조합.
- **번역 엔진**: 유도 웹 채널(기본), MyMemory, 사용자 지정 LLM(OpenAI 호환 API).
- **표시 모드**: 제자리 교체(기본) 또는 떠 있는 자막 카드.
- **글자 크기, 인식 주기, 항상 위, 상태 표시, 휠 확대/축소**.
- **최근 번역문 복사**, **사용자 지정 API 설정**.

> 메뉴는 현재 중국어로 표시됩니다.

## 자주 묻는 질문

<details>
<summary><b>"자동"으로 설정했는데 영어만 인식되는 이유는?</b></summary>

Windows에는 설치한 언어의 OCR만 들어 있습니다. 한국어나 일본어가 설치되어 있지 않으면 해당 문자를 인식할 수 없습니다.

추가 방법: **설정 → 시간 및 언어 → 언어 및 지역 → 언어 추가**에서 한국어 또는 일본어를 선택하고 "광학 문자 인식"이 포함되어 있는지 확인하세요. 표시 언어를 바꿀 필요는 없습니다. 설치 후 GlassTranslate를 다시 실행하세요.
</details>

<details>
<summary><b>API 키가 필요한가요? 기본 채널은 안정적인가요?</b></summary>

키는 필요 없습니다. 다만 기본 유도 채널은 유도의 웹용 엔드포인트를 사용하며 **공식 공개 API가 아닙니다**. 사용량이 많으면 제한될 수 있고, 사이트가 바뀌면 작동하지 않을 수도 있습니다. 요청이 실패하면 유도의 다른 엔드포인트, 그다음 MyMemory로 자동 전환합니다.

오래 안정적으로 쓰려면 우클릭 메뉴의 **🔑 自定义 API 配置...**(사용자 지정 API 설정)에서 LLM을 연결하세요. 예:

- DeepSeek: `https://api.deepseek.com/v1/chat/completions`
- 로컬 Ollama(완전 오프라인): `http://localhost:11434/v1/chat/completions`
</details>

<details>
<summary><b>뷰파인더 자체가 캡처에 찍히지 않나요?</b></summary>

찍히지 않습니다. 창에 `WDA_EXCLUDEFROMCAPTURE`가 설정되어 있어 자기 캡처에는 보이지 않으므로, 화면이 겹쳐 보이거나 깜빡이지 않습니다.
</details>

<details>
<summary><b>긴 문단이 잘리지 않나요?</b></summary>

긴 글은 작은 블록으로 나눠 번역한 뒤 줄 단위로 대조합니다. 맞지 않는 줄이 있으면 그 줄만 다시 번역합니다.
</details>

<details>
<summary><b>Alt + R이 작동하지 않아요</b></summary>

다른 프로그램이 같은 단축키를 쓰고 있을 수 있습니다. 트레이 메뉴의 **⌨️ 唤出快捷键**(호출 단축키)에서 다른 조합으로 바꾸세요. 트레이에 GlassTranslate가 여러 개 실행 중인지도 확인하세요.
</details>

## 개발

Windows 10/11과 Python 3.10 이상(3.12 권장)이 필요합니다.

```bash
git clone https://github.com/newHashub/glass_translate.git
cd glass_translate
pip install -r requirements-dev.txt
python main.py        # 실행
pytest                # 테스트 실행(오프라인)
```

**빌드**: `build_exe.bat`을 더블클릭합니다. `.venv-build`에 깨끗한 가상 환경을 만들고 `dist\GlassTranslate\`, 바탕화면 바로가기, `dist\GlassTranslate-v<버전>-Windows-x64.zip`을 생성합니다. 버전은 `src/version.py`에서 바꿉니다.

<details>
<summary><b>작동 원리와 디렉터리 구조</b></summary>

백그라운드 스레드가 다음을 반복합니다: 뷰파인더 아래 화면 캡처 → 이전 프레임과 같으면 건너뜀 → Windows OCR로 각 줄의 문자와 위치 인식 → 줄 단위 캐시 확인, 없으면 번역 요청 → 각 줄 위치에 번역문 그리기.

```
glass_translate/
├── main.py                  # 진입점
├── src/                     # 소스 코드
│   ├── main.py              # 시작 처리: 트레이, 전역 단축키, 종료 정리
│   ├── glass_window.py      # 투명 뷰파인더, 번역문 레이아웃, 설정 대화상자
│   ├── region_select.py     # Alt+S 영역 선택 오버레이(다중 모니터 지원)
│   ├── worker.py            # 백그라운드 스레드
│   ├── capture_engine.py    # 화면 캡처와 변화 감지
│   ├── ocr_engine.py        # Windows OCR 래퍼, 언어 자동 감지
│   ├── translator_engine.py # 번역 채널 전환, 분할, 캐시
│   ├── global_hotkey.py     # 전역 단축키(RegisterHotKey)
│   ├── tray_manager.py      # 트레이 아이콘과 우클릭 메뉴
│   ├── win32_utils.py       # 캡처 제외, 창 스타일, 고 DPI
│   ├── config.py            # 설정 읽기/쓰기
│   └── version.py           # 버전 번호
├── tests/                   # pytest 테스트
├── packaging/               # 빌드용: PyInstaller 설정, 바로가기·배포 ZIP 생성 스크립트
├── resources/               # 아이콘
├── docs/                    # 다른 언어 README, 유사 도구 비교, 데모 자료
├── build_exe.bat            # 원클릭 빌드
├── requirements.txt         # 실행 의존성
└── requirements-dev.txt     # 개발·빌드 의존성
```
</details>

## 유사 도구

Gaminik, WinLens, Dango Translator, LunaTranslator 등도 각자 장점이 있습니다. GlassTranslate는 오픈 소스, 가벼움, 키 불필요, 손쉬운 이동을 목표로 합니다. 자세한 내용은 [유사 도구 비교](COMPARISON.md)(중국어)를 참고하세요.

## 라이선스

[MIT](../LICENSE). Issue와 Pull Request를 환영합니다. 유용했다면 ⭐ 하나 부탁드립니다.
