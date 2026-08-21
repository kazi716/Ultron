import psutil
import time
import threading

system_history = []

def _sensor_loop():
    while True:
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory().percent
            
            state = {
                "timestamp": time.time(),
                "cpu": cpu,
                "ram": mem
            }
            
            system_history.append(state)
            
            if len(system_history) > 60:
                system_history.pop(0)
                
        except Exception:
            pass
            
        time.sleep(10)

def start_sensors():
    t = threading.Thread(target=_sensor_loop, daemon=True)
    t.start()

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
        
    return trend_str
