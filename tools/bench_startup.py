
import subprocess
import time
import os
import psutil

def run_bench(name, cmd_list):
    print(f"--- Benchmarking {name} ---")
    start_time = time.time()
    
    # Start process
    p = subprocess.Popen(cmd_list, shell=True)
    
    max_rss = 0
    max_cpu = 0
    
    try:
        ps_p = psutil.Process(p.pid)
        while p.poll() is None:
            try:
                # Get stats for process and children
                procs = [ps_p] + ps_p.children(recursive=True)
                rss = sum(proc.memory_info().rss for proc in procs)
                cpu = sum(proc.cpu_percent(interval=0.1) for proc in procs)
                
                if rss > max_rss: max_rss = rss
                if cpu > max_cpu: max_cpu = cpu
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            time.sleep(0.5)
    except Exception as e:
        print(f"Error monitoring {name}: {e}")
        p.wait()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Duration: {duration:.2f}s")
    print(f"Max RAM: {max_rss / 1024 / 1024:.2f} MB")
    print(f"Max CPU (approx): {max_cpu:.1f}%")
    print("-" * 30)
    return {
        "name": name,
        "duration": duration,
        "max_rss_mb": max_rss / 1024 / 1024,
        "max_cpu": max_cpu
    }

results = []
results.append(run_bench("Compiler", ["uv", "run", "python", "-m", "compiler.main"]))
results.append(run_bench("Asset Sync", ["uv", "run", "python", "tools/sync_launcher_assets.py"]))
results.append(run_bench("Translation Analysis", ["uv", "run", "python", "tools/analysis/analyze_translation_coverage.py"]))

with open("reports/bench_results.txt", "w") as f:
    for r in results:
        f.write(f"{r['name']}: {r['duration']:.2f}s, {r['max_rss_mb']:.2f} MB RAM\n")
