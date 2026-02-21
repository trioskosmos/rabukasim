
import json
import re
import os

def fix_pseudocode(text):
    if "CONDITION: TURN_1" not in text:
        return text
    
    lines = text.split("\n")
    new_lines = []
    found_turn1 = False
    
    for line in lines:
        if "CONDITION: TURN_1" in line:
            found_turn1 = True
            # Handle list of conditions: "CONDITION: TURN_1, OTHER_COND"
            line = line.replace("CONDITION: TURN_1, ", "CONDITION: ")
            line = line.replace("CONDITION: TURN_1", "")
            if line.strip() == "CONDITION:":
                continue # Remove empty condition line
        
        new_lines.append(line)
    
    if found_turn1:
        # Add (Once per turn) to the TRIGGER line if not already there
        for i in range(len(new_lines)):
            if new_lines[i].startswith("TRIGGER:") and "(Once per turn)" not in new_lines[i]:
                new_lines[i] = new_lines[i] + " (Once per turn)"
                break
        
        return "\n".join(new_lines)
    
    return text

def main():
    path = "data/manual_pseudocode.json"
    if not os.path.exists(path):
        print(f"File {path} not found.")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for key, value in data.items():
        if "pseudocode" in value:
            original = value["pseudocode"]
            fixed = fix_pseudocode(original)
            if original != fixed:
                value["pseudocode"] = fixed
                count += 1

    if count > 0:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Fixed {count} card abilities in {path}.")
    else:
        print("No changes needed.")

if __name__ == "__main__":
    main()
