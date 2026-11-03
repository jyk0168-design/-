"""주소록 앱 테스트.

실행: 프로젝트 폴더에서 `pytest -v`
fixture(app, client, add_contact)는 tests/conftest.py에 있다.
"""
import os

import pytest

import db


def count_contacts(app):
    """DB에 저장된 연락처 수 (화면이 아니라 DB를 직접 확인할 때 사용)."""
    with app.app_context():
        return len(db.list_contacts())


def page(response):
    """응답 본문을 문자열로."""
    return response.get_data(as_text=True)


# ---------- 0. 테스트 환경 확인 ----------

def test_uses_temporary_db(app):
    """테스트가 실제 DB(instance/addressbook.db)가 아닌 임시 DB를 쓰는지 확인."""
    real_db = os.path.join(app.instance_path, "addressbook.db")
    assert os.path.abspath(app.config["DATABASE"]) != os.path.abspath(real_db)


# ---------- 1. 목록 화면 ----------

def test_index_ok(client):
    """목록 화면이 200으로 응답하고, 비어 있으면 안내 문구가 나온다."""
    response = client.get("/")
    assert response.status_code == 200
    assert "아직 등록된 연락처가 없습니다" in page(response)


# ---------- 2. 등록 ----------

def test_add_shows_in_list(client, add_contact):
    """등록하면 목록으로 이동하고, 목록에 새 연락처와 안내 메시지가 보인다."""
    response = add_contact(name="홍길동", phone="010-1234-5678", email="hong@example.com")
    assert response.status_code == 302                    # 저장 후 redirect
    assert response.headers["Location"] == "/"

    html = page(client.get("/"))
    assert "홍길동" in html
    assert "010-1234-5678" in html
    assert "hong@example.com" in html
    assert "연락처가 등록되었습니다" in html


def test_list_sorted_by_name(client, add_contact):
    """목록은 이름 가나다순."""
    for name in ["홍길동", "강감찬", "이순신"]:
        add_contact(name=name)
    html = page(client.get("/"))
    assert html.index("강감찬") < html.index("이순신") < html.index("홍길동")


# ---------- 3. 수정 ----------

def test_edit_changes_values(app, client, add_contact):
    """수정 화면에 기존 값이 채워져 있고, 저장하면 값이 바뀐다."""
    add_contact(name="홍길동", phone="010-1234-5678")

    form_html = page(client.get("/edit/1"))
    assert 'value="홍길동"' in form_html                  # 기존 값이 폼에 채워짐

    response = client.post(
        "/edit/1",
        data={"name": "홍길동", "phone": "010-9999-8888", "address": "서울시"},
        follow_redirects=True,
    )
    html = page(response)
    assert "수정되었습니다" in html
    assert "010-9999-8888" in html
    assert "010-1234-5678" not in html

    with app.app_context():                                 # DB 값도 직접 확인
        contact = db.get_contact(1)
        assert contact["phone"] == "010-9999-8888"
        assert contact["address"] == "서울시"


# ---------- 4. 삭제 ----------

def test_delete_removes_from_list(app, client, add_contact):
    """삭제하면 목록에서 사라진다."""
    add_contact(name="홍길동")
    add_contact(name="이순신", phone="010-2222-3333")

    response = client.post("/delete/1", follow_redirects=True)
    html = page(response)
    assert "삭제되었습니다" in html
    assert "홍길동" not in html
    assert "이순신" in html                                 # 다른 연락처는 남아 있음
    assert count_contacts(app) == 1


def test_delete_requires_post(app, client, add_contact):
    """GET(주소창, 링크)으로는 삭제할 수 없다 → 405."""
    add_contact()
    assert client.get("/delete/1").status_code == 405
    assert count_contacts(app) == 1


@pytest.mark.parametrize("method, url", [
    ("get", "/edit/999"),
    ("post", "/edit/999"),
    ("post", "/delete/999"),
])
def test_missing_contact_404(client, method, url):
    """없는 id는 404."""
    response = getattr(client, method)(url, data={"name": "a", "phone": "010-1234-5678"})
    assert response.status_code == 404


# ---------- 5. 검색 ----------

def test_search_by_name(client, add_contact):
    """이름 일부로 검색하면 해당 연락처만 나온다."""
    add_contact(name="홍길동", phone="010-1111-1111")
    add_contact(name="홍길순", phone="010-2222-2222")
    add_contact(name="이순신", phone="010-3333-3333")

    html = page(client.get("/?q=홍길"))
    assert "홍길동" in html
    assert "홍길순" in html
    assert "이순신" not in html
    assert "검색 결과: 2건" in html


def test_search_by_phone_ignores_hyphen(client, add_contact):
    """전화번호는 하이픈 없이 검색해도 찾는다."""
    add_contact(name="홍길동", phone="010-1234-5678")
    add_contact(name="이순신", phone="010-9999-0000")

    html = page(client.get("/?q=01012345"))
    assert "홍길동" in html
    assert "이순신" not in html


def test_search_no_result(client, add_contact):
    add_contact(name="홍길동")
    html = page(client.get("/?q=없는사람"))
    assert "검색 결과가 없습니다" in html


# ---------- 6. 입력 검증 ----------

@pytest.mark.parametrize("name, phone, message", [
    ("", "010-1234-5678", "이름을 입력해 주세요"),
    ("   ", "010-1234-5678", "이름을 입력해 주세요"),            # 공백만
    ("가" * 31, "010-1234-5678", "30자 이하"),
    ("홍길동", "", "전화번호를 입력해 주세요"),
    ("홍길동", "010 1234 5678", "숫자와 하이픈"),                 # 공백 포함
    ("홍길동", "010-abcd-5678", "숫자와 하이픈"),                 # 문자 포함
    ("홍길동", "010--1234-5678", "숫자와 하이픈"),                # 하이픈 연속
    ("홍길동", "010-12", "자릿수"),                               # 너무 짧음
], ids=[  # pytest -v 출력에 보일 이름 (한글은 \uXXXX로 깨져 보여서 영어로)
    "empty-name", "blank-name", "name-too-long", "empty-phone",
    "phone-space", "phone-letters", "phone-double-hyphen", "phone-too-short",
])
def test_invalid_input_not_saved(app, add_contact, name, phone, message):
    """이름이 비었거나 전화번호 형식이 틀리면 저장되지 않고 오류 메시지가 나온다."""
    response = add_contact(name=name, phone=phone)
    assert response.status_code == 400
    assert message in page(response)
    assert count_contacts(app) == 0


def test_invalid_email_not_saved(app, add_contact):
    response = add_contact(email="hong-at-example.com")
    assert response.status_code == 400
    assert "이메일 형식" in page(response)
    assert count_contacts(app) == 0


def test_invalid_input_keeps_values(add_contact):
    """검증에 실패해도 입력했던 값은 폼에 남는다."""
    html = page(add_contact(name="홍길동", phone="abc", address="서울시"))
    assert 'value="홍길동"' in html
    assert 'value="abc"' in html
    assert 'value="서울시"' in html


def test_invalid_edit_not_saved(app, client, add_contact):
    """수정할 때도 같은 검증이 적용된다."""
    add_contact(name="홍길동", phone="010-1234-5678")
    response = client.post("/edit/1", data={"name": "", "phone": "010-1234-5678"})
    assert response.status_code == 400
    with app.app_context():
        assert db.get_contact(1)["name"] == "홍길동"         # 원래 값 그대로


# ---------- 7. 보안: SQL 인젝션, XSS ----------

def test_search_sql_injection(client, add_contact):
    """검색어 ' OR '1'='1 로 모든 데이터가 나오면 안 된다.

    문자열을 SQL에 직접 이어 붙였다면 WHERE 조건이 항상 참이 되어 전부 나온다.
    파라미터 바인딩을 쓰면 그 글자 자체를 찾는 검색이 되어 0건이다.
    """
    add_contact(name="홍길동", phone="010-1111-1111")
    add_contact(name="이순신", phone="010-2222-2222")

    response = client.get("/", query_string={"q": "' OR '1'='1"})
    html = page(response)
    assert response.status_code == 200
    assert "홍길동" not in html
    assert "이순신" not in html
    assert "검색 결과가 없습니다" in html


def test_search_like_wildcard_is_literal(client, add_contact):
    """검색어 % 는 '아무 글자'가 아니라 진짜 % 글자로 검색된다."""
    add_contact(name="홍길동")
    html = page(client.get("/", query_string={"q": "%"}))
    assert "홍길동" not in html


def test_sql_injection_in_input_stored_as_text(app, add_contact):
    """입력값에 SQL을 넣어도 글자로 저장될 뿐 테이블은 그대로다."""
    add_contact(name="홍'); DROP TABLE contacts; --")
    with app.app_context():
        contacts = db.list_contacts()
    assert len(contacts) == 1
    assert contacts[0]["name"] == "홍'); DROP TABLE contacts; --"


def test_xss_is_escaped(client, add_contact):
    """이름에 넣은 <script>는 실행되지 않도록 글자로 바뀌어 출력된다."""
    add_contact(name="<script>alert(1)</script>")
    html = page(client.get("/"))
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
