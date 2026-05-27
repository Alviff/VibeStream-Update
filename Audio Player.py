import sys
import warnings
import subprocess

warnings.filterwarnings("ignore")

# 📦 1. AUTO-DEPENDENCY INSTALLER
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
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name, "--quiet", "--no-cache-dir"])
            except Exception as e:
                print(f"Could not install {pip_name} automatically: {e}")

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
import hashlib
import customtkinter as ctk
import pygame
from mutagen.mp3 import MP3
from PIL import Image, ImageTk, ImageDraw  

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
USER_DATA_FILE = "user_profile_data.json" 
GENIUS_ACCESS_TOKEN = "5G_5bJ5jL6Ejfn8IVcMIHUEyvNKeO_UPo3uXj20lq09Qz5FrUxJHU2_1_FbzHpvWrJPxnR88JCmWIYn9C_yqkg"

ctk.set_appearance_mode("Dark")

def _create_rounded_rect(self, x1, y1, x2, y2, radius=10, **kwargs):
    points = [
        x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1, x2, y1+radius, x2, y1+radius, 
        x2, y2-radius, x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2, 
        x1, y2, x1, y2-radius, x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1
    ]
    return self.create_polygon(points, **kwargs, smooth=True)

# Safe injection
if not hasattr(ctk.CTkCanvas, "create_rounded_rect"):
    ctk.CTkCanvas.create_rounded_rect = _create_rounded_rect


class VibeStreamImmersivePlayer(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title(f"VibeStream - Immersive Theater Edition (v{CURRENT_VERSION})")
        self.is_fullscreen = True
        self.attributes('-fullscreen', self.is_fullscreen)
        self.bind("<Escape>", self.toggle_window_fullscreen)  
        
        self.themes = {
            "Spotify Green": {"text": "#FFFFFF", "muted": "#A7A7A7", "accent": "#1ED760", "card_bg": "#121212", "overlay": "#0A0A0A"},
            "Cyberpunk Pink": {"text": "#FFFFFF", "muted": "#A0A0A0", "accent": "#FF007F", "card_bg": "#0B0014", "overlay": "#050008"},
            "Neon Blue": {"text": "#FFFFFF", "muted": "#909090", "accent": "#00E5FF", "card_bg": "#0A1118", "overlay": "#03080C"},
            "Blood Red": {"text": "#FFFFFF", "muted": "#A0A0A0", "accent": "#FF3333", "card_bg": "#140A0A", "overlay": "#080303"}
        }
        self.current_theme_name = "Spotify Green"
        self.c = self.themes[self.current_theme_name]
        self.configure(fg_color=self.c["overlay"])

        # Core State
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
        self.profile_menu_open = False
        self.showing_profile_dashboard = False
        
        # User Data Defaults
        self.user_profile = {
            "username": "Guest",
            "password": "",
            "display_name": "BrokenMelody",
            "bio": "No bio added yet",
            "pfp_path": "",
            "remember_me": False
        }
        
        self.synced_lyrics = []  
        self.last_highlighted_index = -1
        self.bg_image_path = None
        self.current_lyrics_text = "Lyrics will flow smoothly right here! 🎧"
        
        self.num_bars = 100  
        self.circle_radius = 110  
        self.bar_magnitudes = [0.0] * self.num_bars
        self.current_visualizer_template = "Circular Avee"

        # ─── MAIN CANVAS ───
        self.bg_canvas = ctk.CTkCanvas(self, bg=self.c["overlay"], highlightthickness=0, bd=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.load_user_profile_data()
        self.check_account_auth()

    # 🔒 SIGNUP & LOGIN SYSTEM (WITH REMEMBER ME)
    def load_user_profile_data(self):
        if os.path.exists(USER_DATA_FILE):
            try:
                with open(USER_DATA_FILE, "r") as f:
                    self.user_profile.update(json.load(f))
            except Exception: pass

    def save_user_profile_data(self):
        try:
            with open(USER_DATA_FILE, "w") as f:
                json.dump(self.user_profile, f)
        except Exception: pass

    def check_account_auth(self):
        if not self.user_profile.get("password"):
            self.show_signup_screen()
        elif self.user_profile.get("remember_me"):
            self.initialize_main_player()
        else:
            self.show_login_screen()

    def show_signup_screen(self):
        self.auth_frame = ctk.CTkFrame(self, width=420, height=380, corner_radius=15, fg_color=self.c["card_bg"])
        self.auth_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.auth_frame.grid_propagate(False)

        ctk.CTkLabel(self.auth_frame, text="Create Local VibeStream Account 🎉", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
        self.ent_username = ctk.CTkEntry(self.auth_frame, width=280, placeholder_text="Username")
        self.ent_username.pack(pady=8)
        self.ent_display = ctk.CTkEntry(self.auth_frame, width=280, placeholder_text="Display Name (e.g. BrokenMelody)")
        self.ent_display.pack(pady=8)
        self.ent_password = ctk.CTkEntry(self.auth_frame, width=280, placeholder_text="Password", show="*")
        self.ent_password.pack(pady=8)
        self.lbl_auth_error = ctk.CTkLabel(self.auth_frame, text="", text_color="red")
        self.lbl_auth_error.pack(pady=2)

        ctk.CTkButton(self.auth_frame, text="Create Account", fg_color=self.c["accent"], text_color="black", font=ctk.CTkFont(weight="bold"), command=self.process_signup).pack(pady=15)

    def process_signup(self):
        user = self.ent_username.get().strip()
        disp = self.ent_display.get().strip() or user
        pwd = self.ent_password.get().strip()
        if not user or not pwd:
            self.lbl_auth_error.configure(text="Username and Password required!")
            return
        
        hashed_pwd = hashlib.sha256(pwd.encode()).hexdigest()
        self.user_profile.update({"username": user, "display_name": disp, "password": hashed_pwd})
        self.save_user_profile_data()
        self.auth_frame.destroy()
        self.show_login_screen()

    def show_login_screen(self):
        self.auth_frame = ctk.CTkFrame(self, width=400, height=360, corner_radius=15, fg_color=self.c["card_bg"])
        self.auth_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.auth_frame.grid_propagate(False)

        ctk.CTkLabel(self.auth_frame, text="🔒 Unlock Player Profile", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=25)
        self.ent_login_user = ctk.CTkEntry(self.auth_frame, width=280, placeholder_text="Username")
        self.ent_login_user.insert(0, self.user_profile.get("username", ""))
        self.ent_login_user.pack(pady=8)
        self.ent_login_pwd = ctk.CTkEntry(self.auth_frame, width=280, placeholder_text="Password", show="*")
        self.ent_login_pwd.pack(pady=8)
        
        self.cb_remember = ctk.CTkCheckBox(self.auth_frame, text="Remember Me (Auto-Login)", font=ctk.CTkFont(size=12), fg_color=self.c["accent"])
        self.cb_remember.pack(pady=5)
        
        self.lbl_auth_error = ctk.CTkLabel(self.auth_frame, text="", text_color="red")
        self.lbl_auth_error.pack(pady=2)

        ctk.CTkButton(self.auth_frame, text="Sign In", fg_color=self.c["accent"], text_color="black", font=ctk.CTkFont(weight="bold"), command=self.process_login).pack(pady=15)

    def process_login(self):
        user = self.ent_login_user.get().strip()
        pwd = self.ent_login_pwd.get().strip()
        hashed = hashlib.sha256(pwd.encode()).hexdigest()
        
        if self.user_profile.get("username") == user and self.user_profile.get("password") == hashed:
            self.user_profile["remember_me"] = bool(self.cb_remember.get())
            self.save_user_profile_data()
            self.auth_frame.destroy()
            self.initialize_main_player()
        else:
            self.lbl_auth_error.configure(text="Invalid credentials!")

    def generate_circular_pfp(self, path=None, size=(50, 50)):
        try:
            if path and os.path.exists(path):
                img = Image.open(path).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
            else:
                img = Image.new("RGBA", size, "#1ED760" if "Green" in self.current_theme_name else "#00E5FF")
            
            mask = Image.new("L", size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + size, fill=255)
            
            output = Image.new("RGBA", size, (0,0,0,0))
            output.paste(img, (0, 0), mask=mask)
            return ctk.CTkImage(light_image=output, dark_image=output, size=size)
        except Exception:
            return None

    def initialize_main_player(self):
        self.setup_layout()
        
        # Open Menu Button
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
        # Sidebar Base
        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=0, fg_color=self.c["card_bg"])
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(6, weight=1) 

        # 👤 SIDEBAR PROFILE WIDGET
        self.profile_widget = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=70)
        self.profile_widget.grid(row=0, column=0, sticky="ew", padx=20, pady=(75, 10))
        self.profile_widget.pack_propagate(False)
        
        self.pfp_image = self.generate_circular_pfp(self.user_profile.get("pfp_path"), size=(46, 46))
        self.btn_pfp_trigger = ctk.CTkButton(
            self.profile_widget, image=self.pfp_image, text="", width=46, height=46,
            fg_color="transparent", hover_color="#222222", command=self.toggle_profile_menu
        )
        self.btn_pfp_trigger.pack(side="left", padx=(0, 10))
        
        meta_sub = ctk.CTkFrame(self.profile_widget, fg_color="transparent")
        meta_sub.pack(side="left", fill="y", pady=8)
        self.lbl_side_name = ctk.CTkLabel(meta_sub, text=self.user_profile.get("display_name"), font=ctk.CTkFont(size=14, weight="bold"), text_color="white", anchor="w")
        self.lbl_side_name.pack(anchor="w")
        
        self.btn_menu_arrow = ctk.CTkButton(meta_sub, text="Profile Options ▾", font=ctk.CTkFont(size=11), text_color=self.c["muted"], fg_color="transparent", width=80, height=15, hover=False, command=self.toggle_profile_menu)
        self.btn_menu_arrow.pack(anchor="w")

        # Config Box
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
            self.config_box, values=["Circular Avee", "Bottom Waves", "Pulse Star", "WhatsApp Message"], fg_color="#1F1F1F", button_color="#2D2D2D",
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

        # Video Export Button
        self.btn_export_video = ctk.CTkButton(
            self.sidebar, text="📹 Export Live Video (MP4)", font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#291a03", text_color="#FF9900", hover_color="#422b07", height=34, corner_radius=8,
            command=self.toggle_video_recording
        )
        self.btn_export_video.grid(row=2, column=0, sticky="ew", padx=20, pady=5)

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

        # Custom Lyrics Upload Panel
        self.center_lyrics_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.center_lyrics_panel.place(relx=0.5, rely=0.76, relwidth=0.65, relheight=0.06, anchor="center")

        self.btn_manual_lrc = ctk.CTkButton(
            self.center_lyrics_panel, text="📇 Upload Custom .LRC / .TXT File", font=ctk.CTkFont(size=11, weight="bold"),
            width=210, height=30, fg_color="#141414", text_color="#A7A7A7", hover_color="#252525", corner_radius=8,
            command=self.upload_manual_lrc_file
        )
        self.btn_manual_lrc.pack(side="bottom", pady=2)

        # ─── CONTROLS BAR LAYER ───
        self.controls_bar = ctk.CTkFrame(self, height=100, corner_radius=20, fg_color=self.c["card_bg"])
        self.controls_bar.place(relx=0.5, rely=0.92, relwidth=0.92, anchor="center")
        self.controls_bar.grid_propagate(False)
        
        self.controls_bar.grid_columnconfigure(0, weight=1) 
        self.controls_bar.grid_columnconfigure(1, weight=2) 
        self.controls_bar.grid_columnconfigure(2, weight=1) 

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

        self.meta_frame = ctk.CTkFrame(self.controls_bar, fg_color="transparent")
        self.meta_frame.grid(row=1, column=0, sticky="w", padx=30)
        self.lbl_track_name = ctk.CTkLabel(self.meta_frame, text="No Song Loaded", font=ctk.CTkFont(size=13, weight="bold"), text_color="white")
        self.lbl_track_name.pack(anchor="w")

        self.volume_frame = ctk.CTkFrame(self.controls_bar, fg_color="transparent")
        self.volume_frame.grid(row=1, column=2, padx=30, sticky="e")
        self.slider_volume = ctk.CTkSlider(self.volume_frame, width=80, from_=0, to=1, fg_color="#3E3E3E", progress_color="white", button_color="white", command=self.set_volume)
        self.slider_volume.set(0.7)
        self.slider_volume.pack(side="right")
        ctk.CTkLabel(self.volume_frame, text="🔊", text_color="white").pack(side="right", padx=5)

        # Floating Dropdown Menu Window For Profile Widget
        self.pop_menu = ctk.CTkFrame(self, width=150, height=130, corner_radius=10, fg_color="#181818", border_width=1, border_color="#282828")

    # 👤 SYSTEM DROPDOWN MENU & THEATER VIEW DASHBOARD
    def toggle_profile_menu(self):
        if self.profile_menu_open:
            self.pop_menu.place_forget()
            self.profile_menu_open = False
        else:
            for w in self.pop_menu.winfo_children(): w.destroy()
            
            ctk.CTkButton(self.pop_menu, text="👤 Profile", anchor="w", fg_color="transparent", hover_color="#252525", height=30, command=self.show_theater_profile_dashboard).pack(fill="x", padx=5, pady=2)
            ctk.CTkButton(self.pop_menu, text="🎨 Theme Settings", anchor="w", fg_color="transparent", hover_color="#252525", height=30, command=lambda: [self.toggle_profile_menu(), self.toggle_sidebar()]).pack(fill="x", padx=5, pady=2)
            ctk.CTkButton(self.pop_menu, text="🚪 Sign Out", anchor="w", fg_color="transparent", text_color="#FF3333", hover_color="#252525", height=30, command=self.process_sign_out).pack(fill="x", padx=5, pady=2)
            
            x = self.sidebar.winfo_width() - 170
            self.pop_menu.place(x=x, y=125)
            self.pop_menu.lift()
            self.profile_menu_open = True

    def process_sign_out(self):
        self.toggle_profile_menu()
        if self.sidebar_visible: self.toggle_sidebar()
        self.user_profile["remember_me"] = False
        self.save_user_profile_data()
        
        # Shutdown Main Widgets
        self.sidebar.place_forget()
        self.controls_bar.place_forget()
        if hasattr(self, 'dashboard_frame'): self.dashboard_frame.place_forget()
        self.show_login_screen()

    def show_theater_profile_dashboard(self):
        self.toggle_profile_menu()
        if self.sidebar_visible: self.toggle_sidebar()
        self.showing_profile_dashboard = True
        
        self.dashboard_frame = ctk.CTkFrame(self, fg_color="#0D0D0D", corner_radius=20)
        self.dashboard_frame.place(relx=0.5, rely=0.45, relwidth=0.75, relheight=0.68, anchor="center")
        
        # Back Button
        ctk.CTkButton(self.dashboard_frame, text="✕ Close Dashboard", width=120, height=32, fg_color="#222222", hover_color="#333333", command=self.close_profile_dashboard).place(x=20, y=20)
        
        # Banner View Look
        banner = ctk.CTkFrame(self.dashboard_frame, height=180, corner_radius=15, fg_color="transparent")
        banner.pack(fill="x", padx=20, pady=(70, 10))
        
        b_canvas = ctk.CTkCanvas(banner, height=180, highlightthickness=0)
        b_canvas.pack(fill="both", expand=True)
        self.update_idletasks()
        
        accent_color = self.c["accent"]
        b_canvas.create_rectangle(0, 0, 1500, 180, fill=accent_color, outline="")
        b_canvas.configure(bg="#221100") 

        dash_content = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        dash_content.pack(fill="both", expand=True, padx=40, pady=10)

        large_pfp = self.generate_circular_pfp(self.user_profile.get("pfp_path"), size=(110, 110))
        self.lbl_large_pfp = ctk.CTkLabel(dash_content, image=large_pfp, text="")
        self.lbl_large_pfp.place(x=10, y=10)

        self.lbl_dash_name = ctk.CTkLabel(dash_content, text=self.user_profile.get("display_name"), font=ctk.CTkFont(size=26, weight="bold"), text_color="white")
        self.lbl_dash_name.place(x=140, y=25)
        
        self.lbl_dash_handle = ctk.CTkLabel(dash_content, text=f"@{self.user_profile.get('username')}", font=ctk.CTkFont(size=13), text_color=self.c["muted"])
        self.lbl_dash_handle.place(x=145, y=65)

        btn_edit_profile = ctk.CTkButton(dash_content, text="📝 Edit Profile Info", width=130, height=34, fg_color="#1A1A1A", border_width=1, border_color="#333333", command=self.trigger_edit_profile_dialog)
        btn_edit_profile.place(x=145, y=95)

        ctk.CTkLabel(dash_content, text="About Profile", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.c["accent"]).place(x=10, y=150)
        
        self.bio_box = ctk.CTkFrame(dash_content, width=750, height=100, fg_color="#141414", corner_radius=12)
        self.bio_box.place(x=10, y=185, relwidth=0.95)
        
        # 🛠️ FIXED BUG HERE: 'italic=True' এর জায়গায় slant="italic" ব্যবহার করা হয়েছে
        self.lbl_dash_bio = ctk.CTkLabel(self.bio_box, text=self.user_profile.get("bio"), font=ctk.CTkFont(size=13, slant="italic"), text_color="white", justify="left", anchor="nw")
        self.lbl_dash_bio.place(x=15, y=15, relwidth=0.9, relheight=0.7)

    def trigger_edit_profile_dialog(self):
        edit_win = ctk.CTkToplevel(self)
        edit_win.title("Update Dashboard Metadata 📝")
        edit_win.geometry("400x320")
        edit_win.resizable(False, False)
        edit_win.lift(); edit_win.attributes("-topmost", True)
        
        ctk.CTkLabel(edit_win, text="Edit Display Settings", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=15)
        
        ent_disp = ctk.CTkEntry(edit_win, width=280, placeholder_text="New Display Name")
        ent_disp.insert(0, self.user_profile.get("display_name"))
        ent_disp.pack(pady=5)

        ent_bio = ctk.CTkEntry(edit_win, width=280, placeholder_text="Enter custom bio summary text")
        ent_bio.insert(0, self.user_profile.get("bio"))
        ent_bio.pack(pady=5)

        def select_pfp_file():
            fp = ctk.filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
            if fp: self.user_profile["pfp_path"] = fp

        ctk.CTkButton(edit_win, text="🖼️ Upload New Avatar PFP Image", fg_color="#222222", width=280, command=select_pfp_file).pack(pady=10)

        def save_edit_changes():
            self.user_profile["display_name"] = ent_disp.get().strip() or self.user_profile["display_name"]
            self.user_profile["bio"] = ent_bio.get().strip() or self.user_profile["bio"]
            self.save_user_profile_data()
            
            self.lbl_side_name.configure(text=self.user_profile["display_name"])
            updated_pfp = self.generate_circular_pfp(self.user_profile.get("pfp_path"), size=(46, 46))
            self.btn_pfp_trigger.configure(image=updated_pfp)
            
            self.lbl_dash_name.configure(text=self.user_profile["display_name"])
            
            if hasattr(self, 'lbl_dash_bio') and self.lbl_dash_bio.winfo_exists():
                self.lbl_dash_bio.configure(text=self.user_profile["bio"])
            if hasattr(self, 'lbl_large_pfp') and self.lbl_large_pfp.winfo_exists():
                large_pfp_updated = self.generate_circular_pfp(self.user_profile.get("pfp_path"), size=(110, 110))
                self.lbl_large_pfp.configure(image=large_pfp_updated)
            
            edit_win.destroy()

        ctk.CTkButton(edit_win, text="Save Changes", fg_color=self.c["accent"], text_color="black", font=ctk.CTkFont(weight="bold"), command=save_edit_changes).pack(pady=15)

    def close_profile_dashboard(self):
        if hasattr(self, 'dashboard_frame'):
            self.dashboard_frame.destroy()
        self.showing_profile_dashboard = False

    def show_credits_window(self):
        credits_win = ctk.CTkToplevel(self)
        credits_win.title("VibeStream - Production Team 🎖️")
        credits_win.geometry("450x420")
        credits_win.resizable(False, False)
        credits_win.lift(); credits_win.attributes("-topmost", True)
        
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

    # 🎛️ AUDIO VISUALIZER CORE LOGIC
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

        # ───🎤 TRANSPARENT LYRICS OVERLAY ───
        if not self.showing_profile_dashboard:
            lyric_y = ch * 0.69
            text_fill_color = self.c["muted"] if any(msg in self.current_lyrics_text for msg in ["Searching", "Network offline", "error"]) else self.c["text"]
            
            self.bg_canvas.create_text(
                cw / 2, lyric_y, text=self.current_lyrics_text, 
                font=ctk.CTkFont(family="Helvetica", size=23, weight="bold"), 
                fill=text_fill_color, justify="center", anchor="center", tags="live_lyrics"
            )

        # ─── VISUALIZER TEMPLATES ───
        if not self.showing_profile_dashboard:
            if self.current_visualizer_template == "Circular Avee":
                cx, cy = cw / 2, ch * 0.35
                for i in range(self.num_bars):
                    angle = (i / self.num_bars) * 2 * math.pi
                    x_start = cx + self.circle_radius * math.cos(angle)
                    y_start = cy + self.circle_radius * math.sin(angle)
                    x_end = cx + (self.circle_radius + self.bar_magnitudes[i]) * math.cos(angle)
                    y_end = cy + (self.circle_radius + self.bar_magnitudes[i]) * math.sin(angle)
                    self.bg_canvas.create_line(x_start, y_start, x_end, y_end, fill=self.c["accent"], width=5, capstyle="round", tags="visualizer")

            elif self.current_visualizer_template == "Bottom Waves":
                bar_width = cw / self.num_bars
                baseline_y = ch * 0.60 
                for i in range(self.num_bars):
                    x_pos = i * bar_width + (bar_width / 2)
                    height = self.bar_magnitudes[i] * 1.5
                    self.bg_canvas.create_line(x_pos, baseline_y, x_pos, baseline_y - height, fill=self.c["accent"], width=int(bar_width*0.7), capstyle="round", tags="visualizer")

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

        if self.is_recording_video and VIDEO_EXPORT_AVAILABLE:
            self.capture_canvas_frame()

        self.lbl_bass.configure(text=f"Bass Boost: {float(bass_factor):.1f}x")
        self.after(40, self.update_avee_visualizer)

    def toggle_video_recording(self):
        global VIDEO_EXPORT_AVAILABLE
        if not VIDEO_EXPORT_AVAILABLE:
            ctk.filedialog.messagebox.showerror("Error", "OpenCV & NumPy missing!\nPlease check installation.")
            return
        if not self.is_playing:
            ctk.filedialog.messagebox.showwarning("Warning", "Play a track first to export video!")
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
            x, y = self.bg_canvas.winfo_rootx(), self.bg_canvas.winfo_rooty()
            w, h = self.bg_canvas.winfo_width(), self.bg_canvas.winfo_height()
            from PIL import ImageGrab
            cap_img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            frame_np = cv2.cvtColor(np.array(cap_img), cv2.COLOR_RGB2BGR)
            self.video_frames.append(frame_np)
        except Exception: pass

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
                for frame in self.video_frames: video_writer.write(frame)
                video_writer.release()
                ctk.filedialog.messagebox.showinfo("Success 🎉", f"Video exported successfully!\nSaved at: {save_path}")
            except Exception as e: ctk.filedialog.messagebox.showerror("Error", f"Compilation Error: {e}")
        self.reset_video_export_btn()

    def reset_video_export_btn(self):
        self.video_frames = []
        self.btn_export_video.configure(text="📹 Export Live Video (MP4)", fg_color="#291a03", text_color="#FF9900", state="normal")

    # 🔄 OTA UPDATER
    def check_for_updates(self):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(VERSION_URL, headers=headers, timeout=5)
            if res.status_code == 200 and res.text.strip() != CURRENT_VERSION:
                self.after(1000, lambda: self.show_update_dialog(res.text.strip()))
        except Exception: pass  

    def show_update_dialog(self, new_version):
        self.update_win = ctk.CTkToplevel(self)
        self.update_win.title("Update Available! 🎉")
        self.update_win.geometry("400x200")
        self.update_win.resizable(False, False)
        self.update_win.lift(); self.update_win.attributes("-topmost", True)
        
        self.lbl_update_status = ctk.CTkLabel(self.update_win, text=f"A new version ({new_version}) is available!\nDo you want to update VibeStream now?", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_update_status.pack(pady=30)
        
        self.btn_update_frame = ctk.CTkFrame(self.update_win, fg_color="transparent")
        self.btn_update_frame.pack(pady=10)
        ctk.CTkButton(self.btn_update_frame, text="Update Now", fg_color=self.c["accent"], text_color="black", font=ctk.CTkFont(weight="bold"), command=self.start_download_update).pack(side="left", padx=10)
        ctk.CTkButton(self.btn_update_frame, text="Later", fg_color="#333333", command=self.update_win.destroy).pack(side="left", padx=10)

    def start_download_update(self):
        self.btn_update_frame.destroy()
        self.lbl_update_status.configure(text="Downloading VibeStream Update... ⚡")
        self.update_win.update()
        
        def download_worker():
            try:
                is_compiled = getattr(sys, 'frozen', False)
                current_path = os.path.abspath(sys.argv[0])
                current_dir = os.path.dirname(current_path)
                headers = {"User-Agent": "Mozilla/5.0"}
                res = requests.get(CODE_URL, headers=headers, timeout=30, stream=True)
                
                if res.status_code == 200:
                    if is_compiled:
                        new_exe_path = os.path.join(current_dir, "VibeStream_New.exe")
                        with open(new_exe_path, "wb") as f:
                            for chunk in res.iter_content(chunk_size=8192):
                                if chunk: f.write(chunk)
                        
                        bat_path = os.path.join(current_dir, "update_installer.bat")
                        with open(bat_path, "w") as bat:
                            bat.write('@echo off\ntimeout /t 2 /nobreak > nul\ndel "' + current_path + '"\nrename "' + new_exe_path + '" "' + os.path.basename(current_path) + '"\nstart "" "' + current_path + '"\ndel "%~f0"\n')
                        os.startfile(bat_path); self.destroy(); sys.exit()
                    else:
                        temp_script = current_path + ".tmp"
                        with open(temp_script, "w", encoding="utf-8") as f: f.write(res.text)
                        if os.path.exists(temp_script) and os.path.getsize(temp_script) > 1000:
                            if os.path.exists(current_path): os.remove(current_path)
                            os.rename(temp_script, current_path)
                            time.sleep(1)
                            os.execv(sys.executable, ['python', f'"{current_path}"'])
            except Exception: self.lbl_update_status.configure(text="Update Failed! Server offline.")
                
        threading.Thread(target=download_worker, daemon=True).start()

    def toggle_window_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes('-fullscreen', self.is_fullscreen)
        self.after(200, self.pre_cache_and_render_background)

    def on_window_resize(self, event):
        if event.widget == self: self.pre_cache_and_render_background()

    def toggle_playlist_dropdown(self):
        if self.playlist_expanded:
            self.playlist_box.grid_forget(); self.btn_expand_playlist.configure(text="▼ Expand Playlist Tracks"); self.playlist_expanded = False
        else:
            self.playlist_box.grid(row=6, column=0, sticky="nsew", padx=20, pady=(0, 15)); self.btn_expand_playlist.configure(text="▲ Collapse Playlist Tracks"); self.playlist_expanded = True

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar.place_forget(); self.sidebar_visible = False
            self.btn_menu.configure(text="☰ Open Menu", fg_color="#1F1F1F", text_color="white")
            self.pre_cache_and_render_background()
        else:
            self.sidebar.place(x=0, y=0, relheight=1); self.sidebar_visible = True
            self.btn_menu.configure(text="✕ Close Menu", fg_color=self.c["accent"], text_color="black")
            self.pre_cache_and_render_background()
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
        file_path = ctk.filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.webp")])
        if file_path: self.bg_image_path = file_path; self.save_settings(); self.pre_cache_and_render_background()

    def pre_cache_and_render_background(self):
        self.update_idletasks()
        cw, ch = self.bg_canvas.winfo_width(), self.bg_canvas.winfo_height()
        if cw < 200 or ch < 200: return

        if self.bg_image_path and os.path.exists(self.bg_image_path):
            try:
                img = Image.open(self.bg_image_path)
                ow, oh = img.size
                win_aspect, img_aspect = cw / ch, ow / oh
                nw, nh = (cw, int(cw / img_aspect)) if img_aspect > win_aspect else (int(ch * img_aspect), ch)
                img = img.resize((nw, nh), Image.Resampling.LANCZOS)
                cropped = img.crop(((nw - cw)/2, (nh - ch)/2, (nw - cw)/2 + cw, (nh - ch)/2 + ch)).convert('RGBA')
                overlay_color = tuple(int(self.c["overlay"].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                
                blend_val = 220 if self.sidebar_visible else 150
                final_bg = ImageTk.PhotoImage(Image.alpha_composite(cropped, Image.new('RGBA', cropped.size, (*overlay_color, blend_val))).convert('RGB'))
                
                self.bg_canvas.delete("bg_pic")
                self.bg_canvas.bg_image_ref = final_bg  
                self.bg_canvas.create_image(0, 0, image=final_bg, anchor="nw", tags="bg_pic")
                self.bg_canvas.tag_lower("bg_pic")
            except Exception: self.bg_canvas.configure(bg=self.c["overlay"])
        else: self.bg_canvas.configure(bg=self.c["overlay"])

    def parse_lrc_content(self, lines):
        self.synced_lyrics = []
        st = 0
        for line in lines:
            line = line.strip()
            if not line: continue
            match = re.match(r'\[(\d+):(\d+)[\.:](\d+)\](.*)', line)
            if match:
                m, s, _, txt = match.groups()
                self.synced_lyrics.append((int(m) * 60 + int(s), txt.strip()))
            else:
                self.synced_lyrics.append((st, line)); st += 4

    def upload_manual_lrc_file(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("Lyrics", "*.lrc;*.txt")])
        if file_path:
            self.last_highlighted_index = -1
            try:
                with open(file_path, "r", encoding="utf-8") as f: lines = f.readlines()
                self.parse_lrc_content(lines)
                self.current_lyrics_text = "Custom Lyrics Loaded Successfully! 🎧"
            except Exception: self.current_lyrics_text = "Error loading custom lyrics."

    # 🎤 DUAL-SOURCE LYRICS FETCH
    def fetch_lyrics_async(self, track_path):
        self.synced_lyrics = []; self.last_highlighted_index = -1
        self.current_lyrics_text = "Searching Live Lyrics from Genius API... 🔍"
        
        local_lrc = os.path.splitext(track_path)[0] + ".lrc"
        if os.path.exists(local_lrc):
            try:
                with open(local_lrc, "r", encoding="utf-8") as f: self.parse_lrc_content(f.readlines())
                self.current_lyrics_text = "Offline Synchronized Lyrics Loaded! 💾"
                return
            except Exception: pass

        def run_api_call():
            cleaned = re.sub(r'^\d+[\s.\-_]*|\[.*?\]|\(.*?\)|[^\w\s\-]', '', os.path.splitext(os.path.basename(track_path))[0]).replace("_", " ").replace("-", " ").strip()
            try:
                res = requests.get(f"https://lyrist.vercel.app/api/{urllib.parse.quote(cleaned)}", timeout=8)
                if res.status_code == 200 and res.json().get("lyrics"):
                    lines = res.json().get("lyrics").split('\n')
                    self.parse_lrc_content(lines)
                    self.current_lyrics_text = ""
                else: self.current_lyrics_text = "Lyrics Unavailable. Ready for manual upload! 🖨️"
            except Exception: self.current_lyrics_text = "Network offline. Ready for manual upload! 🖨️"

        threading.Thread(target=run_api_call, daemon=True).start()

    def lyrics_sync_loop(self):
        while True:
            if self.is_playing and not self.is_paused and self.synced_lyrics:
                cp = self.current_time_offset
                idx = -1
                for i, (ts, _) in enumerate(self.synced_lyrics):
                    if cp >= ts: idx = i
                    else: break
                if idx != -1 and idx != self.last_highlighted_index:
                    self.last_highlighted_index = idx
                    _, self.current_lyrics_text = self.synced_lyrics[idx]
            time.sleep(0.15)

    def change_theme(self, choice):
        self.current_theme_name = choice; self.c = self.themes[choice]
        self.pre_cache_and_render_background()
        self.sidebar.configure(fg_color=self.c["card_bg"]); self.controls_bar.configure(fg_color=self.c["card_bg"])
        self.slider_progress.configure(progress_color=self.c["accent"], button_color=self.c["accent"])
        self.btn_play.configure(fg_color=self.c["accent"])
        self.slider_bass.configure(progress_color=self.c["accent"], button_color=self.c["accent"])
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
    app = VibeStreamImmersivePlayer()
    app.mainloop()