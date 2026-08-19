# ULTRON // SMART HUB

An autonomous, AI-powered smart hub and virtual assistant built with Python, FastAPI, and Google's Gemini AI. Ultron can control your PC, browse the internet, check live weather, read your emails, and communicate through a futuristic Matrix-themed web dashboard.

## 🚀 Features
* **Matrix HUD Web Dashboard:** A beautiful, fully animated HTML5 canvas UI with neon glass-morphism panels, accessible via any device on your local Wi-Fi.
* **Gemini AI Brain:** Uses Google's `gemini-3.6-flash` for high-speed, conversational context and tool routing.
* **Voice Integration:** Supports high-quality TTS via ElevenLabs API, with an automatic fallback to offline Windows voice (`pyttsx3`) if the internet or API fails.
* **System Automation:** Can execute secure system commands to evaluate memory, open applications, or manage local files.
* **Live Web Search:** Uses DuckDuckGo and Wikipedia to browse the web for up-to-date news and information.
* **Live Weather:** Fetches live weather and temperatures for any city via the Open-Meteo API (no API keys required).
* **Email Reader:** Connects securely to Gmail via IMAP to read your latest unread emails directly on the dashboard.
* **Ghost Mode:** Runs silently in the background (`pythonw`) without requiring a terminal window to remain open.

## ⚙️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/kazi716/Ultron.git
   cd Ultron
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Environment Variables:**
   Rename `.env.example` to `.env` and add your API keys:
   ```env
   GEMINI_API_KEY=your_gemini_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_key_here (optional)
   GMAIL_ADDRESS=your_gmail@gmail.com (optional)
   GMAIL_APP_PASSWORD=your_16_char_app_password (optional)
   ```

## 💻 Usage

To run Ultron with a visible terminal:
```bash
python main.py
```

**To run Ultron invisibly in the background (Recommended):**
```bash
pythonw main.py
```
*(Ultron's internal logs will be saved to `ultron_background.log` when running in this mode).*

Once running, open your web browser (on your PC or your phone) and navigate to:
**`http://localhost:8000`** (or your local IP address, e.g., `http://192.168.31.59:8000`).

## ⚠️ Security Warning
This AI has the capability to run system-level commands on your PC. Do not expose Port 8000 to the public internet without implementing proper authentication first.
