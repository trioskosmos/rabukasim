try:
    with open("engine_rust/build_error.log", "r", encoding="utf-16-le") as f:
        print(f.read())
except Exception as e:
    print(e)
