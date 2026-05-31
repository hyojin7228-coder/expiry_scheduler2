"""
카메라 및 제품 등록 화면 — 트렌디 리디자인
단계별 마법사: 카메라(제품명) → 카메라(유통기한) → 정보 확인 및 등록
"""

import sys
import tkinter as tk
from tkinter import messagebox
import queue
import threading
import tempfile
import time
from datetime import date, datetime
from typing import Callable, Optional
from PIL import Image, ImageTk, ImageDraw
import cv2

from ..core.database import Database, Product
from ..core.gemini import recognize_product_name, recognize_expiry_date, imwrite_unicode
from .theme import *
from .widgets import ScrollableFrame, RoundedPanel
from .product_form import ProductFormMixin, NAME_PLACEHOLDER, EXPIRY_PLACEHOLDER

STEPS = ["제품명 촬영", "유통기한 촬영", "정보 확인 및 등록"]


# ── 카메라 뷰 ─────────────────────────────────────────────────
class CameraView(tk.Label):
    def __init__(self, parent, width=388, height=260, **kwargs):
        super().__init__(parent, bg="#000000", **kwargs)
        self.cam_width = width
        self.cam_height = height
        self._cap = None
        self._running = False
        self._thread = None
        self._last_frame = None
        self._bbox = None
        self._photo = None
        self._frame_queue = queue.Queue(maxsize=1)
        self._poll_id = None

    def _open_capture(self):
        """Windows 등 환경별 카메라 백엔드 시도."""
        if sys.platform == "win32":
            apis = (cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY)
        else:
            apis = (cv2.CAP_ANY,)
        for api in apis:
            cap = cv2.VideoCapture(0, api)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                return cap
            cap.release()
        return cv2.VideoCapture(0)

    def start(self):
        if self._running:
            return
        self.after(50, self._start_deferred)

    def _start_deferred(self):
        if self._running:
            return
        if not self.winfo_exists():
            return
        try:
            self.update_idletasks()
            self._cap = self._open_capture()
            if not self._cap or not self._cap.isOpened():
                self.config(
                    text="카메라를 찾을 수 없습니다.\n권한을 확인하거나 건너뛰기를 누르세요.",
                    fg=TEXT_SECONDARY, font=F(11), wraplength=320, image="",
                )
                return
            self._running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            self._schedule_poll()
        except Exception as e:
            self.config(text=f"카메라 오류: {e}", fg=STATUS_DANGER, font=F(11), image="")

    def stop(self):
        self._running = False
        if self._poll_id is not None:
            try:
                self.after_cancel(self._poll_id)
            except Exception:
                pass
            self._poll_id = None
        while not self._frame_queue.empty():
            try:
                self._frame_queue.get_nowait()
            except queue.Empty:
                break
        if self._cap:
            self._cap.release()
            self._cap = None

    def _schedule_poll(self):
        if self._running and self.winfo_exists():
            self._poll_id = self.after(33, self._poll_frame)

    def _poll_frame(self):
        self._poll_id = None
        if not self._running or not self.winfo_exists():
            return
        try:
            frame = self._frame_queue.get_nowait()
            self._update_display(frame)
        except queue.Empty:
            pass
        self._schedule_poll()

    def _loop(self):
        while self._running:
            if self._cap and self._cap.isOpened():
                ret, frame = self._cap.read()
                if ret:
                    self._last_frame = frame
                    try:
                        self._frame_queue.put_nowait(frame)
                    except queue.Full:
                        try:
                            self._frame_queue.get_nowait()
                        except queue.Empty:
                            pass
                        try:
                            self._frame_queue.put_nowait(frame)
                        except queue.Full:
                            pass
            time.sleep(1 / 30)

    def _update_display(self, frame):
        if not self._running or not self.winfo_exists():
            return
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            img = img.resize((self.cam_width, self.cam_height), Image.LANCZOS)
            if self._bbox:
                draw = ImageDraw.Draw(img)
                b = self._bbox
                x1 = int(b["x"] * self.cam_width)
                y1 = int(b["y"] * self.cam_height)
                x2 = int((b["x"] + b["w"]) * self.cam_width)
                y2 = int((b["y"] + b["h"]) * self.cam_height)
                for t in range(3):
                    draw.rectangle([x1-t, y1-t, x2+t, y2+t],
                                   outline=ACCENT_ORANGE, width=1)
                cl = 16
                for sx, sy, dx, dy in [
                    (x1, y1, x1+cl, y1), (x1, y1, x1, y1+cl),
                    (x2, y1, x2-cl, y1), (x2, y1, x2, y1+cl),
                    (x1, y2, x1+cl, y2), (x1, y2, x1, y2-cl),
                    (x2, y2, x2-cl, y2), (x2, y2, x2, y2-cl),
                ]:
                    draw.line([sx, sy, dx, dy], fill=ACCENT_ORANGE, width=3)
            self._photo = ImageTk.PhotoImage(img)
            self.config(image=self._photo, text="")
        except Exception:
            pass

    def capture_frame(self) -> Optional[str]:
        if self._last_frame is None:
            return None
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        if not imwrite_unicode(tmp.name, self._last_frame):
            return None
        return tmp.name

    def set_bbox(self, bbox):
        self._bbox = bbox


# ── 단계 표시기 ───────────────────────────────────────────────
class StepIndicator(tk.Frame):
    def __init__(self, parent, steps, current=0, **kwargs):
        super().__init__(parent, bg=BG_MAIN, **kwargs)
        for i, step in enumerate(steps):
            active = i == current
            done   = i < current
            # 연결선
            if i > 0:
                line_color = ACCENT_PRIMARY if done else BORDER_LIGHT
                tk.Frame(self, bg=line_color, width=28, height=2).pack(
                    side="left", pady=(0, 0))
            # 원
            dot_bg  = ACCENT_PRIMARY if active else (STATUS_SAFE if done else BG_SECTION)
            dot_fg  = TEXT_ON_COLOR
            dot_txt = "✓" if done else str(i + 1)
            dot = tk.Label(self, text=dot_txt, bg=dot_bg, fg=dot_fg,
                           font=F(10, "bold"), width=2, pady=2,
                           highlightbackground=dot_bg if (active or done) else BORDER_COLOR,
                           highlightthickness=1)
            dot.pack(side="left")
            # 텍스트
            tk.Label(self, text=step, bg=BG_MAIN,
                     fg=TEXT_PRIMARY if active else TEXT_MUTED,
                     font=F(9, "bold") if active else F(9)).pack(
                side="left", padx=(4, 0))


# ── 메인 등록 화면 ────────────────────────────────────────────
class AddProductScreen(tk.Frame, ProductFormMixin):

    def __init__(self, parent, db: Database,
                 on_done: Callable, on_cancel: Callable, **kwargs):
        super().__init__(parent, bg=BG_MAIN, **kwargs)
        self.db = db
        self.on_done = on_done
        self.on_cancel = on_cancel

        self._step = 0
        self._init_form_vars()
        self._product_name_img = None
        self._expiry_img = None
        self._recognizing = False

        self._build_ui()
        self._show_step(0)

    # ── 공통 헤더 ──────────────────────────────────────────────
    def _build_ui(self):
        hdr = tk.Frame(self, bg=BG_HEADER, height=HEADER_H)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        back = tk.Label(hdr, text="←", bg=BG_HEADER, fg=TEXT_SECONDARY,
                        font=F(16), cursor="hand2", padx=PAD)
        back.pack(side="left")
        back.bind("<Button-1>", lambda e: self._go_back())
        back.bind("<Enter>", lambda e: back.config(fg=TEXT_PRIMARY))
        back.bind("<Leave>", lambda e: back.config(fg=TEXT_SECONDARY))

        tk.Label(hdr, text="제품 등록", bg=BG_HEADER, fg=TEXT_PRIMARY,
                 font=F(14, "bold")).pack(side="left", padx=4)

        self.step_frame = tk.Frame(self, bg=BG_MAIN, pady=10)
        self.step_frame.pack(fill="x", padx=PAD)

        self.content = tk.Frame(self, bg=BG_MAIN)
        self.content.pack(fill="both", expand=True)

    def _rebuild_step_indicator(self):
        for w in self.step_frame.winfo_children():
            w.destroy()
        StepIndicator(self.step_frame, STEPS, self._step).pack(anchor="center")

    def _show_step(self, step: int):
        self._step = step
        self._rebuild_step_indicator()
        for w in self.content.winfo_children():
            w.destroy()
        if step == 0:
            self._build_camera_step("제품명 촬영",
                                    "제품명이 잘 보이도록 카메라를 맞춰주세요",
                                    self._capture_product_name)
        elif step == 1:
            self._build_camera_step("유통기한 촬영",
                                    "유통기한 숫자가 선명하게 보이도록 맞춰주세요",
                                    self._capture_expiry_date)
        elif step == 2:
            self._build_confirm_step()

    # ── 카메라 단계 ────────────────────────────────────────────
    def _build_camera_step(self, title: str, hint: str, capture_cb: Callable):
        # 타이틀
        title_frame = tk.Frame(self.content, bg=BG_MAIN)
        title_frame.pack(fill="x", padx=PAD, pady=(4, 0))
        tk.Label(title_frame, text=title, bg=BG_MAIN, fg=TEXT_PRIMARY,
                 font=F(16, "bold")).pack(anchor="w")
        tk.Label(title_frame, text=hint, bg=BG_MAIN, fg=TEXT_SECONDARY,
                 font=F(10)).pack(anchor="w", pady=(2, 0))

        cam_wrap = tk.Frame(self.content, bg="#000000", width=362, height=222,
                            highlightbackground=BORDER_LIGHT,
                            highlightthickness=1)
        cam_wrap.pack(padx=PAD, pady=(10, 0))
        cam_wrap.pack_propagate(False)

        self.camera = CameraView(cam_wrap, width=360, height=220)
        self.camera.pack(expand=True)
        self.after(250, self.camera.start)

        # 상태 메시지
        self.status_label = tk.Label(self.content, text="",
                                     bg=BG_MAIN, fg=STATUS_WARN,
                                     font=F(10))
        self.status_label.pack(pady=6)

        # 버튼 행
        btn_row = tk.Frame(self.content, bg=BG_MAIN)
        btn_row.pack(pady=4)

        # 촬영 버튼 (Image2 빨간 Continue 버튼 느낌)
        cap_btn = tk.Label(btn_row, text="📷  촬영",
                           bg=ACCENT_PRIMARY, fg=TEXT_ON_COLOR,
                           font=F(13, "bold"), padx=28, pady=11,
                           cursor="hand2")
        cap_btn.pack(side="left", padx=(0, 10))
        cap_btn.bind("<Button-1>", lambda e: capture_cb())
        cap_btn.bind("<Enter>", lambda e: cap_btn.config(bg="#E0003A"))
        cap_btn.bind("<Leave>", lambda e: cap_btn.config(bg=ACCENT_PRIMARY))

        # 건너뛰기 버튼
        skip_btn = tk.Label(btn_row, text="건너뛰기",
                            bg=BG_SECTION, fg=TEXT_SECONDARY,
                            font=F(11), padx=16, pady=11,
                            cursor="hand2",
                            highlightbackground=BORDER_LIGHT,
                            highlightthickness=1)
        skip_btn.pack(side="left")
        skip_btn.bind("<Button-1>", lambda e: self._skip_step())
        skip_btn.bind("<Enter>", lambda e: skip_btn.config(fg=TEXT_PRIMARY))
        skip_btn.bind("<Leave>", lambda e: skip_btn.config(fg=TEXT_SECONDARY))

    def _capture_product_name(self):
        if self._recognizing:
            return
        img_path = self.camera.capture_frame()
        if not img_path:
            self._set_status("카메라 프레임을 가져올 수 없습니다.", STATUS_DANGER)
            return
        self._product_name_img = img_path
        self._set_status("제품명 인식 중...", STATUS_WARN)
        self._recognizing = True
        threading.Thread(target=self._do_recognize_name,
                         args=(img_path,), daemon=True).start()

    def _do_recognize_name(self, img_path):
        try:
            name, bbox = recognize_product_name(img_path)
            self.after(0, self._on_name_recognized, name, bbox)
        except Exception as e:
            self.after(0, self._set_status, f"인식 실패: {e}", STATUS_DANGER)
            self._recognizing = False

    def _on_name_recognized(self, name, bbox):
        self._recognizing = False
        if name:
            self._product_name.set(name)
            if bbox:
                self.camera.set_bbox(bbox)
            self._set_status(f"✅  인식됨: {name}", STATUS_SAFE)
            self.after(1200, self._go_to_step1)
        else:
            self._set_status("제품명을 인식하지 못했습니다. 다시 촬영하거나 건너뛰세요.",
                             STATUS_DANGER)

    def _go_to_step1(self):
        if hasattr(self, "camera"):
            self.camera.stop()
        self._show_step(1)

    def _capture_expiry_date(self):
        if self._recognizing:
            return
        img_path = self.camera.capture_frame()
        if not img_path:
            self._set_status("카메라 프레임을 가져올 수 없습니다.", STATUS_DANGER)
            return
        self._expiry_img = img_path
        self._set_status("유통기한 인식 중...", STATUS_WARN)
        self._recognizing = True
        threading.Thread(target=self._do_recognize_expiry,
                         args=(img_path,), daemon=True).start()

    def _do_recognize_expiry(self, img_path):
        try:
            expiry, bbox = recognize_expiry_date(img_path)
            self.after(0, self._on_expiry_recognized, expiry, bbox)
        except Exception as e:
            self.after(0, self._set_status, f"인식 실패: {e}", STATUS_DANGER)
            self._recognizing = False

    def _on_expiry_recognized(self, expiry, bbox):
        self._recognizing = False
        if expiry:
            self._expiry_date.set(expiry)
            if bbox:
                self.camera.set_bbox(bbox)
            self._set_status(f"✅  유통기한: {expiry}", STATUS_SAFE)
            self.after(1200, self._go_to_step2)
        else:
            self._set_status("유통기한을 인식하지 못했습니다. 다시 촬영하거나 건너뛰세요.",
                             STATUS_DANGER)

    def _go_to_step2(self):
        if hasattr(self, "camera"):
            self.camera.stop()
        self._show_step(2)

    def _skip_step(self):
        if hasattr(self, 'camera'):
            try:
                self.camera.stop()
            except Exception:
                pass
        self._show_step(min(self._step + 1, len(STEPS) - 1))

    def _set_status(self, msg: str, color: str = TEXT_SECONDARY):
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            self.status_label.config(text=msg, fg=color)

    # ── 확인 / 등록 단계 ──────────────────────────────────────
    def _build_confirm_step(self):
        scroll = ScrollableFrame(self.content, bg=BG_MAIN)
        scroll.pack(fill="both", expand=True)
        form = scroll.inner

        tk.Label(form, text="정보 확인 및 등록", bg=BG_MAIN, fg=TEXT_PRIMARY,
                 font=F(16, "bold")).pack(anchor="w", padx=PAD, pady=(14, 2))
        tk.Label(form, text="AI가 인식한 정보를 확인하고 필요시 수정하세요.",
                 bg=BG_MAIN, fg=TEXT_SECONDARY, font=F(10)).pack(
            anchor="w", padx=PAD, pady=(0, 10))

        self._field(form, "제품명 *", self._product_name, NAME_PLACEHOLDER)
        self._field(form, "유통기한 * (YYYY-MM-DD)", self._expiry_date, EXPIRY_PLACEHOLDER)
        self._build_category_row(form)
        self._field(form, "메모 (선택)", self._notes, "비고 사항을 입력하세요")

        self._action_btn(form, "✅  등록하기", ACCENT_PRIMARY, TEXT_ON_COLOR,
                         self._submit_product, pady=2, font=F(13, "bold"))
        self._action_btn(form, "취소", BG_SECTION, TEXT_SECONDARY,
                         self.on_cancel, pady=2, font=F(11), last=True)

    def _action_btn(self, parent, text, bg, fg, command, pady=10, font=None, last=False):
        wrap = tk.Frame(parent, bg=BG_MAIN)
        wrap.pack(fill="x", padx=PAD, pady=(12 if "등록" in text else 0, 24 if last else 6))
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

    def _submit_product(self):
        parsed = self._parse_form()
        if not parsed:
            return
        name, exp_date, category, notes_val = parsed
        self.db.add_product(Product(
            id=None, name=name, category=category,
            registered_date=date.today(), expiry_date=exp_date,
            image_path=self._product_name_img, notes=notes_val
        ))
        self.on_done()

    def _go_back(self):
        if self._step == 0:
            if hasattr(self, 'camera'):
                self.camera.stop()
            self.on_cancel()
        else:
            if hasattr(self, 'camera'):
                try:
                    self.camera.stop()
                except Exception:
                    pass
            self._show_step(self._step - 1)