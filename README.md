# Alfred Wayne OS 🦇

> **Autonomous AI Companion & Operating Butler**

[![Render Deployment](https://img.shields.io/badge/Render-Live_App-00bfff?style=for-the-badge&logo=render&logoColor=white)](https://alfredwayneos.onrender.com)
[![Python Version](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## 🌐 Live Web Application & Demo

Alfred Wayne OS is deployed live on Render! Access the interactive HUD and talk with Alfred directly from your web browser:

LIVE :  https://alfred-wayne-os.onrender.com/

---

## 🌟 Key Features

- **Dual-Engine Intelligence**: Powered by **Groq (Llama 3.1 8B Instant)** as primary engine with automatic fallback to **Google Gemini (Gemini 2.0 Flash Lite)**.
- **Interactive Web HUD**: Futuristic sci-fi animated dashboard with real-time system telemetry and state visualization.
- **Web Speech Integration**: Native browser speech recognition and text-to-speech voice synthesis.
- **Persistent Long-Term Memory**: Autonomous memory extraction and conversation summaries.
- **Render Ready**: Pre-configured Blueprint (`render.yaml`) and WSGI production server (`gunicorn web_app:app`).

---

## 🚀 Deploying to Render

### Option 1: Render Blueprint (Recommended)

1. Log in to your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** and select **Blueprint**.
3. Connect your GitHub repository: `Snehilxcoding/AlfredWayneOS`.
4. Render will automatically detect `render.yaml`.
5. Add your Environment Variables:
   - `GROQ_API_KEY`: Your Groq API key
   - `GEMINI_API_KEY`: Your Gemini API key
6. Click **Apply**. Your app will be live at `https://alfredwayneos.onrender.com`!

### Option 2: Manual Web Service Setup on Render

1. Click **New +** -> **Web Service**.
2. Connect `Snehilxcoding/AlfredWayneOS`.
3. Set the following settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn web_app:app`
4. Add environment variables `GROQ_API_KEY` & `GEMINI_API_KEY`.
5. Click **Create Web Service**.

---

## 💻 Local Development

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/Snehilxcoding/AlfredWayneOS.git
cd AlfredWayneOS
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### 3. Run Web Application
```bash
python web_app.py
```
Open `http://localhost:5000` in your web browser.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11, Flask, Gunicorn
- **AI Models**: Groq API (Llama 3.1), Google GenAI SDK (Gemini 2.0 Flash)
- **Frontend**: Vanilla HTML5, CSS3 Glassmorphism, Canvas API, Web Speech API
- **Cloud Infrastructure**: Render

---

Made with ❤️ by [Snehilxcoding](https://github.com/Snehilxcoding)
