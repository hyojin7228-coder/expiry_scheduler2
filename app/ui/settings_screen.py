"""
설정 화면 (인식은 EasyOCR 로컬 — 외부 API 없음)
"""

import tkinter as tk
import json
import os

from .theme import *


CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                           "data", "config.json")


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(cfg: dict):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f)


def apply_saved_config():
    """앱 기동 시 설정 파일 로드(향후 항목 확장용). 레거시 gemini_api_key 필드는 무시합니다."""
    load_config()


class SettingsScreen(tk.Toplevel):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.title("설정")
        self.configure(bg=BG_MAIN)
        self.geometry("380x300")
        self.resizable(False, False)
        self._build()

    def _build(self):
        tk.Label(self, text="⚙  설정", bg=BG_MAIN, fg=TEXT_PRIMARY,
                 font=F(17, "bold")).pack(pady=(20, 4), padx=20, anchor="w")

        tk.Frame(self, bg=BORDER_COLOR, height=1).pack(fill="x", padx=20, pady=8)

        tk.Label(self, text="인식 엔진", bg=BG_MAIN, fg=TEXT_SECONDARY,
                 font=F(11)).pack(anchor="w", padx=20, pady=(8, 4))
        tk.Label(self, text="✅  EasyOCR (로컬 동작 — API 키 불필요)\n제품명 및 유통기한을 카메라로 자동 인식합니다.",
                 bg=BG_MAIN, fg=TEXT_MUTED, font=F(10), justify="left").pack(anchor="w", padx=20)

        close_btn = tk.Label(self, text="닫기", bg=ACCENT_PRIMARY, fg=TEXT_ON_COLOR,
                             font=F(13, "bold"), pady=10, cursor="hand2")
        close_btn.pack(fill="x", padx=20, pady=24)
        close_btn.bind("<Button-1>", lambda e: self.destroy())
