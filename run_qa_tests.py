import sys
import os

with open("engine_rust_src/src/qa_verification_tests.rs") as f:
    code = f.read()

print("Q102 test exists:", "q102" in code.lower())
print("Q73 test exists:", "q73" in code.lower())
