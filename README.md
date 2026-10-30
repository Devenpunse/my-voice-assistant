# Charu — Personal Voice Assistant

Charu is a desktop voice assistant written in Python. It listens for the wake word
“Charu,” responds with speech, and helps with everyday desktop tasks through a
simple animated interface. Speech recognition uses Google’s online recognition
service, so an internet connection is required for voice commands.

## Features

- Wake-word activation and standby mode
- Spoken responses for the time, date, and Wikipedia searches
- Open Google and YouTube, or search Google by voice
- Find and play YouTube music in a separate Microsoft Edge window
- Open Windows File Explorer to This PC and take a screenshot
- Short, supportive companion responses
- Animated assistant window and an optional ambient music-light panel
- Optional launch at Windows sign-in

Charu recognizes and responds in English.

## Requirements

- Windows with a working microphone and speakers
- Python 3.10 or later
- Internet access for speech recognition, web searches, Wikipedia, and YouTube
- Microsoft Edge for the separate YouTube playback window

Python packages listed in [`requirements.txt`](requirements.txt):

| Package | Purpose |
| --- | --- |
| `pyttsx3` | Offline text-to-speech |
| `wikipedia` | Wikipedia summaries |
| `PyAutoGUI` | Screenshot capture |
| `SpeechRecognition` | Microphone input and online speech recognition |
| `yt-dlp` | YouTube search and video information |

The assistant uses Python’s built-in Tkinter module for its desktop interface.
Microphone input through `SpeechRecognition` also requires PyAudio. If the
microphone cannot be opened after installing the requirements, install its audio
extra:

```powershell
.\.venv\Scripts\python.exe -m pip install "SpeechRecognition[audio]"
```

## Installation

Open PowerShell in the repository directory, then create a virtual environment
and install the project dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

From the repository directory, start Charu with:

```powershell
.\.venv\Scripts\python.exe .\Jarvis\jarvis.py
```

Keep the PowerShell window open while the assistant is running. Allow microphone
access if Windows prompts you.

## Use Charu

Say **“Charu”** and wait for the listening prompt, then give one request. You
can also combine the wake word and request, for example, **“Charu, open
YouTube.”** Say “Charu” again before each new request; after handling a request,
the assistant returns to standby.

Examples:

| Say | What Charu does |
| --- | --- |
| “What time is it?” / “What is the date?” | Announces the current time or date |
| “Open YouTube” / “Open Google” | Opens the requested website |
| “Open Google and search for GitHub” | Searches Google for the requested phrase |
| “Play [song title] song” | Finds a YouTube match and opens it in Edge |
| “Close” | Closes the YouTube playback window opened by Charu |
| “Wikipedia [topic]” | Reads a short Wikipedia summary |
| “Take a screenshot” | Saves a screenshot in your Pictures folder |
| “Open my laptop drive” / “Show my drives” | Opens This PC in File Explorer |
| “Light off” / “Light on” | Hides or shows the ambient music-light panel |
| “Offline” | Hides the window and waits for the wake word |
| “Exit” | Closes the assistant |

For YouTube playback, say “play a song” to be asked for a title, or include the
title in your request. The ambient-light panel can also be dismissed with its
**OFF** button.

## Start at Windows sign-in (optional)

From PowerShell, run the installer in the `Jarvis` directory:

```powershell
Set-Location .\Jarvis
.\install_startup.ps1
```

This creates a shortcut in your Windows Startup folder. To remove it:

```powershell
.\uninstall_startup.ps1
```

If PowerShell blocks the script, allow scripts for the current PowerShell
process, then retry:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

## Project layout

```text
Jarvis/
  companion.py             Companion response handling
  jarvis.py                Assistant, interface, and command handling
  install_startup.ps1      Optional Windows sign-in setup
  uninstall_startup.ps1    Remove the sign-in shortcut
requirements.txt           Python package dependencies
```

## Author

**Deven**
