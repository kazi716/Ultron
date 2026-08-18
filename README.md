# Project Ultron 🤖

An advanced, voice-activated AI assistant powered by the Gemini API and ElevenLabs for realistic Text-To-Speech.

## Features
* **Intelligent Core**: Uses Google's `gemini-2.5-flash` model for reasoning and conversation.
* **Cinematic Voice**: Integrates with ElevenLabs so you can use custom voice clones (like James Spader's Ultron).
* **Speech Recognition**: Uses your microphone to listen and transcribe speech.

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/kazi716/Ultron.git
cd Ultron
```

2. **Create a virtual environment (Optional but recommended):**
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the `.env.example` file and rename it to `.env`:
```bash
cp .env.example .env
```
2. Open the `.env` file and replace the placeholder text with your actual API keys:
   * **`GEMINI_API_KEY`**: Get this from Google AI Studio.
   * **`ELEVENLABS_API_KEY`**: Get this from your ElevenLabs profile.
   * **`ELEVENLABS_VOICE_ID`**: Get this from your ElevenLabs VoiceLab.

*(Note: The `.env` file is ignored by git, so your API keys will remain private and won't be uploaded to GitHub).*

## Usage

Run the main script to bring Ultron online:
```bash
python main.py
```
Press `[Enter]` to use your microphone, or type your text directly.
