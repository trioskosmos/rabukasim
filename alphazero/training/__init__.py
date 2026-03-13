def __getattr__(name):
    """Lazy import to avoid circular dependencies."""
    if name in ("OvernightConfig", "load_tournament_decks", "main"):
        from alphazero.training.overnight_vanilla import OvernightConfig, load_tournament_decks, main
        if name == "OvernightConfig":
            return OvernightConfig
        elif name == "load_tournament_decks":
            return load_tournament_decks
        elif name == "main":
            return main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["OvernightConfig", "load_tournament_decks", "main"]
