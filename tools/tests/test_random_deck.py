import time

import requests

URL = "http://localhost:8000/api/reset"


def reset_with_seed(seed):
    print(f"Resetting with seed: {seed}")
    res = requests.post(URL, json={"seed": seed, "deck_type": "normal"})
    if res.status_code != 200:
        print(f"Error: {res.text}")
        return None

    # Get State to see deck content (first 5 cards in hand)
    state = requests.get("http://localhost:8000/api/state").json()
    hand = state["players"][0]["hand"]
    print(f"Hand: {hand}")
    return hand


print("Testing Determinism...")
h1 = reset_with_seed(12345)
time.sleep(1)
h2 = reset_with_seed(12345)

if h1 == h2:
    print("SUCCESS: Seed 12345 produced identical hands.")
else:
    print("FAIL: Seed 12345 produced DIFFERENT hands.")

print("\nTesting Randomness...")
h3 = reset_with_seed(67890)

if h1 != h3:
    print("SUCCESS: Seed 67890 produced different hand.")
else:
    print("FAIL: Seed 67890 produced SAME hand as 12345 (Unlikely).")
