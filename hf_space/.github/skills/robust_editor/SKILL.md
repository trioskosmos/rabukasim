# Robust Editor Skill

> [!IMPORTANT]
> Use this skill whenever `replace_file_content` or `multi_replace_file_content` fails with "target content not found", especially in files with complex indentation or Windows line endings.

## 1. Purpose
The `replace_file_content` tool requires a character-perfect match. Invisible differences in spaces, tabs, or line endings can cause failures that are hard to debug by sight alone.

## 2. The Robust Workflow

### Phase 1: Extraction
Use the `robust_edit_helper.py` script to get the **exact** string from the file.

```powershell
uv run python tools/robust_edit_helper.py <ABS_PATH_TO_FILE> <START_LINE> <END_LINE>
```

### Phase 3: Replacement
Use the extracted text as the `TargetContent` in your edit tool.

## 3. Tooling
- **Script**: [robust_edit_helper.py](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tools/robust_edit_helper.py)
- **Utility**: Detects LF vs CRLF and counts exact space/tab occurrences.
