import os
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.append(str(Path(__file__).parent / "alphazero" / "training"))
from disk_buffer import PersistentBuffer


def test_buffer():
    test_dir = "test_buffer_data"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    obs_dim = 100
    num_actions = 1000
    max_size = 1000

    buf = PersistentBuffer(test_dir, max_size, obs_dim, num_actions)

    # 1. Add some data
    obs_in = np.random.randn(obs_dim).astype(np.float32)
    p_idx_in = np.array([1, 5, 10], dtype=np.uint16)
    p_val_in = np.array([0.5, 0.3, 0.2], dtype=np.float16)
    targets_in = np.array([1.0, 0.5, 0.2], dtype=np.float32)
    mask_in = np.array([1, 5, 10, 20], dtype=np.uint32)

    buf.add(obs_in, (p_idx_in, p_val_in), targets_in, mask_in)

    print(f"Added 1 sample. Buffer count: {buf.count}")

    # 2. Sample data
    batch = buf.sample(1)
    obs_out, p_out, mask_out, val_out = batch

    # Verify values
    # Obs might have slight precision loss from f16 conversion
    np.testing.assert_allclose(obs_in, obs_out[0], atol=1e-2)
    np.testing.assert_array_equal(p_idx_in, p_out[0][0])
    np.testing.assert_allclose(p_val_in, p_out[0][1], atol=1e-3)
    np.testing.assert_array_equal(targets_in, val_out[0])
    np.testing.assert_array_equal(mask_in, mask_out[0])

    print("Verification passed!")

    # 3. Test persistence
    buf.flush()
    buf2 = PersistentBuffer(test_dir, max_size, obs_dim, num_actions)
    print(f"Reloaded buffer count: {buf2.count}")
    assert buf2.count == 1

    # Clean up
    shutil.rmtree(test_dir)
    print("Cleanup complete.")


if __name__ == "__main__":
    test_buffer()
