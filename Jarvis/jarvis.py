"""Charu personal voice assistant, maintained by Deven Punse."""

import datetime
import math
import os
import queue
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
from typing import NamedTuple
from urllib.parse import quote
import webbrowser as wb
from pathlib import Path

import pyautogui
import pyttsx3
import speech_recognition as sr
import wikipedia
import yt_dlp
from companion import companion_response

# ASSISTANT STRINGS
STRINGS = {
    'en': {
        'welcome': "Welcome back, Deven!",
        'morning': "Good morning!",
        'afternoon': "Good afternoon!",
        'evening': "Good evening!",
        'night': "Good night, see you tomorrow.",
        'service': "{} at your service. How may I assist you?",
        'time': "The current time is ",
        'date': "The current date is ",
        'screenshot': "Screenshot saved as {}.",
        'listening': "Listening...",
        'recognizing': "Recognizing...",
        'error_music': "Music directory not found.",
        'playing': "Playing {}.",
        'no_song': "No song found.",
        'ask_name': "What would you like to name me?",
        'name_set': "Alright, I will be called {} from now on.",
        'wiki_search': "Searching Wikipedia...",
        'no_result': "I couldn't find anything.",
        'shutdown': "Shutting down system!",
        'restart': "Restarting system!",
        'offline': "Going to sleep. Call me by saying start Charu.",
        'exit': "Goodbye!"
    }
}

class YouTubeVideo(NamedTuple):
    title: str
    uploader: str
    url: str


playback_process = None
playback_profile = None

# INIT
engine = None
VOICE_MAP = {'en': None}

def initialize_engine():
    global engine, VOICE_MAP
    if engine is None:
        engine = pyttsx3.init()
        for voice in engine.getProperty('voices'):
            v_lang = str(voice.languages).lower()
            if "en-us" in v_lang or "english" in voice.name.lower():
                VOICE_MAP['en'] = voice.id
        engine.setProperty('rate', 170)
        engine.setProperty('volume', 1)
    return engine

def set_voice(lang):
    speech_engine = initialize_engine()
    if VOICE_MAP.get(lang):
        speech_engine.setProperty('voice', VOICE_MAP[lang])

# CORE FUNCTIONS
def speak(text, lang='en'):
    speech_engine = initialize_engine()
    set_voice(lang)
    speech_engine.say(text)
    speech_engine.runAndWait()

def open_media(path):
    cmd = "xdg-open" if sys.platform != "win32" else "start"
    if sys.platform == "win32":
        os.startfile(path)
    else:
        subprocess.call([cmd, str(path)])

def get_time(lang='en'):
    timer = datetime.datetime.now().strftime("%H:%M:%S")
    speak(STRINGS[lang]['time'], lang)
    speak(timer, lang='en')
    print(f"[{lang}] {timer}")

def get_date(lang='en'):
    now = datetime.datetime.now()
    speak(STRINGS[lang]['date'], lang)
    date_str = f"{now.day} {now.strftime('%B')} {now.year}"
    speak(date_str, lang)
    print(f"[{lang}] {date_str}")

def wish_me(lang='en'):
    speak(STRINGS[lang]['welcome'], lang)
    hour = datetime.datetime.now().hour
    if 4 <= hour < 12: key = 'morning'
    elif 12 <= hour < 18: key = 'afternoon'
    elif 18 <= hour < 24: key = 'evening'
    else: key = 'night'
    speak(STRINGS[lang][key], lang)
    name = load_name()
    speak(STRINGS[lang]['service'].format(name), lang)

def take_screenshot(lang='en'):
    path = Path.home() / "Pictures" / "screenshot.png"
    pyautogui.screenshot().save(str(path))
    speak(STRINGS[lang]['screenshot'].format(path), lang)

def take_command(
    prompt="Listening... speak now.",
    report_no_speech=True,
    report_unclear=True,
):
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print(prompt)
            r.pause_threshold = 1
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
    except sr.WaitTimeoutError:
        if report_no_speech:
            print("No speech detected. Check your microphone and try again.")
        return None
    except OSError as error:
        print(f"Microphone error: {error}")
        return None

    return recognize_audio(r, audio, report_unclear=report_unclear)

def recognize_audio(recognizer, audio, report_unclear=True):
    try:
        query = recognizer.recognize_google(audio, language="en-US")
        print(f"(en-US) {query}")
        return query.lower()
    except sr.UnknownValueError:
        if report_unclear:
            print(
                "Speech wasn't clear enough to recognize in English. "
                "Speak clearly near your default microphone and try again."
            )
        return None
    except sr.RequestError as error:
        print(f"Speech recognition service error: {error}")
        return None

def is_wake_command(query):
    return re.match(
        r"^(?:(?:hey|start|wake up)\s+)?charu\b(?:$|[\s,])",
        query.strip(),
        re.IGNORECASE,
    ) is not None

def remove_wake_word(query):
    match = re.match(
        r"^(?:(?:hey|start|wake up)\s+)?charu\b[\s,]*(.*)$",
        query.strip(),
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else query.strip()

def is_offline_command(query):
    normalized = " ".join(query.lower().split())
    words = set(normalized.split())
    return "offline" in words or normalized in {
        "sleep",
        "go to sleep",
        "stop charu",
    }

def is_exit_command(query):
    words = set(query.lower().split())
    return bool(words.intersection({"exit", "quit"})) or any(
        phrase in query.lower() for phrase in ("close charu", "close assistant")
    )

def is_close_playback_command(query):
    normalized = " ".join(query.lower().split())
    return normalized in {
        "close",
        "close playback",
        "close the video",
        "close the song",
        "close youtube",
        "stop playback",
        "stop the video",
        "stop the song",
    }

def is_youtube_music_command(query):
    normalized = " ".join(query.lower().split())
    if any(
        phrase in normalized
        for phrase in (
            "play song",
            "play songs",
            "play a song",
            "play me a song",
            "play some songs",
            "play some music",
            "play music",
        )
    ):
        return True

    has_youtube_music_terms = "youtube" in normalized and any(
        word in normalized.split() for word in ("song", "songs", "music")
    )
    has_play_verb = any(word in normalized.split() for word in ("play", "playing", "listen"))
    has_named_song = re.search(r"\bplay\s+.+\s+song\b", normalized) is not None
    has_youtube_play_request = "youtube" in normalized and re.search(
        r"\b(?:play|playing|listen)\s+\S+", normalized
    ) is not None
    return has_play_verb and (has_youtube_music_terms or has_named_song or has_youtube_play_request)

def extract_youtube_song_title(query):
    normalized = " ".join(query.split())
    patterns = (
        r"\bplay\s+(?:the\s+)?song\s+(.+?)(?:\s+on\s+youtube)?$",
        r"\bplay\s+(.+?)\s+(?:song|songs|music)(?:\s+on\s+youtube)?$",
        r"\bplay\s+(.+?)(?:\s+on\s+youtube)?$",
    )

    for pattern in patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match:
            title = match.group(1).strip(" .,!?'\"")
            if title.lower() not in {
                "a",
                "a song",
                "the",
                "the song",
                "some",
                "some music",
                "some songs",
                "music",
                "song",
                "songs",
                "youtube",
                "youtube music",
                "youtube songs",
            }:
                return title

    return None

def extract_google_search_query(query):
    normalized = " ".join(query.split())
    patterns = (
        r"\bopen\s+google(?:\.com)?\s+and\s+search(?:\s+for)?\s+(.+)$",
        r"\bsearch\s+(?:google(?:\.com)?\s+)?for\s+(.+?)(?:\s+on\s+google(?:\.com)?)?$",
        r"\bgoogle(?:\.com)?\s+search\s+for\s+(.+)$",
    )

    for pattern in patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match:
            search_query = match.group(1).strip(" .,!?'\"")
            if search_query:
                return search_query

    return None

def is_drive_command(query):
    normalized = " ".join(query.lower().split())
    return any(
        phrase in normalized
        for phrase in (
            "open this pc",
            "open my computer",
            "open my laptop",
            "open laptop drive",
            "open my drive",
            "show my drives",
        )
    )

def is_light_on_command(query):
    normalized = " ".join(query.lower().split())
    return normalized in {
        "light on",
        "turn on the light",
        "turn the light on",
        "flashlight on",
        "turn on flashlight",
        "ambient light on",
    }

def is_light_off_command(query):
    normalized = " ".join(query.lower().split())
    return normalized in {
        "light off",
        "turn off the light",
        "turn the light off",
        "flashlight off",
        "turn off flashlight",
        "stop light",
        "stop the light",
    }

def find_youtube_video(song):
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "extract_flat": True,
    }

    try:
        with yt_dlp.YoutubeDL(options) as youtube:
            results = youtube.extract_info(f"ytsearch1:{song}", download=False)
    except yt_dlp.utils.DownloadError as error:
        print(f"YouTube search failed: {error}")
        return None

    entries = results.get("entries") if results else None
    result = next((entry for entry in entries or () if entry), None)
    if result is None or not result.get("id"):
        print(f"No YouTube results found for: {song}")
        return None

    video_id = result["id"]
    title = result.get("title") or song
    uploader = result.get("uploader") or result.get("channel") or "unknown artist"
    url = f"https://www.youtube.com/watch?v={quote(video_id, safe='')}"
    return YouTubeVideo(title, uploader, url)

def find_edge_executable():
    if sys.platform != "win32":
        raise OSError("Charu-managed YouTube playback currently requires Microsoft Edge on Windows.")

    candidates = (
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
        / "Microsoft"
        / "Edge"
        / "Application"
        / "msedge.exe",
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
        / "Microsoft"
        / "Edge"
        / "Application"
        / "msedge.exe",
        Path(os.environ.get("LOCALAPPDATA", ""))
        / "Microsoft"
        / "Edge"
        / "Application"
        / "msedge.exe",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate

    edge_on_path = shutil.which("msedge")
    if edge_on_path:
        return Path(edge_on_path)

    raise FileNotFoundError("Microsoft Edge was not found. Install Edge to use managed YouTube playback.")

def close_youtube_playback():
    global playback_process, playback_profile
    process = playback_process
    profile = playback_profile
    was_running = process is not None and process.poll() is None
    playback_process = None
    playback_profile = None

    if was_running:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    if profile is not None:
        profile.cleanup()

    return was_running

def play_youtube_video(video):
    global playback_process, playback_profile
    close_youtube_playback()

    edge = find_edge_executable()
    profile = tempfile.TemporaryDirectory(prefix="charu-youtube-")
    try:
        process = subprocess.Popen(
            [
                str(edge),
                f"--user-data-dir={profile.name}",
                "--no-first-run",
                "--no-default-browser-check",
                "--autoplay-policy=no-user-gesture-required",
                f"--app={video.url}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        profile.cleanup()
        raise

    playback_process = process
    playback_profile = profile
    return process

def search_youtube_song(query):
    song = extract_youtube_song_title(query)
    if not song:
        print("What song would you like to hear? Say only the song title.")
        speak("What song would you like to hear?")
        print("Listening for the song title...")
        song = take_command()
        if not song:
            print("No song title was recognized. Charu will keep listening for another command.")
            speak("I didn't catch the song name. Please try again.")
            return None

    print(f"Searching YouTube for: {song}")
    video = find_youtube_video(song)
    if video is None:
        speak(f"I couldn't find a YouTube result for {song}.", "en")
        return None

    print(f"Found: {video.title} by {video.uploader}")
    try:
        play_youtube_video(video)
    except (OSError, subprocess.SubprocessError) as error:
        print(f"Could not open YouTube playback: {error}")
        speak("I found the video, but couldn't open the playback window.", "en")
        return None

    speak(f"I found {video.title} by {video.uploader}. Playing it now.", "en")
    print(f"Started YouTube playback: {video.title}")
    return video

def open_laptop_drives():
    if sys.platform == "win32":
        subprocess.Popen(["explorer.exe", "shell:MyComputerFolder"])
    else:
        open_media(Path.home())

class CharuWindow:
    def __init__(self, active, running):
        self.active = active
        self.running = running
        self.events = queue.Queue()
        self.root = tk.Tk()
        self.root.title("Charu - Personal Voice Assistant")
        self.root.geometry("520x620")
        self.root.minsize(460, 560)
        self.root.configure(bg="#080d1b")
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        tk.Label(
            self.root,
            text="CHARU",
            font=("Segoe UI", 26, "bold"),
            fg="#e8f2ff",
            bg="#080d1b",
        ).pack(pady=(24, 2))
        tk.Label(
            self.root,
            text="PERSONAL VOICE ASSISTANT  |  MAINTAINED BY DEVEN PUNSE",
            font=("Segoe UI", 9, "bold"),
            fg="#7387aa",
            bg="#080d1b",
        ).pack()

        self.canvas = tk.Canvas(
            self.root,
            width=460,
            height=330,
            bg="#080d1b",
            highlightthickness=0,
        )
        self.canvas.pack(pady=(12, 0))
        self.center = (230, 160)
        star_generator = random.Random(31)
        self.stars = []
        for index in range(48):
            star_x = star_generator.randint(8, 452)
            star_y = star_generator.randint(8, 312)
            star_size = star_generator.choice((1, 1, 2))
            star = self.canvas.create_oval(
                star_x,
                star_y,
                star_x + star_size,
                star_y + star_size,
                fill="#29405c",
                outline="",
            )
            self.stars.append((star, index * 0.37))

        self.rings = [
            self.canvas.create_oval(0, 0, 0, 0, outline=color, width=width)
            for color, width in (
                ("#153b59", 2),
                ("#17617b", 2),
                ("#2b9bb1", 2),
            )
        ]
        self.arcs = [
            self.canvas.create_arc(
                0,
                0,
                0,
                0,
                style=tk.ARC,
                outline=color,
                width=3,
                extent=105,
            )
            for color in ("#2b9bb1", "#3676a3", "#1a526f")
        ]
        self.halo = self.canvas.create_oval(0, 0, 0, 0, fill="#10334d", outline="")
        self.core = self.canvas.create_oval(0, 0, 0, 0, fill="#1682a2", outline="")
        self.inner_core = self.canvas.create_oval(0, 0, 0, 0, fill="#a5f3fc", outline="")
        self.logo = self.canvas.create_text(
            *self.center,
            text="C",
            font=("Segoe UI", 30, "bold"),
            fill="#12617b",
        )
        self.orbit_particles = [
            (
                self.canvas.create_oval(0, 0, 0, 0, fill=color, outline=""),
                radius,
                speed,
                phase,
                size,
            )
            for color, radius, speed, phase, size in (
                ("#d5fbff", 112, 0.9, 0.0, 4),
                ("#58d8eb", 132, -0.65, 2.2, 3),
                ("#83b9ff", 94, 1.15, 4.1, 3),
            )
        ]

        self.status = tk.StringVar(value='Say "Charu" when you are ready.')
        tk.Label(
            self.root,
            textvariable=self.status,
            font=("Segoe UI", 12),
            fg="#c7d7f0",
            bg="#080d1b",
        ).pack(pady=(4, 18))

        controls = tk.Frame(self.root, bg="#080d1b")
        controls.pack()
        tk.Button(
            controls,
            text="Go offline",
            command=self.go_offline,
            font=("Segoe UI", 10, "bold"),
            fg="#e8f2ff",
            bg="#17243a",
            activebackground="#263b59",
            activeforeground="#ffffff",
            relief="flat",
            padx=18,
            pady=9,
            cursor="hand2",
        ).pack(side="left", padx=6)
        tk.Button(
            controls,
            text="Exit",
            command=self.close,
            font=("Segoe UI", 10),
            fg="#aab8cf",
            bg="#111a2b",
            activebackground="#263b59",
            activeforeground="#ffffff",
            relief="flat",
            padx=18,
            pady=9,
            cursor="hand2",
        ).pack(side="left", padx=6)

        tk.Label(
            self.root,
            text='Say "Charu" to give a command. Charu returns to standby after each task.',
            font=("Segoe UI", 9),
            fg="#7387aa",
            bg="#080d1b",
        ).pack(side="bottom", pady=20)

        self.root.after(50, self.process_events)
        self.animate()
        self.light_window = None
        self.light_canvas = None

    def post(self, event, value=None):
        self.events.put((event, value))

    def show_music_light(self):
        if self.light_window is not None and self.light_window.winfo_exists():
            return

        self.light_window = tk.Toplevel(self.root)
        self.light_window.title("Charu ambient light")
        self.light_window.overrideredirect(True)
        self.light_window.attributes("-topmost", True)
        self.light_window.configure(bg="#091526")
        width, height = 300, 82
        x = self.root.winfo_screenwidth() - width - 24
        self.light_window.geometry(f"{width}x{height}+{x}+24")

        self.light_canvas = tk.Canvas(
            self.light_window,
            width=width,
            height=height,
            bg="#091526",
            highlightthickness=0,
        )
        self.light_canvas.pack(fill="both", expand=True)
        self.light_canvas.create_text(
            18,
            height // 2,
            anchor="w",
            text="♪  MUSIC LIGHT",
            fill="#c6f7ff",
            font=("Segoe UI", 13, "bold"),
        )
        tk.Button(
            self.light_window,
            text="OFF",
            command=self.hide_music_light,
            font=("Segoe UI", 9, "bold"),
            fg="#e8f2ff",
            bg="#20374c",
            activebackground="#34546f",
            activeforeground="#ffffff",
            relief="flat",
            padx=10,
            cursor="hand2",
        ).place(relx=0.92, rely=0.5, anchor="center")
        self.animate_music_light()

    def animate_music_light(self):
        if self.light_window is None or not self.light_window.winfo_exists():
            return

        pulse = (math.sin(time.monotonic() * 0.7) + 1) / 2
        red = int(13 + pulse * 8)
        green = int(31 + pulse * 26)
        blue = int(47 + pulse * 34)
        color = f"#{red:02x}{green:02x}{blue:02x}"
        self.light_window.configure(bg=color)
        self.light_canvas.configure(bg=color)
        if self.running.is_set():
            self.root.after(100, self.animate_music_light)

    def hide_music_light(self):
        if self.light_window is not None and self.light_window.winfo_exists():
            self.light_window.destroy()
        self.light_window = None
        self.light_canvas = None

    def process_events(self):
        while True:
            try:
                event, value = self.events.get_nowait()
            except queue.Empty:
                break

            if event == "status":
                self.status.set(value)
            elif event == "show":
                self.root.deiconify()
                self.root.lift()
                self.status.set("I'm here. Listening...")
            elif event == "hide":
                self.root.withdraw()
            elif event == "light_on":
                self.show_music_light()
            elif event == "light_off":
                self.hide_music_light()
            elif event == "close":
                self.running.clear()
                close_youtube_playback()
                self.hide_music_light()
                self.root.quit()

        if self.running.is_set():
            self.root.after(50, self.process_events)

    def animate(self):
        if self.active.is_set():
            now = time.monotonic()
            pulse = math.sin(now * 2.2)
            star_colors = ("#1b2b46", "#305275", "#527f9f")
            for star, phase in self.stars:
                brightness = int(now * 1.6 + phase) % len(star_colors)
                self.canvas.itemconfigure(star, fill=star_colors[brightness])

            x, y = self.center
            for index, base_radius in enumerate((76, 105, 136)):
                radius = base_radius + pulse * (5 + index * 3)
                self.canvas.coords(
                    self.rings[index],
                    x - radius,
                    y - radius,
                    x + radius,
                    y + radius,
                )
            for index, radius in enumerate((105, 124, 144)):
                self.canvas.coords(
                    self.arcs[index],
                    x - radius,
                    y - radius,
                    x + radius,
                    y + radius,
                )
                self.canvas.itemconfigure(
                    self.arcs[index],
                    start=int(now * (45 + index * 18) + index * 120) % 360,
                )

            halo_radius = 58 + pulse * 5
            self.canvas.coords(
                self.halo,
                x - halo_radius,
                y - halo_radius,
                x + halo_radius,
                y + halo_radius,
            )
            core_radius = 47 + pulse * 4
            self.canvas.coords(
                self.core,
                x - core_radius,
                y - core_radius,
                x + core_radius,
                y + core_radius,
            )
            self.canvas.coords(
                self.inner_core,
                x - 31,
                y - 31,
                x + 31,
                y + 31,
            )
            for particle, radius, speed, phase, size in self.orbit_particles:
                angle = now * speed + phase
                particle_x = x + math.cos(angle) * radius
                particle_y = y + math.sin(angle) * radius * 0.72
                self.canvas.coords(
                    particle,
                    particle_x - size,
                    particle_y - size,
                    particle_x + size,
                    particle_y + size,
                )

        if self.running.is_set():
            self.root.after(30 if self.active.is_set() else 1000, self.animate)

    def go_offline(self):
        self.active.clear()
        self.root.withdraw()

    def close(self):
        self.running.clear()
        close_youtube_playback()
        self.root.quit()

    def run(self):
        self.root.mainloop()
        self.root.destroy()

def music_player(query, lang='en'):
    music_dir = Path.home() / "Music"
    if not music_dir.exists():
        return speak(STRINGS[lang]['error_music'], lang)
    
    songs = [f for f in music_dir.iterdir() if f.is_file()]
    if music_dir.exists():
        q_clean = query.replace("play music", "").strip()
        if q_clean:
            songs = [s for s in songs if q_clean in s.name.lower()]
        
        if songs:
            song = random.choice(songs)
            open_media(song)
            speak(STRINGS[lang]['playing'].format(song.name), lang)
        else:
            speak(STRINGS[lang]['no_song'], lang)

def wiki_search(query, lang='en'):
    speak(STRINGS[lang]['wiki_search'], lang)
    try:
        wikipedia.set_lang(lang)
        summary = wikipedia.summary(query, sentences=2)
        speak(summary, lang)
    except:
        speak(STRINGS[lang]['no_result'], lang)

def load_name():
    try:
        return Path("assistant_name.txt").read_text().strip()
    except:
        return "Charu"

# MAIN
if __name__ == "__main__":
    active = threading.Event()
    running = threading.Event()
    running.set()
    window = CharuWindow(active, running)

    def assistant_loop():
        while running.is_set():
            waiting_for_wake_word = not active.is_set()
            if waiting_for_wake_word:
                window.post("status", 'Waiting for "Charu"...')
            query = take_command(
                prompt=(
                    'Waiting for wake word "Charu"...'
                    if waiting_for_wake_word
                    else "Listening for your request..."
                ),
                report_no_speech=not waiting_for_wake_word,
                report_unclear=not waiting_for_wake_word,
            )
            if not query or not running.is_set():
                continue

            if not active.is_set():
                if is_wake_command(query):
                    active.set()
                    window.post("show")
                    speak("I'm listening. What can I do for you?", 'en')
                else:
                    continue

            query = remove_wake_word(query)
            if not query:
                continue

            if is_exit_command(query):
                speak(STRINGS['en']['exit'], 'en')
                window.post("close")
                break

            lang = 'en'

            if is_offline_command(query):
                speak(STRINGS[lang]['offline'], lang)
                active.clear()
                close_youtube_playback()
                window.post("light_off")
                window.post("hide")
            elif is_close_playback_command(query):
                if close_youtube_playback():
                    window.post("light_off")
                    speak("I closed the YouTube playback I opened.", lang)
                else:
                    speak("There is no YouTube playback open from Charu.", lang)
            elif is_light_off_command(query):
                window.post("light_off")
                speak("Ambient music light is off.", lang)
            elif is_light_on_command(query):
                window.post("light_on")
                speak("Ambient music light is on. It uses a gentle glow, not flashing lights.", lang)
            elif is_youtube_music_command(query):
                video = search_youtube_song(query)
                if video:
                    window.post("light_on")
                    window.post("status", f"Playing: {video.title} - {video.uploader}")
            elif is_drive_command(query):
                open_laptop_drives()
                speak("I opened your drives.", lang)
            elif any(
                phrase in query
                for phrase in ("let's chat", "lets chat", "talk to me", "chat with me", "let's talk")
            ):
                speak(companion_response(query), lang)
            elif "time" in query:
                get_time(lang)
            elif "date" in query:
                get_date(lang)
            elif "wikipedia" in query:
                wiki_search(query.replace("wikipedia", "").strip(), lang)
            elif "music" in query:
                music_player(query, lang)
            elif (search_query := extract_google_search_query(query)):
                search_url = f"https://www.google.com/search?q={quote(search_query)}"
                wb.open_new_tab(search_url)
                speak(f"Here are Google search results for {search_query}.", lang)
            elif "open youtube" in query:
                wb.open("https://www.youtube.com")
            elif "open google" in query:
                wb.open("https://www.google.com")
            elif any(word in query for word in ["capture", "screenshot"]):
                take_screenshot(lang)
            elif "shutdown" in query:
                speak(STRINGS[lang]['shutdown'], lang)
                os.system("systemctl poweroff" if sys.platform != "win32" else "shutdown /s /f /t 1")
                window.post("close")
                break
            elif "restart" in query:
                speak(STRINGS[lang]['restart'], lang)
                os.system("systemctl reboot" if sys.platform != "win32" else "shutdown /r /f /t 1")
                window.post("close")
                break
            else:
                speak(companion_response(query), lang)

            if running.is_set():
                active.clear()
                window.post("hide")
                window.post("status", 'Waiting for "Charu"...')

    threading.Thread(target=assistant_loop, daemon=True).start()
    window.run()
