import os
import sys
import traceback

sys.path.append(os.getcwd())

try:
    print("Importing VectorEnv...")
    print("Success")
except Exception:
    print("Import Failed!")
    traceback.print_exc()
