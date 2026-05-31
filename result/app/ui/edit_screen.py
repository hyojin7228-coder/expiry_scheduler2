"""
등록 제품 수정 화면
"""

import tkinter as tk
from typing import Callable

from ..core.database import Database, Product
from .theme import *
from .widgets import ScrollableFrame, RoundedPanel
from .product_form import ProductFormMixin


class EditProductScreen(tk.Frame, ProductFormMixin):
    def __init__(self, parent, db: Database, product: Product,
                 on_done: Callable, on_cancel: Callable, **kwargs):
        super().__init__(parent, bg=BG_MAIN, **kwargs)
        self.db = db
        self.product = product
        self.on_done = on_done
        self.on_cancel = on_cancel
        self._init_form_vars(product)
        self._build_ui()

    def _build_ui(self):
        hdr = tk.Frame(self, bg=BG_HEADER, height=HEADER_H)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        back = tk.Label(hdr, text="←", bg=BG_HEADER, fg=TEXT_SECONDARY,
                        font=F(16), cursor="hand2", padx=PAD)
        back.pack(side="left")
        back.bind("<Button-1>", lambda e: self.on_cancel())
        back.bind("<Enter>", lambda e: back.config(fg=TEXT_PRIMARY))
        back.bind("<Leave>", lambda e: back.config(fg=TEXT_SECONDARY))

        tk.Label(hdr, text="제품 수정", bg=BG_HEADER, fg=TEXT_PRIMARY,
                 font=F(14, "bold")).pack(side="left", padx=4)

        scroll = ScrollableFrame(self, bg=BG_MAIN)
        scroll.pack(fill="both", expand=True)
        form = scroll.inner

        tk.Label(form, text="제품 정보 수정", bg=BG_MAIN, fg=TEXT_PRIMARY,
                 font=F(15, "bold")).pack(anchor="w", padx=PAD, pady=(10, 2))
        tk.Label(
            form,
            text=f"등록일 {self.product.registered_date.strftime('%Y-%m-%d')} · 유통기한·제품명·카테고리·메모 수정",
            bg=BG_MAIN, fg=TEXT_SECONDARY, font=F(9),
        ).pack(anchor="w", padx=PAD, pady=(0, 6))

        self._field(form, "제품명 *", self._product_name)
        self._field(form, "유통기한 * (YYYY-MM-DD)", self._expiry_date)
        self._build_category_row(form)
        self._field(form, "메모 (선택)", self._notes)

        self._action_btn(form, "💾  저장하기", ACCENT_PRIMARY, TEXT_ON_COLOR,
                         self._save, pady=5, font=F(13, "bold"))
        self._action_btn(form, "취소", BG_SECTION, TEXT_SECONDARY,
                         self.on_cancel, pady=4, font=F(11), last=True)

    def _action_btn(self, parent, text, bg, fg, command, pady=8, font=None, last=False):
        wrap = tk.Frame(parent, bg=BG_MAIN)
        wrap.pack(fill="x", padx=PAD, pady=(10 if text.startswith("💾") else 0, 16 if last else 4))
        panel = RoundedPanel(wrap, radius=CARD_RADIUS, bg=bg, border_width=0,
                             container_bg=BG_MAIN)
        panel.pack(fill="x")
        lbl = tk.Label(panel.inner, text=text, bg=bg, fg=fg,
                       font=font or F(13, "bold"), pady=pady, cursor="hand2")
        lbl.pack(fill="x")
        lbl.bind("<Button-1>", lambda e: command())
        if bg == ACCENT_PRIMARY:
            lbl.bind("<Enter>", lambda e: lbl.config(bg="#E0003A"))
            lbl.bind("<Leave>", lambda e: lbl.config(bg=ACCENT_PRIMARY))

    def _save(self):
        parsed = self._parse_form()
        if not parsed:
            return
        name, exp_date, category, notes_val = parsed

        updated = Product(
            id=self.product.id,
            name=name,
            category=category,
            registered_date=self.product.registered_date,
            expiry_date=exp_date,
            image_path=self.product.image_path,
            notes=notes_val,
        )
        self.db.update_product(updated)
        self.on_done()
