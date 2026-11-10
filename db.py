"""데이터베이스 관련 코드를 모아 둔 모듈.

파이썬 기본 내장 sqlite3 모듈만 사용한다 (추가 설치 불필요).
SQL 쿼리는 이 파일에만 두고, app.py는 여기 함수만 불러 쓴다.
"""
import sqlite3

import click
from flask import current_app, g


def get_db():
    """현재 요청에서 사용할 DB 연결을 돌려준다.

    한 요청 안에서는 연결을 하나만 만들어 g(요청별 저장 공간)에 보관하고 재사용한다.
    """
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        # 조회 결과를 row["name"]처럼 컬럼 이름으로 꺼낼 수 있게 설정
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    """요청이 끝나면 DB 연결을 닫는다 (Flask가 자동 호출)."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """schema.sql을 실행해 테이블을 만든다."""
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))


def _like_contains(text):
    """LIKE '포함' 검색용 패턴을 만든다: 앞뒤에 %를 붙인다.

    사용자가 입력한 %, _ 는 LIKE에서 '아무 글자'라는 특수 의미가 있으므로
    앞에 \\ 를 붙여 일반 글자로 바꾼다 (쿼리의 ESCAPE '\\' 와 짝).
    """
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def list_contacts(q=None):
    """연락처를 이름 가나다순으로 돌려준다 (이름이 같으면 먼저 등록한 순).

    q가 있으면 이름 또는 전화번호에 q가 포함된 연락처만 돌려준다.
    전화번호는 하이픈을 빼고 비교하므로 '01012' 로 '010-1234-...' 를 찾을 수 있다.
    """
    if not q:
        return get_db().execute(
            "SELECT id, name, phone, email, address, memo, created_at"
            " FROM contacts ORDER BY name, id"
        ).fetchall()

    # 검색어도 하이픈을 뺀다. 하이픈만 입력해 비게 되면 None을 넘기는데,
    # SQL에서 'LIKE NULL'은 참이 되지 않으므로 전화번호 조건은 무시된다.
    phone_q = q.replace("-", "")
    phone_pattern = _like_contains(phone_q) if phone_q else None

    # 검색어는 SQL 문자열에 넣지 않고 ? 자리에 파라미터로 넘긴다
    return get_db().execute(
        "SELECT id, name, phone, email, address, memo, created_at"
        " FROM contacts"
        " WHERE name LIKE ? ESCAPE '\\'"
        "    OR REPLACE(phone, '-', '') LIKE ? ESCAPE '\\'"
        " ORDER BY name, id",
        (_like_contains(q), phone_pattern),
    ).fetchall()


def create_contact(name, phone, email=None, address=None, memo=None):
    """연락처 한 건을 저장하고 새 id를 돌려준다.

    값은 반드시 ? 자리에 파라미터로 넘긴다 (SQL 인젝션 방지).
    """
    db = get_db()
    cur = db.execute(
        "INSERT INTO contacts (name, phone, email, address, memo)"
        " VALUES (?, ?, ?, ?, ?)",
        (name, phone, email, address, memo),
    )
    db.commit()  # commit 해야 실제로 파일에 저장된다
    return cur.lastrowid


def get_contact(contact_id):
    """id로 연락처 한 건을 찾는다. 없으면 None을 돌려준다."""
    return get_db().execute(
        "SELECT id, name, phone, email, address, memo, created_at"
        " FROM contacts WHERE id = ?",
        (contact_id,),  # 값이 하나여도 튜플로 넘긴다 (쉼표 주의)
    ).fetchone()


def update_contact(contact_id, name, phone, email=None, address=None, memo=None):
    """연락처 한 건의 값을 바꾼다."""
    db = get_db()
    db.execute(
        "UPDATE contacts SET name = ?, phone = ?, email = ?, address = ?, memo = ?"
        " WHERE id = ?",
        (name, phone, email, address, memo, contact_id),
    )
    db.commit()


def delete_contact(contact_id):
    """연락처 한 건을 지운다."""
    db = get_db()
    db.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    db.commit()


@click.command("init-db")
def init_db_command():
    """`flask --app app init-db` 명령: 테이블을 만든다."""
    init_db()
    click.echo(f"DB 초기화 완료: {current_app.config['DATABASE']}")


def init_app(app):
    """앱에 DB 관련 기능을 등록한다 (create_app에서 호출)."""
    app.teardown_appcontext(close_db)       # 요청이 끝날 때마다 연결 닫기
    app.cli.add_command(init_db_command)    # flask 명령어에 init-db 추가
