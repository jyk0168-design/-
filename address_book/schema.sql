-- 주소록 테이블 정의
-- IF NOT EXISTS: 이미 테이블이 있으면 건너뛰므로 여러 번 실행해도 기존 데이터가 지워지지 않는다.
CREATE TABLE IF NOT EXISTS contacts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,  -- 자동 증가 기본키
    name       TEXT NOT NULL,                      -- 이름 (필수)
    phone      TEXT NOT NULL,                      -- 전화번호 (필수)
    email      TEXT,                               -- 이메일 (선택)
    address    TEXT,                               -- 주소 (선택)
    memo       TEXT,                               -- 메모 (선택)
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))  -- 등록 시각 (자동 기록)
);

-- 이름순 정렬·검색을 빠르게 하기 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts (name);
