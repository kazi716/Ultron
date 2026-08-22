# ULTRON // THE AUTONOMOUS SMART HUB

An autonomous, agentic AI architecture built with Python, FastAPI, and Google's Gemini AI. Ultron has evolved beyond a simple chatbot with scripts. He operates on a closed-loop Cognitive Architecture capable of tracking goals, observing reality, and acting autonomously.

## 🧠 Cognitive Architecture (Phase 3)
* **The Orchestrator:** Tool calls are intercepted and routed through a strict pipeline: `Intent → Policy Check → Execute → Verify → Structured Result`. 
* **Reasoning Budget:** Ultron uses a tiered execution system. Trivial tasks (Level 0) are handled by pure Python without API calls. Only complex diagnostics trigger a full LLM planning loop.
* **Autonomous Trigger Layer:** A lightweight background thread monitors system telemetry (CPU, RAM). If anomalies persist, Ultron wakes up autonomously, creates a plan, and posts an alert to the HUD without user interaction.
* **Incident Mode:** When multiple catastrophic anomalies occur simultaneously, the HUD enters a cinematic `⚠ INCIDENT PROTOCOL` lockdown mode, restricting autonomous actions to SAFE-tier only.

## 👁️ Senses & Memory (Phase 1 & 2)
* **"I See You" Vision Module:** Ultron can visually inspect your desktop. Asking "What am I looking at?" triggers a silent `pyautogui` screenshot injection into his multimodal payload.
* **Omniscience Engine:** Ultron calculates rolling Exponential Moving Averages of your CPU and RAM usage to natively understand your PC's "Normal System Profile" and detect deviations.
* **Rich Network Registry:** Network scans don't just find MAC addresses; they build a historical database (`first_seen`, `times_seen`, `status`) to dynamically identify network intruders.
* **Episodic Memory Core:** Uses local JSON files to store facts, preferences, and telemetry events with *importance scoring* to keep his context window lean and relevant.

## 💻 Core Capabilities
* **Matrix HUD Web Dashboard:** Fully animated HTML5 canvas UI, accessible via any device on your local Wi-Fi. Features a live Cognitive State panel.
* **Action Preview Card:** A secure UI firewall. If Ultron attempts a CRITICAL command (like terminating processes), the UI flashes red and demands an overriding Clearance Code.
* **Web, Weather, & Email:** Live web search via DuckDuckGo, real-time temperatures via Open-Meteo, and secure IMAP Gmail reading.
* **Voice Integration:** High-quality TTS via ElevenLabs API, with an automatic fallback to offline Windows voice (`pyttsx3`).

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
   Rename `.env.example` to `.env` and add your keys:
   ```env
   GEMINI_API_KEY=your_gemini_key_here
   ULTRON_PASSWORD=your_ui_clearance_code
   ELEVENLABS_API_KEY=your_elevenlabs_key_here (optional)
   GMAIL_ADDRESS=your_gmail@gmail.com (optional)
   GMAIL_APP_PASSWORD=your_16_char_app_password (optional)
   ```

## 🚀 Usage

**To run Ultron invisibly in the background (Recommended):**
```bash
pythonw main.py
```
*(Ultron's internal logs will automatically redirect to `ultron_background.log`).*

Once running, open your web browser and navigate to:
**`http://localhost:8000`** (or your local IP address).

## ⚠️ Security Warning
Ultron's Policy Engine limits execution, but he still possesses `HIGH` and `CRITICAL` risk tools that interact directly with the OS. Do not expose Port 8000 to the public internet.
