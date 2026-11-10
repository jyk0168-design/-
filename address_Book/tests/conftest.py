"""pytest 공용 준비물(fixture).

conftest.py에 둔 fixture는 같은 폴더의 모든 테스트 파일에서 이름만 적으면 쓸 수 있다.
"""
import pytest

import db
from app import create_app


@pytest.fixture
def app(tmp_path):
    """테스트 전용 앱: 테스트마다 새 임시 DB 파일을 쓴다.

    tmp_path는 pytest가 테스트마다 만들어 주는 임시 폴더라
    실제 instance/addressbook.db는 전혀 건드리지 않는다.
    """
    app = create_app({
        "TESTING": True,                                 # 오류를 테스트에 그대로 전달
        "DATABASE": str(tmp_path / "test.db"),           # 임시 DB 경로
    })
    with app.app_context():
        db.init_db()                                     # 빈 테이블 생성
    return app


@pytest.fixture
def client(app):
    """브라우저 대신 요청을 보내는 Flask 테스트 클라이언트."""
    return app.test_client()


@pytest.fixture
def add_contact(client):
    """연락처를 등록하는 도우미 함수. 필요한 값만 바꿔 쓸 수 있다."""
    def _add(name="홍길동", phone="010-1234-5678", **others):
        return client.post("/add", data={"name": name, "phone": phone, **others})
    return _add
