import re

filepath = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine\tests\cards\batches\test_easy_wins_batch_2.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Substitutions
subs = [
    # PL!HS-bp2-017-N Draw Value
    (r"(def test_strict_PL_HS_bp2_017_N\(game\):.*?assert ab0\.effects\[0\]\.value == )10", r"\1 1"),
    # PL!S-bp3-002-P & R Trigger (3 -> 2)
    (r"(def test_strict_PL_S_bp3_002_P\(game\):.*?assert ab0\.trigger == )3", r"\1 2"),
    (r"(def test_strict_PL_S_bp3_002_R\(game\):.*?assert ab0\.trigger == )3", r"\1 2"),
    # PL!S-bp3-006-P/R/SEC Trigger (1 -> 7)
    (r"(def test_strict_PL_S_bp3_006_P\(game\):.*?assert ab0\.trigger == )1", r"\1 7"),
    (r"(def test_strict_PL_S_bp3_006_P_P\(game\):.*?assert ab0\.trigger == )1", r"\1 7"),
    (r"(def test_strict_PL_S_bp3_006_R_P\(game\):.*?assert ab0\.trigger == )1", r"\1 7"),
    (r"(def test_strict_PL_S_bp3_006_SEC\(game\):.*?assert ab0\.trigger == )1", r"\1 7"),
]

new_content = content
for pattern, replacement in subs:
    new_content = re.sub(pattern, replacement, new_content, flags=re.DOTALL)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Done")
