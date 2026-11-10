# 주소록 웹 애플리케이션

## 프로젝트 목적
Python Flask + SQLite로 만드는 주소록 관리 웹앱. 대학 4학년 학생이 단계별로 따라 할 수 있도록
파일 수는 적게, 구조는 실무형(앱 팩토리, DB 모듈 분리, 템플릿 상속, pytest)으로 유지한다.

- 항목: 이름(필수), 전화번호(필수), 이메일, 주소, 메모, 등록 시각(created_at, 자동)
- 기능: 목록, 등록, 수정, 삭제(POST만), 이름·전화번호 검색, 서버 입력 검증
- DB: 별도 서버 없이 `instance/addressbook.db` 파일 하나에 저장 (파이썬 내장 sqlite3, ORM 없음)

## 폴더 구조
```
address_book/
├── app.py              # create_app(), 라우트, 입력 검증(validate), 폼 처리 도우미
├── db.py               # get_db/close_db, init-db 명령, list/get/create/update/delete_contact (SQL은 여기에만)
├── schema.sql          # contacts 테이블 정의 (CREATE TABLE IF NOT EXISTS)
├── templates/          # base.html(공통 레이아웃), index.html(목록·검색), form.html(등록·수정 공용)
├── static/style.css    # 디자인 (외부 CSS 라이브러리 없음, 640px 이하 반응형)
├── tests/              # conftest.py(임시 DB fixture), test_app.py
├── instance/           # DB 파일 위치 (자동 생성, git 제외)
├── pytest.ini          # pythonpath = . , testpaths = tests
├── requirements.txt
└── README.md           # 학생용 설치·실행 안내 (Windows/Mac)
```

## URL
| URL | 메서드 | 설명 |
|---|---|---|
| `/` , `/?q=검색어` | GET | 목록·검색 |
| `/add` | GET, POST | 등록 |
| `/edit/<id>` | GET, POST | 수정 (없는 id → 404) |
| `/delete/<id>` | POST만 | 삭제 (GET → 405) |

## 실행 명령 (Windows PowerShell 기준, Mac은 README 참고)
```powershell
.\.venv\Scripts\Activate.ps1          # 가상환경 활성화
pip install -r requirements.txt       # 의존성 설치
flask --app app init-db               # DB 초기화 (최초 1회)
flask --app app run --debug           # 개발 서버 실행 → http://127.0.0.1:5000
```

## 테스트 명령
```powershell
pytest -v
```
- 테스트는 `tmp_path` 임시 DB를 쓴다. 실제 `instance/addressbook.db`를 쓰는 테스트를 만들지 않는다.
- 기능을 바꾸면 `tests/test_app.py`에 테스트를 추가하고 전부 통과하는지 확인한다.

## 코딩 규칙
- 주석과 docstring은 **한글**로 작성한다.
- SQL은 **반드시 파라미터 바인딩(`?`)** 을 사용한다. f-string·`%`·`+`로 SQL 문자열에 값을 넣지 않는다.
  - 좋음: `db.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))`
  - 나쁨: `db.execute(f"SELECT * FROM contacts WHERE id = {contact_id}")`
  - LIKE 검색은 `_like_contains()`로 `%`, `_`를 이스케이프하고 `ESCAPE '\'`와 함께 쓴다.
- SQL 쿼리는 `db.py`에만 두고, 라우트(`app.py`)는 db 함수만 호출한다.
- 데이터를 바꾸는 요청(등록·수정·삭제)은 POST로 처리하고, 처리 후 redirect한다(PRG 패턴).
- 입력 검증은 서버(`validate()`)에서 반드시 한다. 브라우저 검사(required, maxlength)는 보조일 뿐이다.
- 템플릿에서 `|safe`, `Markup()`을 쓰지 않는다. JS 안에 사용자 값을 넣어야 하면 `|tojson`을 쓴다.
- 새 패키지를 설치하면 `pip freeze > requirements.txt`로 갱신한다.
