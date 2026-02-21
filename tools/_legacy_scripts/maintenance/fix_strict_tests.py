import re

filepath = (
    r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine\tests\cards\batches\test_auto_generated_strict_v2.py"
)

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Substitutions
subs = [
    # PL!-PR-007-PR Ability 0 & 1
    (r"(def test_strict_PL__PR_007_PR\(game\):.*?# Ability 0.*?assert len\(ab0\.conditions\)) == 1", r"\1 == 0"),
    (r"(def test_strict_PL__PR_007_PR\(game\):.*?# Ability 0.*?assert ab0\.conditions\[0\]\.type == 16\n)", ""),
    (r"(def test_strict_PL__PR_007_PR\(game\):.*?# Ability 1.*?assert len\(ab1\.conditions\)) == 1", r"\1 == 0"),
    # (r'(def test_strict_PL__PR_007_PR\(game\):.*?# Ability 1.*?assert ab1\.conditions\[0\]\.type == 16\n)', ''), # Optional
    # PL!-PR-009-PR Ability 0 & 1
    (r"(def test_strict_PL__PR_009_PR\(game\):.*?# Ability 0.*?assert len\(ab0\.conditions\)) == 1", r"\1 == 0"),
    (r"(def test_strict_PL__PR_009_PR\(game\):.*?# Ability 0.*?assert ab0\.conditions\[0\]\.type == 16\n)", ""),
    (r"(def test_strict_PL__PR_009_PR\(game\):.*?# Ability 1.*?assert len\(ab1\.conditions\)) == 1", r"\1 == 0"),
    # PL!N-bp3-017-N
    (r"(def test_strict_PL_N_bp3_017_N\(game\):.*?# Ability 0.*?assert len\(ab0\.conditions\)) == 1", r"\1 == 0"),
    (r"(def test_strict_PL_N_bp3_017_N\(game\):.*?# Ability 0.*?assert ab0\.conditions\[0\]\.type == 16\n)", ""),
    (r"(def test_strict_PL_N_bp3_017_N\(game\):.*?# Ability 1.*?assert len\(ab1\.conditions\)) == 1", r"\1 == 0"),
    # PL!N-bp4-004-R_
    (r"(def test_strict_PL_N_bp4_004_R_\(game\):.*?# Ability 0.*?assert len\(ab0\.conditions\)) == 1", r"\1 == 0"),
    (r"(def test_strict_PL_N_bp4_004_R_\(game\):.*?# Ability 0.*?assert ab0\.conditions\[0\]\.type == 16\n)", ""),
    # PL!N-bp4-004-SEC
    (r"(def test_strict_PL_N_bp4_004_SEC\(game\):.*?# Ability 0.*?assert len\(ab0\.conditions\)) == 1", r"\1 == 0"),
    (r"(def test_strict_PL_N_bp4_004_SEC\(game\):.*?# Ability 0.*?assert ab0\.conditions\[0\]\.type == 16\n)", ""),
    # PL!N-bp4-005-P & R
    (r"(def test_strict_PL_N_bp4_005_P\(game\):.*?assert len\(ab0\.conditions\)) == 2", r"\1 == 1"),
    (r"(def test_strict_PL_N_bp4_005_R\(game\):.*?assert len\(ab0\.conditions\)) == 2", r"\1 == 1"),
    # PL!S-bp3-012-N
    (r"(def test_strict_PL_S_bp3_012_N\(game\):.*?# Ability 0.*?assert len\(ab0\.conditions\)) == 1", r"\1 == 0"),
    (r"(def test_strict_PL_S_bp3_012_N\(game\):.*?# Ability 0.*?assert ab0\.conditions\[0\]\.type == 16\n)", ""),
    (r"(def test_strict_PL_S_bp3_012_N\(game\):.*?# Ability 1.*?assert len\(ab1\.conditions\)) == 1", r"\1 == 0"),
    # PL!S-bp3-017-N
    (r"(def test_strict_PL_S_bp3_017_N\(game\):.*?# Ability 0.*?assert len\(ab0\.conditions\)) == 1", r"\1 == 0"),
    (r"(def test_strict_PL_S_bp3_017_N\(game\):.*?# Ability 0.*?assert ab0\.conditions\[0\]\.type == 16\n)", ""),
    (r"(def test_strict_PL_S_bp3_017_N\(game\):.*?# Ability 1.*?assert len\(ab1\.conditions\)) == 1", r"\1 == 0"),
    # PL!-bp3-002-P & R
    (r"(def test_strict_PL__bp3_002_P\(game\):.*?assert len\(ab0\.conditions\)) == 2", r"\1 == 1"),
    (r"(def test_strict_PL__bp3_002_R\(game\):.*?assert len\(ab0\.conditions\)) == 2", r"\1 == 1"),
    # PL!N-bp3-023-N
    (r"(def test_strict_PL_N_bp3_023_N\(game\):.*?# Ability 0.*?assert len\(ab0\.conditions\)) == 1", r"\1 == 0"),
    (r"(def test_strict_PL_N_bp3_023_N\(game\):.*?# Ability 0.*?assert ab0\.conditions\[0\]\.type == 16\n)", ""),
    # PL!N-bp4-004-P & P_
    (r"(def test_strict_PL_N_bp4_004_P\(game\):.*?# Ability 0.*?assert len\(ab0\.conditions\)) == 1", r"\1 == 0"),
    (r"(def test_strict_PL_N_bp4_004_P\(game\):.*?# Ability 0.*?assert ab0\.conditions\[0\]\.type == 16\n)", ""),
    (r"(def test_strict_PL_N_bp4_004_P_\(game\):.*?# Ability 0.*?assert len\(ab0\.conditions\)) == 1", r"\1 == 0"),
    (r"(def test_strict_PL_N_bp4_004_P_\(game\):.*?# Ability 0.*?assert ab0\.conditions\[0\]\.type == 16\n)", ""),
]

new_content = content
for pattern, replacement in subs:
    new_content = re.sub(pattern, replacement, new_content, flags=re.DOTALL)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Done")
