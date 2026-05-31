"""
UI 테마 — 트렌디 다크 + 컬러 블록 (Image 1,2 방향성)
"""

# ── Backgrounds ──────────────────────────────────────────────────
BG_MAIN        = "#141414"   # 전체 배경 (순수 검정보다 약간 따뜻)
BG_CARD        = "#1E1E24"   # 카드
BG_CARD_HOVER  = "#26262E"   # 카드 호버
BG_INPUT       = "#1E1E24"   # 입력창
BG_HEADER      = "#0F0F13"   # 헤더
BG_SECTION     = "#19191F"   # 섹션 구분

# ── Accent ───────────────────────────────────────────────────────
ACCENT_PRIMARY = "#FF3B5C"   # 핫핑크-레드 (Image2 버튼 컬러)
ACCENT_RED     = ACCENT_PRIMARY  # 하위 호환
ACCENT_BLUE    = "#4F8EF7"   # 블루 (Image2 Shower 블록)
ACCENT_ORANGE  = "#FF9500"   # 오렌지 (Image2 Breakfast 블록)
ACCENT_PURPLE  = "#BF6BFF"   # 퍼플 (Image2 Email 블록)
ACCENT_TEAL    = "#2FD8C5"   # 틸 포인트

# ── Status ───────────────────────────────────────────────────────
STATUS_SAFE    = "#30D158"   # 초록
STATUS_WARN    = "#FFD60A"   # 노랑
STATUS_DANGER  = "#FF453A"   # 빨강
STATUS_EXPIRED = "#636366"   # 회색

# ── Category colors (Image1 캘린더 블록 느낌) ───────────────────
CAT_FOOD_COLOR  = "#FF9500"   # 오렌지
CAT_COSM_COLOR  = "#BF6BFF"   # 보라
CAT_MED_COLOR   = "#4F8EF7"   # 블루
CAT_OTHER_COLOR = "#636366"   # 회색

# ── Text ─────────────────────────────────────────────────────────
TEXT_PRIMARY   = "#F2F2F7"
TEXT_SECONDARY = "#8E8E93"
TEXT_MUTED     = "#3A3A3C"
TEXT_ON_COLOR  = "#FFFFFF"

# ── Border ───────────────────────────────────────────────────────
BORDER_COLOR   = "#2C2C2E"
BORDER_LIGHT   = "#38383A"

# ── Fonts ────────────────────────────────────────────────────────
FONT_FAMILY = "Malgun Gothic"

def F(size, weight="normal"):
    return (FONT_FAMILY, size, weight)

FONT_TITLE     = F(20, "bold")
FONT_SUBTITLE  = F(12)
FONT_CARD_NAME = F(13, "bold")
FONT_CARD_SUB  = F(10)
FONT_BADGE     = F(9,  "bold")
FONT_LABEL     = F(11)
FONT_BTN       = F(13, "bold")
FONT_SMALL     = F(9)

# ── Sizes ────────────────────────────────────────────────────────
PAD         = 14
HEADER_H    = 56
CARD_H      = 64    # 카드 높이 (컴팩트)
CARD_RADIUS = 12    # 카드·입력창 모서리
CHIP_RADIUS = 8     # 필터 칩 모서리
