INPUT_SIZE = 1200
HIDDEN_SIZE = 256  # d_model for Transformer
NUM_LAYERS = 4  # Transformer Encoder Layers
N_HEADS = 8  # Attention Heads
DROPOUT = 0.1
OUTPUT_SIZE = 1  # Value Head (Score)
WIN_SIZE = 1  # Value Head (Win Prob)
POLICY_SIZE = 2000  # Action Head


def get_feature_size():
    return INPUT_SIZE
