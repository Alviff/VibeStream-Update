import sys
import warnings

warnings.filterwarnings("ignore")

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

pygame.mixer.init()

# ────────────── OTA AUTO-UPDATE CONFIGURATION ──────────────
CURRENT_VERSION = "1.0.0"
VERSION_URL = "https://raw.githubusercontent.com/Alviff/VibeStream-Update/main/version.txt"
CODE_URL = "https://raw.githubusercontent.com/Alviff/VibeStream-Update/main/Audio%20Player.py"
# ──────────────────────────────────────────────────────────

SETTINGS_FILE = "settings.json"
ctk.set_appearance_mode("Dark")

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
        
        self.synced_lyrics = []  
        self.last_highlighted_index = -1
        self.bg_image_path = None
        
        # 🧠 IMAGE CACHE CHANNELS (ফ্রিজিং বন্ধ করার জন্য)
        self.cached_normal_bg = None
        self.cached_sidebar_bg = None
        
        # Visualizer Config
        self.num_bars = 75  
        self.circle_radius = 110  
        self.bar_magnitudes = [0.0] * self.num_bars

        # 🖼️ LAYER 1: Full window Background Canvas
        self.bg_canvas = ctk.CTkCanvas(self, bg=self.c["overlay"], highlightthickness=0, bd=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # 🎭 LAYER 2: Layout Setup
        self.setup_layout()
        
        # ☰ LAYER 3: Floating Hamburger Menu Button
        self.btn_menu = ctk.CTkButton(
            self, text="☰ Open Menu", font=ctk.CTkFont(size=14, weight="bold"),
            width=120, height=38, fg_color="#1F1F1F", text_color="white",
            hover_color="#333333", corner_radius=10, command=self.toggle_sidebar
        )
        self.btn_menu.place(x=25, y=25)
        self.btn_menu.lift()

        # 💾 LOAD SETTINGS
        self.load_saved_settings()
        self.sidebar.place_forget()

        # 🔄 INITIAL REFRESH & CACHE
        self.after(300, self.pre_cache_and_render_background)

        self.bind("<Configure>", self.on_window_resize)

        # Background Animation Loops
        self.update_avee_visualizer()
        threading.Thread(target=self.lyrics_sync_loop, daemon=True).start()
        threading.Thread(target=self.update_progress_loop, daemon=True).start()

        # 🚀 START BACKGROUND OTA UPDATE CHECK
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    # 📡 OTA AUTO-UPDATE LOGIC
    def check_for_updates(self):
        try:
            response = requests.get(VERSION_URL, timeout=5)
            if response.status_code == 200:
                remote_version = response.text.strip()
                if remote_version != CURRENT_VERSION:
                    self.after(1000, lambda: self.show_update_dialog(remote_version))
        except Exception:
            pass  

    def show_update_dialog(self, new_version):
        self.update_win = ctk.CTkToplevel(self)
        self.update_win.title("Update Available! 🎉")
        self.update_win.geometry("400x200")
        self.update_win.resizable(False, False)
        self.update_win.lift()
        self.update_win.attributes("-topmost", True)
        
        lbl = ctk.CTkLabel(
            self.update_win, 
            text=f"A new version ({new_version}) is available!\nDo you want to update VibeStream now?", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        lbl.pack(pady=30)
        
        btn_frame = ctk.CTkFrame(self.update_win, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        btn_yes = ctk.CTkButton(btn_frame, text="Update Now", fg_color=self.c["accent"], text_color="black", font=ctk.CTkFont(weight="bold"), command=self.start_download_update)
        btn_yes.pack(side="left", padx=10)
        
        btn_no = ctk.CTkButton(btn_frame, text="Later", fg_color="#333333", text_color="white", command=self.update_win.destroy)
        btn_no.pack(side="left", padx=10)

    def start_download_update(self):
        for widget in self.update_win.winfo_children():
            widget.destroy()
            
        lbl_status = ctk.CTkLabel(self.update_win, text="Downloading updates... Please wait. ⚡", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_status.pack(pady=50)
        self.update_win.update()
        
        def download_worker():
            try:
                code_response = requests.get(CODE_URL, timeout=15)
                if code_response.status_code == 200:
                    current_script = sys.argv[0]
                    with open(current_script, "w", encoding="utf-8") as f:
                        f.write(code_response.text)
                    
                    lbl_status.configure(text="Update Success! Restarting App... 🔄")
                    self.update_win.update()
                    time.sleep(2)
                    
                    os.execv(sys.executable, ['python', f'"{current_script}"'])
                else:
                    lbl_status.configure(text="Download Failed! Server busy.")
            except Exception as e:
                lbl_status.configure(text="Error updating file. Try later!")
                
        threading.Thread(target=download_worker, daemon=True).start()

    def toggle_window_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes('-fullscreen', self.is_fullscreen)
        self.after(200, self.pre_cache_and_render_background)

    def on_window_resize(self, event):
        if event.widget == self:
            # উইন্ডোজ রিসাইজ বা মিনিমাইজ করলে ব্যাকগ্রাউন্ড রি-ক্যাশ হবে
            self.pre_cache_and_render_background()

    def setup_layout(self):
        # ────────────── SLIDING SIDEBAR (LEFT) ──────────────
        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=0, fg_color=self.c["card_bg"])
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(3, weight=1) 

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
            button_hover_color="#444444", dropdown_fg_color="#121212", font=ctk.CTkFont(size=12), command=self.change_theme
        )
        self.theme_selector.set(self.current_theme_name)
        self.theme_selector.pack(fill="x", pady=5)

        self.btn_upload_bg = ctk.CTkButton(
            self.config_box, text="🖼️ Upload Custom Wallpaper", font=ctk.CTkFont(size=12, weight="bold"),
            height=32, fg_color="#252525", text_color="white", hover_color="#333333",
            corner_radius=8, command=self.upload_bg_image
        )
        self.btn_upload_bg.pack(fill="x", pady=5)

        self.slider_bass = ctk.CTkSlider(self.config_box, from_=0.5, to=2.5, height=12, fg_color="#3E3E3E", progress_color=self.c["accent"], button_color=self.c["accent"])
        self.slider_bass.set(1.0)
        self.slider_bass.pack(fill="x", pady=(15, 2))
        self.lbl_bass = ctk.CTkLabel(self.config_box, text="Bass Boost: 1.0x", font=ctk.CTkFont(size=11), text_color=self.c["muted"])
        self.lbl_bass.pack(anchor="w")

        self.btn_expand_playlist = ctk.CTkButton(
            self.sidebar, text="▼ Expand Playlist Tracks", font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1A1A1A", text_color="white", hover_color="#252525", height=38, corner_radius=8,
            command=self.toggle_playlist_dropdown
        )
        self.btn_expand_playlist.grid(row=2, column=0, sticky="ew", padx=20, pady=(15, 5))

        self.playlist_box = ctk.CTkScrollableFrame(self.sidebar, corner_radius=8, fg_color="#0A0A0A")

        # ────────────── IMMERSIVE LYRICS CENTER ──────────────
        self.center_lyrics_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.center_lyrics_panel.place(relx=0.5, rely=0.73, relwidth=0.65, relheight=0.20, anchor="center")
        
        self.txt_lyrics = ctk.CTkTextbox(
            self.center_lyrics_panel, fg_color="transparent", 
            font=ctk.CTkFont(size=20, weight="bold"), text_color=self.c["muted"], 
            wrap="word", height=75, activate_scrollbars=False
        )
        self.txt_lyrics.pack(fill="x", expand=False)
        self.txt_lyrics.tag_config("center", justify="center")
        self.txt_lyrics.insert("0.0", "Lyrics will flow smoothly right here!", "center")

        self.btn_manual_lrc = ctk.CTkButton(
            self.center_lyrics_panel, text="📇 Upload Custom .LRC / .TXT File", font=ctk.CTkFont(size=11, weight="bold"),
            width=190, height=28, fg_color="#1A1A1A", text_color=self.c["muted"], hover_color="#333333", corner_radius=6,
            command=self.upload_manual_lrc_file
        )
        self.btn_manual_lrc.pack(pady=(10, 0))

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

        self.btn_shuffle = ctk.CTkButton(self.buttons_frame, text="🔀", width=35, font=ctk.CTkFont(size=14), fg_color="transparent", text_color=self.c["muted"], command=self.toggle_shuffle)
        self.btn_shuffle.pack(side="left", padx=5)

        self.btn_prev = ctk.CTkButton(self.buttons_frame, text="⏮", width=35, font=ctk.CTkFont(size=16), fg_color="transparent", text_color="white", command=self.prev_track)
        self.btn_prev.pack(side="left", padx=5)

        self.btn_play = ctk.CTkButton(self.buttons_frame, text="▶", width=40, height=40, corner_radius=20, font=ctk.CTkFont(size=16), fg_color=self.c["accent"], text_color="black", hover_color="white", command=self.toggle_play)
        self.btn_play.pack(side="left", padx=5)

        self.btn_next = ctk.CTkButton(self.buttons_frame, text="⏭", width=35, font=ctk.CTkFont(size=16), fg_color="transparent", text_color="white", command=self.next_track)
        self.btn_next.pack(side="left", padx=5)

        self.btn_loop = ctk.CTkButton(self.buttons_frame, text="🔁", width=35, font=ctk.CTkFont(size=14), fg_color="transparent", text_color=self.c["muted"], command=self.toggle_loop)
        self.btn_loop.pack(side="left", padx=5)

        # Track Meta Display
        self.meta_frame = ctk.CTkFrame(self.controls_bar, fg_color="transparent")
        self.meta_frame.grid(row=1, column=0, sticky="w", padx=30)
        self.lbl_track_name = ctk.CTkLabel(self.meta_frame, text="No Song Loaded", font=ctk.CTkFont(size=13, weight="bold"), text_color="white", anchor="w")
        self.lbl_track_name.pack(anchor="w")

        # Volume Controls
        self.volume_frame = ctk.CTkFrame(self.controls_bar, fg_color="transparent")
        self.volume_frame.grid(row=1, column=2, padx=30, sticky="e")
        self.slider_volume = ctk.CTkSlider(self.volume_frame, width=80, from_=0, to=1, fg_color="#3E3E3E", progress_color="white", button_color="white", command=self.set_volume)
        self.slider_volume.set(0.7)
        self.slider_volume.pack(side="right")
        ctk.CTkLabel(self.volume_frame, text="🔊", font=ctk.CTkFont(size=12), text_color="white").pack(side="right", padx=5)

    def toggle_playlist_dropdown(self):
        if self.playlist_expanded:
            self.playlist_box.grid_forget()
            self.btn_expand_playlist.configure(text="▼ Expand Playlist Tracks")
            self.playlist_expanded = False
        else:
            self.playlist_box.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 15))
            self.btn_expand_playlist.configure(text="▲ Collapse Playlist Tracks")
            self.playlist_expanded = True

    def toggle_sidebar(self):
        # 🚀 মেমোরি থেকে ইনস্ট্যান্ট রেন্ডার হবে, নো ইমেজ প্রসেসিং ল্যাগ!
        if self.sidebar_visible:
            self.sidebar.place_forget()
            self.sidebar_visible = False
            self.btn_menu.configure(text="☰ Open Menu", fg_color="#1F1F1F", text_color="white")
            if self.cached_normal_bg:
                self.bg_canvas.delete("bg_pic")
                self.bg_canvas.create_image(0, 0, image=self.cached_normal_bg, anchor="nw", tags="bg_pic")
                self.bg_canvas.tag_lower("bg_pic")
        else:
            self.sidebar.place(x=0, y=0, relheight=1)
            self.sidebar_visible = True
            self.btn_menu.configure(text="✕ Close Menu", fg_color=self.c["accent"], text_color="black")
            if self.cached_sidebar_bg:
                self.bg_canvas.delete("bg_pic")
                self.bg_canvas.create_image(0, 0, image=self.cached_sidebar_bg, anchor="nw", tags="bg_pic")
                self.bg_canvas.tag_lower("bg_pic")
            
        self.sidebar.lift()            
        self.btn_menu.lift()           

    def save_settings(self, folder_path=None):
        existing_settings = {}
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f: existing_settings = json.load(f)
            except Exception: pass
            
        if folder_path: existing_settings["last_folder"] = folder_path
        if self.bg_image_path: existing_settings["custom_wallpaper"] = self.bg_image_path
        
        try:
            with open(SETTINGS_FILE, "w") as f: json.dump(existing_settings, f)
        except Exception: pass

    def load_saved_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    saved_data = json.load(f)
                    saved_wp = saved_data.get("custom_wallpaper", "")
                    if saved_wp and os.path.exists(saved_wp):
                        self.bg_image_path = saved_wp
                    folder_path = saved_data.get("last_folder", "")
                    if folder_path and os.path.exists(folder_path): 
                        self.load_music_from_path(folder_path)
            except Exception: pass

    def upload_bg_image(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp")])
        if file_path:
            self.bg_image_path = file_path
            self.save_settings() 
            self.pre_cache_and_render_background()

    # 🧠 নতুন আল্ট্রা-স্মুথ ইমেজ প্রি-ক্যাশিং ফাংশন
    def pre_cache_and_render_background(self):
        self.update_idletasks()
        cw = self.bg_canvas.winfo_width()
        ch = self.bg_canvas.winfo_height()
        if cw < 200 or ch < 200: return

        if self.bg_image_path:
            try:
                img = Image.open(self.bg_image_path)
                original_width, original_height = img.size
                win_aspect = cw / ch
                img_aspect = original_width / original_height

                if img_aspect > win_aspect:
                    new_height = ch
                    new_width = int(new_height * img_aspect)
                else:
                    new_width = cw
                    new_height = int(new_width / img_aspect)

                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                left = (new_width - cw) / 2
                top = (new_height - ch) / 2
                cropped_base = img.crop((left, top, left + cw, top + ch)).convert('RGBA')
                
                overlay_color = self.hex_to_rgb(self.c["overlay"])
                
                # ১. নরমাল মোডের জন্য ডার্ক ওভারলে ক্যাশ করুন
                overlay_normal = Image.new('RGBA', cropped_base.size, (*overlay_color, 150))
                img_normal = Image.alpha_composite(cropped_base, overlay_normal).convert('RGB')
                self.cached_normal_bg = ImageTk.PhotoImage(img_normal)
                
                # ২. সাইডবার ওপেন মোডের জন্য এক্সট্রা ডার্ক ওভারলে ক্যাশ করুন
                overlay_sidebar = Image.new('RGBA', cropped_base.size, (*overlay_color, 220))
                img_sidebar = Image.alpha_composite(cropped_base, overlay_sidebar).convert('RGB')
                self.cached_sidebar_bg = ImageTk.PhotoImage(img_sidebar)

                # কারেন্টলি যে মোড অন আছে সেই ইমেজটি স্ক্রিনে পুশ করুন
                self.bg_canvas.delete("bg_pic")
                active_img = self.cached_sidebar_bg if self.sidebar_visible else self.cached_normal_bg
                self.bg_canvas.create_image(0, 0, image=active_img, anchor="nw", tags="bg_pic")
                self.bg_canvas.tag_lower("bg_pic")
                
            except Exception:
                self.bg_canvas.configure(bg=self.c["overlay"])
        else:
            self.bg_canvas.configure(bg=self.c["overlay"])

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def update_avee_visualizer(self):
        cw = self.bg_canvas.winfo_width()
        ch = self.bg_canvas.winfo_height()
        
        if cw < 300 or ch < 300: 
            self.after(100, self.update_avee_visualizer)
            return
            
        cx = cw / 2
        cy = ch * 0.35

        self.bg_canvas.delete("visualizer")
        bass_factor = self.slider_bass.get()

        for i in range(self.num_bars):
            if self.is_playing and not self.is_paused:
                target = random.uniform(5, 65) * bass_factor
                self.bar_magnitudes[i] += (target - self.bar_magnitudes[i]) * 0.3
            else:
                self.bar_magnitudes[i] += (2 - self.bar_magnitudes[i]) * 0.2

            angle = (i / self.num_bars) * 2 * math.pi
            
            x_start = cx + self.circle_radius * math.cos(angle)
            y_start = cy + self.circle_radius * math.sin(angle)
            x_end = cx + (self.circle_radius + self.bar_magnitudes[i]) * math.cos(angle)
            y_end = cy + (self.circle_radius + self.bar_magnitudes[i]) * math.sin(angle)

            bar_color = self.c["accent"]
            
            self.bg_canvas.create_line(
                x_start, y_start, x_end, y_end,
                fill=bar_color, width=5, capstyle="round", tags="visualizer"
            )
            
        if self.bg_canvas.find_withtag("bg_pic"):
            self.bg_canvas.tag_raise("visualizer", "bg_pic")

        self.lbl_bass.configure(text=f"Bass Boost: {float(bass_factor):.1f}x")
        self.after(40, self.update_avee_visualizer)

    def parse_lrc_content(self, lines):
        self.synced_lyrics = []
        simulated_time = 0
        for line in lines:
            line = line.strip()
            if not line: continue
            match = re.match(r'\[(\d+):(\d+)[\.:](\d+)\](.*)', line)
            if match:
                minutes, seconds, _, text = match.groups()
                timestamp = int(minutes) * 60 + int(seconds)
                self.synced_lyrics.append((timestamp, text.strip()))
            else:
                self.synced_lyrics.append((simulated_time, line))
                simulated_time += 4

    def upload_manual_lrc_file(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("LRC/TXT Files", "*.lrc;*.txt")])
        if file_path:
            self.last_highlighted_index = -1
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                self.parse_lrc_content(lines)
                self.txt_lyrics.delete("0.0", "end")
                self.txt_lyrics.insert("0.0", "Custom Lyrics Loaded Successfully! 🎧", "center")
            except Exception:
                self.txt_lyrics.delete("0.0", "end")
                self.txt_lyrics.insert("0.0", "Error loading custom lyrics file.", "center")

    def hide_lyrics_notice(self):
        self.txt_lyrics.delete("0.0", "end")

    def fetch_lyrics_async(self, track_path):
        self.synced_lyrics = []; self.last_highlighted_index = -1
        self.txt_lyrics.delete("0.0", "end")
        self.txt_lyrics.insert("0.0", "Searching lyrics online... 🔍", "center")
        
        track_dir = os.path.dirname(track_path)
        track_name = os.path.basename(track_path)
        base_name_no_ext = os.path.splitext(track_name)[0]
        
        local_lrc_path = os.path.join(track_dir, base_name_no_ext + ".lrc")
        if os.path.exists(local_lrc_path):
            try:
                with open(local_lrc_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                self.parse_lrc_content(lines)
                self.txt_lyrics.delete("0.0", "end")
                self.txt_lyrics.insert("0.0", "Offline Synchronized Lyrics Loaded! 💾", "center")
                return
            except Exception: pass

        def run_api_call():
            cleaned_name = base_name_no_ext
            cleaned_name = re.sub(r'^\d+[\s.\-_]*', '', cleaned_name)
            cleaned_name = re.sub(r'\[.*?\]|\(.*?\)', '', cleaned_name)
            cleaned_name = re.sub(r'[^\w\s\-]', '', cleaned_name)
            cleaned_name = cleaned_name.replace("_", " ").replace("-", " ").strip()
            
            encoded_name = urllib.parse.quote(cleaned_name)
            url = f"https://lyrist.vercel.app/api/{encoded_name}"
            
            try:
                response = requests.get(url, timeout=8)
                if response.status_code == 200:
                    response_json = response.json()
                    lyrics_text = response_json.get("lyrics")
                    self.txt_lyrics.delete("0.0", "end")
                    
                    if lyrics_text:
                        lines = lyrics_text.split('\n')
                        self.parse_lrc_content(lines)
                        
                        try:
                            with open(local_lrc_path, "w", encoding="utf-8") as f:
                                simulated_time = 0
                                for line in lines:
                                    if line.strip():
                                        min_str = f"{simulated_time // 60:02d}"
                                        sec_str = f"{simulated_time % 60:02d}"
                                        f.write(f"[{min_str}:{sec_str}.00] {line.strip()}\n")
                                        simulated_time += 4
                        except Exception: pass
                    else:
                        self.txt_lyrics.insert("0.0", "Lyrics not found for this track.", "center")
                        self.after(10000, self.hide_lyrics_notice) 
                else:
                    self.txt_lyrics.delete("0.0", "end")
                    self.txt_lyrics.insert("0.0", "Lyrics server busy. Try manual upload!", "center")
                    self.after(10000, self.hide_lyrics_notice)
            except Exception:
                self.txt_lyrics.delete("0.0", "end")
                self.txt_lyrics.insert("0.0", "Lyrics Unavailable. Ready for manual upload! 📇", "center")
                self.after(10000, self.hide_lyrics_notice) 

        threading.Thread(target=run_api_call, daemon=True).start()

    def lyrics_sync_loop(self):
        while True:
            if self.is_playing and not self.is_paused and self.synced_lyrics:
                current_pos = self.current_time_offset
                target_idx = -1
                for i, (timestamp, _) in enumerate(self.synced_lyrics):
                    if current_pos >= timestamp: target_idx = i
                    else: break
                
                if target_idx != -1 and target_idx != self.last_highlighted_index:
                    self.last_highlighted_index = target_idx
                    self.txt_lyrics.delete("0.0", "end")
                    
                    _, current_text = self.synced_lyrics[target_idx]
                    self.txt_lyrics.insert("0.0", current_text, "center")
                    self.txt_lyrics.tag_config("center", justify="center", foreground=self.c["accent"])
            time.sleep(0.15)

    def change_theme(self, choice):
        self.current_theme_name = choice
        self.c = self.themes[choice]
        self.pre_cache_and_render_background() # থিম বদলালে ব্যাকগ্রাউন্ড রি-কালার হবে
        self.sidebar.configure(fg_color=self.c["card_bg"])
        self.controls_bar.configure(fg_color=self.c["card_bg"])
        self.slider_progress.configure(progress_color=self.c["accent"], button_color=self.c["accent"])
        self.btn_play.configure(fg_color=self.c["accent"])
        self.slider_bass.configure(progress_color=self.c["accent"], button_color=self.c["accent"])
        if self.sidebar_visible:
            self.btn_menu.configure(fg_color=self.c["accent"])
        self.btn_manual_lrc.configure(text_color=self.c["muted"])
        self.update_playlist_ui()

    def import_folder(self):
        folder_path = ctk.filedialog.askdirectory()
        if folder_path:
            self.load_music_from_path(folder_path)
            self.save_settings(folder_path)

    def load_music_from_path(self, folder_path):
        self.playlist = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".mp3")]
        self.update_playlist_ui()

    def format_time(self, seconds): return f"{int(seconds // 60)}:{int(seconds % 60):02d}"

    def update_playlist_ui(self):
        for widget in self.playlist_box.winfo_children(): widget.destroy()
        for idx, track_path in enumerate(self.playlist):
            btn = ctk.CTkButton(
                self.playlist_box, text=f" {idx+1:02d}.  {os.path.basename(track_path)[:26]}...", anchor="w",
                fg_color="transparent", text_color="white", hover_color="#1F1F1F",
                height=38, corner_radius=6, font=ctk.CTkFont(size=12), command=lambda i=idx: self.play_track(i),
            )
            btn.pack(fill="x", pady=2)

    def play_track(self, index):
        if index >= len(self.playlist) or index < 0: return
        self.current_index = index
        track_path = self.playlist[self.current_index]
        try:
            audio = MP3(track_path)
            self.song_length = audio.info.length
            self.current_time_offset = 0; self.start_timestamp = time.time()
            self.slider_progress.configure(to=self.song_length)
            self.lbl_total_time.configure(text=self.format_time(self.song_length))
            pygame.mixer.music.load(track_path)
            pygame.mixer.music.play()
            self.is_playing = True; self.is_paused = False; self.btn_play.configure(text="⏸")
            self.lbl_track_name.configure(text=os.path.basename(track_path)[:35])
            self.fetch_lyrics_async(track_path)
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
            new_pos = self.slider_progress.get()
            pygame.mixer.music.play(start=float(new_pos))
            self.current_time_offset = new_pos; self.start_timestamp = time.time() - self.current_time_offset
            if self.is_paused: pygame.mixer.music.pause()

    def set_volume(self, value): pygame.mixer.music.set_volume(float(value))
    def toggle_shuffle(self): self.is_shuffling = not self.is_shuffling; self.btn_shuffle.configure(text_color=self.c["accent"] if self.is_shuffling else self.c["muted"])
    def toggle_loop(self): self.is_looping = not self.is_looping; self.btn_loop.configure(text_color=self.c["accent"] if self.is_looping else self.c["muted"])

    def update_progress_loop(self):
        while True:
            if self.is_playing and not self.is_paused:
                if not pygame.mixer.music.get_busy(): self.after(100, self.next_track); time.sleep(1); continue
                calculated_pos = time.time() - self.start_timestamp
                if calculated_pos <= self.song_length:
                    self.current_time_offset = calculated_pos
                    self.lbl_current_time.configure(text=self.format_time(calculated_pos))
                    self.slider_progress.set(calculated_pos)
            time.sleep(0.5)

if __name__ == "__main__":
    app = UltimateFullAppPlayer()
    app.mainloop()