import os
import subprocess
import webbrowser
from datetime import datetime

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

# List of tools available to Ultron's Brain
ultron_tools = [open_website, execute_system_command, get_system_time]
