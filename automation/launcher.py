import os
import subprocess
import webbrowser
from config.settings import USER_NAME

APP_MAP = {
    "vs code":       "code",
    "vscode":        "code",
    "notepad":       "notepad",
    "chrome":        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":       r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge":          "msedge",
    "task manager":  "taskmgr",
    "file explorer": "explorer",
    "calculator":    "calc",
    "cmd":           "cmd",
    "powershell":    "powershell",
    "paint":         "mspaint",
    "spotify":       r"%APPDATA%\Spotify\Spotify.exe",
    "discord":       r"%LOCALAPPDATA%\Discord\Update.exe --processStart Discord.exe",
    "word":          r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":         r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
}

SITE_MAP = {
    "youtube":       "https://youtube.com",
    "google":        "https://google.com",
    "github":        "https://github.com",
    "gmail":         "https://mail.google.com",
    "reddit":        "https://reddit.com",
    "twitter":       "https://twitter.com",
    "netflix":       "https://netflix.com",
    "stackoverflow": "https://stackoverflow.com",
    "chatgpt":       "https://chat.openai.com",
    "claude":        "https://claude.ai",
    "whatsapp":      "https://web.whatsapp.com",
}

def open_application(name):
    key = name.lower().strip()
    exe = APP_MAP.get(key)
    try:
        if exe:
            subprocess.Popen(os.path.expandvars(exe), shell=True)
        else:
            subprocess.Popen(key, shell=True)
        return True, f"Opening {name} for you, {USER_NAME}."
    except Exception as e:
        return False, f"I couldn't open {name}, {USER_NAME}: {e}"

def open_website(name):
    key = name.lower().strip()
    url = SITE_MAP.get(key)
    if not url:
        url = name if name.startswith("http") else f"https://{name}"
    webbrowser.open(url)
    return True, f"Opening {name} for you, {USER_NAME}."

def search_web(query):
    webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
    return True, f"Searching for '{query}', {USER_NAME}."

def create_text_file(filename):
    path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
    try:
        with open(path, "w") as f:
            f.write("")
        return True, f"Created '{filename}' on your Desktop, {USER_NAME}."
    except Exception as e:
        return False, f"Couldn't create the file, {USER_NAME}: {e}"
    