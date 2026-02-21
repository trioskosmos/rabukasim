import os

cmd = "uv run pytest engine/tests/cards/batches/test_verification_batch_12.py::TestVerificationBatch12::test_pl_sd1_016_sd_look3_pick1 -s > debug_runner_output.txt 2>&1"

os.system(cmd)
print("Finished execution")
