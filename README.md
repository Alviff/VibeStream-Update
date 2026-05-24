# 🎵 VibeStream - Immersive Theater Edition

VibeStream is a cutting-edge, fully immersive local MP3 music player designed with a premium, sleek UI using CustomTkinter. Featuring dynamic real-time audio visualizers, automatic lyrics synchronization via Genius API, local user authentication, and customizable aesthetic themes, it brings a theater-like music listening experience right to your desktop.

---

## 🚀 What's New in v1.0.1 (Latest Update)
We are excited to roll out **v1.0.1**, focusing on celebrating the team and collaborators behind the project!

* **🎖️ New Interactive Credits Window:** Added a dedicated Production Team portal accessible directly from the sidebar.
* **💻 Developer & Squad Branding:** Spotlights the lead developer (`Alviff / Atta`) and the elite circle of **Authorized Beta Testers**.
* **🤖 AI Collaboration:** Proudly honors `Gemini AI (Google)` as the core UI & Engine optimization partner within the credits console.
* **⚙️ Performance Improvements:** Optimized rendering logic for floating panels and custom pop-ups.

---

## ✨ Key Features

* **🎭 Immersive Theater UI:** Minimalist, fullscreen design (`Escape` key toggles fullscreen) with smooth card overlays.
* **📊 Multi-Template Visualizers:** Switch seamlessly between 4 responsive visualizer modes:
    * *Circular Avee* (Classic audio ring)
    * *Bottom Waves* (Linear frequencies)
    * *Pulse Star* (Dynamic beating core)
    * *WhatsApp Message* (A unique, personalized voice-note simulator style!)
* **🎙️ Live Synchronized Lyrics:** Fetches lyrics in real-time from the Genius API, parsing offline `.lrc` or `.txt` files automatically if present. Manual upload is also supported!
* **🎨 Premium Sound Themes:** Instantly shift vibes with preset styling templates like *Spotify Green*, *Cyberpunk Pink*, *Neon Blue*, and *Blood Red*.
* **🖼️ Custom Wallpaper Engine:** Upload any custom image to serve as a blurred background canvas overlay.
* **🔒 Local Security Console:** Secure individual profiles via an offline SignUp/Login credential authentication workflow (`user_account.json`).
* **📡 Smart OTA Updates:** Embedded auto-update engine that cross-references remote versions and triggers downloads seamlessly.

---

## 🛠️ Prerequisites & Installation

Ensure you have Python installed, then set up the required dependencies:

```bash
pip install customtkinter pygame mutagen pillow requests
Note: The script features an automated runtime patch for audioop handling, keeping it seamlessly compatible with newer Python environments!

🔑 Configuration Setup
Clone or download Audio Player.py.

Open the file and navigate to line 39.

Replace the placeholder token with your active Genius Client Secret:

Python
GENIUS_CLIENT_SECRET = "YOUR_ACTUAL_GENIUS_SECRET_KEY"
Customize your beta tester crew roster near line 303:

Python
testers_list = ["Friend_1", "Friend_2", "Your_Squad_Name"]
🎮 How To Play
Run the script:

Bash
python "Audio Player.py"
Create your local profile on first launch, then log in.

Tap ☰ Open Menu on the top-left corner.

Load your music directory using 📁 Change Music Folder.

Press Escape anytime to step into the complete theater visualizer mode.

🎖️ Production & Credits
Lead UI Architect & Developer: Alviff (Atta)

AI Collaborator & Optimizer: Gemini AI (Google)

Quality Control: Authorized Beta Testers Team

Developed with 🤍 for audiophiles and code enthusiasts alike.


---

### 💡 এটি যেভাবে ব্যবহার করবেন:
১. আপনার প্রজেক্ট ফোল্ডারে `README.md` নামে একটি ফাইল তৈরি করুন (যদি আগে থেকে না থাকে)।
২. উপরের কোড ব্লকের সম্পূর্ণ টেক্সটটুকু কপি করে সেখানে পেস্ট করে দিন। 
৩. আপনার GitHub রিপোজিটরিতে পুশ করলে এটি একটি চমৎকার প্রফেশনাল লুক পাবে!
