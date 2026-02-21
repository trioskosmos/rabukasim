
import subprocess
import time
import os
import psutil
import requests
import signal
import sys

def get_process_stats(proc):
    try:
        if not proc.is_running():
            return None
        procs = [proc] + proc.children(recursive=True)
        rss = sum(p.memory_info().rss for p in procs)
        cpu = sum(p.cpu_percent(interval=0.1) for p in procs)
        return {"rss": rss / 1024 / 1024, "cpu": cpu}
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None

def main():
    print("Starting Loveca Launcher Performance Monitor...")
    
    # Start the server
    # We use cargo run --release --bin loveca_launcher
    # Cwd should be launcher directory
    launcher_cwd = os.path.join(os.getcwd(), "launcher")
    server_process = subprocess.Popen(
        ["cargo", "run", "--release", "--bin", "loveca_launcher"],
        cwd=launcher_cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8"
    )

    print("Waiting for server to bind...")
    server_started = False
    for _ in range(30):
        try:
            resp = requests.get("http://127.0.0.1:8000/api/version", timeout=1)
            if resp.status_code == 200:
                server_started = True
                break
        except:
            time.sleep(1)
    
    if not server_started:
        print("Server failed to start within 30s.")
        server_process.kill()
        return

    print("Server joined! Monitoring for 60 seconds...")
    
    # Find the actual binary process (cargo run spawns it)
    main_proc = psutil.Process(server_process.pid)
    launcher_proc = None
    for child in main_proc.children(recursive=True):
        if "loveca_launcher" in child.name().lower():
            launcher_proc = child
            break
    
    if not launcher_proc:
        launcher_proc = main_proc

    stats = []
    
    # Idle Monitoring (30s)
    print("Capturing Idle stats (30s)...")
    for i in range(30):
        s = get_process_stats(launcher_proc)
        if s:
            stats.append(("idle", s))
        time.sleep(1)

    # Active Monitoring (Simulated Load)
    print("Capturing Active (Simulated Load) stats (30s)...")
    def simulate_load():
        try:
            # Simulate a few rapid requests
            requests.get("http://127.0.0.1:8000/index.html")
            requests.get("http://127.0.0.1:8000/api/cards")
            # Create a room and join
            room_resp = requests.post("http://127.0.0.1:8000/api/rooms/create", json={"name": "perf_test"})
        except:
            pass

    for i in range(30):
        simulate_load()
        s = get_process_stats(launcher_proc)
        if s:
            stats.append(("active", s))
        time.sleep(1)

    # Shutdown
    print("Shutting down...")
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except:
        server_process.kill()

    # Report
    idle_rss = [s["rss"] for label, s in stats if label == "idle"]
    active_rss = [s["rss"] for label, s in stats if label == "active"]
    idle_cpu = [s["cpu"] for label, s in stats if label == "idle"]
    active_cpu = [s["cpu"] for label, s in stats if label == "active"]

    report = f"""
# Runtime Performance Report
Generated: {time.ctime()}

## Rust Launcher (loveca_launcher)

| Metric | Idle (Avg) | Active (Avg) | Peak |
| :--- | :--- | :--- | :--- |
| **RAM (MB)** | {sum(idle_rss)/len(idle_rss):.2f} | {sum(active_rss)/len(active_rss):.2f} | {max(idle_rss + active_rss):.2f} |
| **CPU (%)** | {sum(idle_cpu)/len(idle_cpu):.2f} | {sum(active_cpu)/len(active_cpu):.2f} | {max(idle_cpu + active_cpu):.2f} |

Note: Active simulated load consisted of rapid API requests (room creation, card DB fetch).
"""
    print(report)
    with open("reports/runtime_performance.md", "w") as f:
        f.write(report)

if __name__ == "__main__":
    main()
