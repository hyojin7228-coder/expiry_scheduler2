"""
메인 제품 목록 화면 — 트렌디 리디자인
Image1(구글캘린더 블록) + Image2(다크 타임라인) 방향성
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable

from ..core.database import Database, Product, ExpiryStatus
from .theme import *
from .widgets import ScrollableFrame, FABButton, SectionHeader, RoundedPanel, RoundedChip

FILTER_CATEGORIES = ["전체", "식품", "화장품", "의약품", "기타"]

CAT_COLORS = {
    "식품":  CAT_FOOD_COLOR,
    "화장품": CAT_COSM_COLOR,
    "의약품": CAT_MED_COLOR,
    "기타":  CAT_OTHER_COLOR,
}

STATUS_PILL = {
    ExpiryStatus.SAFE:    (STATUS_SAFE,    "널널"),
    ExpiryStatus.WARNING: (STATUS_WARN,    "애매"),
    ExpiryStatus.DANGER:  (STATUS_DANGER,  "임박"),
    ExpiryStatus.EXPIRED: (STATUS_EXPIRED, "만료"),
}


class ProductCard(tk.Frame):
    """제품 카드 — 둥근 모서리, 탭하여 수정"""

    def __init__(self, parent, product: Product,
                 on_edit: Callable, on_delete: Callable, **kwargs):
        super().__init__(parent, bg=BG_MAIN, **kwargs)
        self.product = product
        self._on_edit = on_edit
        self._on_delete = on_delete

        self.panel = RoundedPanel(
            self, radius=CARD_RADIUS, bg=BG_CARD,
            container_bg=BG_MAIN, fit_content=True,
        )
        self.panel.pack(fill="x")
        self._inner = self.panel.inner
        self._build()
        self._bind_edit_area()

    def _bind_edit_recursive(self, widget):
        if getattr(widget, "_no_edit", False):
            return
        widget.bind("<Button-1>", lambda e: self._on_edit(self.product))
        try:
            widget.config(cursor="hand2")
        except Exception:
            pass
        for child in widget.winfo_children():
            self._bind_edit_recursive(child)

    def _bind_edit_area(self):
        self._bind_edit_recursive(self._mid)

    def _build(self):
        p = self.product
        status_color, status_label = STATUS_PILL[p.status]
        cat_color = CAT_COLORS.get(p.category.value, CAT_OTHER_COLOR)

        left_bar = tk.Frame(self._inner, bg=cat_color, width=40)
        left_bar.pack(side="left", fill="y")
        left_bar.pack_propagate(False)
        left_bar._no_edit = True

        tk.Label(left_bar, text=p.category_icon,
                 bg=cat_color, fg=TEXT_ON_COLOR, font=F(16)).pack(expand=True)

        self._mid = tk.Frame(self._inner, bg=BG_CARD)
        self._mid.pack(side="left", fill="both", expand=True, padx=10, pady=6)

        tk.Label(self._mid, text=p.name, bg=BG_CARD, fg=TEXT_PRIMARY,
                 font=FONT_CARD_NAME, anchor="w").pack(fill="x")

        if p.status == ExpiryStatus.EXPIRED:
            exp_txt = f"{p.expiry_date.strftime('%Y.%m.%d')}  ·  만료됨"
        else:
            exp_txt = f"{p.expiry_date.strftime('%Y.%m.%d')}  ·  {p.days_remaining}일 남음"

        tk.Label(self._mid, text=exp_txt, bg=BG_CARD, fg=TEXT_SECONDARY,
                 font=FONT_CARD_SUB, anchor="w").pack(fill="x", pady=(3, 0))

        tk.Label(self._mid, text=f"등록 {p.registered_date.strftime('%Y.%m.%d')}",
                 bg=BG_CARD, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w").pack(
            fill="x", pady=(1, 0))

        right = tk.Frame(self._inner, bg=BG_CARD)
        right.pack(side="right", fill="y", padx=(0, 8))
        right._no_edit = True

        pill = tk.Label(right, text=status_label,
                        bg=status_color, fg=TEXT_ON_COLOR,
                        font=FONT_BADGE, padx=8, pady=2)
        pill.pack(pady=(8, 4))
        pill._no_edit = True

        btn_row = tk.Frame(right, bg=BG_CARD)
        btn_row.pack()
        btn_row._no_edit = True

        edit_btn = tk.Label(btn_row, text="✎", bg=BG_CARD, fg=TEXT_SECONDARY,
                            font=F(13), cursor="hand2", padx=4)
        edit_btn.pack(side="left")
        edit_btn.bind("<Button-1>", lambda e: self._on_edit(self.product))
        edit_btn.bind("<Enter>", lambda e: edit_btn.config(fg=ACCENT_PRIMARY))
        edit_btn.bind("<Leave>", lambda e: edit_btn.config(fg=TEXT_SECONDARY))

        self._del_btn = tk.Label(btn_row, text="✕", bg=BG_CARD,
                                 fg=TEXT_MUTED, font=F(12), cursor="hand2", padx=4)
        self._del_btn.pack(side="left")
        self._del_btn.bind("<Button-1>", lambda e: self._on_delete(self.product))
        self._del_btn.bind("<Enter>", lambda e: self._del_btn.config(fg=ACCENT_PRIMARY))
        self._del_btn.bind("<Leave>", lambda e: self._del_btn.config(fg=TEXT_MUTED))


class ProductListScreen(tk.Frame):
    """메인 제품 목록 화면"""

    def __init__(self, parent, db: Database, on_add: Callable,
                 on_edit: Callable = None, on_settings: Callable = None,
                 on_calendar: Callable = None, **kwargs):
        super().__init__(parent, bg=BG_MAIN, **kwargs)
        self.db = db
        self.on_add = on_add
        self.on_edit = on_edit
        self.on_settings = on_settings
        self.on_calendar = on_calendar
        self._filter_cat = "전체"
        self._filter_status = "전체"
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        hdr = tk.Frame(self, bg=BG_HEADER, height=HEADER_H)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="⚡", bg=BG_HEADER, fg=ACCENT_PRIMARY,
                 font=F(18)).pack(side="left", padx=(PAD, 4))
        tk.Label(hdr, text="전기실 제품 관리", bg=BG_HEADER, fg=TEXT_PRIMARY,
                 font=F(15, "bold")).pack(side="left")

        gear = tk.Label(hdr, text="⚙", bg=BG_HEADER, fg=TEXT_SECONDARY,
                        font=F(17), cursor="hand2", padx=PAD)
        gear.pack(side="right")
        if self.on_settings:
            gear.bind("<Button-1>", lambda e: self.on_settings())
        gear.bind("<Enter>", lambda e: gear.config(fg=TEXT_PRIMARY))
        gear.bind("<Leave>", lambda e: gear.config(fg=TEXT_SECONDARY))

        # Calendar button
        cal_btn = tk.Label(hdr, text="📅 캘린더", bg=BG_HEADER, fg=TEXT_SECONDARY,
                           font=F(11), cursor="hand2", padx=PAD)
        cal_btn.pack(side="right")
        if self.on_calendar:
            cal_btn.bind("<Button-1>", lambda e: self.on_calendar())
        cal_btn.bind("<Enter>", lambda e: cal_btn.config(fg=TEXT_PRIMARY))
        cal_btn.bind("<Leave>", lambda e: cal_btn.config(fg=TEXT_SECONDARY))

        self.summary_frame = tk.Frame(self, bg=BG_HEADER)
        self.summary_frame.pack(fill="x")

        tk.Frame(self, bg=BORDER_COLOR, height=1).pack(fill="x")

        cat_row = tk.Frame(self, bg=BG_MAIN)
        cat_row.pack(fill="x", padx=PAD, pady=(10, 4))

        tk.Label(cat_row, text="분류", bg=BG_MAIN, fg=TEXT_MUTED,
                 font=F(9)).pack(side="left", padx=(0, 8))

        self._cat_buttons = {}
        for cat in FILTER_CATEGORIES:
            chip = RoundedChip(
                cat_row, text=cat, radius=CHIP_RADIUS,
                command=lambda c=cat: self._set_cat_filter(c),
            )
            chip.config(width=max(len(cat) * 11 + 22, 40), height=30)
            chip.pack(side="left", padx=(0, 5))
            self._cat_buttons[cat] = chip

        st_row = tk.Frame(self, bg=BG_MAIN)
        st_row.pack(fill="x", padx=PAD, pady=(0, 8))

        tk.Label(st_row, text="상태", bg=BG_MAIN, fg=TEXT_MUTED,
                 font=F(9)).pack(side="left", padx=(0, 8))

        self._status_buttons = {}
        status_opts = [
            ("전체",  TEXT_SECONDARY),
            ("널널",  STATUS_SAFE),
            ("애매",  STATUS_WARN),
            ("임박",  STATUS_DANGER),
            ("만료",  STATUS_EXPIRED),
        ]
        for label, color in status_opts:
            chip = RoundedChip(
                st_row, text=label, radius=CHIP_RADIUS,
                fg=color, active_fg=TEXT_ON_COLOR,
                command=lambda l=label: self._set_status_filter(l),
            )
            chip.config(width=max(len(label) * 11 + 22, 40), height=30)
            chip.pack(side="left", padx=(0, 5))
            chip._chip_color = color
            self._status_buttons[label] = chip

        tk.Frame(self, bg=BORDER_COLOR, height=1).pack(fill="x")

        self.scroll = ScrollableFrame(self, bg=BG_MAIN)
        self.scroll.pack(fill="both", expand=True)
        self.list_frame = self.scroll.inner

        self.fab = FABButton(self, command=self.on_add, size=52)
        self.fab.place(relx=1.0, rely=1.0, x=-(PAD + 52), y=-(PAD + 52))

        self._update_filter_ui()

    def _set_cat_filter(self, cat: str):
        self._filter_cat = cat
        self._update_filter_ui()
        self.refresh()

    def _set_status_filter(self, s: str):
        self._filter_status = s
        self._update_filter_ui()
        self.refresh()

    def _update_filter_ui(self):
        for cat, chip in self._cat_buttons.items():
            active = cat == self._filter_cat
            color = CAT_COLORS.get(cat, ACCENT_PRIMARY)
            chip.set_active(active, active_bg=color if active else None)

        for s, chip in self._status_buttons.items():
            active = s == self._filter_status
            color = chip._chip_color
            chip.set_active(active, active_bg=color if active else None)

    def _rebuild_summary(self, all_p):
        for w in self.summary_frame.winfo_children():
            w.destroy()

        items = [
            ("임박", STATUS_DANGER,  sum(1 for p in all_p if p.status == ExpiryStatus.DANGER)),
            ("애매", STATUS_WARN,    sum(1 for p in all_p if p.status == ExpiryStatus.WARNING)),
            ("널널", STATUS_SAFE,    sum(1 for p in all_p if p.status == ExpiryStatus.SAFE)),
            ("만료", STATUS_EXPIRED, sum(1 for p in all_p if p.status == ExpiryStatus.EXPIRED)),
        ]
        for label, color, count in items:
            cell = tk.Frame(self.summary_frame, bg=BG_HEADER)
            cell.pack(side="left", expand=True, fill="x")

            tk.Label(cell, text=str(count), bg=BG_HEADER,
                     fg=color, font=F(17, "bold")).pack(pady=(6, 0))
            tk.Label(cell, text=label, bg=BG_HEADER,
                     fg=TEXT_MUTED, font=F(8)).pack(pady=(0, 6))

            if label != "만료":
                tk.Frame(self.summary_frame, bg=BORDER_COLOR,
                         width=1).pack(side="left", fill="y", pady=6)

    def refresh(self):
        all_p = self.db.get_all_products()
        self._rebuild_summary(all_p)

        products = list(all_p)
        if self._filter_cat != "전체":
            products = [p for p in products if p.category.value == self._filter_cat]
        status_map = {
            "널널": ExpiryStatus.SAFE, "애매": ExpiryStatus.WARNING,
            "임박": ExpiryStatus.DANGER, "만료": ExpiryStatus.EXPIRED
        }
        if self._filter_status != "전체":
            target = status_map[self._filter_status]
            products = [p for p in products if p.status == target]

        for w in self.list_frame.winfo_children():
            w.destroy()

        if not products:
            empty = tk.Frame(self.list_frame, bg=BG_MAIN)
            empty.pack(expand=True, pady=60)
            tk.Label(empty, text="📦", bg=BG_MAIN, fg=TEXT_MUTED,
                     font=F(36)).pack()
            tk.Label(empty, text="등록된 제품이 없습니다.",
                     bg=BG_MAIN, fg=TEXT_MUTED, font=F(12)).pack(pady=(8, 0))
            tk.Label(empty, text="+ 버튼을 눌러 첫 제품을 등록하세요.",
                     bg=BG_MAIN, fg=TEXT_MUTED, font=F(10)).pack(pady=(4, 0))
            return

        if not self.on_edit:
            def _noop(_p):
                pass
            on_edit = _noop
        else:
            on_edit = self.on_edit

        groups = [
            ("임박 제품", STATUS_DANGER,  ExpiryStatus.DANGER),
            ("주의 제품", STATUS_WARN,    ExpiryStatus.WARNING),
            ("여유 제품", STATUS_SAFE,    ExpiryStatus.SAFE),
            ("만료 제품", STATUS_EXPIRED, ExpiryStatus.EXPIRED),
        ]

        for group_title, color, status in groups:
            group_items = [p for p in products if p.status == status]
            if not group_items:
                continue

            hdr = SectionHeader(self.list_frame, group_title, color, len(group_items))
            hdr.pack(fill="x", padx=PAD, pady=(16, 6))

            for product in group_items:
                card = ProductCard(
                    self.list_frame, product,
                    on_edit=on_edit,
                    on_delete=self._confirm_delete,
                )
                card.pack(fill="x", padx=PAD, pady=(0, 5))

        tk.Frame(self.list_frame, bg=BG_MAIN, height=80).pack()

    def _confirm_delete(self, product: Product):
        if messagebox.askyesno("삭제 확인",
                               f"'{product.name}'을(를) 삭제하시겠습니까?",
                               icon="warning"):
            self.db.delete_product(product.id)
            self.refresh()
