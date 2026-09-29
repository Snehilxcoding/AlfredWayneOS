import datetime
import socket
try:
    import psutil
except ImportError:
    psutil = None

from config.settings import (
    INTERNET_CHECK_HOST, INTERNET_CHECK_PORT, INTERNET_CHECK_TIMEOUT,
    HIGH_CPU_THRESHOLD, HIGH_RAM_THRESHOLD
)

def get_time_context():
    now  = datetime.datetime.now()
    hour = now.hour
    if   5  <= hour < 12: period = "morning"
    elif 12 <= hour < 17: period = "afternoon"
    elif 17 <= hour < 21: period = "evening"
    else:                 period = "night"
    return {
        "time":         now.strftime("%I:%M %p"),
        "day":          now.strftime("%A"),
        "date":         now.strftime("%B %d, %Y"),
        "year":         now.year,
        "hour":         hour,
        "period":       period,
        "working_late": hour >= 23 or hour < 4,
        "is_weekend":   now.weekday() >= 5,
    }

def get_battery_context():
    try:
        b = psutil.sensors_battery()
        if b is None:
            return {"available": False}
        return {
            "available": True,
            "percent":   round(b.percent),
            "plugged":   b.power_plugged,
            "low":       b.percent < 20 and not b.power_plugged,
        }
    except Exception:
        return {"available": False}

def get_system_context():
    if psutil is None:
        return {
            "cpu_percent": 5,
            "ram_percent": 25,
            "ram_used_gb": 2.0,
            "ram_total_gb": 8.0,
            "cpu_high": False,
            "ram_high": False,
        }
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    return {
        "cpu_percent":  round(cpu),
        "ram_percent":  round(ram.percent),
        "ram_used_gb":  round(ram.used  / (1024**3), 1),
        "ram_total_gb": round(ram.total / (1024**3), 1),
        "cpu_high":     cpu > HIGH_CPU_THRESHOLD,
        "ram_high":     ram.percent > HIGH_RAM_THRESHOLD,
    }

def check_internet():
    try:
        socket.setdefaulttimeout(INTERNET_CHECK_TIMEOUT)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(
            (INTERNET_CHECK_HOST, INTERNET_CHECK_PORT)
        )
        return True
    except OSError:
        return False

def get_full_context():
    tc = get_time_context()
    bc = get_battery_context()
    sc = get_system_context()
    return {**tc, "battery": bc, "system": sc, "online": check_internet()}

def build_context_summary(ctx):
    lines = [
        f"Time: {ctx['time']} on {ctx['day']}, {ctx['date']}",
        f"Internet: {'online' if ctx['online'] else 'OFFLINE'}",
        f"CPU: {ctx['system']['cpu_percent']}% | RAM: {ctx['system']['ram_percent']}%",
    ]
    if ctx['battery']['available']:
        b = ctx['battery']
        lines.append(f"Battery: {b['percent']}% ({'charging' if b['plugged'] else 'on battery'})")
    return "\n".join(lines)
