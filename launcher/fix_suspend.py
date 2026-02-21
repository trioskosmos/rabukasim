import re

path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src\core\logic\interpreter.rs"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Pattern for suspend_interaction(state, ctx, ip, op, type, text, filter, v)
# We want to change the 7th argument (filter) to "filter as u64"
# The pattern should handle multi-line calls as well.

def fix_suspend(match):
    full_call = match.group(0)
    args_str = match.group(1)
    
    # Split by comma but handle nested parens if any (unlikely here but safe)
    # Actually, let's just use a simpler split if args are simple.
    args = []
    current_arg = ""
    paren_depth = 0
    for char in args_str:
        if char == ',' and paren_depth == 0:
            args.append(current_arg.strip())
            current_arg = ""
        else:
            if char == '(': paren_depth += 1
            if char == ')': paren_depth -= 1
            current_arg += char
    args.append(current_arg.strip())
    
    if len(args) >= 7:
        filter_arg = args[6]
        if " as u64" not in filter_arg and filter_arg != "0":
             args[6] = f"{filter_arg} as u64"
    
    return f"suspend_interaction({', '.join(args)})"

# Using a regex that captures the arguments list
new_content = re.sub(r"suspend_interaction\((.*?)\)", fix_suspend, content, flags=re.DOTALL)

with open(path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Done")
