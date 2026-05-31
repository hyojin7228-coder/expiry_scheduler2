"""
제품 정보 입력 폼 — 등록·수정 화면 공통
"""

import tkinter as tk
from tkinter import messagebox
from datetime import date, datetime
from typing import Dict, Optional, Tuple

from ..core.database import Product, Category
from .theme import *

CAT_DEFS = [
    ("🍱", "식품",   CAT_FOOD_COLOR),
    ("💄", "화장품", CAT_COSM_COLOR),
    ("💊", "의약품", CAT_MED_COLOR),
    ("📦", "기타",   CAT_OTHER_COLOR),
]

NAME_PLACEHOLDER = "예: 라면 5개입"
EXPIRY_PLACEHOLDER = "예: 2026-12-31"
NOTES_PLACEHOLDER = "비고 사항을 입력하세요"


class ProductFormMixin:
    """제품명·유통기한·카테고리·메모 폼 빌드/검증"""

    def _init_form_vars(self, product: Optional[Product] = None):
        self._product_name = tk.StringVar(value=product.name if product else "")
        self._expiry_date = tk.StringVar(
            value=product.expiry_date.isoformat() if product else ""
        )
        self._category = tk.StringVar(
            value=product.category.value if product else "식품"
        )
        self._notes = tk.StringVar(value=product.notes if product else "")
        self._cat_btns: Dict = {}

    def _field(self, parent, label_text, var, placeholder=""):
        tk.Label(parent, text=label_text, bg=BG_MAIN, fg=TEXT_SECONDARY,
                 font=F(10)).pack(anchor="w", padx=PAD, pady=(6, 2))
        from .widgets import RoundedEntry
        entry = RoundedEntry(parent, textvariable=var, compact=True)
        entry.pack(fill="x", padx=PAD)
        if placeholder and not var.get():
            entry.set_placeholder(placeholder)

    def _build_category_row(self, parent):
        tk.Label(parent, text="카테고리 *", bg=BG_MAIN, fg=TEXT_SECONDARY,
                 font=F(10)).pack(anchor="w", padx=PAD, pady=(6, 3))

        cat_row = tk.Frame(parent, bg=BG_MAIN)
        cat_row.pack(fill="x", padx=PAD)
        self._cat_btns = {}
        for icon, val, color in CAT_DEFS:
            btn = tk.Frame(cat_row, bg=BG_SECTION,
                           highlightbackground=BORDER_COLOR,
                           highlightthickness=1, cursor="hand2")
            btn.pack(side="left", padx=(0, 6))
            tk.Label(btn, text=icon, bg=BG_SECTION, fg=TEXT_PRIMARY,
                     font=F(14)).pack(side="left", padx=(8, 2), pady=5)
            tk.Label(btn, text=val, bg=BG_SECTION, fg=TEXT_SECONDARY,
                     font=F(9)).pack(side="left", padx=(0, 8), pady=5)
            btn.bind("<Button-1>", lambda e, v=val: self._select_cat(v))
            for child in btn.winfo_children():
                child.bind("<Button-1>", lambda e, v=val: self._select_cat(v))
            self._cat_btns[val] = (btn, color)
        self._select_cat(self._category.get())

    def _select_cat(self, val: str):
        self._category.set(val)
        for v, (btn, color) in self._cat_btns.items():
            active = v == val
            bg = color if active else BG_SECTION
            hl = color if active else BORDER_COLOR
            btn.config(bg=bg, highlightbackground=hl, highlightthickness=2 if active else 1)
            for child in btn.winfo_children():
                try:
                    child.config(bg=bg)
                except Exception:
                    pass

    def _parse_form(self) -> Optional[Tuple[str, date, Category, str]]:
        name = self._product_name.get().strip()
        expiry_str = self._expiry_date.get().strip()
        cat_val = self._category.get()

        if not name or name == NAME_PLACEHOLDER:
            messagebox.showerror("입력 오류", "제품명을 입력하세요.")
            return None
        if not expiry_str or expiry_str == EXPIRY_PLACEHOLDER:
            messagebox.showerror("입력 오류", "유통기한을 입력하세요.")
            return None
        try:
            exp_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror(
                "입력 오류",
                "유통기한 형식이 올바르지 않습니다.\n(예: 2026-12-31)",
            )
            return None

        try:
            category = Category(cat_val)
        except ValueError:
            category = Category.OTHER

        notes_val = self._notes.get().strip()
        if notes_val == NOTES_PLACEHOLDER:
            notes_val = ""

        return name, exp_date, category, notes_val
