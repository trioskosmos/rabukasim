import os
import sys

import gymnasium as gym
import numpy as np
import torch

sys.path.append(os.getcwd())
from ai.loveca_features_extractor import LovecaFeaturesExtractor


def test_semantics():
    print("=== LovecaFeaturesExtractor Rigorous Semantic Test ===")

    # 1. Setup
    obs_space = gym.spaces.Box(low=-100, high=100, shape=(2240,), dtype=np.float32)
    extractor = LovecaFeaturesExtractor(obs_space, features_dim=256)
    extractor.eval()  # No dropout/norm updates

    def get_base_obs():
        obs = torch.zeros((1, 2240))
        # Set some base "presence" for cards to ensure attention isn't all-masked
        for i in range(16):  # Hand
            obs[0, i * 64] = 1.0
        for i in range(3):  # Stage
            obs[0, 1024 + i * 64] = 1.0
        # Phase = 4 (Main)
        obs[0, 2176 + 3] = 0.4
        return obs

    def check_diff(name, obs_a, obs_b, expected_diff=True):
        with torch.no_grad():
            feat_a = extractor(obs_a)
            feat_b = extractor(obs_b)

        diff = torch.norm(feat_a - feat_b).item()
        cos_sim = torch.nn.functional.cosine_similarity(feat_a, feat_b).item()

        status = "PASSED" if (diff > 1e-6 if expected_diff else diff < 1e-6) else "FAILED"
        print(f"[{status}] {name:30} | L2 Dist: {diff:.6f} | CosSim: {cos_sim:.6f}")

        if status == "FAILED":
            # Just for debugging info
            pass

    # --- TEST 1: Phase Sensitivity ---
    obs_main = get_base_obs()
    obs_mull = get_base_obs()
    obs_mull[0, 2176 + 3] = -0.1  # Phase -1
    check_diff("Phase Sensitivity (Main/Mull)", obs_main, obs_mull)

    # --- TEST 2: Heart Sensitivity (Specific slot) ---
    obs_no_heart = get_base_obs()
    obs_red_heart = get_base_obs()
    # Card 0 in Hand, Index 3 is Red Heart (based on your 64-dim plan)
    obs_red_heart[0, 3] = 1.0
    check_diff("Heart Sensitivity (Red Heart)", obs_no_heart, obs_red_heart)

    # --- TEST 3: Heart Color Differentiation ---
    obs_blue_heart = get_base_obs()
    obs_blue_heart[0, 7] = 1.0  # Index 7 is Blue Heart
    check_diff("Heart Differentiation (Red/Blue)", obs_red_heart, obs_blue_heart)

    # --- TEST 4: Trait Sensitivity ---
    obs_no_trait = get_base_obs()
    obs_trait = get_base_obs()
    obs_trait[0, 12] = 1.0  # Index 12 is a Trait bit
    check_diff("Trait Sensitivity", obs_no_trait, obs_trait)

    # --- TEST 5: Positional Sensitivity (Hand vs Stage) ---
    # Put same card in Hand Slot 0 vs Hand Slot 5
    obs_h1 = torch.zeros((1, 2240))
    obs_h2 = torch.zeros((1, 2240))
    # Card content
    card = torch.randn(64)
    card[0] = 1.0  # Present
    obs_h1[0, 0:64] = card
    obs_h2[0, 5 * 64 : 6 * 64] = card
    # Hand is order-invariant due to Mean Pooling, so they SHOULD be very similar/identical
    # unless attention adds positional info (which it doesn't in Hand block currently).
    check_diff("Hand Order Invariance", obs_h1, obs_h2, expected_diff=False)

    # --- TEST 6: Stage Slot Sensitivity ---
    obs_s1 = torch.zeros((1, 2240))
    obs_s2 = torch.zeros((1, 2240))
    # Put same card in Stage Slot 0 vs Slot 1
    obs_s1[0, 1024 : 1024 + 64] = card
    obs_s2[0, 1024 + 64 : 1024 + 128] = card
    # Should be DIFFERENT due to positional embeddings in stage
    check_diff("Stage Slot Sensitivity", obs_s1, obs_s2)

    # --- TEST 7: Global Scalar Sensitivity (Score) ---
    obs_s0 = get_base_obs()
    obs_s1 = get_base_obs()
    obs_s1[0, 2176 + 0] = 0.1  # Score 1
    check_diff("Score Sensitivity", obs_s0, obs_s1)

    # --- TEST 8: Mulligan Flag Sensitivity ---
    obs_m0 = get_base_obs()
    obs_m1 = get_base_obs()
    obs_m1[0, 2176 + 50] = 1.0  # Card 0 selected
    check_diff("Mulligan Flag Sensitivity", obs_m0, obs_m1)

    print("\nVerification Complete.")


if __name__ == "__main__":
    test_semantics()
