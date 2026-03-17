import ast
import traceback

try:
    with open("compiler/parser.py", encoding="utf-8") as f:
        ast.parse(f.read())
    print("Syntax OK")
except SyntaxError as e:
    print(f"Syntax Error: {e.lineno}:{e.offset} {e.msg}")
    print(e.text)
except Exception:
    traceback.print_exc()
