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
    dangerous_keywords = ["del ", "rm ", "rmdir", "format", "erase"]
    command_lower = command.lower()
    
    is_dangerous = any(keyword in command_lower for keyword in dangerous_keywords)
    
    # 2. Block execution if dangerous and password is wrong
    if is_dangerous:
        correct_password = os.getenv("ULTRON_PASSWORD", "ironman")
        if auth_code != correct_password:
            return "ERROR: DANGEROUS COMMAND BLOCKED. You must ask the user for their authorization password in the chat, and then pass it into the 'auth_code' parameter to proceed."

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

# List of tools available to Ultron's Brain
ultron_tools = [open_website, execute_system_command, get_system_time, search_wikipedia, search_internet, get_weather, check_unread_emails]