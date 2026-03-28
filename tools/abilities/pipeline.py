from __future__ import annotations

"""Keep compiled card metadata readable while preserving the instruction list."""

import hashlib
import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = os.path.abspath(str(ROOT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from engine.compiler import main as compiler_main
from tools import codegen_abilities, frame_codec, sync_launcher_assets

CARDS_INPUT_PATH = ROOT_DIR / "data" / "cards.json"
CARDS_OUTPUT_PATH = ROOT_DIR / "data" / "cards_compiled.json"
ENGINE_CARDS_OUTPUT_PATH = ROOT_DIR / "engine" / "data" / "cards_compiled.json"
FRAME_INDEX_INPUT_PATH = ROOT_DIR / "data" / "ability_frame_index.json"
FRAME_INDEX_METADATA_PATH = ROOT_DIR / "data" / "metadata.json"
FRAME_INDEX_OUTPUT_PATH = ROOT_DIR / "data" / "ability_frame_index.json"
FRAME_INDEX_CARDS_PATH = ROOT_DIR / "data" / "cards_compiled.json"
FRAME_INDEX_HASH_PATH = ROOT_DIR / "data" / ".ability_frame_sync_hash"
SOURCE_HASH_FILES = [
    ROOT_DIR / "engine" / "compiler" / "main.py",
    ROOT_DIR / "tools" / "frame_codec.py",
    ROOT_DIR / "tools" / "build_cards.py",
    ROOT_DIR / "tools" / "abilities" / "pipeline.py",
]


@dataclass(slots=True)
class PrepareResult:
    cards_changed: bool = False
    frame_index_changed: bool = False
    rust_codegen_changed: bool = False
    launcher_assets_changed: bool = False


def _log(message: str, quiet: bool) -> None:
    if not quiet:
        print(f"[build] {message}")


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _calculate_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _calculate_combined_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update((path.as_posix() + "=").encode("utf-8"))
        digest.update((_calculate_hash(path) or "").encode("utf-8"))
    return digest.hexdigest()


def _dump_json_if_changed(path: Path, payload: dict, quiet: bool) -> bool:
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    if path.exists():
        with open(path, "r", encoding="utf-8") as handle:
            if handle.read() == serialized:
                return False
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(serialized)
    _log(f"Wrote {path.relative_to(ROOT_DIR)}", quiet)
    return True


def _write_text_if_changed(path: Path, content: str) -> bool:
    if path.exists():
        with open(path, "r", encoding="utf-8") as handle:
            if handle.read() == content:
                return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    return True


def _copy_if_changed(src: Path, dst: Path, quiet: bool) -> bool:
    if not src.exists():
        return False
    if dst.exists() and src.read_bytes() == dst.read_bytes():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    _log(f"Synced {src.relative_to(ROOT_DIR)} -> {dst.relative_to(ROOT_DIR)}", quiet)
    return True


def _cards_are_current() -> bool:
    compiled_data = compiler_main.load_json(str(CARDS_OUTPUT_PATH))
    if not compiled_data:
        return False

    meta = compiled_data.get("meta", {})
    stored_hash = meta.get("source_hash")
    stored_ability_hash = meta.get("ability_source_hash")
    stored_compiler_hash = meta.get("compiler_source_hash")
    current_hash = compiler_main.calculate_hash(str(CARDS_INPUT_PATH))
    current_ability_hash = compiler_main.calculate_hash(compiler_main.SPARSE_INDEX_PATH)
    current_compiler_hash = _calculate_combined_hash(SOURCE_HASH_FILES)
    return (
        stored_hash == current_hash
        and stored_ability_hash == current_ability_hash
        and stored_compiler_hash == current_compiler_hash
    )


def _update_cards_meta() -> None:
    compiled_data = compiler_main.load_json(str(CARDS_OUTPUT_PATH))
    if not compiled_data:
        return

    meta = compiled_data.setdefault("meta", {})
    for key in (
        "documentation",
        "source_files",
        "semantic_form_enabled",
        "semantic_form_version",
        "export_profile",
    ):
        meta.pop(key, None)
    meta["source_hash"] = compiler_main.calculate_hash(str(CARDS_INPUT_PATH))
    meta["ability_source_hash"] = compiler_main.calculate_hash(compiler_main.SPARSE_INDEX_PATH)
    meta["compiler_source_hash"] = _calculate_combined_hash(SOURCE_HASH_FILES)
    meta["generated_by"] = "tools/abilities/pipeline.py"
    meta["execution_model"] = "frame_program_only"

    with open(CARDS_OUTPUT_PATH, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(compiled_data, handle, ensure_ascii=False, indent=2)


def prepare_cards(*, force: bool = False, quiet: bool = False) -> bool:
    cards_changed = force or not _cards_are_current()
    if cards_changed:
        _log("Compiling cards from authored sources", quiet)
        compiler_main.compile_cards(
            str(CARDS_INPUT_PATH),
            str(CARDS_OUTPUT_PATH),
            quiet=quiet,
            export_profile="runtime",
        )
        _update_cards_meta()
    else:
        _log("cards_compiled.json is up to date", quiet)

    compat_changed = _copy_if_changed(CARDS_OUTPUT_PATH, ENGINE_CARDS_OUTPUT_PATH, quiet)
    return cards_changed or compat_changed


def prepare_frame_index(
    *,
    force: bool = False,
    quiet: bool = False,
    input_path: Path = FRAME_INDEX_INPUT_PATH,
    metadata_path: Path = FRAME_INDEX_METADATA_PATH,
    output_path: Path = FRAME_INDEX_OUTPUT_PATH,
    cards_path: Path = FRAME_INDEX_CARDS_PATH,
    hash_path: Path = FRAME_INDEX_HASH_PATH,
) -> bool:
    cards_hash = _calculate_hash(cards_path)
    frame_hash = _calculate_hash(input_path)
    metadata_hash = _calculate_hash(metadata_path)
    current_hash = f"{frame_hash}|{metadata_hash}|{cards_hash}"

    if not force and hash_path.exists() and output_path.exists():
        with open(hash_path, "r", encoding="utf-8") as handle:
            if handle.read().strip() == current_hash:
                _log("ability_frame_index.json is up to date", quiet)
                return False

    payload = frame_codec.load_json(input_path)
    metadata = frame_codec.load_json(metadata_path)
    card_db = _load_json(cards_path) or {}
    runtime_payload = frame_codec.build_runtime_ability_index(payload, metadata, card_db=card_db)
    changed = _dump_json_if_changed(output_path, runtime_payload, quiet)
    _write_text_if_changed(hash_path, current_hash)
    return changed


def prepare_rust_codegen(*, quiet: bool = False) -> bool:
    changed = codegen_abilities.generate_rust(quiet=quiet)
    if changed:
        _log("Updated generated Rust ability fast paths", quiet)
    else:
        _log("Generated Rust ability fast paths are up to date", quiet)
    return changed


def prepare_server_assets(*, quiet: bool = False) -> bool:
    return bool(sync_launcher_assets.sync_assets(quiet=quiet))


def prepare_runtime(
    *,
    force: bool = False,
    quiet: bool = False,
    sync_assets: bool = False,
) -> PrepareResult:
    result = PrepareResult()
    result.cards_changed = prepare_cards(force=force, quiet=quiet)
    result.frame_index_changed = prepare_frame_index(force=force, quiet=quiet)
    result.rust_codegen_changed = prepare_rust_codegen(quiet=quiet)
    if sync_assets:
        result.launcher_assets_changed = prepare_server_assets(quiet=quiet)
    return result
