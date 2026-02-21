import os
import re


def clean_file(filename):
    try:
        if not os.path.exists(filename):
            return f"File {filename} not found."

        # Try reading as utf-8 first, then utf-16
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeError:
            with open(filename, "r", encoding="utf-16") as f:
                content = f.read()
        except Exception:
            with open(filename, "rb") as f:
                content = f.read().decode("utf-8", "replace")

        # Strip ANSI codes
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        content = ansi_escape.sub("", content)
        return content
    except Exception as e:
        return f"Error reading {filename}: {e}"


content = clean_file("error_log.txt")
with open("debug_output.txt", "w", encoding="utf-8") as f:
    f.write(content)
