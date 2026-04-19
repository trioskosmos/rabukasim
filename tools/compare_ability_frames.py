import json
from pathlib import Path
from typing import Dict, Any, Set, Tuple

def load_json(filepath: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def compare_values(val1: Any, val2: Any, path: str = "") -> Dict[str, Any]:
    """Recursively compare two values and return differences."""
    differences = {}
    
    if val1 == val2:
        return differences
    
    if isinstance(val1, dict) and isinstance(val2, dict):
        all_keys = set(val1.keys()) | set(val2.keys())
        for key in all_keys:
            current_path = f"{path}.{key}" if path else key
            if key not in val1:
                differences[current_path] = {"status": "missing_in_authored", "value": val2[key]}
            elif key not in val2:
                differences[current_path] = {"status": "missing_in_automated", "value": val1[key]}
            else:
                nested_diff = compare_values(val1[key], val2[key], current_path)
                if nested_diff:
                    differences.update(nested_diff)
    elif isinstance(val1, list) and isinstance(val2, list):
        if val1 != val2:
            differences[path] = {
                "status": "different",
                "authored": val1,
                "automated": val2
            }
    else:
        differences[path] = {
            "status": "different",
            "authored": val1,
            "automated": val2
        }
    
    return differences

def compare_frames(authored_path: Path, automated_path: Path, output_path: Path = None):
    """Compare two ability frame JSON files."""
    authored = load_json(authored_path)
    automated = load_json(automated_path)
    
    authored_frames = set(authored.keys())
    automated_frames = set(automated.keys())
    
    lines = []
    lines.append(f"Authored frames: {len(authored_frames)}")
    lines.append(f"Automated frames: {len(automated_frames)}")
    lines.append("")
    
    # Frames only in authored
    only_authored = authored_frames - automated_frames
    if only_authored:
        lines.append(f"Frames ONLY in authored ({len(only_authored)}):")
        for frame in sorted(only_authored):
            lines.append(f"  - {frame}")
    else:
        lines.append("No frames only in authored")
    lines.append("")
    
    # Frames only in automated
    only_automated = automated_frames - authored_frames
    if only_automated:
        lines.append(f"Frames ONLY in automated ({len(only_automated)}):")
        for frame in sorted(only_automated):
            lines.append(f"  - {frame}")
    else:
        lines.append("No frames only in automated")
    lines.append("")
    
    # Common frames with differences
    common_frames = authored_frames & automated_frames
    frames_with_differences = []
    
    for frame in sorted(common_frames):
        if authored[frame] != automated[frame]:
            frames_with_differences.append(frame)
    
    if frames_with_differences:
        lines.append(f"Common frames with content differences ({len(frames_with_differences)}):")
        for frame in frames_with_differences:
            lines.append(f"\n  Frame: {frame}")
            differences = compare_values(authored[frame], automated[frame], frame)
            for path, diff in sorted(differences.items()):
                if diff["status"] == "different":
                    lines.append(f"    {path}:")
                    lines.append(f"      Authored:  {diff['authored']}")
                    lines.append(f"      Automated: {diff['automated']}")
                elif diff["status"] == "missing_in_authored":
                    lines.append(f"    {path}: MISSING in authored")
                    lines.append(f"      Automated value: {diff['value']}")
                elif diff["status"] == "missing_in_automated":
                    lines.append(f"    {path}: MISSING in automated")
                    lines.append(f"      Authored value: {diff['value']}")
    else:
        lines.append("No content differences in common frames")
    
    lines.append("")
    lines.append(f"Summary:")
    lines.append(f"  Total unique frames: {len(authored_frames | automated_frames)}")
    lines.append(f"  Only in authored: {len(only_authored)}")
    lines.append(f"  Only in automated: {len(only_automated)}")
    lines.append(f"  Common frames: {len(common_frames)}")
    lines.append(f"  Common frames with differences: {len(frames_with_differences)}")
    
    output = "\n".join(lines)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Output saved to {output_path}")
    else:
        print(output)

if __name__ == "__main__":
    base_path = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data")
    authored_path = base_path / "ability_frame_source_authored.json"
    automated_path = base_path / "ability_frame_source.json"
    output_path = base_path / "frame_comparison_output.txt"
    
    compare_frames(authored_path, automated_path, output_path)
