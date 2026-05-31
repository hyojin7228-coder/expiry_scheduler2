"""
캘린더 화면 - 유통기한 마감일 표시 (화이트 테마 + 날짜 클릭 상세)
"""

import tkinter as tk
from datetime import date
import calendar
from typing import Callable, Optional, List

from ..core.database import Database, Product, Category
from .theme import F, PAD, HEADER_H

# ── 로컬 색상 (화이트 테마) ─────────────────────────────────────
CAL_BG        = "#FFFFFF"
CAL_BORDER    = "#E5E5EA"
CAL_TEXT      = "#1C1C1E"
CAL_MUTED     = "#8E8E93"
CAL_WEEKEND   = "#555555"
CAL_TODAY_BG  = "#FF3B30"
CAL_TODAY_FG  = "#FFFFFF"
CAL_SEL_BG    = "#E5E5EA"
CAL_DOT       = "#8E8E93"
CAL_DETAIL_BG = "#F9F9F9"
CAL_DIVIDER   = "#E5E5EA"

CATEGORY_ORDER = [Category.FOOD, Category.MEDICINE, Category.COSMETIC, Category.OTHER]
CATEGORY_LABELS = {
    Category.FOOD: "식품", Category.MEDICINE: "의약품",
    Category.COSMETIC: "화장품", Category.OTHER: "기타",
}
KOR_DAYS = ["일", "월", "화", "수", "목", "금", "토"]

# 캘린더 셀 고정 크기 — 6주분 높이를 항상 확보
CELL_W, CELL_H = 44, 50
CELL_PX, CELL_PY = 3, 3
# 달력 상단 고정 높이: nav(month) + dow header + 6주 그리드
NAV_H   = 52   # month nav 영역
DOW_H   = 28   # 요일 헤더 영역
GRID_H  = 6 * (CELL_H + CELL_PY * 2)   # 항상 6행 확보
CAL_FIXED_H = NAV_H + DOW_H + GRID_H   # ≈ 440


class CalendarScreen(tk.Frame):

    def __init__(self, parent, db: Database, on_back: Callable, **kwargs):
        super().__init__(parent, bg=CAL_BG, **kwargs)
        self.db = db
        self.on_back = on_back

        today = date.today()
        self._year   = today.year
        self._month  = today.month
        self._today  = today
        self._selected: Optional[date] = None
        self._expiry_map: dict = {}

        self._load_products()
        self._build_ui()

    # ── Data ─────────────────────────────────────────────────────────

    def _load_products(self):
        self._expiry_map = {}
        for p in self.db.get_all_products():
            self._expiry_map.setdefault(p.expiry_date, []).append(p)

    # ── Build ─────────────────────────────────────────────────────────

    def _build_ui(self):
        # 상단 앱 헤더
        header = tk.Frame(self, bg=CAL_BG, height=HEADER_H,
                          highlightbackground=CAL_DIVIDER, highlightthickness=1)
        header.pack(fill="x")
        header.pack_propagate(False)

        back_btn = tk.Label(header, text="목록 보기", bg=CAL_BG,
                            fg=CAL_MUTED, font=F(12), cursor="hand2", padx=PAD)
        back_btn.pack(side="right")
        back_btn.bind("<Button-1>", lambda e: self.on_back())
        back_btn.bind("<Enter>",    lambda e: back_btn.config(fg=CAL_TEXT))
        back_btn.bind("<Leave>",    lambda e: back_btn.config(fg=CAL_MUTED))

        # ── 캘린더 영역: 고정 높이 프레임 ──
        # month nav + dow + 6-week grid 를 항상 같은 높이로 고정
        cal_wrapper = tk.Frame(self, bg=CAL_BG, height=CAL_FIXED_H)
        cal_wrapper.pack(fill="x")
        cal_wrapper.pack_propagate(False)

        self._cal_frame = tk.Frame(cal_wrapper, bg=CAL_BG)
        self._cal_frame.place(relx=0.5, rely=0.55, anchor="center")

        # ── 하단 상세 영역: 고정 높이 (창 높이의 약 1/4) ──
        self._detail_outer = tk.Frame(self, bg=CAL_DETAIL_BG,
                                      highlightbackground=CAL_DIVIDER,
                                      highlightthickness=1,
                                      height=200)
        self._detail_outer.pack(fill="x", side="bottom")
        self._detail_outer.pack_propagate(False)

        self._render_calendar()
        self._render_detail(None)

    # ── Calendar ──────────────────────────────────────────────────────

    def _render_calendar(self):
        for w in self._cal_frame.winfo_children():
            w.destroy()

        # Month nav
        nav = tk.Frame(self._cal_frame, bg=CAL_BG)
        nav.pack(pady=(8, 10))

        def nav_lbl(parent, text, cmd):
            l = tk.Label(parent, text=text, bg=CAL_BG, fg=CAL_MUTED,
                         font=F(22), cursor="hand2")
            l.pack(side="left", padx=8)
            l.bind("<Button-1>", lambda e: cmd())
            l.bind("<Enter>",    lambda e: l.config(fg=CAL_TEXT))
            l.bind("<Leave>",    lambda e: l.config(fg=CAL_MUTED))

        nav_lbl(nav, "‹", lambda: self._change_month(-1))
        tk.Label(nav, text=f"{self._year}년 {self._month:02d}월",
                 bg=CAL_BG, fg=CAL_TEXT, font=F(17, "bold"),
                 width=13, anchor="center").pack(side="left")
        nav_lbl(nav, "›", lambda: self._change_month(1))

        # 요일 헤더 + 날짜 — 동일 그리드·동일 셀 너비(픽셀)로 정렬
        cal_body = tk.Frame(self._cal_frame, bg=CAL_BG)
        cal_body.pack()
        for c in range(7):
            cal_body.grid_columnconfigure(c, minsize=CELL_W, uniform="cal_col")

        for i, d in enumerate(KOR_DAYS):
            color = CAL_WEEKEND if i in (0, 6) else CAL_MUTED
            dow_cell = tk.Frame(cal_body, bg=CAL_BG, width=CELL_W, height=DOW_H)
            dow_cell.grid(row=0, column=i, padx=CELL_PX, pady=(0, 6))
            dow_cell.pack_propagate(False)
            tk.Label(dow_cell, text=d, bg=CAL_BG, fg=color,
                     font=F(10), anchor="center").place(relx=0.5, rely=0.5, anchor="center")

        weeks = calendar.monthcalendar(self._year, self._month)
        # 6행 보장: 부족하면 빈 주 추가
        while len(weeks) < 6:
            weeks.append([0] * 7)

        for row_i, week in enumerate(weeks):
            for col_i, day in enumerate(week):
                cell = tk.Frame(cal_body, bg=CAL_BG,
                                width=CELL_W, height=CELL_H)
                cell.grid(row=row_i + 1, column=col_i,
                          padx=CELL_PX, pady=CELL_PY)
                cell.pack_propagate(False)

                if day == 0:
                    continue

                cur = date(self._year, self._month, day)
                is_today = cur == self._today
                is_sel   = cur == self._selected
                is_exp   = cur in self._expiry_map
                is_wkend = col_i in (0, 6)

                if is_today:
                    num_bg, num_fg = CAL_TODAY_BG, CAL_TODAY_FG
                elif is_sel:
                    num_bg, num_fg = CAL_SEL_BG, CAL_TEXT
                else:
                    num_bg = CAL_BG
                    num_fg = CAL_WEEKEND if is_wkend else CAL_TEXT

                if is_today or is_sel:
                    circle = tk.Frame(cell, bg=num_bg, width=34, height=34)
                    circle.place(relx=0.5, y=3, anchor="n")

                num_lbl = tk.Label(cell, text=str(day), bg=num_bg, fg=num_fg,
                                   font=F(13, "bold" if is_today else "normal"),
                                   anchor="center")
                num_lbl.place(relx=0.5, y=3, anchor="n")

                if is_exp:
                    dot_bg = num_bg if (is_today or is_sel) else CAL_BG
                    tk.Label(cell, text="●", bg=dot_bg, fg=CAL_DOT,
                             font=F(5)).place(relx=0.5, y=38, anchor="n")

                for w in [cell, num_lbl]:
                    w.bind("<Button-1>",
                           lambda e, d=cur: self._on_date_click(d))
                    w.config(cursor="hand2")

    # ── Detail panel ──────────────────────────────────────────────────

    def _render_detail(self, sel: Optional[date]):
        for w in self._detail_outer.winfo_children():
            w.destroy()

        if sel is None:
            return

        # 날짜 헤더 텍스트
        dow_idx  = (sel.weekday() + 1) % 7
        date_str = f"{sel.month}월 {sel.day}일 {KOR_DAYS[dow_idx]}요일"

        hdr = tk.Frame(self._detail_outer, bg=CAL_DETAIL_BG)
        hdr.pack(fill="x", padx=PAD, pady=(12, 8))
        tk.Label(hdr, text=date_str, bg=CAL_DETAIL_BG, fg=CAL_TEXT,
                 font=F(13, "bold")).pack(side="left")

        tk.Frame(self._detail_outer, bg=CAL_DIVIDER, height=1).pack(fill="x")

        products_on_day = self._expiry_map.get(sel, [])

        if not products_on_day:
            tk.Label(self._detail_outer, text="마감 제품 없음",
                     bg=CAL_DETAIL_BG, fg=CAL_MUTED, font=F(11)
                     ).pack(pady=10)
            return

        def sort_key(p: Product):
            ci = CATEGORY_ORDER.index(p.category) if p.category in CATEGORY_ORDER else 99
            return (ci, p.name)

        sorted_p = sorted(products_on_day, key=sort_key)

        # 스크롤 캔버스
        canvas = tk.Canvas(self._detail_outer, bg=CAL_DETAIL_BG,
                           highlightthickness=0)
        sb = tk.Scrollbar(self._detail_outer, orient="vertical",
                          command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=CAL_DETAIL_BG)
        win   = canvas.create_window((0, 0), window=inner, anchor="nw")

        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
        inner.bind("<Configure>",
                   lambda e: canvas.configure(
                       scrollregion=canvas.bbox("all")))

        for p in sorted_p:
            row = tk.Frame(inner, bg=CAL_DETAIL_BG)
            row.pack(fill="x", padx=PAD, pady=5)
            tk.Label(row, text=p.name, bg=CAL_DETAIL_BG, fg=CAL_TEXT,
                     font=F(12)).pack(side="left")
            tk.Label(row, text=f"  {CATEGORY_LABELS.get(p.category, '기타')}",
                     bg=CAL_DETAIL_BG, fg=CAL_MUTED, font=F(11)).pack(side="left")

    # ── Interaction ───────────────────────────────────────────────────

    def _on_date_click(self, d: date):
        self._selected = d
        self._render_calendar()
        self._render_detail(d)

    def _change_month(self, delta: int):
        m, y = self._month + delta, self._year
        if m > 12: m, y = 1,  y + 1
        if m < 1:  m, y = 12, y - 1
        self._year, self._month = y, m
        self._selected = None
        self._load_products()
        self._render_calendar()
        self._render_detail(None)
