import json

report_path = "reports/report_20260112_042512.json"
try:
    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Data Type: {type(data)}")
    steps = []  # Default
    if isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")
        steps = data.get("steps", [])
        print(f"Steps count: {len(steps)}")
    elif isinstance(data, list):
        print(f"List length: {len(data)}")
        if len(data) > 0:
            print(f"First item keys: {data[0].keys()}")

    # steps = data.get("steps", []) # Old logic

    if steps:
        last_step = steps[-1]
        print("Last Step Details:")
        print(f"  Phase: {last_step.get('phase')}")
        print(f"  Action: {last_step.get('action')}")
        print(f"  Legal Actions: {last_step.get('legal_actions')}")

    # Check for logs
    logs = data.get("logs", [])
    if logs:
        print("Last 5 Logs:")
        for log in logs[-5:]:
            print(f"  {log}")

except Exception as e:
    print(f"Error: {e}")
