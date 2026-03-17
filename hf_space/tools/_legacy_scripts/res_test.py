import subprocess
from multiprocessing import cpu_count


class ResourceMonitor:
    @staticmethod
    def get_free_vram() -> int:
        try:
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"], encoding="utf-8"
            )
            return int(output.strip().split("\n")[0])
        except Exception:
            return 999999

    @staticmethod
    def get_free_ram() -> int:
        try:
            output = subprocess.check_output(["wmic", "OS", "get", "FreePhysicalMemory", "/Value"], encoding="utf-8")
            for line in output.splitlines():
                if "FreePhysicalMemory" in line:
                    val = int(line.split("=")[1].strip())
                    print(f"DEBUG: FreePhysicalMemory (KB): {val}")
                    return val // 1024
            return 4096
        except Exception as e:
            print(f"DEBUG: Error in RAM check: {e}")
            return 4096


ram_free = ResourceMonitor.get_free_ram()
vram_free = ResourceMonitor.get_free_vram()
print(f"DEBUG: ram_free (MB): {ram_free}")
print(f"DEBUG: vram_free (MB): {vram_free}")

ram_cost = 236
vram_cost = 84
system_cores = cpu_count()
print(f"DEBUG: system_cores: {system_cores}")

safe_ram = ram_free * 0.85
safe_vram = vram_free * 0.85
print(f"DEBUG: safe_ram: {safe_ram}")
print(f"DEBUG: safe_vram: {safe_vram}")

max_by_ram = int(safe_ram // ram_cost) if ram_cost > 0 else system_cores
max_by_vram = int(safe_vram // vram_cost) if vram_cost > 0 else system_cores
print(f"DEBUG: max_by_ram: {max_by_ram}")
print(f"DEBUG: max_by_vram: {max_by_vram}")

optimal = min(max_by_ram, max_by_vram, system_cores - 1)
print(f"DEBUG: Final Calculated Optimal Workers: {max(1, optimal)}")
