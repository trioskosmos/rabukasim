import engine_rust

print("engine_rust dir:", dir(engine_rust))
if hasattr(engine_rust, "PyVectorGameState"):
    print("PyVectorGameState methods:", dir(engine_rust.PyVectorGameState))
else:
    print("PyVectorGameState not found")
