import subprocess

# Run the test
result = subprocess.run(
    ["cargo", "test", "test_card_47_live_start_third_mode_grants_heart06_only_to_selected_self_member", "--", "--nocapture"],
    cwd="engine_rust_src",
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="ignore"
)

# Search for SELECT_MEMBER frames in output
output = result.stdout + result.stderr
lines = output.split("\n")

for i, line in enumerate(lines):
    if "opcode=65" in line or "SELECT_MEMBER" in line:
        # Print context around the line
        start = max(0, i - 2)
        end = min(len(lines), i + 3)
        print("Context around SELECT_MEMBER frame:")
        for j in range(start, end):
            print(f"  {j}: {lines[j]}")
        print()

# Also search for filter_attr in SELECT_MEMBER context
for i, line in enumerate(lines):
    if "SELECT_MEMBER" in line or ("opcode=65" in line):
        # Look for filter_attr in nearby lines
        start = max(0, i - 5)
        end = min(len(lines), i + 5)
        for j in range(start, end):
            if "filter_attr=" in lines[j]:
                print(f"Found filter_attr near SELECT_MEMBER at line {j}:")
                print(f"  {lines[j]}")
