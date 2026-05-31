"""
재사용 가능한 UI 위젯 — 트렌디 리디자인
"""

import tkinter as tk
from tkinter import ttk
from .theme import *


def _round_polygon(canvas, x1, y1, x2, y2, r, **kwargs):
    r = min(r, (x2 - x1) // 2, (y2 - y1) // 2)
    if r < 1:
        return canvas.create_rectangle(x1, y1, x2, y2, **kwargs)
    pts = [
        x1 + r, y1, x2 - r, y1,
        x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2,
        x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r,
        x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kwargs)


# ── ttk 스크롤바 스타일 ────────────────────────────────────────
def _apply_scrollbar_style(root_or_widget):
    style = ttk.Style(root_or_widget)
    style.theme_use("clam")
    style.configure("Dark.Vertical.TScrollbar",
                    gripcount=0,
                    background=BORDER_LIGHT,
                    troughcolor=BG_MAIN,
                    bordercolor=BG_MAIN,
                    arrowcolor=BG_MAIN,
                    relief="flat")


def _parent_bg(parent, fallback=BG_MAIN):
    try:
        return parent.cget("bg")
    except Exception:
        return fallback


class RoundedPanel(tk.Frame):
    """둥근 모서리 패널 (카드·입력창 테두리)"""

    def __init__(self, parent, radius=CARD_RADIUS, bg=BG_CARD,
                 border_color=BORDER_COLOR, border_width=1, pad=0,
                 container_bg=None, fit_content=False, min_height=None,
                 **kwargs):
        container_bg = container_bg or _parent_bg(parent)
        super().__init__(parent, bg=container_bg, **kwargs)
        self._radius = radius
        self._bg = bg
        self._border = border_color
        self._border_w = border_width
        self._pad = pad
        self._container_bg = container_bg
        self._fit_content = fit_content
        self._min_height = CARD_H if min_height is None else min_height
        self._inset = max(2, radius // 2) + pad

        self.canvas = tk.Canvas(self, bg=container_bg, highlightthickness=0, bd=0)
        if fit_content:
            self.canvas.pack(fill="x")
        else:
            self.canvas.pack(fill="both", expand=True)

        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win_id = self.canvas.create_window(
            self._inset, self._inset, window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", self._redraw)
        if fit_content:
            self.inner.bind("<Configure>", self._on_inner_resize)

    def _on_inner_resize(self, event=None):
        if not self._fit_content:
            return
        h = event.height + self._inset * 2 + 4
        self.canvas.config(height=max(h, self._min_height))
        self._redraw()

    def _redraw(self, event=None):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 8 or h < 8:
            return
        self.canvas.delete("round")
        r = min(self._radius, w // 2, h // 2)
        inset = self._inset
        if self._border_w:
            _round_polygon(
                self.canvas, 1, 1, w - 1, h - 1, r,
                fill="", outline=self._border, width=self._border_w, tags="round",
            )
        _round_polygon(
            self.canvas, 2, 2, w - 2, h - 2, max(1, r - 1),
            fill=self._bg, outline="", tags="round",
        )
        inner_w = max(20, w - inset * 2)
        self.canvas.coords(self._win_id, inset, inset)
        self.canvas.itemconfig(self._win_id, width=inner_w)
        if not self._fit_content:
            inner_h = max(10, h - inset * 2)
            self.canvas.itemconfig(self._win_id, height=inner_h)
        self.canvas.tag_lower("round")
        self.canvas.tag_raise(self._win_id)

    def set_bg(self, bg: str):
        self._bg = bg
        self.inner.config(bg=bg)
        self._redraw()


def RoundedFrame(parent, bg=BG_CARD, bd_color=BORDER_COLOR, **kwargs):
    """하위 호환 — 둥근 패널 반환"""
    return RoundedPanel(parent, bg=bg, border_color=bd_color, **kwargs)


class RoundedChip(tk.Canvas):
    """둥근 필터·카테고리 칩 버튼"""

    def __init__(self, parent, text, command=None, radius=CHIP_RADIUS,
                 bg=BG_SECTION, fg=TEXT_SECONDARY, active=False,
                 active_bg=ACCENT_PRIMARY, active_fg=TEXT_ON_COLOR, **kwargs):
        container_bg = kwargs.pop("container_bg", _parent_bg(parent))
        super().__init__(parent, bg=container_bg, highlightthickness=0, bd=0,
                         cursor="hand2", **kwargs)
        self._text = text
        self._cmd = command
        self._radius = radius
        self._bg = bg
        self._fg = fg
        self._active = active
        self._active_bg = active_bg
        self._active_fg = active_fg
        self.bind("<Button-1>", self._click)
        self.bind("<Configure>", lambda e: self._draw())
        self.after(10, self._draw)

    def set_active(self, active: bool, active_bg=None):
        self._active = active
        if active_bg is not None:
            self._active_bg = active_bg
        self._draw()

    def _click(self, _e=None):
        if self._cmd:
            self._cmd()

    def _draw(self):
        w = max(self.winfo_width(), 44)
        h = max(self.winfo_height(), 30)
        if self.winfo_width() < 40:
            self.config(width=w, height=h)
        self.delete("all")
        r = min(self._radius, w // 2, h // 2)
        fill = self._active_bg if self._active else self._bg
        outline = fill if self._active else BORDER_COLOR
        _round_polygon(self, 1, 1, w - 1, h - 1, r, fill=fill, outline=outline, width=1)
        fg = self._active_fg if self._active else self._fg
        lines = self._text.split("\n")
        if len(lines) >= 2:
            self.create_text(w // 2, h // 2 - 7, text=lines[0], fill=fg, font=F(14))
            self.create_text(w // 2, h // 2 + 9, text=lines[1], fill=fg, font=F(9))
        else:
            self.create_text(w // 2, h // 2, text=self._text, fill=fg, font=F(10))


class RoundedEntry(tk.Frame):
    """둥근 테두리 입력창"""

    def __init__(self, parent, textvariable=None, compact=False, **kwargs):
        super().__init__(parent, bg=BG_MAIN)
        self._panel = RoundedPanel(
            self, radius=CHIP_RADIUS, bg=BG_INPUT,
            border_color=BORDER_LIGHT, container_bg=BG_MAIN,
            fit_content=True,
        )
        self._panel.pack(fill="x")
        py = 4 if compact else 5
        px = 8
        self.entry = tk.Entry(
            self._panel.inner, textvariable=textvariable,
            bg=BG_INPUT, fg=TEXT_PRIMARY, font=F(11 if compact else 12),
            insertbackground=TEXT_PRIMARY, relief="flat", bd=0,
        )
        self.entry.pack(fill="x", padx=px, pady=py)
        self._placeholder = None

    def set_placeholder(self, text: str):
        self._placeholder = text
        if not self.entry.get():
            self.entry.insert(0, text)
            self.entry.config(fg=TEXT_MUTED)
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, _e):
        if self._placeholder and self.entry.get() == self._placeholder:
            self.entry.delete(0, "end")
            self.entry.config(fg=TEXT_PRIMARY)

    def _on_focus_out(self, _e):
        if self._placeholder and not self.entry.get():
            self.entry.insert(0, self._placeholder)
            self.entry.config(fg=TEXT_MUTED)

    def get(self):
        return self.entry.get()


class ScrollableFrame(tk.Frame):
    """스크롤 가능한 프레임"""
    def __init__(self, parent, bg=BG_MAIN, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        _apply_scrollbar_style(self)

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical",
                                       command=self.canvas.yview,
                                       style="Dark.Vertical.TScrollbar")
        self.inner = tk.Frame(self.canvas, bg=bg)

        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.inner.bind("<Configure>", self._on_inner)
        self.canvas.bind("<Configure>", self._on_canvas)
        self.canvas.bind("<Enter>", self._bind_wheel)
        self.canvas.bind("<Leave>", self._unbind_wheel)
        self.bind("<Destroy>", self._on_destroy)

    def _on_inner(self, e):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas(self, e):
        self.canvas.itemconfig(self.inner_id, width=e.width)

    def _bind_wheel(self, _e):
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)

    def _unbind_wheel(self, _e):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_wheel(self, e):
        self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def _on_destroy(self, e):
        if e.widget is self:
            try:
                self.canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass


class FABButton(tk.Canvas):
    """Floating Action Button  ＋"""
    def __init__(self, parent, command=None, size=52, **kwargs):
        super().__init__(parent, width=size, height=size,
                         bg=BG_MAIN, highlightthickness=0, **kwargs)
        self._cmd = command
        self._size = size
        self._draw(ACCENT_PRIMARY)
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>",    lambda e: self._draw("#E0003A"))
        self.bind("<Leave>",    lambda e: self._draw(ACCENT_PRIMARY))

    def _draw(self, color):
        s = self._size
        self.delete("all")
        r = s // 2 - 1
        cx = cy = s // 2
        self.create_oval(cx-r+2, cy-r+2, cx+r+2, cy+r+2,
                         fill="#2a2a2a", outline="")
        self.create_oval(cx-r, cy-r, cx+r, cy+r, fill=color, outline="")
        arm = s // 5
        self.create_line(cx, cy-arm, cx, cy+arm,
                         fill=TEXT_ON_COLOR, width=2.5, capstyle="round")
        self.create_line(cx-arm, cy, cx+arm, cy,
                         fill=TEXT_ON_COLOR, width=2.5, capstyle="round")

    def _click(self, e):
        if self._cmd:
            self._cmd()


class ColorDot(tk.Canvas):
    """작은 색상 원형 점"""
    def __init__(self, parent, color, size=10, **kwargs):
        super().__init__(parent, width=size, height=size,
                         bg=BG_CARD, highlightthickness=0, **kwargs)
        r = size // 2 - 1
        cx = cy = size // 2
        self.create_oval(cx-r, cy-r, cx+r, cy+r, fill=color, outline="")


class SectionHeader(tk.Frame):
    """섹션 헤더 — 컬러 블록 + 제목 + 카운트"""
    def __init__(self, parent, title: str, color: str, count: int = 0, **kwargs):
        super().__init__(parent, bg=BG_MAIN, **kwargs)

        block = tk.Frame(self, bg=color, width=6, height=18)
        block.pack(side="left", padx=(0, 8))
        block.pack_propagate(False)

        tk.Label(self, text=title, bg=BG_MAIN, fg=TEXT_PRIMARY,
                 font=F(12, "bold")).pack(side="left")

        if count > 0:
            badge = tk.Label(self, text=str(count), bg=color,
                             fg=TEXT_ON_COLOR, font=F(9, "bold"),
                             padx=6, pady=1)
            badge.pack(side="left", padx=(6, 0))


class RoundedButton(tk.Canvas):
    """둥근 모서리 텍스트 버튼"""

    def __init__(self, parent, text, command=None, bg=ACCENT_PRIMARY, fg=TEXT_ON_COLOR,
                 font=None, radius=CARD_RADIUS, hover_bg="#E0003A", pady=13, **kwargs):
        container_bg = kwargs.pop("container_bg", _parent_bg(parent))
        super().__init__(parent, bg=container_bg, highlightthickness=0, bd=0,
                         cursor="hand2", **kwargs)
        self._text = text
        self._cmd = command
        self._bg = bg
        self._hover_bg = hover_bg
        self._fg = fg
        self._font = font or F(14, "bold")
        self._radius = radius
        self._pady = pady
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", lambda e: self._paint(self._hover_bg))
        self.bind("<Leave>", lambda e: self._paint(self._bg))
        self.bind("<Configure>", lambda e: self._paint(self._bg))

    def _click(self, _e=None):
        if self._cmd:
            self._cmd()

    def _paint(self, fill):
        w = max(self.winfo_width(), 80)
        h = max(self.winfo_height(), self._pady * 2 + 8)
        self.config(width=w, height=h)
        self.delete("all")
        r = min(self._radius, w // 2, h // 2)
        _round_polygon(self, 1, 1, w - 1, h - 1, r, fill=fill, outline="")
        self.create_text(w // 2, h // 2, text=self._text, fill=self._fg, font=self._font)
