from engine.tests.test_logging import test_logging_ability_resolution

try:
    print("Running test...")
    test_logging_ability_resolution()
    print("Test Passed!")
except AssertionError as e:
    print(f"Test Failed: {e}")
except Exception:
    import traceback

    traceback.print_exc()
