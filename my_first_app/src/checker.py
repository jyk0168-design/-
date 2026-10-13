"""비밀번호를 입력받아 보안 등급을 평가하는 프로그램."""

import os
import secrets
import string
import sys
from getpass import getpass

SPECIAL_CHARS = "!@#$%^&*"
MIN_LENGTH = 8
RECOMMENDED_LENGTH = 12

# ANSI 색상 코드
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def check_rules(password: str) -> list[tuple[str, bool]]:
    """각 검사 규칙의 이름과 충족 여부를 반환한다."""
    return [
        (f"{MIN_LENGTH}자리 이상", len(password) >= MIN_LENGTH),
        (
            "대문자와 소문자 혼합",
            any(c.isupper() for c in password) and any(c.islower() for c in password),
        ),
        ("숫자 포함", any(c.isdigit() for c in password)),
        (f"특수문자({SPECIAL_CHARS}) 포함", any(c in SPECIAL_CHARS for c in password)),
    ]


def get_grade(passed_count: int) -> tuple[str, str]:
    """충족한 규칙 개수에 따라 (등급, 색상)을 반환한다."""
    if passed_count <= 1:
        return "취약", RED
    if passed_count <= 3:
        return "보통", YELLOW
    return "강력", GREEN


def generate_strong_password(length: int = RECOMMENDED_LENGTH) -> str:
    """모든 검사 규칙을 충족하는 무작위 비밀번호를 생성한다."""
    if length < MIN_LENGTH:
        raise ValueError(f"비밀번호 길이는 {MIN_LENGTH} 이상이어야 합니다.")

    # 각 문자 종류를 최소 1개씩 넣어 모든 규칙 충족을 보장
    required = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice(SPECIAL_CHARS),
    ]
    all_chars = string.ascii_letters + string.digits + SPECIAL_CHARS
    rest = [secrets.choice(all_chars) for _ in range(length - len(required))]

    chars = required + rest
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def print_recommendation() -> None:
    """'강력' 등급의 추천 비밀번호를 출력한다."""
    print(f"{BOLD}💡 추천 비밀번호 ({GREEN}강력{RESET}{BOLD} 등급){RESET}")
    print(f"  {GREEN}{generate_strong_password()}{RESET}")
    print()


def print_report(password: str) -> None:
    """검사 결과를 보기 좋게 출력한다."""
    results = check_rules(password)
    passed_count = sum(passed for _, passed in results)
    grade, color = get_grade(passed_count)

    print()
    print(f"{BOLD}🔐 비밀번호 보안 검사 결과{RESET}")
    print("─" * 32)
    for name, passed in results:
        mark = f"{GREEN}✅" if passed else f"{RED}❌"
        print(f"  {mark} {name}{RESET}")
    print("─" * 32)
    print(f"  충족 조건: {passed_count} / {len(results)}")
    print(f"  보안 등급: {color}{BOLD}{grade}{RESET}")
    print()


def main() -> None:
    # Windows 터미널에서 ANSI 색상과 이모지가 제대로 보이도록 설정
    if os.name == "nt":
        os.system("")
    sys.stdout.reconfigure(encoding="utf-8")

    # 입력한 비밀번호가 화면에 보이지 않도록 getpass 사용
    password = getpass("비밀번호를 입력하세요: ")
    print_report(password)
    print_recommendation()


if __name__ == "__main__":
    main()
