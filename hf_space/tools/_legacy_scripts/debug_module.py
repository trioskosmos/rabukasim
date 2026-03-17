import engine_rust


def debug_module(mod, indent=0):
    print("  " * indent + f"Module/Object: {mod}")
    print("  " * indent + f"File: {getattr(mod, '__file__', 'N/A')}")
    print("  " * indent + f"Path: {getattr(mod, '__path__', 'N/A')}")
    print("  " * indent + f"Dir: {dir(mod)}")

    # Check for HeuristicConfig at this level
    if hasattr(mod, "HeuristicConfig"):
        print("  " * indent + f"!!! FOUND HeuristicConfig in {mod}")
        print("  " * indent + f"Type: {type(mod.HeuristicConfig)}")

    # If it has a member with the same name as the module, explore it
    mod_name = mod.__name__.split(".")[-1]
    if hasattr(mod, mod_name) and indent < 2:
        child = getattr(mod, mod_name)
        if child is not mod:
            debug_module(child, indent + 1)


print("--- DEBUG START ---")
debug_module(engine_rust)
print("--- DEBUG END ---")
