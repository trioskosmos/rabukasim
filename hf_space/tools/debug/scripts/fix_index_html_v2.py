file_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\frontend\web_ui\index.html"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find clearHighlights definition
clear_highlights_idx = -1
for i, line in enumerate(lines):
    if "function clearHighlights()" in line:
        clear_highlights_idx = i
        break

if clear_highlights_idx == -1:
    print("Could not find clearHighlights function")
    exit(1)

print(f"Found clearHighlights at line {clear_highlights_idx + 1}")

# Find duplicate actionsDiv.innerHTML = '' AFTER clearHighlights
start_delete_idx = -1
for i in range(clear_highlights_idx + 1, len(lines)):
    if "actionsDiv.innerHTML = '';" in line:  # This might be indented
        # let's look for the specific line
        pass
    if "actionsDiv.innerHTML = '';" in lines[i]:
        start_delete_idx = i
        break

if start_delete_idx == -1:
    print("Could not find duplicate actionsDiv.innerHTML")
    exit(1)

print(f"Found duplicate start at line {start_delete_idx + 1}")

# Find toggleFullLog
end_delete_idx = -1
for i in range(start_delete_idx, len(lines)):
    if "async function toggleFullLog" in lines[i]:
        end_delete_idx = i
        break

if end_delete_idx == -1:
    print("Could not find toggleFullLog")
    exit(1)

print(f"Found toggleFullLog at line {end_delete_idx + 1}")

# Adjust end_delete_idx to include the closing braces of the bad block if they are before toggleFullLog
# Actually, we likely want to keep toggleFullLog, so end_delete_idx is the start of the KEPT block.
# We should delete [start_delete_idx, end_delete_idx)

# Verify content to be deleted
print("Deleting lines:")
print(lines[start_delete_idx].strip())
print("...")
print(lines[end_delete_idx - 1].strip())

new_lines = lines[:start_delete_idx] + lines[end_delete_idx:]

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("File updated successfully.")
