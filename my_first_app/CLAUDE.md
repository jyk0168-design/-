# CLAUDE.md

이 파일은 이 저장소에서 작업할 때 Claude Code가 참고하는 안내서입니다.

## 프로젝트 개요

비밀번호의 보안성(강도)을 검사하는 파이썬 애플리케이션입니다.
길이, 문자 종류(대문자/소문자/숫자/특수문자) 조합, 흔한 비밀번호 여부 등을 평가합니다.

## 디렉터리 구조

```
my_first_app/
├── .venv/          # 가상환경 (Python 3.13)
├── src/            # 애플리케이션 소스 코드
│   └── __init__.py
├── tests/          # 테스트 코드
│   └── __init__.py
├── CLAUDE.md
└── .gitignore
```

## 개발 환경

- Python 3.13, 가상환경은 `.venv/`
- 가상환경 활성화 (Windows PowerShell): `.venv\Scripts\Activate.ps1`
- 테스트 실행: `python -m pytest tests/`

## 코딩 규칙

- PEP 8 스타일을 따르고, 함수에는 타입 힌트를 붙인다.
- 새 기능을 추가하면 `tests/`에 대응하는 테스트를 함께 작성한다.
- 실제 비밀번호를 로그로 출력하거나 파일에 저장하지 않는다.
