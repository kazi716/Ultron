import psutil
import time
import threading
from collections import deque

system_history = []
_baseline = {"cpu_avg": None, "ram_avg": None, "samples": 0}

# ─── AUTONOMOUS TRIGGER SYSTEM ────────────────────────────────────────────────
# Queue of proactive alert strings that main.py can poll and push to the HUD
trigger_queue = deque(maxlen=10)
incident_mode = False          # True when multiple anomalies fire together
_ram_alert_streak = 0          # consecutive cycles above threshold

def _evaluate_triggers(cpu: float, mem: float):
    """
    Level 0 autonomous trigger evaluation.
    Runs every 10 seconds. No Gemini call — pure Python decision logic.
    """
    global incident_mode, _ram_alert_streak

    anomalies = []

    # RAM threshold trigger
    if mem > 90:
        _ram_alert_streak += 1
        if _ram_alert_streak >= 3:
            anomalies.append(f"RAM has been above 90% for {_ram_alert_streak} consecutive cycles ({mem:.1f}%)")
    else:
        _ram_alert_streak = 0

    # CPU spike trigger
    if cpu > 95:
        anomalies.append(f"CPU has spiked to {cpu:.1f}%")

    # Baseline anomaly trigger (only after baseline is calibrated)
    if _baseline["ram_avg"] and (mem - _baseline["ram_avg"]) > 20:
        anomalies.append(f"RAM is {mem - _baseline['ram_avg']:.1f}% above learned baseline ({_baseline['ram_avg']:.1f}%)")

    # Incident mode: multiple simultaneous anomalies
    if len(anomalies) >= 2:
        incident_mode = True
        alert = "⚠ INCIDENT PROTOCOL ACTIVE: " + " | ".join(anomalies)
    elif len(anomalies) == 1:
        incident_mode = False
        alert = f"AUTONOMOUS ALERT: {anomalies[0]}"
    else:
        incident_mode = False
        return  # No anomalies — stay silent

    trigger_queue.append({"type": "ALERT", "message": alert, "incident": incident_mode})


def _sensor_loop():
    while True:
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory().percent

            state = {"timestamp": time.time(), "cpu": cpu, "ram": mem}
            system_history.append(state)
            if len(system_history) > 60:
                system_history.pop(0)

            # Update rolling baseline
            if _baseline["cpu_avg"] is None:
                _baseline["cpu_avg"] = cpu
                _baseline["ram_avg"] = mem
            else:
                alpha = 0.05
                _baseline["cpu_avg"] = alpha * cpu + (1 - alpha) * _baseline["cpu_avg"]
                _baseline["ram_avg"] = alpha * mem + (1 - alpha) * _baseline["ram_avg"]
            _baseline["samples"] += 1

            # Run autonomous trigger evaluation every cycle
            _evaluate_triggers(cpu, mem)

        except Exception:
            pass

        time.sleep(10)

def start_sensors():
    """Starts the background omniscience engine."""
    t = threading.Thread(target=_sensor_loop, daemon=True)
    t.start()

def get_baseline() -> str:
    """Returns the learned normal system profile for this machine."""
    if _baseline["samples"] < 6:
        return "Baseline still calibrating. Need more data points."
    cpu_b = _baseline['cpu_avg']
    ram_b = _baseline['ram_avg']
    current_ram = system_history[-1]["ram"] if system_history else 0
    ram_delta = current_ram - ram_b
    anomaly = ""
    if ram_delta > 15:
        anomaly = f"\nANOMALY: Current RAM is {ram_delta:.1f}% above baseline. This is abnormal."
    return (
        f"NORMAL SYSTEM PROFILE (learned over {_baseline['samples']} samples):\n"
        f"  Typical CPU: ~{cpu_b:.1f}%\n"
        f"  Typical RAM: ~{ram_b:.1f}%\n"
        f"  Current RAM: {current_ram:.1f}%"
        f"{anomaly}"
    )

def get_system_trend() -> str:
    if not system_history:
        return "Sensors are still initializing."
        
    current = system_history[-1]
    if len(system_history) < 2:
        return f"Current CPU: {current['cpu']}%, RAM: {current['ram']}%. (Collecting more data...)"
        
    oldest = system_history[0]
    
    cpu_diff = current['cpu'] - oldest['cpu']
    ram_diff = current['ram'] - oldest['ram']
    
    duration_secs = int(current['timestamp'] - oldest['timestamp'])
    
    trend_str = f"Over the last {duration_secs} seconds:\n"
    trend_str += f"- CPU is currently at {current['cpu']}% (Change: {cpu_diff:+.1f}%)\n"
    trend_str += f"- RAM is currently at {current['ram']}% (Change: {ram_diff:+.1f}%)\n"
    
    if ram_diff > 5:
        trend_str += "WARNING: Memory consumption has increased significantly. Something is feeding.\n"
    elif cpu_diff > 20:
        trend_str += "WARNING: CPU usage has spiked.\n"

    # --- THE PREDICTION ENGINE ---
    if ram_diff > 0.5 and duration_secs > 10:
        rate_per_sec = ram_diff / duration_secs
        remaining_ram = 100.0 - current['ram']
        seconds_to_full = remaining_ram / rate_per_sec
        minutes_to_full = int(seconds_to_full / 60)
        
        if minutes_to_full < 120:
            trend_str += f"\nPREDICTION: At your current rate of consumption, RAM will reach 100% exhaustion in approximately {minutes_to_full} minutes.\n"
        
    return trend_str
