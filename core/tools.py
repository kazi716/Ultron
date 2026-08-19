import os
import subprocess
import webbrowser
from datetime import datetime
import wikipedia
import requests
from duckduckgo_search import DDGS

def open_website(url: str) -> str:
    """Opens a website in the default browser. Ensure the URL starts with http:// or https://."""
    try:
        webbrowser.open(url)
        return f"Successfully opened {url}"
    except Exception as e:
        return f"Failed to open website: {e}"

def execute_system_command(command: str) -> str:
    """Executes a terminal/command prompt command and returns the output. Use this to open applications, manage files, or get system info."""
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

# List of tools available to Ultron's Brain
ultron_tools = [open_website, execute_system_command, get_system_time, search_wikipedia, search_internet, get_weather]