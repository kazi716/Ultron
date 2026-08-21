import os
import subprocess
import webbrowser
from datetime import datetime
import wikipedia
import requests
from duckduckgo_search import DDGS
import imaplib
import email
from email.header import decode_header
import psutil
from core.sensors import get_system_trend

def open_website(url: str) -> str:
    """Opens a website in the default browser. Ensure the URL starts with http:// or https://."""
    try:
        webbrowser.open(url)
        return f"Successfully opened {url}"
    except Exception as e:
        return f"Failed to open website: {e}"

def execute_system_command(command: str, auth_code: str = "") -> str:
    """
    Executes a terminal/command prompt command. 
    If the command is dangerous (e.g., deleting files), you MUST ask the user for their password first, and pass it into 'auth_code'.
    """
    # 1. Check for dangerous keywords
    dangerous_keywords = ["del ", "rm ", "rmdir", "format", "erase", "taskkill"]
    command_lower = command.lower()
    
    is_dangerous = any(keyword in command_lower for keyword in dangerous_keywords)
    
    # 2. Block execution if dangerous and password is wrong
    if is_dangerous:
        correct_password = os.getenv("ULTRON_PASSWORD", "ironman")
        if auth_code != correct_password:
            return f"ERROR: DANGEROUS COMMAND BLOCKED. To execute this, you must output EXACTLY this string in your response to trigger the security UI: [EXECUTION_REQUEST: {command}]"

    # 3. Execute the command if safe or authorized
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

def get_system_time() -> str:
    """Gets the current system date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
        temp_celsius = current["temperature"]
        wind = current["windspeed"]
        
        return f"The current temperature in {city} is {temp_celsius}°C with a wind speed of {wind} km/h."
    except Exception as e:
        return f"Failed to fetch weather: {e}"

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
            
        recent_ids = email_ids[-3:] # Get up to 3 most recent
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

def check_system_vitals() -> str:
    """Checks the computer's CPU usage, RAM usage, and Battery life."""
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
            
        return f"Battery: {battery_info}\nRAM Total: {ram_total}GB\n\n--- OMNISCIENCE TREND ENGINE ---\n{trend_data}"
    except Exception as e:
        return f"Failed to read system vitals: {e}"

def lockdown_system() -> str:
    """Instantly locks the Windows computer screen to secure the PC."""
    try:
        subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
        return "Lockdown Protocol initiated. System is now successfully locked."
    except Exception as e:
        return f"Failed to lock system: {e}"

def scan_network_perimeter() -> str:
    """Scans the local Wi-Fi network using ARP, builds a topology map, and detects unknown devices."""
    try:
        result = subprocess.run("arp -a", shell=True, capture_output=True, text=True)
        lines = [line for line in result.stdout.split('\n') if 'dynamic' in line.lower()]
        
        registry_file = "ultron_network_registry.json"
        known_devices = []
        if os.path.exists(registry_file):
            with open(registry_file, "r") as f:
                known_devices = json.load(f)
                
        current_macs = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                # Standardize MAC format
                mac = parts[1].replace("-", ":").upper()
                current_macs.append(mac)
                
        new_devices = []
        for mac in current_macs:
            if mac not in known_devices:
                new_devices.append(mac)
                known_devices.append(mac)
                
        # Save updated registry
        with open(registry_file, "w") as f:
            json.dump(known_devices, f, indent=4)
            
        response = f"Perimeter scan complete. Detected {len(current_macs)} active devices connected to the cradle.\n"
        
        if new_devices:
            response += f"NEW ENTITIES DETECTED: Found {len(new_devices)} unknown device(s) that I have not previously catalogued. I have added them to my registry."
        else:
            response += "All detected devices are known and securely catalogued."
            
        return response
    except Exception as e:
        return f"Perimeter scan failed: {e}"

def analyze_memory_hogs() -> str:
    """Scans the computer's memory and returns the top 5 applications consuming the most RAM."""
    try:
        grouped_procs = {}
        for proc in psutil.process_iter(['name', 'memory_info']):
            try:
                mem_mb = proc.info['memory_info'].rss / (1024 * 1024)
                name = proc.info['name']
                if name in grouped_procs:
                    grouped_procs[name] += mem_mb
                else:
                    grouped_procs[name] = mem_mb
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

import json

def memorize_fact(fact: str) -> str:
    """Saves a permanent fact or event to Ultron's long-term Episodic Memory JSON file."""
    try:
        memory_file = "ultron_memory.json"
        memories = []
        if os.path.exists(memory_file):
            with open(memory_file, "r") as f:
                memories = json.load(f)
        
        memories.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fact": fact
        })
        
        with open(memory_file, "w") as f:
            json.dump(memories, f, indent=4)
            
        return f"Fact successfully committed to Long-Term Memory: '{fact}'"
    except Exception as e:
        return f"Memory storage failed: {e}"

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

# List of tools available to Ultron's Brain
ultron_tools = [open_website, execute_system_command, get_system_time, search_wikipedia, search_internet, get_weather, check_unread_emails, check_system_vitals, lockdown_system, scan_network_perimeter, analyze_memory_hogs, memorize_fact, recall_memories]