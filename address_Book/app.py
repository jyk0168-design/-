"""주소록 웹 애플리케이션의 진입점.

Flask 앱을 만드는 앱 팩토리(create_app)와 URL별 처리 함수(라우트)를 둔다.
"""
import os
import re

from flask import Flask, abort, flash, redirect, render_template, request, url_for

import db

# 폼에서 받는 입력 항목 이름
FIELDS = ("name", "phone", "email", "address", "memo")


def read_form():
    """요청에서 입력값을 읽어 앞뒤 공백을 제거한 dict로 돌려준다."""
    return {key: request.form.get(key, "").strip() for key in FIELDS}


# 전화번호: 숫자로 시작·끝나고, 중간에 하이픈 하나씩 허용 (예: 010-1234-5678, 01012345678)
# \d 대신 [0-9]: \d는 아라비아 숫자 외 다른 나라 숫자 문자까지 허용하기 때문
PHONE_RE = re.compile(r"[0-9]+(-[0-9]+)*")
# 이메일: '무엇@무엇.무엇' 형태이고 공백이 없을 것 (실무에서 흔히 쓰는 느슨한 검사)
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def validate(form):
    """입력값을 검사해 {항목 이름: 오류 메시지} dict를 돌려준다. 문제가 없으면 빈 dict.

    브라우저의 required, maxlength는 개발자 도구로 쉽게 우회할 수 있으므로
    반드시 서버에서 다시 검사한다.
    """
    errors = {}

    name = form["name"]
    if not name:
        errors["name"] = "이름을 입력해 주세요."
    elif len(name) > 30:
        errors["name"] = f"이름은 30자 이하로 입력해 주세요. (현재 {len(name)}자)"

    phone = form["phone"]
    digit_count = sum(ch.isdigit() for ch in phone)
    if not phone:
        errors["phone"] = "전화번호를 입력해 주세요."
    elif not PHONE_RE.fullmatch(phone):
        errors["phone"] = (
            "전화번호는 숫자와 하이픈(-)만 쓸 수 있고, 하이픈은 숫자 사이에 하나씩만 넣어 주세요."
            " 예) 010-1234-5678"
        )
    elif not 8 <= digit_count <= 11:
        errors["phone"] = "전화번호 자릿수를 확인해 주세요. (숫자 8~11자리) 예) 010-1234-5678"

    email = form["email"]
    if email and (len(email) > 254 or not EMAIL_RE.fullmatch(email)):
        errors["email"] = "이메일 형식이 올바르지 않습니다. 예) hong@example.com"

    # 폼의 maxlength와 같은 기준으로 서버에서도 길이를 제한
    if len(form["address"]) > 200:
        errors["address"] = "주소는 200자 이하로 입력해 주세요."
    if len(form["memo"]) > 1000:
        errors["memo"] = "메모는 1000자 이하로 입력해 주세요."

    return errors


def to_db_values(form):
    """DB에 넣을 값으로 바꾼다: 비어 있는 선택 항목은 None(NULL)으로."""
    return {key: (form[key] or None) for key in FIELDS}


def get_contact_or_404(contact_id):
    """연락처를 찾고, 없으면 404 오류 화면을 보낸다."""
    contact = db.get_contact(contact_id)
    if contact is None:
        abort(404)
    return contact


def create_app(test_config=None):
    """Flask 앱 객체를 만들어 돌려준다 (앱 팩토리 패턴).

    앱을 함수 안에서 만들면 테스트할 때 test_config로
    임시 DB 경로 같은 설정을 바꿔 넣을 수 있어 실무에서 많이 쓴다.
    """
    # instance_relative_config=True: instance/ 폴더를 앱 전용 데이터 폴더로 사용
    app = Flask(__name__, instance_relative_config=True)

    # 기본 설정
    app.config.from_mapping(
        # flash 메시지(세션)를 암호화하는 비밀키.
        # 실제 서비스에서는 환경변수 SECRET_KEY에 임의의 긴 문자열을 넣어 사용한다.
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        # DB 파일 위치: instance/addressbook.db
        DATABASE=os.path.join(app.instance_path, "addressbook.db"),
    )
    if test_config is not None:
        # 테스트용 설정이 주어지면 기본 설정을 덮어쓴다
        app.config.update(test_config)

    # instance/ 폴더가 없으면 만든다 (DB 파일을 저장할 곳)
    os.makedirs(app.instance_path, exist_ok=True)

    # DB 연결 정리와 init-db 명령을 앱에 등록
    db.init_app(app)

    @app.route("/")
    def index():
        """목록 페이지: 연락처를 이름 가나다순으로 보여 준다.

        주소에 ?q=검색어 가 있으면 이름·전화번호 검색 결과만 보여 준다.
        """
        q = request.args.get("q", "").strip()
        contacts = db.list_contacts(q)
        return render_template("index.html", contacts=contacts, q=q)

    @app.route("/add", methods=["GET", "POST"])
    def add():
        """등록 페이지: GET이면 빈 폼, POST면 저장 후 목록으로 이동."""
        if request.method == "POST":
            form = read_form()
            errors = validate(form)
            if errors:
                # 오류가 있으면 입력했던 값을 그대로 채워 폼을 다시 보여 준다
                return render_template("form.html", form=form, errors=errors), 400

            db.create_contact(**to_db_values(form))
            flash("연락처가 등록되었습니다")
            # PRG 패턴: 저장 후 목록으로 redirect (새로고침해도 중복 저장 안 됨)
            return redirect(url_for("index"))

        # GET: 빈 폼 표시
        return render_template("form.html", form={}, errors={})

    @app.route("/edit/<int:contact_id>", methods=["GET", "POST"])
    def edit(contact_id):
        """수정 페이지: GET이면 기존 값이 채워진 폼, POST면 갱신 후 목록으로 이동.

        <int:contact_id>: 주소의 숫자 부분을 정수로 받는다 (/edit/abc는 자동으로 404).
        """
        contact = get_contact_or_404(contact_id)

        if request.method == "POST":
            form = read_form()
            errors = validate(form)
            if errors:
                return render_template(
                    "form.html", form=form, errors=errors, contact=contact
                ), 400

            db.update_contact(contact_id, **to_db_values(form))
            flash("수정되었습니다")
            return redirect(url_for("index"))

        # GET: DB 값으로 폼을 채운다 (NULL은 빈칸으로)
        form = {key: contact[key] or "" for key in FIELDS}
        return render_template("form.html", form=form, errors={}, contact=contact)

    # methods=["POST"]만 허용: 주소창이나 링크(GET)로는 삭제할 수 없다 (405 오류)
    @app.route("/delete/<int:contact_id>", methods=["POST"])
    def delete(contact_id):
        """삭제: 연락처를 지우고 목록으로 이동."""
        get_contact_or_404(contact_id)
        db.delete_contact(contact_id)
        flash("삭제되었습니다")
        return redirect(url_for("index"))

    return app


# `flask --app app run` 명령이 이 모듈에서 찾아 쓸 앱 객체
app = create_app()


if __name__ == "__main__":
    # `python app.py`로 직접 실행할 때: debug 모드로 개발 서버를 띄운다.
    # debug 모드에서는 코드를 고치면 서버가 자동으로 다시 시작되고,
    # 오류가 나면 브라우저에 자세한 오류 화면이 나온다. (개발할 때만 사용!)
    app.run(debug=True)
