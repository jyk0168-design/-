# 주소록 (Flask + SQLite)

연락처를 등록·수정·삭제·검색할 수 있는 간단한 웹 주소록입니다.
Python **Flask**와 파이썬에 기본으로 들어 있는 **SQLite**를 사용하므로, 별도 DB 서버 없이 파일 하나(`instance/addressbook.db`)에 데이터가 저장됩니다.

파일 수는 적게 유지하면서 실무에서 쓰는 구조(앱 팩토리, DB 모듈 분리, 템플릿 상속, 서버 입력 검증, pytest 테스트)를 따릅니다.

## 주요 기능

| 기능 | 설명 |
|---|---|
| 목록 보기 | 모든 연락처를 이름 가나다순으로 표시 (휴대폰에서는 카드 형태) |
| 등록 | 이름·전화번호(필수), 이메일·주소·메모(선택) |
| 수정 | 기존 값이 채워진 폼에서 수정 |
| 삭제 | 확인 창을 거쳐 삭제 (POST 요청으로만 처리) |
| 검색 | 이름 또는 전화번호 일부로 검색. 전화번호는 하이픈 없이 검색해도 찾음 |
| 입력 검증 | 이름 30자 이하, 전화번호는 숫자와 하이픈만(예: 010-1234-5678), 이메일 형식. 틀리면 칸마다 한글 오류 메시지 표시 |
| 보안 | 모든 SQL은 파라미터 바인딩(SQL 인젝션 방지), 템플릿 자동 이스케이프(XSS 방지) |

## 폴더 구조

```
address_book/
├── app.py              # 앱 팩토리 create_app(), 라우트(목록/등록/수정/삭제), 입력 검증
├── db.py               # DB 연결·종료, init-db 명령, 연락처 조회·등록·수정·삭제·검색 함수
├── schema.sql          # contacts 테이블 정의
├── templates/
│   ├── base.html       # 공통 레이아웃 (상단 바, 안내 메시지)
│   ├── index.html      # 목록 + 검색
│   └── form.html       # 등록·수정 공용 폼
├── static/
│   └── style.css       # 화면 디자인 (외부 라이브러리 없음, 반응형)
├── tests/
│   ├── conftest.py     # 테스트 준비물 (임시 DB를 쓰는 앱, 테스트 클라이언트)
│   └── test_app.py     # 기능·검증·보안 테스트
├── instance/           # DB 파일이 생기는 곳 (자동 생성, git 제외)
├── pytest.ini          # pytest 설정
├── requirements.txt    # 필요한 패키지 목록
├── CLAUDE.md           # Claude Code용 프로젝트 안내
└── README.md
```

## 준비물

- **Python 3.10 이상** (3.13에서 확인)
  - 설치 확인: Windows `python --version` / Mac `python3 --version`
  - 없으면 https://www.python.org/downloads/ 에서 설치합니다. Windows는 설치 첫 화면에서 **"Add python.exe to PATH"를 체크**하세요.
- 터미널: Windows는 **PowerShell**, Mac은 **터미널(Terminal)** 앱

## 설치 방법

### 1. 프로젝트 폴더로 이동

```bash
cd address_book
```

### 2. 가상환경 만들기 (최초 1회)

가상환경은 이 프로젝트 전용 파이썬 패키지 공간입니다. 다른 프로젝트와 패키지 버전이 섞이지 않게 해 줍니다.

**Windows (PowerShell)**
```powershell
python -m venv .venv
```

**Mac**
```bash
python3 -m venv .venv
```

### 3. 가상환경 켜기 (터미널을 새로 열 때마다)

**Windows (PowerShell)**
```powershell
.\.venv\Scripts\Activate.ps1
```
> "이 시스템에서 스크립트를 실행할 수 없으므로…" 오류가 나면 아래 명령을 한 번 실행한 뒤 다시 시도하세요.
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

**Mac**
```bash
source .venv/bin/activate
```

켜지면 프롬프트 앞에 `(.venv)`가 붙습니다. 끌 때는 `deactivate`를 입력합니다.

### 4. 패키지 설치 (최초 1회)

가상환경이 켜진 상태에서 실행합니다. (Windows·Mac 공통)

```bash
pip install -r requirements.txt
```

## DB 초기화 (최초 1회)

테이블을 만듭니다. (Windows·Mac 공통, 가상환경이 켜진 상태에서)

```bash
flask --app app init-db
```

`DB 초기화 완료: .../instance/addressbook.db`가 출력되면 성공입니다.
여러 번 실행해도 기존 데이터는 지워지지 않습니다.

> 이 단계를 건너뛰고 실행하면 목록 화면에서 `no such table: contacts` 오류가 납니다.

## 실행 방법

(Windows·Mac 공통, 가상환경이 켜진 상태에서)

```bash
flask --app app run --debug
```

브라우저에서 **http://127.0.0.1:5000** 을 엽니다. 서버를 끄려면 터미널에서 `Ctrl + C`를 누릅니다.

- `--debug`: 코드를 고치면 서버가 자동으로 다시 시작되고, 오류가 나면 자세한 화면이 나옵니다. **개발할 때만** 사용하세요.
- `python app.py`(Mac은 `python3 app.py`)로 실행해도 같습니다.
- 5000번 포트가 이미 쓰이고 있으면(특히 Mac의 AirPlay 수신 기능) 다른 포트를 지정하세요: `flask --app app run --debug --port 5001`

## 테스트 방법

(Windows·Mac 공통, 가상환경이 켜진 상태에서)

```bash
pytest -v
```

- 테스트는 테스트마다 새로 만드는 **임시 DB**를 사용하므로 실제 `instance/addressbook.db`는 바뀌지 않습니다.
- 확인하는 내용: 목록·등록·수정·삭제, 이름·전화번호 검색, 입력 검증, 없는 연락처 404, 삭제는 POST만 허용, SQL 인젝션(`' OR '1'='1`) 방어, XSS(`<script>`) 이스케이프

마지막 줄에 `28 passed`처럼 나오면 모두 통과한 것입니다.

## 처음부터 끝까지 한 번에 (요약)

**Windows (PowerShell)**
```powershell
cd address_book
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app app init-db
flask --app app run --debug
```

**Mac**
```bash
cd address_book
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app init-db
flask --app app run --debug
```

## 참고

- 데이터를 모두 지우고 새로 시작하려면 서버를 끄고 `instance/addressbook.db` 파일을 삭제한 뒤 `flask --app app init-db`를 다시 실행합니다.
- 비밀키: 개발용 기본값(`dev`)이 들어 있습니다. 실제로 배포한다면 환경변수 `SECRET_KEY`에 임의의 긴 문자열을 설정하고 `--debug` 없이 실행하세요.
