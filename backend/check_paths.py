import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
IMG_DIR = os.path.join(FRONTEND_DIR, "img")

results = []
results.append(f"CD: {CURRENT_DIR}")
results.append(f"PR: {PROJECT_ROOT}")
results.append(f"ID: {IMG_DIR}")

filename = "icon_blade.png"
p1 = os.path.join(IMG_DIR, filename)
results.append(f"P1: {p1}")
results.append(f"E1: {os.path.exists(p1)}")

p2 = os.path.join(IMG_DIR, "texticon", filename)
results.append(f"P2: {p2}")
results.append(f"E2: {os.path.exists(p2)}")

for r in results:
    print(r)
