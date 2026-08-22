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
_last_alert_sent = 0          # Tracks when we last sent an alert
_last_alert_msg = ""          # Tracks what the last alert was

def _evaluate_triggers(cpu: float, mem: float):
    """
    Level 0 autonomous trigger evaluation.
    Runs every 10 seconds. No Gemini call — pure Python decision logic.
    """
    global incident_mode, _ram_alert_streak, _last_alert_sent, _last_alert_msg

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

    # --- COOLDOWN LOGIC (Anti-Spam) ---
    current_time = time.time()
    
    # If the message is the same, wait 120 seconds before repeating it
    if alert == _last_alert_msg and (current_time - _last_alert_sent) < 120:
        return 
        
    _last_alert_sent = current_time
    _last_alert_msg = alert

    trigger_queue.append({"type": "ALERT", "message": alert, "incident": incident_mode})


# ─── RESOURCE MODE STATE MACHINE ──────────────────────────────────────────────
_resource_mode = "NORMAL"   # NORMAL | DEGRADED | SURVIVAL

def get_resource_mode_str() -> str:
    return _resource_mode


def _sensor_loop():
    global _resource_mode
    while True:
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory().percent

            # ── RESOURCE MODE EVALUATION ──────────────────────────────────────
            prev_mode = _resource_mode
            if mem > 92:
                _resource_mode = "SURVIVAL"
            elif mem > 85:
                _resource_mode = "DEGRADED"
            else:
                _resource_mode = "NORMAL"

            # In SURVIVAL mode, cap history to 10 entries to free RAM
            max_history = 10 if _resource_mode == "SURVIVAL" else 60
            state = {"timestamp": time.time(), "cpu": cpu, "ram": mem}
            system_history.append(state)
            if len(system_history) > max_history:
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

            # Update heartbeat with resource mode
            try:
                from core.state import update_heartbeat
                update_heartbeat(resource_mode=_resource_mode)
            except Exception:
                pass

            # Run trigger evaluation (skip in SURVIVAL to save CPU)
            if _resource_mode != "SURVIVAL":
                _evaluate_triggers(cpu, mem)
            elif prev_mode != "SURVIVAL":
                # Announce entry into SURVIVAL mode once
                trigger_queue.append({
                    "type": "ALERT",
                    "message": f"⚠ SURVIVAL MODE ACTIVATED: RAM at {mem:.1f}%. Non-essential cognitive operations suspended.",
                    "incident": True
                })

        except Exception:
            pass

        # Slow down sensor loop when under pressure
        sleep_time = 20 if _resource_mode == "DEGRADED" else (30 if _resource_mode == "SURVIVAL" else 10)
        time.sleep(sleep_time)

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
