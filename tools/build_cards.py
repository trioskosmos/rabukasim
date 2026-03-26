import os
import sys
import time
import datetime
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

try:
    from compiler import main as compiler_main
    from tools import sync_ability_frame_index, codegen_abilities
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def print_status(message, is_done=False):
    """Prints an updating status line."""
    if is_done:
        print(f"\r[build] {message:<60}")
    else:
        sys.stdout.write(f"\r[build] {message}...")
        sys.stdout.flush()

def main():
    force = "--force" in sys.argv
    quiet = "--quiet" in sys.argv
    
    input_path = "data/cards.json"
    output_path = "data/cards_compiled.json"
    
    # 1. Parity Check
    if not force:
        print_status("Checking card data parity")
        if compiler_main.check_parity(input_path, output_path):
            print_status("Card data is up to date.", is_done=True)
            return
    
    # 2. Rebuild
    start_time = time.time()
    
    # Step A: Compile Cards
    print_status("Compiling frame data (1/3)")
    compiler_main.compile_cards(input_path, output_path, quiet=True, export_profile="runtime")
    
    # Update hash in the output file (mirrors original main behavior)
    compiled_data = compiler_main.load_json(output_path)
    if compiled_data:
        if "meta" not in compiled_data:
            compiled_data["meta"] = {}
        compiled_data["meta"]["source_hash"] = compiler_main.calculate_hash(input_path)
        compiled_data["meta"]["ability_source_hash"] = compiler_main.calculate_hash(compiler_main.SPARSE_INDEX_PATH)
        compiled_data["meta"]["generated_by"] = "tools/build_cards.py"
        compiled_data["meta"]["generated_at"] = datetime.datetime.now().isoformat()
        import json
        with open(output_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(compiled_data, f, ensure_ascii=False, indent=2)

    # Sync to engine/data/
    import shutil
    engine_data_path = ROOT_DIR / "engine" / "data" / "cards_compiled.json"
    os.makedirs(engine_data_path.parent, exist_ok=True)
    shutil.copy(output_path, engine_data_path)
    
    # Step B: Sync Ability Frame Index
    print_status("Syncing ability frame index (2/3)")
    # We call the logic from sync_ability_frame_index directly
    from tools import frame_codec
    payload = frame_codec.load_json(sync_ability_frame_index.DEFAULT_INPUT_PATH)
    metadata = frame_codec.load_json(sync_ability_frame_index.DEFAULT_METADATA_PATH)
    runtime_payload = frame_codec.build_runtime_ability_index(payload, metadata)
    frame_codec.dump_json(sync_ability_frame_index.DEFAULT_OUTPUT_PATH, runtime_payload)
    
    # Step C: Codegen
    print_status("Generating Rust optimizations (3/3)")
    codegen_abilities.generate_rust()
    
    end_time = time.time()
    print_status(f"Build complete in {end_time - start_time:.2f}s.", is_done=True)

if __name__ == "__main__":
    main()
