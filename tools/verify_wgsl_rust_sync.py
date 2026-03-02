#!/usr/bin/env python3
"""
WGSL-Rust Struct Synchronization Verification Tool

This tool parses WGSL shader files and Rust source files to verify that
GPU-facing structs are synchronized between CPU (Rust) and GPU (WGSL).

Usage:
    python tools/verify_wgsl_rust_sync.py [--fix] [--report]

Features:
    - Parses WGSL struct definitions (name, fields, types, array sizes)
    - Parses Rust #[repr(C)] structs with Pod/Zeroable
    - Compares field names, types, offsets, and sizes
    - Generates detailed sync report
    - Can auto-generate Rust structs from WGSL (with --fix)
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class StructField:
    """Represents a field in a struct."""

    name: str
    type_name: str
    array_size: Optional[int] = None  # None for scalars, size for arrays
    offset: Optional[int] = None
    size: Optional[int] = None
    is_padding: bool = False


@dataclass
class StructDef:
    """Represents a struct definition."""

    name: str
    fields: List[StructField] = field(default_factory=list)
    total_size: Optional[int] = None
    source_file: str = ""
    source_line: int = 0


# Type size mappings for WGSL
WGSL_TYPE_SIZES = {
    # Scalar types
    "u32": 4,
    "i32": 4,
    "f32": 4,
    "bool": 4,  # WGSL bool is 4 bytes in memory
    # Vector types
    "vec2<u32>": 8,
    "vec2<i32>": 8,
    "vec2<f32>": 8,
    "vec3<u32>": 12,
    "vec3<i32>": 12,
    "vec3<f32>": 12,
    "vec4<u32>": 16,
    "vec4<i32>": 16,
    "vec4<f32>": 16,
    # Special
    "atomic<u32>": 4,
    "atomic<i32>": 4,
}

# Rust to WGSL type mapping
RUST_TO_WGSL_TYPES = {
    "u32": "u32",
    "i32": "i32",
    "f32": "f32",
    "bool": "u32",  # Rust bool -> WGSL u32 (with value 0/1)
    "u64": "vec2<u32>",  # u64 split into two u32s
    "i64": "vec2<i32>",
    "u16": "u32",  # Promoted to u32 for alignment
    "i16": "i32",
    "u8": "u32",  # Promoted to u32
    "i8": "i32",
}

# Rust to WGSL struct name mapping
RUST_TO_WGSL_STRUCT_NAMES = {
    "GpuTriggerRequest": "GpuTriggerRequest",
    "GpuPlayerState": "GpuPlayerState",
    "GpuGameState": "GpuGameState",
    "GpuCardStats": "GpuCardStats",
    # Handle case where WGSL has different name
    "TriggerRequest": "GpuTriggerRequest",
}

# Structs to skip (internal WGSL structs not used for GPU buffers)
SKIP_WGSL_STRUCTS = {
    "TriggerRequest",  # Internal WGSL struct, not a GPU buffer type
}


# WGSL array element alignment rules
def get_wgsl_alignment(type_name: str) -> int:
    """Get alignment requirement for a WGSL type."""
    if type_name.startswith("vec3"):
        return 16  # vec3 has 16-byte alignment
    elif type_name.startswith("vec4"):
        return 16
    elif type_name.startswith("vec2"):
        return 8
    elif type_name.startswith("array"):
        # Arrays have alignment of element type, rounded up to 16
        return 16
    else:
        return 4  # Scalar types


def parse_wgsl_struct(wgsl_content: str, filename: str = "") -> List[StructDef]:
    """Parse WGSL struct definitions from source code."""
    structs = []

    # Pattern to match struct definitions (handle nested braces for arrays)
    struct_pattern = re.compile(r"struct\s+(\w+)\s*\{([^}]+)\}", re.MULTILINE)

    for match in struct_pattern.finditer(wgsl_content):
        struct_name = match.group(1)
        body = match.group(2)
        line_num = wgsl_content[: match.start()].count("\n") + 1

        struct_def = StructDef(name=struct_name, source_file=filename, source_line=line_num)

        # Parse each field - handle both simple types and array<T, N>
        # Split by lines and process each field
        lines = body.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("//"):
                continue

            # Remove trailing comma and comments
            line = line.split("//")[0].strip().rstrip(",")
            if not line:
                continue

            # Match field: type or field: array<T, N>
            field_match = re.match(r"(\w+)\s*:\s*(.+)$", line)
            if not field_match:
                continue

            field_name = field_match.group(1).strip()
            field_type = field_match.group(2).strip()

            # Handle arrays: array<T, N> or array<T,N>
            array_match = re.match(r"array<(\w+),\s*(\d+)>", field_type)
            array_size = None
            base_type = field_type

            if array_match:
                base_type = array_match.group(1)
                array_size = int(array_match.group(2))

            # Skip padding fields (usually named _pad or _padding)
            is_padding = field_name.startswith("_pad") or field_name.startswith("_padding")

            struct_def.fields.append(
                StructField(name=field_name, type_name=base_type, array_size=array_size, is_padding=is_padding)
            )

        structs.append(struct_def)

    return structs


def parse_rust_struct(rust_content: str, filename: str = "") -> List[StructDef]:
    """Parse Rust struct definitions from source code."""
    structs = []

    # Pattern to match struct definitions with attributes
    struct_pattern = re.compile(
        r"(?:#\[[^\]]+\]\s*)*"  # Attributes
        r"pub\s+struct\s+(\w+)\s*\{([^}]+)\}",
        re.MULTILINE | re.DOTALL,
    )

    for match in struct_pattern.finditer(rust_content):
        struct_name = match.group(1)
        body = match.group(2)
        line_num = rust_content[: match.start()].count("\n") + 1

        # Check if this is a GPU struct (has repr(C) or Pod)
        full_match = match.group(0)
        if "#[repr(C)]" not in full_match and "Pod" not in full_match:
            continue

        struct_def = StructDef(name=struct_name, source_file=filename, source_line=line_num)

        # Parse each field
        field_pattern = re.compile(r"pub\s+(\w+)\s*:\s*([^,/\n]+?)(?:\s*,|\s*$)", re.MULTILINE)

        for field_match in field_pattern.finditer(body):
            field_name = field_match.group(1).strip()
            field_type = field_match.group(2).strip()

            # Handle arrays: [T; N]
            array_match = re.match(r"\[(\w+);\s*(\d+)\]", field_type)
            array_size = None
            base_type = field_type

            if array_match:
                base_type = array_match.group(1)
                array_size = int(array_match.group(2))

            # Skip padding fields
            is_padding = field_name.startswith("_pad") or field_name.startswith("_padding")

            struct_def.fields.append(
                StructField(name=field_name, type_name=base_type, array_size=array_size, is_padding=is_padding)
            )

        structs.append(struct_def)

    return structs


def calculate_wgsl_offsets(struct_def: StructDef, struct_sizes: Dict[str, int] = None) -> int:
    """Calculate field offsets and total size for WGSL struct.

    Args:
        struct_def: The struct definition to calculate offsets for
        struct_sizes: Optional dict mapping custom struct names to their sizes
    """
    if struct_sizes is None:
        struct_sizes = {}

    current_offset = 0

    for field in struct_def.fields:
        field.offset = current_offset

        if field.array_size:
            # Array: alignment * ceil(size/alignment) * count
            elem_size = WGSL_TYPE_SIZES.get(field.type_name, struct_sizes.get(field.type_name, 4))
            elem_align = get_wgsl_alignment(field.type_name)
            # Align current offset
            current_offset = ((current_offset + elem_align - 1) // elem_align) * elem_align
            field.offset = current_offset
            field.size = elem_size * field.array_size
            current_offset += field.size
        else:
            # Check if it's a custom struct type
            field.size = WGSL_TYPE_SIZES.get(field.type_name, struct_sizes.get(field.type_name, 4))
            current_offset += field.size

    # Align total size to 16 bytes (WebGPU requirement)
    total = ((current_offset + 15) // 16) * 16
    struct_def.total_size = total
    return total


def calculate_rust_offsets(struct_def: StructDef, struct_sizes: Dict[str, int] = None) -> int:
    """Calculate field offsets for Rust struct (simplified).

    Args:
        struct_def: The struct definition to calculate offsets for
        struct_sizes: Optional dict mapping custom struct names to their sizes
    """
    if struct_sizes is None:
        struct_sizes = {}

    current_offset = 0

    for field in struct_def.fields:
        field.offset = current_offset

        if field.array_size:
            # Array: element_size * count
            elem_size = 4  # Assume u32/i32 for GPU structs
            if field.type_name in struct_sizes:
                elem_size = struct_sizes[field.type_name]
            field.size = elem_size * field.array_size
            current_offset += field.size
        else:
            # Check if it's a custom struct type
            if field.type_name in struct_sizes:
                field.size = struct_sizes[field.type_name]
            else:
                field.size = 4  # Assume u32/i32/f32 for GPU structs
            current_offset += field.size

    struct_def.total_size = current_offset
    return current_offset


def compare_structs(wgsl_struct: StructDef, rust_struct: StructDef) -> List[dict]:
    """Compare WGSL and Rust struct definitions, return discrepancies."""
    discrepancies = []

    # Compare field count
    wgsl_fields = [f for f in wgsl_struct.fields if not f.is_padding]
    rust_fields = [f for f in rust_struct.fields if not f.is_padding]

    if len(wgsl_fields) != len(rust_fields):
        discrepancies.append(
            {
                "type": "field_count_mismatch",
                "wgsl_count": len(wgsl_fields),
                "rust_count": len(rust_fields),
                "severity": "error",
            }
        )

    # Compare each field
    for i, (wf, rf) in enumerate(zip(wgsl_fields, rust_fields)):
        if wf.name != rf.name:
            discrepancies.append(
                {
                    "type": "field_name_mismatch",
                    "index": i,
                    "wgsl_name": wf.name,
                    "rust_name": rf.name,
                    "severity": "warning",
                }
            )

        # Compare array sizes
        if wf.array_size != rf.array_size:
            discrepancies.append(
                {
                    "type": "array_size_mismatch",
                    "field": wf.name,
                    "wgsl_size": wf.array_size,
                    "rust_size": rf.array_size,
                    "severity": "error",
                }
            )

        # Compare types (with mapping)
        expected_wgsl_type = RUST_TO_WGSL_TYPES.get(rf.type_name, rf.type_name)
        if wf.type_name != expected_wgsl_type and wf.type_name != rf.type_name:
            discrepancies.append(
                {
                    "type": "type_mismatch",
                    "field": wf.name,
                    "wgsl_type": wf.type_name,
                    "rust_type": rf.type_name,
                    "severity": "warning",
                }
            )

    # Compare total size
    if wgsl_struct.total_size and rust_struct.total_size:
        if wgsl_struct.total_size != rust_struct.total_size:
            discrepancies.append(
                {
                    "type": "size_mismatch",
                    "wgsl_size": wgsl_struct.total_size,
                    "rust_size": rust_struct.total_size,
                    "severity": "error",
                }
            )

    return discrepancies


def generate_rust_struct(wgsl_struct: StructDef) -> str:
    """Generate Rust struct definition from WGSL struct."""
    lines = []
    lines.append("#[repr(C)]")
    lines.append("#[derive(Copy, Clone, Debug, Pod, Zeroable, Default)]")
    lines.append(f"pub struct {wgsl_struct.name} {{")

    for field in wgsl_struct.fields:
        rust_type = field.type_name  # Default: same as WGSL

        # Convert WGSL type to Rust type
        if field.array_size:
            lines.append(f"    pub {field.name}: [{rust_type}; {field.array_size}],")
        else:
            lines.append(f"    pub {field.name}: {rust_type},")

    lines.append("}")
    return "\n".join(lines)


def generate_wgsl_struct(rust_struct: StructDef) -> str:
    """Generate WGSL struct definition from Rust struct."""
    lines = []
    lines.append(f"struct {rust_struct.name} {{")

    for field in rust_struct.fields:
        wgsl_type = field.type_name  # Default: same as Rust

        # Convert Rust type to WGSL type
        if field.array_size:
            lines.append(f"    {field.name}: array<{wgsl_type}, {field.array_size}>,")
        else:
            lines.append(f"    {field.name}: {wgsl_type},")

    lines.append("}")
    return "\n".join(lines)


def verify_sync(wgsl_path: str, rust_path: str, output_report: str = None) -> dict:
    """Main verification function."""
    results = {
        "wgsl_file": wgsl_path,
        "rust_file": rust_path,
        "structs": {},
        "summary": {"total_structs": 0, "synced": 0, "discrepancies": 0, "errors": []},
    }

    # Read files
    wgsl_content = ""
    rust_content = ""

    if os.path.exists(wgsl_path):
        with open(wgsl_path, "r", encoding="utf-8") as f:
            wgsl_content = f.read()
    else:
        results["summary"]["errors"].append(f"WGSL file not found: {wgsl_path}")

    if os.path.exists(rust_path):
        with open(rust_path, "r", encoding="utf-8") as f:
            rust_content = f.read()
    else:
        results["summary"]["errors"].append(f"Rust file not found: {rust_path}")

    # Parse structs
    wgsl_structs = parse_wgsl_struct(wgsl_content, wgsl_path)
    rust_structs = parse_rust_struct(rust_content, rust_path)

    # First pass: calculate sizes for simple structs (no nested types)
    # Build struct size lookup for nested struct handling
    struct_sizes = {}

    # Process in dependency order - simple structs first
    def get_struct_dependencies(struct_def: StructDef, all_structs: Dict[str, StructDef]) -> set:
        """Get set of struct types this struct depends on."""
        deps = set()
        for field in struct_def.fields:
            if field.type_name not in WGSL_TYPE_SIZES and field.type_name in all_structs:
                deps.add(field.type_name)
        return deps

    # Build dependency graph and process in order
    wgsl_lookup = {s.name: s for s in wgsl_structs}
    rust_lookup = {s.name: s for s in rust_structs}

    # Simple topological sort for size calculation
    def calculate_struct_sizes_in_order(structs: List[StructDef], lookup: Dict[str, StructDef], is_wgsl: bool):
        """Calculate struct sizes in dependency order."""
        calculated = {}
        remaining = list(structs)
        max_iterations = len(structs) * 2  # Prevent infinite loops

        while remaining and max_iterations > 0:
            max_iterations -= 1
            for struct_def in remaining[:]:
                deps = get_struct_dependencies(struct_def, lookup)
                # Check if all dependencies are calculated
                if all(d in calculated for d in deps):
                    if is_wgsl:
                        calculate_wgsl_offsets(struct_def, calculated)
                    else:
                        calculate_rust_offsets(struct_def, calculated)
                    calculated[struct_def.name] = struct_def.total_size
                    remaining.remove(struct_def)

        return calculated

    wgsl_sizes = calculate_struct_sizes_in_order(wgsl_structs, wgsl_lookup, True)
    rust_sizes = calculate_struct_sizes_in_order(rust_structs, rust_lookup, False)

    # Compare each WGSL struct with corresponding Rust struct
    for wgsl_struct in wgsl_structs:
        struct_name = wgsl_struct.name

        # Skip internal WGSL structs
        if struct_name in SKIP_WGSL_STRUCTS:
            continue

        if struct_name in rust_lookup:
            rust_struct = rust_lookup[struct_name]
            discrepancies = compare_structs(wgsl_struct, rust_struct)

            results["structs"][struct_name] = {
                "wgsl": {
                    "fields": len(wgsl_struct.fields),
                    "size": wgsl_struct.total_size,
                    "source": f"{wgsl_struct.source_file}:{wgsl_struct.source_line}",
                },
                "rust": {
                    "fields": len(rust_struct.fields),
                    "size": rust_struct.total_size,
                    "source": f"{rust_struct.source_file}:{rust_struct.source_line}",
                },
                "discrepancies": discrepancies,
                "synced": len(discrepancies) == 0,
            }

            if discrepancies:
                results["summary"]["discrepancies"] += 1
            else:
                results["summary"]["synced"] += 1
        else:
            results["structs"][struct_name] = {
                "wgsl": {
                    "fields": len(wgsl_struct.fields),
                    "size": wgsl_struct.total_size,
                    "source": f"{wgsl_struct.source_file}:{wgsl_struct.source_line}",
                },
                "rust": None,
                "discrepancies": [{"type": "missing_rust_struct", "severity": "error"}],
                "synced": False,
            }
            results["summary"]["discrepancies"] += 1

    results["summary"]["total_structs"] = len(wgsl_structs)

    # Write report if requested
    if output_report:
        os.makedirs(os.path.dirname(output_report) or ".", exist_ok=True)
        with open(output_report, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Report written to: {output_report}")

    return results


def print_report(results: dict):
    """Print a human-readable report."""
    print("\n" + "=" * 60)
    print("WGSL-RUST SYNC VERIFICATION REPORT")
    print("=" * 60)

    print(f"\nWGSL File: {results['wgsl_file']}")
    print(f"Rust File: {results['rust_file']}")

    print("\nSummary:")
    print(f"  Total structs: {results['summary']['total_structs']}")
    print(f"  Synced: {results['summary']['synced']}")
    print(f"  With discrepancies: {results['summary']['discrepancies']}")

    if results["summary"]["errors"]:
        print("\nErrors:")
        for err in results["summary"]["errors"]:
            print(f"  - {err}")

    print("\n" + "-" * 60)
    print("STRUCT DETAILS")
    print("-" * 60)

    for name, data in results["structs"].items():
        status = "OK" if data["synced"] else "MISMATCH"
        print(f"\n[{status}] {name}")

        if data["wgsl"]:
            print(f"  WGSL: {data['wgsl']['fields']} fields, {data['wgsl']['size']} bytes")
        if data["rust"]:
            print(f"  Rust: {data['rust']['fields']} fields, {data['rust']['size']} bytes")

        if data["discrepancies"]:
            print("  Discrepancies:")
            for d in data["discrepancies"]:
                print(f"    - {d['type']}: {d}")

    print("\n" + "=" * 60)

    if results["summary"]["discrepancies"] > 0:
        print("RESULT: SYNC ISSUES DETECTED")
        return 1
    else:
        print("RESULT: ALL STRUCTS IN SYNC")
        return 0


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Verify WGSL-Rust struct synchronization")
    parser.add_argument(
        "--wgsl", default="engine_rust_src/debug_concatenated_shader.wgsl", help="Path to WGSL shader file"
    )
    parser.add_argument("--rust", default="engine_rust_src/src/core/gpu_state.rs", help="Path to Rust source file")
    parser.add_argument("--report", default="reports/wgsl_rust_sync_report.json", help="Path to output JSON report")
    parser.add_argument("--fix", action="store_true", help="Generate missing Rust structs from WGSL")
    parser.add_argument("--quiet", action="store_true", help="Only print errors")

    args = parser.parse_args()

    results = verify_sync(args.wgsl, args.rust, args.report)

    if not args.quiet:
        exit_code = print_report(results)
    else:
        exit_code = 1 if results["summary"]["discrepancies"] > 0 else 0

    # Handle --fix
    if args.fix and results["summary"]["discrepancies"] > 0:
        print("\nGenerating missing/mismatched Rust structs...")
        wgsl_content = open(args.wgsl).read()
        wgsl_structs = parse_wgsl_struct(wgsl_content, args.wgsl)

        for ws in wgsl_structs:
            if ws.name in results["structs"] and not results["structs"][ws.name]["synced"]:
                print(f"\n// Generated from {args.wgsl}")
                print(generate_rust_struct(ws))

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
