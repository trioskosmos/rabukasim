import subprocess
import sys

# Run the test and save full output
result = subprocess.run(
    ["cargo", "test", "test_card_47_live_start_third_mode_grants_heart06_only_to_selected_self_member", "--", "--nocapture"],
    cwd="engine_rust_src",
    capture_output=True,
    text=True
)

# Save to file
with open("test_output_full.txt", "w", encoding="utf-8") as f:
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\n\nSTDERR:\n")
    f.write(result.stderr)

print(f"Test output saved to test_output_full.txt")
print(f"Exit code: {result.returncode}")
