import sys
import warnings
import subprocess

warnings.filterwarnings("ignore")

# 📦 AUTO-DEPENDENCY INSTALLER (ইউজারের পিসিতে না থাকলে নিজে ডাউনলোড করে নেবে)
def install_missing_libraries():
    required_libraries = {
        "cv2": "opencv-python",
        "numpy": "numpy",
        "mutagen": "mutagen",
        "PIL": "pillow",
        "requests": "requests",
        "customtkinter": "customtkinter",
        "pygame": "pygame"
    }
    for module_name, pip_name in required_libraries.items():
        try:
            __import__(module_name)
        except ImportError:
            print(f"Installing missing dependency: {pip_name}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name, "--quiet"])
            except Exception as e:
                print(f"Could not install {pip_name} automatically: {e}")

# রান করার সাথে সাথেই চেক এবং ইনস্টল হবে
install_missing_libraries()

try:
    import audioop
except ImportError:
    import math
    sys.modules['audioop'] = math

import os
import threading
import time
import random
import json  
import urllib.parse
import re
import requests
import customtkinter as ctk
import pygame
from mutagen.mp3 import MP3
from PIL import Image, ImageTk  

# 🎥 Video Export Utilities
try:
    import cv2
    import numpy as np
    VIDEO_EXPORT_AVAILABLE = True
except ImportError:
    VIDEO_EXPORT_AVAILABLE = False

pygame.mixer.init()

# ────────────── CONFIG & DATA PATHS ──────────────
CURRENT_VERSION = "1.0.1"  
VERSION_URL = "https://raw.githubusercontent.com/Alviff/VibeStream-Update/main/version.txt"
CODE_URL = "https://github.com/Alviff/VibeStream-Update/raw/main/VibeStream.exe" 

SETTINGS_FILE = "settings.json"
USER_DATA_FILE = "user_account.json" 

# 🔑 GENIUS API CONFIGURATION
GENIUS_ACCESS_TOKEN = "5G_5bJ5jL6Ejfn8IVcMIHUEyvNKeO_UPo3uXj20lq09Qz5FrUxJHU2_1_FbzHpvWrJPxnR88JCmWIYn9C_yqkg"

ctk.set_appearance_mode("Dark")

def _create_rounded_rect(self, x1, y1, x2, y2, radius=10, **kwargs):
    points = [
        x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1, x2, y1+radius, x2, y1+radius, 
        x2, y2-radius, x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2, 
        x1, y2, x1, y2-radius, x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1
    ]
    return self.create_polygon(points, **kwargs, smooth=True)

ctk.CTkCanvas.create_rounded_rect = _create_rounded_rect


class UltimateFullAppPlayer(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title(f"VibeStream - Immersive Theater Edition (v{CURRENT_VERSION})")
        self.is_fullscreen = True
        self.attributes('-fullscreen', self.is_fullscreen)
        self.bind("<Escape>", self.toggle_window_fullscreen)  
        
        # 🎨 Themes Configuration
        self.themes = {
            "Spotify Green": {"text": "#FFFFFF", "muted": "#A7A7A7", "accent": "#1ED760", "card_bg": "#121212", "overlay": "#0A0A0A"},
            "Cyberpunk Pink": {"text": "#FFFFFF", "muted": "#A0A0A0", "accent": "#FF007F", "card_bg": "#0B0014", "overlay": "#050008"},
            "Neon Blue": {"text": "#FFFFFF", "muted": "#909090", "accent": "#00E5FF", "card_bg": "#0A1118", "overlay": "#03080C"},
            "Blood Red": {"text": "#FFFFFF", "muted": "#A0A0A0", "accent": "#FF3333", "card_bg": "#140A0A", "overlay": "#080303"}
        }
        self.current_theme_name = "Spotify Green"
        self.c = self.themes[self.current_theme_name]
        self.configure(fg_color=self.c["overlay"])

        # States
        self.playlist = []
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False
        self.song_length = 0  
        self.current_time_offset = 0  
        self.start_timestamp = 0      
        self.is_looping = False
        self.is_shuffling = False
        
        self.sidebar_visible = False 
        self.playlist_expanded = False 
        self.is_recording_video = False
        self.video_frames = []
        
        self.synced_lyrics = []  
        self.last_highlighted_index = -1
        self.bg_image_path = None
        self.current_lyrics_text = "Lyrics will flow smoothly right here!"
        
        # Image Cache
        self.cached_normal_bg = None
        self.cached_sidebar_bg = None
        
        # 📊 VISUALIZER CONFIG
        self.num_bars = 100  
        self.circle_radius = 110  
        self.bar_magnitudes = [0.0] * self.num_bars
        self.visualizer_templates = ["Circular Avee", "Bottom Waves", "Pulse Star", "WhatsApp Message"]
        self.current_visualizer_template = "Circular Avee"

        # Background Canvas
        self.bg_canvas = ctk.CTkCanvas(self, bg=self.c["overlay"], highlightthickness=0, bd=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.check_account_auth()

    def check_account_auth(self):
        if not os.path.exists(USER_DATA_FILE):
            self.show_signup_screen()
        else:
            self.show_login_screen()

    def show_signup_screen(self):
        self.auth_frame = ctk.CTkFrame(self, width=400, height=350, corner_radius=15, fg_color=self.c["card_bg"])
        self.auth_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.auth_frame.grid_propagate(False)

        ctk.CTkLabel(self.auth_frame, text="Welcome to VibeStream 🎉\nCreate Local Account", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        self.ent_username = ctk.CTkEntry(self.auth_frame, width=280, placeholder_text="Enter Username")
        self.ent_username.pack(pady=10)
        self.ent_password = ctk.CTkEntry(self.auth_frame, width=280, placeholder_text="Enter Password", show="*")
        self.ent_password.pack(pady=10)
        self.lbl_auth_error = ctk.CTkLabel(self.auth_frame, text="", text_color="red")
        self.lbl_auth_error.pack(pady=5)

        btn_signup = ctk.CTkButton(self.auth_frame, text="Sign Up", fg_color=self.c["accent"], text_color="black", font=ctk.CTkFont(weight="bold"), command=self.process_signup)
        btn_signup.pack(pady=15)

    def process_signup(self):
        user = self.ent_username.get().strip()
        pwd = self.ent_password.get().strip()
        if not user or not pwd:
            self.lbl_auth_error.configure(text="Fields cannot be empty!")
            return
        with open(USER_DATA_FILE, "w") as f:
            json.dump({"username": user, "password": pwd}, f)
        self.auth_frame.destroy()
        self.show_login_screen()

    def show_login_screen(self):
        self.auth_frame = ctk.CTkFrame(self, width=400, height=350, corner_radius=15, fg_color=self.c["card_bg"])
        self.auth_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.auth_frame.grid_propagate(False)

        ctk.CTkLabel(self.auth_frame, text="🔒 Login to VibeStream", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=25)
        self.ent_login_user = ctk.CTkEntry(self.auth_frame, width=280, placeholder_text="Username")
        self.ent_login_user.pack(pady=10)
        self.ent_login_pwd = ctk.CTkEntry(self.auth_frame, width=280, placeholder_text="Password", show="*")
        self.ent_login_pwd.pack(pady=10)
        self.lbl_auth_error = ctk.CTkLabel(self.auth_frame, text="", text_color="red")
        self.lbl_auth_error.pack(pady=5)

        btn_login = ctk.CTkButton(self.auth_frame, text="Unlock Player 🔓", fg_color=self.c["accent"], text_color="black", font=ctk.CTkFont(weight="bold"), command=self.process_login)
        btn_login.pack(pady=15)

    def process_login(self):
        user = self.ent_login_user.get().strip()
        pwd = self.ent_login_pwd.get().strip()
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, "r") as f:
                saved = json.load(f)
            if saved.get("username") == user and saved.get("password") == pwd:
                self.auth_frame.destroy()
                self.initialize_main_player() 
            else:
                self.lbl_auth_error.configure(text="Incorrect credentials!")
        else:
            self.lbl_auth_error.configure(text="No account found!")

    def initialize_main_player(self):
        self.setup_layout()
        
        self.btn_menu = ctk.CTkButton(
            self, text="☰ Open Menu", font=ctk.CTkFont(size=14, weight="bold"),
            width=120, height=38, fg_color="#1F1F1F", text_color="white",
            hover_color="#333333", corner_radius=10, command=self.toggle_sidebar
        )
        self.btn_menu.place(x=25, y=25)
        self.btn_menu.lift()

        self.load_saved_settings()
        self.sidebar.place_forget()

        self.after(300, self.pre_cache_and_render_background)
        self.bind("<Configure>", self.on_window_resize)

        self.update_avee_visualizer()
        threading.Thread(target=self.lyrics_sync_loop, daemon=True).start()
        threading.Thread(target=self.update_progress_loop, daemon=True).start()
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def setup_layout(self):
        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=0, fg_color=self.c["card_bg"])
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(6, weight=1) 

        ctk.CTkLabel(self.sidebar, text="", height=65).grid(row=0, column=0)

        self.config_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.config_box.grid(row=1, column=0, sticky="ew", padx=20, pady=5)

        self.btn_import = ctk.CTkButton(
            self.config_box, text="📁 Change Music Folder", font=ctk.CTkFont(size=13, weight="bold"),
            height=36, fg_color="white", text_color="black", hover_color="#EAEAEA",
            corner_radius=10, command=self.import_folder,
        )
        self.btn_import.pack(fill="x", pady=5)

        self.theme_selector = ctk.CTkOptionMenu(
            self.config_box, values=list(self.themes.keys()), fg_color="#1F1F1F", button_color="#2D2D2D",
            dropdown_fg_color="#121212", font=ctk.CTkFont(size=12), command=self.change_theme
        )
        self.theme_selector.set(self.current_theme_name)
        self.theme_selector.pack(fill="x", pady=5)

        self.visualizer_selector = ctk.CTkOptionMenu(
            self.config_box, values=self.visualizer_templates, fg_color="#1F1F1F", button_color="#2D2D2D",
            dropdown_fg_color="#121212", font=ctk.CTkFont(size=12), command=self.change_visualizer_template
        )
        self.visualizer_selector.set(self.current_visualizer_template)
        self.visualizer_selector.pack(fill="x", pady=5)

        self.btn_upload_bg = ctk.CTkButton(
            self.config_box, text="🖼️ Upload Custom Wallpaper", font=ctk.CTkFont(size=12, weight="bold"),
            height=32, fg_color="#252525", text_color="white", corner_radius=8, command=self.upload_bg_image
        )
        self.btn_upload_bg.pack(fill="x", pady=5)

        self.slider_bass = ctk.CTkSlider(self.config_box, from_=0.5, to=2.5, height=12, fg_color="#3E3E3E", progress_color=self.c["accent"], button_color=self.c["accent"])
        self.slider_bass.set(1.0)
        self.slider_bass.pack(fill="x", pady=(15, 2))
        self.lbl_bass = ctk.CTkLabel(self.config_box, text="Bass Boost: 1.0x", font=ctk.CTkFont(size=11), text_color=self.c["muted"])
        self.lbl_bass.pack(anchor="w")

        # 🎥 VIDEO EXPORT TRIGGER BUTTON
        self.btn_export_video = ctk.CTkButton(
            self.sidebar, text="📹 Export Live Video (MP4)", font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#291a03", text_color="#FF9900", hover_color="#422b07", height=34, corner_radius=8,
            command=self.toggle_video_recording
        )
        self.btn_export_video.grid(row=2, column=0, sticky="ew", padx=20, pady=5)

        # 🎖️ CREDIT & TESTERS
        self.btn_credits = ctk.CTkButton(
            self.sidebar, text="🎖️ Credits & Beta Testers", font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#252525", text_color="#1ED760", hover_color="#333333", height=32, corner_radius=8,
            command=self.show_credits_window
        )
        self.btn_credits.grid(row=3, column=0, sticky="ew", padx=20, pady=5)

        self.btn_expand_playlist = ctk.CTkButton(
            self.sidebar, text="▼ Expand Playlist Tracks", font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1A1A1A", text_color="white", height=38, corner_radius=8, command=self.toggle_playlist_dropdown
        )
        self.btn_expand_playlist.grid(row=4, column=0, sticky="ew", padx=20, pady=(10, 5))

        self.playlist_box = ctk.CTkScrollableFrame(self.sidebar, corner_radius=8, fg_color="#0A0A0A")

        # ────────────── TRANSPARENT UTILITIES PANEL ──────────────
        self.center_lyrics_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.center_lyrics_panel.place(relx=0.5, rely=0.75, relwidth=0.65, relheight=0.15, anchor="center")

        self.btn_manual_lrc = ctk.CTkButton(
            self.center_lyrics_panel, text="📇 Upload Custom .LRC / .TXT File", font=ctk.CTkFont(size=11, weight="bold"),
            width=190, height=28, fg_color="#1A1A1A", text_color=self.c["muted"], hover_color="#333333", corner_radius=6,
            command=self.upload_manual_lrc_file
        )
        self.btn_manual_lrc.pack(side="bottom", pady=(5, 0))

        # ────────────── BOTTOM CONTROLS FLOATING BAR ──────────────
        self.controls_bar = ctk.CTkFrame(self, height=100, corner_radius=20, fg_color=self.c["card_bg"])
        self.controls_bar.place(relx=0.5, rely=0.92, relwidth=0.92, anchor="center")
        self.controls_bar.grid_propagate(False)
        
        self.controls_bar.grid_columnconfigure(0, weight=1) 
        self.controls_bar.grid_columnconfigure(1, weight=2) 
        self.controls_bar.grid_columnconfigure(2, weight=1) 

        # Timeline
        self.timeline_frame = ctk.CTkFrame(self.controls_bar, fg_color="transparent")
        self.timeline_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=30, pady=(10, 0))
        self.timeline_frame.grid_columnconfigure(1, weight=1)

        self.lbl_current_time = ctk.CTkLabel(self.timeline_frame, text="0:00", font=ctk.CTkFont(size=11), text_color=self.c["muted"])
        self.lbl_current_time.grid(row=0, column=0, padx=(0, 10))

        self.slider_progress = ctk.CTkSlider(self.timeline_frame, from_=0, to=100, height=6, fg_color="#3E3E3E", progress_color=self.c["accent"], button_color=self.c["accent"])
        self.slider_progress.set(0)
        self.slider_progress.grid(row=0, column=1, sticky="ew")
        self.slider_progress.bind("<ButtonRelease-1>", self.slide_progress)

        self.lbl_total_time = ctk.CTkLabel(self.timeline_frame, text="0:00", font=ctk.CTkFont(size=11), text_color=self.c["muted"])
        self.lbl_total_time.grid(row=0, column=2, padx=(10, 0))

        # Media Buttons
        self.buttons_frame = ctk.CTkFrame(self.controls_bar, fg_color="transparent")
        self.buttons_frame.grid(row=1, column=1, pady=(2, 5))

        self.btn_shuffle = ctk.CTkButton(self.buttons_frame, text="🔀", width=35, fg_color="transparent", text_color=self.c["muted"], command=self.toggle_shuffle)
        self.btn_shuffle.pack(side="left", padx=5)

        self.btn_prev = ctk.CTkButton(self.buttons_frame, text="⏮", width=35, fg_color="transparent", text_color="white", command=self.prev_track)
        self.btn_prev.pack(side="left", padx=5)

        self.btn_play = ctk.CTkButton(self.buttons_frame, text="▶", width=40, height=40, corner_radius=20, fg_color=self.c["accent"], text_color="black", hover_color="white", command=self.toggle_play)
        self.btn_play.pack(side="left", padx=5)

        self.btn_next = ctk.CTkButton(self.buttons_frame, text="⏭", width=35, fg_color="transparent", text_color="white", command=self.next_track)
        self.btn_next.pack(side="left", padx=5)

        self.btn_loop = ctk.CTkButton(self.buttons_frame, text="🔁", width=35, fg_color="transparent", text_color=self.c["muted"], command=self.toggle_loop)
        self.btn_loop.pack(side="left", padx=5)

        # Track Meta Display
        self.meta_frame = ctk.CTkFrame(self.controls_bar, fg_color="transparent")
        self.meta_frame.grid(row=1, column=0, sticky="w", padx=30)
        self.lbl_track_name = ctk.CTkLabel(self.meta_frame, text="No Song Loaded", font=ctk.CTkFont(size=13, weight="bold"), text_color="white")
        self.lbl_track_name.pack(anchor="w")

        # Volume Controls
        self.volume_frame = ctk.CTkFrame(self.controls_bar, fg_color="transparent")
        self.volume_frame.grid(row=1, column=2, padx=30, sticky="e")
        self.slider_volume = ctk.CTkSlider(self.volume_frame, width=80, from_=0, to=1, fg_color="#3E3E3E", progress_color="white", button_color="white", command=self.set_volume)
        self.slider_volume.set(0.7)
        self.slider_volume.pack(side="right")
        ctk.CTkLabel(self.volume_frame, text="🔊", text_color="white").pack(side="right", padx=5)

    def show_credits_window(self):
        credits_win = ctk.CTkToplevel(self)
        credits_win.title("VibeStream - Production Team 🎖️")
        credits_win.geometry("450x420")
        credits_win.resizable(False, False)
        credits_win.lift()
        credits_win.attributes("-topmost", True)
        
        ctk.CTkLabel(credits_win, text="🌟 VIBESTREAM CREDITS 🌟", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.c["accent"]).pack(pady=(20, 15))
        
        dev_frame = ctk.CTkFrame(credits_win, fg_color="#161616", width=400, height=80, corner_radius=10)
        dev_frame.pack(pady=5, padx=20, fill="x")
        dev_frame.pack_propagate(False)
        ctk.CTkLabel(dev_frame, text="💻 Lead Developer & UI Architect", font=ctk.CTkFont(size=11), text_color=self.c["muted"]).pack(pady=(8, 0))
        ctk.CTkLabel(dev_frame, text="MD Adiat Islam (Alvi)", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(pady=(2, 5))
        
        ai_frame = ctk.CTkFrame(credits_win, fg_color="#1a233a", width=400, height=75, corner_radius=10, border_width=1, border_color="#00E5FF")
        ai_frame.pack(pady=5, padx=20, fill="x")
        ai_frame.pack_propagate(False)
        ctk.CTkLabel(ai_frame, text="✨ AI Assistant & Core Engine Optimizer", font=ctk.CTkFont(size=11), text_color="#909090").pack(pady=(8, 0))
        ctk.CTkLabel(ai_frame, text="Gemini AI (Google)", font=ctk.CTkFont(size=15, weight="bold"), text_color="#00E5FF").pack(pady=(2, 5))
        
        testers_frame = ctk.CTkFrame(credits_win, fg_color="#121212", width=400, corner_radius=10)
        testers_frame.pack(pady=10, padx=20, fill="both", expand=True)
        ctk.CTkLabel(testers_frame, text="🧪 Authorized Beta Tester", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.c["accent"]).pack(pady=(10, 5))
        
        ctk.CTkLabel(testers_frame, text="• Xtreme Plabon", font=ctk.CTkFont(family="Courier", size=14, weight="bold"), text_color="#EAEAEA").pack(anchor="center", pady=10)
        ctk.CTkLabel(credits_win, text="Thank you for making VibeStream amazing! 🤍", font=ctk.CTkFont(size=11, italic=True), text_color=self.c["muted"]).pack(pady=10)

    def change_visualizer_template(self, choice):
        self.current_visualizer_template = choice

    def update_avee_visualizer(self):
        cw = self.bg_canvas.winfo_width()
        ch = self.bg_canvas.winfo_height()
        
        if cw < 300 or ch < 300: 
            self.after(100, self.update_avee_visualizer)
            return
            
        self.bg_canvas.delete("visualizer")
        self.bg_canvas.delete("live_lyrics") 
        bass_factor = self.slider_bass.get()

        for i in range(self.num_bars):
            if self.is_playing and not self.is_paused:
                target = random.uniform(4, 65) * bass_factor
                self.bar_magnitudes[i] += (target - self.bar_magnitudes[i]) * 0.3
            else:
                self.bar_magnitudes[i] += (2 - self.bar_magnitudes[i]) * 0.2

        # ─── 📝 RENDER FLOATING TRANSPARENT LYRICS ───
        lyric_y = ch * 0.71
        self.bg_canvas.create_text(
            cw / 2, lyric_y, text=self.current_lyrics_text, 
            font=ctk.CTkFont(family="Helvetica", size=22, weight="bold"), 
            fill=self.c["accent"] if "Genius" not in self.current_lyrics_text else self.c["muted"], 
            justify="center", anchor="center", tags="live_lyrics"
        )

        # ─── טেমপ্লেট ১: CIRCULAR AVEE ───
        if self.current_visualizer_template == "Circular Avee":
            cx, cy = cw / 2, ch * 0.35
            for i in range(self.num_bars):
                angle = (i / self.num_bars) * 2 * math.pi
                x_start = cx + self.circle_radius * math.cos(angle)
                y_start = cy + self.circle_radius * math.sin(angle)
                x_end = cx + (self.circle_radius + self.bar_magnitudes[i]) * math.cos(angle)
                y_end = cy + (self.circle_radius + self.bar_magnitudes[i]) * math.sin(angle)
                self.bg_canvas.create_line(x_start, y_start, x_end, y_end, fill=self.c["accent"], width=5, capstyle="round", tags="visualizer")

        # ─── טেমপ্লেট ২: BOTTOM WAVES ───
        elif self.current_visualizer_template == "Bottom Waves":
            bar_width = cw / self.num_bars
            baseline_y = ch * 0.62 
            for i in range(self.num_bars):
                x_pos = i * bar_width + (bar_width / 2)
                height = self.bar_magnitudes[i] * 1.5
                self.bg_canvas.create_line(x_pos, baseline_y, x_pos, baseline_y - height, fill=self.c["accent"], width=int(bar_width*0.7), capstyle="round", tags="visualizer")

        # ─── טেমপ্লেট ৩: PULSE STAR ───
        elif self.current_visualizer_template == "Pulse Star":
            cx, cy = cw / 2, ch * 0.35
            avg_magnitude = sum(self.bar_magnitudes) / self.num_bars
            dynamic_radius = self.circle_radius + (avg_magnitude * 0.8)
            self.bg_canvas.create_oval(cx - dynamic_radius, cy - dynamic_radius, cx + dynamic_radius, cy + dynamic_radius, outline=self.c["accent"], width=8, tags="visualizer")
            for i in range(0, self.num_bars, 2):
                angle = (i / self.num_bars) * 2 * math.pi
                x_start = cx + dynamic_radius * math.cos(angle)
                y_start = cy + dynamic_radius * math.sin(angle)
                x_end = cx + (dynamic_radius + self.bar_magnitudes[i]*1.2) * math.cos(angle)
                y_end = cy + (dynamic_radius + self.bar_magnitudes[i]*1.2) * math.sin(angle)
                self.bg_canvas.create_line(x_start, y_start, x_end, y_end, fill=self.c["accent"], width=4, tags="visualizer")

        # ─── ტেমপ্লেট ৪: WHATSAPP MESSAGE VISUALIZER ───
        elif self.current_visualizer_template == "WhatsApp Message":
            msg_width = cw * 0.45
            msg_height = 85
            cx, cy = cw / 2, ch * 0.38
            x1, y1 = cx - (msg_width / 2), cy - (msg_height / 2)
            x2, y2 = cx + (msg_width / 2), cy + (msg_height / 2)
            
            self.bg_canvas.create_rounded_rect(x1, y1, x2, y2, radius=15, fill="#121D25", outline="#1F2C34", width=1, tags="visualizer")
            play_x, play_y = x1 + 35, cy - 5
            self.bg_canvas.create_oval(play_x - 14, play_y - 14, play_x + 14, play_y + 14, fill="", outline="#8696A0", width=2, tags="visualizer")
            
            if self.is_playing and not self.is_paused:
                self.bg_canvas.create_line(play_x - 4, play_y - 6, play_x - 4, play_y + 6, fill="#8696A0", width=3, tags="visualizer")
                self.bg_canvas.create_line(play_x + 4, play_y - 6, play_x + 4, play_y + 6, fill="#8696A0", width=3, tags="visualizer")
            else:
                self.bg_canvas.create_polygon(play_x - 4, play_y - 7, play_x + 8, play_y, play_x - 4, play_y + 7, fill="#8696A0", tags="visualizer")
            
            self.bg_canvas.create_text(x1 + 75, y1 + 18, text="ATTA", font=ctk.CTkFont(family="Helvetica", size=13, weight="bold"), fill="#E9EDEF", anchor="w", tags="visualizer")
            self.bg_canvas.create_text(x2 - 75, y1 + 18, text="03410989787", font=ctk.CTkFont(family="Helvetica", size=11), fill="#8696A0", anchor="e", tags="visualizer")
            self.bg_canvas.create_text(x1 + 75, y2 - 18, text=self.lbl_current_time.cget("text"), font=ctk.CTkFont(family="Helvetica", size=11), fill="#8696A0", anchor="w", tags="visualizer")

            wave_start_x = x1 + 75
            wave_max_end_x = x2 - 75
            step = 5
            total_possible_bars = int((wave_max_end_x - wave_start_x) / step)
            for i in range(total_possible_bars):
                x_pos = wave_start_x + (i * step)
                height = max(3, self.bar_magnitudes[i % self.num_bars] * 0.45)
                self.bg_canvas.create_line(x_pos, cy + 5 - (height / 2), x_pos, cy + 5 + (height / 2), fill=self.c["accent"], width=3, capstyle="round", tags="visualizer")

            mic_x, mic_y = x2 - 35, cy
            self.bg_canvas.create_oval(mic_x - 18, mic_y - 18, mic_x + 18, mic_y + 18, fill="#00A884", outline="", tags="visualizer") 
            self.bg_canvas.create_text(mic_x, mic_y, text="🎙️", font=ctk.CTkFont(size=14), tags="visualizer")

        if self.bg_canvas.find_withtag("bg_pic"):
            self.bg_canvas.tag_raise("visualizer", "bg_pic")
            self.bg_canvas.tag_raise("live_lyrics", "bg_pic")

        # 🎥 Capture frames safely if recording
        if self.is_recording_video and VIDEO_EXPORT_AVAILABLE:
            self.capture_canvas_frame()

        self.lbl_bass.configure(text=f"Bass Boost: {float(bass_factor):.1f}x")
        self.after(40, self.update_avee_visualizer)

    def toggle_video_recording(self):
        # টগল করার আগে রান-টাইম মডিউল রিলোড নিশ্চিত করা
        global VIDEO_EXPORT_AVAILABLE, cv2, np
        try:
            import cv2
            import numpy as np
            VIDEO_EXPORT_AVAILABLE = True
        except ImportError:
            VIDEO_EXPORT_AVAILABLE = False

        if not VIDEO_EXPORT_AVAILABLE:
            ctk.filedialog.messagebox.showerror("Error", "OpenCV & NumPy are downloading or failed!\nPlease wait a moment and try again.")
            return
        if not self.is_playing:
            ctk.filedialog.messagebox.showwarning("Warning", "Play a song first to record video!")
            return

        if not self.is_recording_video:
            self.video_frames = []
            self.is_recording_video = True
            self.btn_export_video.configure(text="🛑 Stop & Save Video", fg_color="red", text_color="white")
        else:
            self.is_recording_video = False
            self.btn_export_video.configure(text="⌛ Processing MP4...", fg_color="gray", state="disabled")
            threading.Thread(target=self.save_recorded_video_file, daemon=True).start()

    def capture_canvas_frame(self):
        try:
            self.update_idletasks()
            x = self.bg_canvas.winfo_rootx()
            y = self.bg_canvas.winfo_rooty()
            w = self.bg_canvas.winfo_width()
            h = self.bg_canvas.winfo_height()
            
            from PIL import ImageGrab
            cap_img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            frame_np = cv2.cvtColor(np.array(cap_img), cv2.COLOR_RGB2BGR)
            self.video_frames.append(frame_np)
        except Exception:
            pass

    def save_recorded_video_file(self):
        if not self.video_frames:
            self.reset_video_export_btn()
            return
        
        save_path = ctk.filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 Video", "*.mp4")])
        if save_path:
            try:
                height, width, _ = self.video_frames[0].shape
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video_writer = cv2.VideoWriter(save_path, fourcc, 20.0, (width, height))
                
                for frame in self.video_frames:
                    video_writer.write(frame)
                video_writer.release()
                
                ctk.filedialog.messagebox.showinfo("Success 🎉", f"Video exported successfully!\nSaved at: {save_path}")
            except Exception as e:
                ctk.filedialog.messagebox.showerror("Error", f"Failed to compile video: {e}")
        
        self.reset_video_export_btn()

    def reset_video_export_btn(self):
        self.video_frames = []
        self.btn_export_video.configure(text="📹 Export Live Video (MP4)", fg_color="#291a03", text_color="#FF9900", state="normal")

    def check_for_updates(self):
        try:
            res = requests.get(VERSION_URL, timeout=5)
            if res.status_code == 200 and res.text.strip() != CURRENT_VERSION:
                self.after(1000, lambda: self.show_update_dialog(res.text.strip()))
        except Exception: pass  

    def show_update_dialog(self, new_version):
        self.update_win = ctk.CTkToplevel(self)
        self.update_win.title("Update Available! 🎉")
        self.update_win.geometry("400x200")
        self.update_win.resizable(False, False)
        self.update_win.lift(); self.update_win.attributes("-topmost", True)
        
        lbl = ctk.CTkLabel(self.update_win, text=f"A new version ({new_version}) is available!\nDo you want to update VibeStream now?", font=ctk.CTkFont(size=14, weight="bold"))
        lbl.pack(pady=30)
        
        btn_frame = ctk.CTkFrame(self.update_win, fg_color="transparent")
        btn_frame.pack(pady=10)
        btn_yes = ctk.CTkButton(btn_frame, text="Update Now", fg_color=self.c["accent"], text_color="black", font=ctk.CTkFont(weight="bold"), command=self.start_download_update)
        btn_yes.pack(side="left", padx=10)
        btn_no = ctk.CTkButton(btn_frame, text="Later", fg_color="#333333", command=self.update_win.destroy)
        btn_no.pack(side="left", padx=10)

    def start_download_update(self):
        for widget in self.update_win.winfo_children(): widget.destroy()
        lbl_status = ctk.CTkLabel(self.update_win, text="Downloading VibeStream Update... ⚡", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_status.pack(pady=50); self.update_win.update()
        
        def download_worker():
            try:
                is_compiled = getattr(sys, 'frozen', False)
                current_path = os.path.abspath(sys.argv[0])
                current_dir = os.path.dirname(current_path)
                res = requests.get(CODE_URL, timeout=30, stream=True)
                
                if res.status_code == 200:
                    if is_compiled:
                        new_exe_path = os.path.join(current_dir, "VibeStream_New.exe")
                        with open(new_exe_path, "wb") as f:
                            for chunk in res.iter_content(chunk_size=8192):
                                if chunk: f.write(chunk)
                        
                        lbl_status.configure(text="Applying updates... Restarting App! 🔄"); self.update_win.update()
                        time.sleep(1.5)
                        
                        bat_path = os.path.join(current_dir, "update_installer.bat")
                        with open(bat_path, "w") as bat:
                            bat.write('@echo off\n')
                            bat.write('timeout /t 2 /nobreak > nul\n')  
                            bat.write(f'del "{current_path}"\n')          
                            bat.write(f'rename "{new_exe_path}" "{os.path.basename(current_path)}"\n') 
                            bat.write(f'start "" "{current_path}"\n')     
                            bat.write('del "%~f0"\n')                    
                        
                        os.startfile(bat_path); self.destroy(); sys.exit()
                    else:
                        temp_script = current_path + ".tmp"
                        with open(temp_script, "w", encoding="utf-8") as f: f.write(res.text)
                        if os.path.exists(temp_script) and os.path.getsize(temp_script) > 1000:
                            if os.path.exists(current_path): os.remove(current_path)
                            os.rename(temp_script, current_path)
                            lbl_status.configure(text="Update Success! Restarting... 🔄"); self.update_win.update()
                            time.sleep(2)
                            os.execv(sys.executable, ['python', f'"{current_path}"'])
            except Exception:
                lbl_status.configure(text="Update failed! File is system locked.")
                
        threading.Thread(target=download_worker, daemon=True).start()

    def toggle_window_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes('-fullscreen', self.is_fullscreen)
        self.after(200, self.pre_cache_and_render_background)

    def on_window_resize(self, event):
        if event.widget == self: self.pre_cache_and_render_background()

    def toggle_playlist_dropdown(self):
        if self.playlist_expanded:
            self.playlist_box.grid_forget()
            self.btn_expand_playlist.configure(text="▼ Expand Playlist Tracks")
            self.playlist_expanded = False
        else:
            self.playlist_box.grid(row=6, column=0, sticky="nsew", padx=20, pady=(0, 15))
            self.btn_expand_playlist.configure(text="▲ Collapse Playlist Tracks")
            self.playlist_expanded = True

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar.place_forget(); self.sidebar_visible = False
            self.btn_menu.configure(text="☰ Open Menu", fg_color="#1F1F1F", text_color="white")
            if self.cached_normal_bg:
                self.bg_canvas.delete("bg_pic")
                self.bg_canvas.create_image(0, 0, image=self.cached_normal_bg, anchor="nw", tags="bg_pic")
        else:
            self.sidebar.place(x=0, y=0, relheight=1); self.sidebar_visible = True
            self.btn_menu.configure(text="✕ Close Menu", fg_color=self.c["accent"], text_color="black")
            if self.cached_sidebar_bg:
                self.bg_canvas.delete("bg_pic")
                self.bg_canvas.create_image(0, 0, image=self.cached_sidebar_bg, anchor="nw", tags="bg_pic")
            
        self.sidebar.lift(); self.btn_menu.lift()           

    def save_settings(self, folder_path=None):
        existing = {}
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f: existing = json.load(f)
            except Exception: pass
        if folder_path: existing["last_folder"] = folder_path
        if self.bg_image_path: existing["custom_wallpaper"] = self.bg_image_path
        try:
            with open(SETTINGS_FILE, "w") as f: json.dump(existing, f)
        except Exception: pass

    def load_saved_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    saved = json.load(f)
                    if saved.get("custom_wallpaper") and os.path.exists(saved["custom_wallpaper"]):
                        self.bg_image_path = saved["custom_wallpaper"]
                    if saved.get("last_folder") and os.path.exists(saved["last_folder"]): 
                        self.load_music_from_path(saved["last_folder"])
            except Exception: pass

    def upload_bg_image(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp")])
        if file_path:
            self.bg_image_path = file_path; self.save_settings() 
            self.pre_cache_and_render_background()

    def pre_cache_and_render_background(self):
        self.update_idletasks()
        cw = self.bg_canvas.winfo_width()
        ch = self.bg_canvas.winfo_height()
        if cw < 200 or ch < 200: return

        if self.bg_image_path:
            try:
                img = Image.open(self.bg_image_path)
                ow, oh = img.size
                win_aspect, img_aspect = cw / ch, ow / oh
                if img_aspect > win_aspect:
                    nh = ch; nw = int(nh * img_aspect)
                else:
                    nw = cw; nh = int(nw / img_aspect)

                img = img.resize((nw, nh), Image.Resampling.LANCZOS)
                cropped = img.crop(((nw - cw)/2, (nh - ch)/2, (nw - cw)/2 + cw, (nh - ch)/2 + ch)).convert('RGBA')
                overlay_color = tuple(int(self.c["overlay"].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                
                self.cached_normal_bg = ImageTk.PhotoImage(Image.alpha_composite(cropped, Image.new('RGBA', cropped.size, (*overlay_color, 150))).convert('RGB'))
                self.cached_sidebar_bg = ImageTk.PhotoImage(Image.alpha_composite(cropped, Image.new('RGBA', cropped.size, (*overlay_color, 220))).convert('RGB'))

                self.bg_canvas.delete("bg_pic")
                self.bg_canvas.create_image(0, 0, image=self.cached_sidebar_bg if self.sidebar_visible else self.cached_normal_bg, anchor="nw", tags="bg_pic")
                self.bg_canvas.tag_lower("bg_pic")
            except Exception: self.bg_canvas.configure(bg=self.c["overlay"])
        else: self.bg_canvas.configure(bg=self.c["overlay"])

    def parse_lrc_content(self, lines):
        self.synced_lyrics = []
        simulated_time = 0
        for line in lines:
            line = line.strip()
            if not line: continue
            match = re.match(r'\[(\d+):(\d+)[\.:](\d+)\](.*)', line)
            if match:
                minutes, seconds, _, text = match.groups()
                self.synced_lyrics.append((int(minutes) * 60 + int(seconds), text.strip()))
            else:
                self.synced_lyrics.append((simulated_time, line))
                simulated_time += 4

    def upload_manual_lrc_file(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("LRC/TXT Files", "*.lrc;*.txt")])
        if file_path:
            self.last_highlighted_index = -1
            try:
                with open(file_path, "r", encoding="utf-8") as f: lines = f.readlines()
                self.parse_lrc_content(lines)
                self.current_lyrics_text = "Custom Lyrics Loaded Successfully! 🎧"
            except Exception: self.current_lyrics_text = "Error loading custom lyrics file."

    def fetch_lyrics_async(self, track_path):
        self.synced_lyrics = []; self.last_highlighted_index = -1
        self.current_lyrics_text = "Searching Live Lyrics from Genius API... 🔍"
        
        track_dir = os.path.dirname(track_path)
        base_name_no_ext = os.path.splitext(os.path.basename(track_path))[0]
        local_lrc_path = os.path.join(track_dir, base_name_no_ext + ".lrc")
        
        if os.path.exists(local_lrc_path):
            try:
                with open(local_lrc_path, "r", encoding="utf-8") as f: lines = f.readlines()
                self.parse_lrc_content(lines)
                self.current_lyrics_text = "Offline Synchronized Lyrics Loaded! 💾"
                return
            except Exception: pass

        def run_api_call():
            cleaned = re.sub(r'^\d+[\s.\-_]*|\[.*?\]|\(.*?\)|[^\w\s\-]', '', base_name_no_ext).replace("_", " ").replace("-", " ").strip()
            headers = {"Authorization": f"Bearer {GENIUS_ACCESS_TOKEN}"}
            search_url = f"https://api.genius.com/search?q={urllib.parse.quote(cleaned)}"
            
            try:
                res = requests.get(search_url, headers=headers, timeout=8)
                if res.status_code == 200 and res.json().get("response", {}).get("hits"):
                    lyrics_res = requests.get(f"https://lyrist.vercel.app/api/{urllib.parse.quote(cleaned)}", timeout=8)
                    if lyrics_res.status_code == 200 and lyrics_res.json().get("lyrics"):
                        lines = lyrics_res.json().get("lyrics").split('\n')
                        self.parse_lrc_content(lines)
                        self.current_lyrics_text = ""
                        try:
                            with open(local_lrc_path, "w", encoding="utf-8") as f:
                                st = 0
                                for l in lines:
                                    if l.strip(): f.write(f"[{st // 60:02d}:{st % 60:02d}.00] {l.strip()}\n"); st += 4
                        except Exception: pass
                        return
                
                alt_res = requests.get(f"https://lyrist.vercel.app/api/{urllib.parse.quote(cleaned)}", timeout=8)
                if alt_res.status_code == 200 and alt_res.json().get("lyrics"):
                    self.parse_lrc_content(alt_res.json().get("lyrics").split('\n'))
                    self.current_lyrics_text = ""
                else: self.current_lyrics_text = "Lyrics not found in Genius database."
            except Exception: self.current_lyrics_text = "Lyrics fetch error. Ready for manual upload! 📇"

        threading.Thread(target=run_api_call, daemon=True).start()

    def lyrics_sync_loop(self):
        while True:
            if self.is_playing and not self.is_paused and self.synced_lyrics:
                cp = self.current_time_offset
                target_idx = -1
                for i, (ts, _) in enumerate(self.synced_lyrics):
                    if cp >= ts: target_idx = i
                    else: break
                if target_idx != -1 and target_idx != self.last_highlighted_index:
                    self.last_highlighted_index = target_idx
                    _, self.current_lyrics_text = self.synced_lyrics[target_idx]
            time.sleep(0.15)

    def change_theme(self, choice):
        self.current_theme_name = choice; self.c = self.themes[choice]
        self.pre_cache_and_render_background()
        self.sidebar.configure(fg_color=self.c["card_bg"]); self.controls_bar.configure(fg_color=self.c["card_bg"])
        self.slider_progress.configure(progress_color=self.c["accent"], button_color=self.c["accent"])
        self.btn_play.configure(fg_color=self.c["accent"])
        self.slider_bass.configure(progress_color=self.c["accent"], button_color=self.c["accent"])
        if self.sidebar_visible: self.btn_menu.configure(fg_color=self.c["accent"])
        self.btn_manual_lrc.configure(text_color=self.c["muted"])
        self.update_playlist_ui()

    def import_folder(self):
        fp = ctk.filedialog.askdirectory()
        if fp: self.load_music_from_path(fp); self.save_settings(fp)

    def load_music_from_path(self, fp):
        self.playlist = [os.path.join(fp, f) for f in os.listdir(fp) if f.endswith(".mp3")]
        self.update_playlist_ui()

    def format_time(self, sec): return f"{int(sec // 60)}:{int(sec % 60):02d}"

    def update_playlist_ui(self):
        for w in self.playlist_box.winfo_children(): w.destroy()
        for idx, track in enumerate(self.playlist):
            ctk.CTkButton(
                self.playlist_box, text=f" {idx+1:02d}.  {os.path.basename(track)[:26]}...", anchor="w",
                fg_color="transparent", text_color="white", hover_color="#1F1F1F",
                height=38, corner_radius=6, command=lambda i=idx: self.play_track(i)
            ).pack(fill="x", pady=2)

    def play_track(self, index):
        if index >= len(self.playlist) or index < 0: return
        self.current_index = index; track = self.playlist[self.current_index]
        try:
            self.song_length = MP3(track).info.length
            self.current_time_offset = 0; self.start_timestamp = time.time()
            self.slider_progress.configure(to=self.song_length)
            self.lbl_total_time.configure(text=self.format_time(self.song_length))
            pygame.mixer.music.load(track); pygame.mixer.music.play()
            self.is_playing = True; self.is_paused = False; self.btn_play.configure(text="⏸")
            self.lbl_track_name.configure(text=os.path.basename(track)[:35])
            self.fetch_lyrics_async(track)
        except Exception as e: print(f"Error: {e}")

    def toggle_play(self):
        if not self.playlist: return
        if not self.is_playing: self.play_track(self.current_index)
        elif self.is_paused: pygame.mixer.music.unpause(); self.start_timestamp = time.time() - self.current_time_offset; self.is_paused = False; self.btn_play.configure(text="⏸")
        else: pygame.mixer.music.pause(); self.is_paused = True; self.btn_play.configure(text="▶")

    def next_track(self):
        if not self.playlist: return
        if self.is_looping: self.play_track(self.current_index); return
        if self.is_shuffling: self.play_track(random.randint(0, len(self.playlist) - 1)); return
        self.play_track((self.current_index + 1) % len(self.playlist))

    def prev_track(self):
        if self.playlist: self.play_track((self.current_index - 1) % len(self.playlist))

    def slide_progress(self, event):
        if self.is_playing:
            np = self.slider_progress.get()
            pygame.mixer.music.play(start=float(np))
            self.current_time_offset = np; self.start_timestamp = time.time() - self.current_time_offset
            if self.is_paused: pygame.mixer.music.pause()

    def set_volume(self, val): pygame.mixer.music.set_volume(float(val))
    def toggle_shuffle(self): self.is_shuffling = not self.is_shuffling; self.btn_shuffle.configure(text_color=self.c["accent"] if self.is_shuffling else self.c["muted"])
    def toggle_loop(self): self.is_looping = not self.is_looping; self.btn_loop.configure(text_color=self.c["accent"] if self.is_looping else self.c["muted"])

    def update_progress_loop(self):
        while True:
            if self.is_playing and not self.is_paused:
                if not pygame.mixer.music.get_busy(): self.after(100, self.next_track); time.sleep(1); continue
                calc = time.time() - self.start_timestamp
                if calc <= self.song_length:
                    self.current_time_offset = calc
                    self.lbl_current_time.configure(text=self.format_time(calc))
                    self.slider_progress.set(calc)
            time.sleep(0.5)


if __name__ == "__main__":
    app = UltimateFullAppPlayer()
    app.mainloop()