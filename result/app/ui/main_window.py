"""
메인 윈도우 - 화면 전환 오케스트레이터
"""

import tkinter as tk
from ..core.database import Database, Product
from .theme import *
from .list_screen import ProductListScreen
from .add_screen import AddProductScreen
from .edit_screen import EditProductScreen
from .settings_screen import SettingsScreen, apply_saved_config
from .calendar_screen import CalendarScreen


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.db = Database()

        apply_saved_config()

        self._current_screen = None
        self._show_list()

    def _show_list(self):
        self._clear()
        screen = ProductListScreen(
            self.root,
            db=self.db,
            on_add=self._show_add,
            on_edit=self._show_edit,
            on_settings=self._open_settings,
            on_calendar=self._show_calendar,
        )
        screen.pack(fill="both", expand=True)
        self._current_screen = screen

    def _show_add(self):
        self._clear()
        screen = AddProductScreen(
            self.root,
            db=self.db,
            on_done=self._on_add_done,
            on_cancel=self._show_list,
        )
        screen.pack(fill="both", expand=True)
        self._current_screen = screen

    def _show_edit(self, product: Product):
        self._clear()
        screen = EditProductScreen(
            self.root,
            db=self.db,
            product=product,
            on_done=lambda: self._on_edit_done(),
            on_cancel=self._show_list,
        )
        screen.pack(fill="both", expand=True)
        self._current_screen = screen

    def _show_calendar(self):
        self._clear()
        screen = CalendarScreen(
            self.root,
            db=self.db,
            on_back=self._show_list,
        )
        screen.pack(fill="both", expand=True)
        self._current_screen = screen

    def _on_add_done(self):
        self._show_list()
        self._show_toast("  ✅  제품이 등록되었습니다  ")

    def _on_edit_done(self):
        self._show_list()
        self._show_toast("  ✅  수정이 저장되었습니다  ")

    def _show_toast(self, message: str):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.configure(bg=STATUS_SAFE)
        toast.attributes("-alpha", 0.95)
        tk.Label(toast, text=message, bg=STATUS_SAFE,
                 fg=TEXT_PRIMARY, font=F(12, "bold"), pady=10).pack()
        self.root.update_idletasks()
        rx, ry = self.root.winfo_rootx(), self.root.winfo_rooty()
        rw = self.root.winfo_width()
        toast.geometry(f"+{rx + rw//2 - 120}+{ry + 80}")
        toast.after(2000, toast.destroy)

    def _open_settings(self):
        SettingsScreen(self.root)

    def _clear(self):
        # Stop camera if running
        if self._current_screen and hasattr(self._current_screen, 'camera'):
            try:
                self._current_screen.camera.stop()
            except Exception:
                pass
        for widget in self.root.winfo_children():
            widget.destroy()
