import json
import os
import zipfile


def inspect_model(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    with zipfile.ZipFile(path, "r") as z:
        # SB3 models store their metadata in the 'data' file
        with z.open("data") as f:
            data = json.loads(f.read().decode("utf-8"))
            obs_shape = data.get("observation_space", {}).get("_shape", "Unknown")
            act_n = data.get("action_space", {}).get("n", "Unknown")
            print(f"--- {os.path.basename(path)} ---")
            print(f"  Observation Shape: {obs_shape}")
            print(f"  Action Space (n):  {act_n}")
            print(f"  Num Timesteps:     {data.get('num_timesteps', 'N/A')}")


if __name__ == "__main__":
    inspect_model("checkpoints/historiccheckpoints/firstspeedup_347537408.zip")
    inspect_model("checkpoints/historiccheckpoints/limitedcardsbutbetterthansmart_2320000.zip")
