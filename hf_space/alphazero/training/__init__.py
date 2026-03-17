def __getattr__(name):
    """Lazy import to avoid circular dependencies."""
    if name in (
        "OvernightConfig",
        "SelfPlayConfig",
        "VanillaPolicyModel",
        "load_tournament_decks",
        "load_vanilla_database_json",
        "main",
    ):
        from alphazero.training.overnight_vanilla import (
            OvernightConfig,
            SelfPlayConfig,
            VanillaPolicyModel,
            load_tournament_decks,
            load_vanilla_database_json,
            main,
        )
        if name == "OvernightConfig":
            return OvernightConfig
        elif name == "SelfPlayConfig":
            return SelfPlayConfig
        elif name == "VanillaPolicyModel":
            return VanillaPolicyModel
        elif name == "load_tournament_decks":
            return load_tournament_decks
        elif name == "load_vanilla_database_json":
            return load_vanilla_database_json
        elif name == "main":
            return main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "OvernightConfig",
    "SelfPlayConfig",
    "VanillaPolicyModel",
    "load_tournament_decks",
    "load_vanilla_database_json",
    "main",
]
