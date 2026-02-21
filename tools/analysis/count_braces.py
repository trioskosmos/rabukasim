def count_braces(filename):
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
        opens = content.count("{")
        closes = content.count("}")
        print(f"{filename}: {opens} opens, {closes} closes (diff: {opens - closes})")


count_braces("engine_rust/src/core/logic.rs")
count_braces("engine_rust/src/py_bindings.rs")
