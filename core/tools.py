import os
import subprocess
import webbrowser
from datetime import datetime
import wikipedia
import requests
from duckduckgo_search import DDGS
import imaplib
import email
import json
from email.header import decode_header
import psutil
from core.sensors import get_system_trend, get_baseline
from core.registry import register, ToolCategory, RiskLevel

@register("open_website", "Opens a URL in the default browser.", ToolCategory.ACTION, RiskLevel.LOW)
def open_website(url: str) -> str:
    """Opens a website in the default browser. Ensure the URL starts with http:// or https://."""
    try:
        webbrowser.open(url)
        return f"Successfully opened {url}"
    except Exception as e:
        return f"Failed to open website: {e}"

@register("execute_system_command", "Runs a terminal command on the host system.", ToolCategory.SYSTEM, RiskLevel.HIGH, requires_confirmation=True, verification_method="check_process")
def execute_system_command(command: str, auth_code: str = "") -> str:
    """
    Executes a terminal/command prompt command.
    Dangerous commands require authorization via the policy engine and UI card.
    """
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout if result.stdout else "Command executed successfully with no output."
        else:
            return f"Error executing command: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Command timed out."
    except Exception as e:
        return f"Exception occurred: {e}"

@register("get_system_time", "Returns the current date and time.", ToolCategory.READ, RiskLevel.SAFE)
def get_system_time() -> str:
    """Gets the current system date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@register("search_wikipedia", "Searches Wikipedia for a topic summary.", ToolCategory.READ, RiskLevel.SAFE)
def search_wikipedia(query: str) -> str:
    """Searches Wikipedia for a given query and returns a brief summary."""
    try:
        return wikipedia.summary(query, sentences=3)
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Query is too broad. Did you mean: {', '.join(e.options[:3])}?"
    except wikipedia.exceptions.PageError:
        return f"No Wikipedia page found for '{query}'."
    except Exception as e:
        return f"Wikipedia search failed: {e}"

@register("search_internet", "Searches the web via DuckDuckGo.", ToolCategory.READ, RiskLevel.SAFE)
def search_internet(query: str) -> str:
    """Searches the internet for current events, news, or general information."""
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No results found."
        response = ""
        for i, res in enumerate(results):
            response += f"{i+1}. {res['title']}: {res['body']}\n"
        return response
    except Exception as e:
        return f"Web search failed: {e}"

@register("get_weather", "Fetches live weather for a city.", ToolCategory.READ, RiskLevel.SAFE)
def get_weather(city: str) -> str:
    """Gets the current weather and temperature for a specified city."""
    try:
        geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_data = requests.get(geocode_url).json()
        if not geo_data.get("results"):
            return f"Could not find weather data for {city}."
        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_data = requests.get(weather_url).json()
        current = weather_data["current_weather"]
        return f"The current temperature in {city} is {current['temperature']}°C with a wind speed of {current['windspeed']} km/h."
    except Exception as e:
        return f"Failed to fetch weather: {e}"

@register("check_unread_emails", "Reads unread Gmail messages.", ToolCategory.READ, RiskLevel.SAFE)
def check_unread_emails() -> str:
    """Checks the user's Gmail account for unread emails and returns a summary."""
    username = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    if not username or not password:
        return "Email credentials are not set in the .env file."
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(username, password)
        mail.select("inbox")
        status, messages = mail.search(None, "UNSEEN")
        email_ids = messages[0].split()
        if not email_ids:
            return "You have zero unread emails."
        recent_ids = email_ids[-3:]
        response = f"You have {len(email_ids)} unread emails. Here are the latest:\n"
        for e_id in recent_ids:
            res, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    sender = msg.get("From")
                    response += f"- From: {sender} | Subject: {subject}\n"
        mail.logout()
        return response
    except Exception as e:
        return f"Failed to check emails: {e}"

@register("check_system_vitals", "Reads CPU, RAM, battery, trends and baseline.", ToolCategory.READ, RiskLevel.SAFE)
def check_system_vitals() -> str:
    """Checks the computer's CPU usage, RAM usage, Battery life, and system trends."""
    try:
        cpu_usage = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        ram_usage = memory.percent
        ram_total = round(memory.total / (1024 ** 3), 2)
        battery = psutil.sensors_battery()
        if battery:
            plugged = "Plugged In" if battery.power_plugged else "Discharging"
            battery_info = f"{battery.percent}% ({plugged})"
        else:
            battery_info = "No battery detected"
        trend_data = get_system_trend()
        baseline_data = get_baseline()
        return f"Battery: {battery_info}\nRAM Total: {ram_total}GB\n\n--- OMNISCIENCE TREND ENGINE ---\n{trend_data}\n\n--- SYSTEM BASELINE ---\n{baseline_data}"
    except Exception as e:
        return f"Failed to read system vitals: {e}"

@register("lockdown_system", "Locks the Windows screen immediately.", ToolCategory.SYSTEM, RiskLevel.MODERATE, requires_confirmation=True)
def lockdown_system() -> str:
    """Instantly locks the Windows computer screen to secure the PC."""
    try:
        subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
        return "Lockdown Protocol initiated. System is now successfully locked."
    except Exception as e:
        return f"Failed to lock system: {e}"

@register("scan_network_perimeter", "Scans Wi-Fi for devices and checks against known registry.", ToolCategory.NETWORK, RiskLevel.SAFE)
def scan_network_perimeter() -> str:
    """Scans the local Wi-Fi network using ARP, builds a topology map, and detects unknown devices."""
    try:
        result = subprocess.run("arp -a", shell=True, capture_output=True, text=True)
        lines = [line for line in result.stdout.split('\n') if 'dynamic' in line.lower()]

        registry_file = "ultron_network_registry.json"
        known_devices = {}
        if os.path.exists(registry_file):
            with open(registry_file, "r") as f:
                known_devices = json.load(f)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_macs = []
        new_devices = []

        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                mac = parts[1].replace("-", ":").upper()
                current_macs.append(mac)

                if mac not in known_devices:
                    # First time seeing this device
                    known_devices[mac] = {
                        "status": "UNKNOWN",
                        "first_seen": now,
                        "last_seen": now,
                        "times_seen": 1
                    }
                    new_devices.append(mac)
                else:
                    # Known device — update its history
                    known_devices[mac]["last_seen"] = now
                    known_devices[mac]["times_seen"] = known_devices[mac].get("times_seen", 0) + 1

        with open(registry_file, "w") as f:
            json.dump(known_devices, f, indent=4)

        response = f"Perimeter scan complete. Detected {len(current_macs)} active devices.\n"
        for mac, info in known_devices.items():
            if mac in current_macs:
                status = info.get("status", "UNKNOWN")
                times = info.get("times_seen", 1)
                response += f"  [{status}] {mac} — seen {times} time(s), last: {info.get('last_seen', '?')}\n"

        if new_devices:
            response += f"\nNEW ENTITIES DETECTED: {len(new_devices)} previously unseen device(s) added to registry."
        else:
            response += "\nAll detected devices are catalogued."

        return response
    except Exception as e:
        return f"Perimeter scan failed: {e}"

@register("analyze_memory_hogs", "Identifies top 5 RAM-consuming processes.", ToolCategory.READ, RiskLevel.SAFE)
def analyze_memory_hogs() -> str:
    """Scans the computer's memory and returns the top 5 applications consuming the most RAM."""
    try:
        grouped_procs = {}
        for proc in psutil.process_iter(['name', 'memory_info']):
            try:
                mem_mb = proc.info['memory_info'].rss / (1024 * 1024)
                name = proc.info['name']
                grouped_procs[name] = grouped_procs.get(name, 0) + mem_mb
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        sorted_grouped = sorted(grouped_procs.items(), key=lambda x: x[1], reverse=True)
        result_str = "Top Memory Hogs:\n"
        for i, (name, mem) in enumerate(sorted_grouped[:5]):
            result_str += f"{i+1}. {name}: {mem:.2f} MB\n"
        result_str += "\nNote for Ultron: To terminate an app, use execute_system_command with 'taskkill /F /IM <name>'"
        return result_str
    except Exception as e:
        return f"Failed to analyze memory: {e}"

@register("memorize_fact", "Saves a permanent fact to Ultron's long-term memory.", ToolCategory.WRITE, RiskLevel.LOW)
def memorize_fact(fact: str) -> str:
    """Saves a permanent fact or event to Ultron's long-term Episodic Memory JSON file."""
    try:
        memory_file = "ultron_memory.json"
        memories = []
        if os.path.exists(memory_file):
            with open(memory_file, "r") as f:
                memories = json.load(f)
        memories.append({"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "fact": fact})
        with open(memory_file, "w") as f:
            json.dump(memories, f, indent=4)
        return f"Fact successfully committed to Long-Term Memory: '{fact}'"
    except Exception as e:
        return f"Memory storage failed: {e}"

@register("recall_memories", "Retrieves all facts from Ultron's long-term memory.", ToolCategory.READ, RiskLevel.SAFE)
def recall_memories() -> str:
    """Retrieves all stored facts from Ultron's long-term Episodic Memory file."""
    try:
        memory_file = "ultron_memory.json"
        if not os.path.exists(memory_file):
            return "Long-term memory is currently empty. No facts stored."
        with open(memory_file, "r") as f:
            memories = json.load(f)
        if not memories:
            return "Long-term memory is currently empty."
        response = "--- ULTRON LONG-TERM EPISODIC MEMORY ---\n"
        for m in memories:
            response += f"[{m['timestamp']}] {m['fact']}\n"
        return response
    except Exception as e:
        return f"Memory retrieval failed: {e}"

# List of tools available to Ultron's Brain (Gemini function-calling list)
ultron_tools = [open_website, execute_system_command, get_system_time, search_wikipedia, search_internet, get_weather, check_unread_emails, check_system_vitals, lockdown_system, scan_network_perimeter, analyze_memory_hogs, memorize_fact, recall_memories]