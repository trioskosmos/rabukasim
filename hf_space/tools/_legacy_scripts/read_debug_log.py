def read_log():
    encodings = ["utf-16", "utf-8", "cp932", "ascii"]
    content = None
    for enc in encodings:
        try:
            file_path = "debug_runner_output.txt"
            with open(file_path, "r", encoding=enc) as f:
                content = f.read()
            print(f"Successfully read with {enc}")
            break
        except Exception:
            continue

    if content:
        print(content)


if __name__ == "__main__":
    read_log()
