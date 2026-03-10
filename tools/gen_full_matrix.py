import json
import os
import re

MIN_TEST_SCORE = 2
SUSPICIOUS_TEST_PATTERNS = [
    r"simplified",
    r"structural verification",
    r"implicitly enforcing",
    r"no actual placement needed",
    r"assuming current engine logic",
    r"just check logic",
    r"simulating wait state",
]
ENGINE_SIGNAL_PATTERNS = [
    r"load_real_db\s*\(",
    r"play_member\s*\(",
    r"auto_step\s*\(",
    r"do_draw_phase\s*\(",
    r"do_performance_phase\s*\(",
    r"do_live_result\s*\(",
    r"finalize_live_result\s*\(",
    r"generate_legal_actions\s*\(",
    r"trigger_abilities\s*\(",
    r"process_trigger_queue\s*\(",
    r"resolve_bytecode\s*\(",
    r"get_effective_(?:blades|hearts)\s*\(",
    r"get_live_requirements\s*\(",
    r"check_condition_opcode\s*\(",
    r"handle_liveresult\s*\(",
    r"\.step\s*\(",
]


def clean_text(text):
    if not text:
        return ""
    # Replace newlines with a space and a separator to keep it on one line but readable
    text = text.replace("\n", " <br> ")
    # Escape pipe characters which are the primary table breakers
    text = text.replace("|", "\\|")
    return text.strip()


def score_test_body(body):
    score = 0
    lowered = body.lower()

    assert_count = len(re.findall(r"\bassert(?:_eq|_ne)?!\s*\(", body))
    score += min(assert_count, 4)

    engine_signal_count = 0
    for pattern in ENGINE_SIGNAL_PATTERNS:
        if re.search(pattern, body):
            engine_signal_count += 1
    score += min(engine_signal_count * 3, 12)

    if "load_real_db(" in body:
        score += 3

    if engine_signal_count == 0:
        score -= 5

    if assert_count == 0:
        score -= 4

    for pattern in SUSPICIOUS_TEST_PATTERNS:
        if re.search(pattern, lowered, re.I):
            score -= 6

    return score


def extract_test_functions(lines):
    fn_line_pattern = re.compile(r"fn\s+((?:test_|repro_)[a-zA-Z0-9_]*)")
    functions = []
    line_count = len(lines)
    i = 0

    while i < line_count:
        fn_match = fn_line_pattern.search(lines[i])
        if not fn_match:
            i += 1
            continue

        fn_name = fn_match.group(1)
        start = i
        brace_depth = lines[i].count("{") - lines[i].count("}")
        j = i + 1

        while j < line_count:
            brace_depth += lines[j].count("{") - lines[j].count("}")
            if brace_depth <= 0:
                break
            j += 1

        end = min(j, line_count - 1)
        functions.append((fn_name, start, end))
        i = end + 1

    return functions


def extract_q_ids(text):
    q_ids = set()

    for start_str, end_str in re.findall(r"q(\d+)_to_q?(\d+)", text, re.I):
        start = int(start_str)
        end = int(end_str)
        if start <= end and end - start <= 20:
            q_ids.update(range(start, end + 1))

    q_ids.update(int(q_id) for q_id in re.findall(r"q(\d+)", text, re.I))
    return q_ids


def extract_leading_comment_block(lines, start, end):
    header_lines = []
    for idx in range(start + 1, min(end + 1, start + 12)):
        stripped = lines[idx].strip()
        if not stripped:
            if header_lines:
                break
            continue
        if stripped.startswith("//"):
            header_lines.append(stripped)
            continue
        break
    return "\n".join(header_lines)


def extract_attached_comment_block_above(lines, start):
    header_lines = []
    idx = start - 1

    while idx >= 0 and lines[idx].strip().startswith("#"):
        idx -= 1

    while idx >= 0:
        stripped = lines[idx].strip()
        if not stripped:
            if header_lines:
                break
            idx -= 1
            continue
        if not stripped.startswith("//"):
            break
        if "GROUP" in stripped or "====" in stripped:
            break
        header_lines.append(stripped)
        idx -= 1

    header_lines.reverse()
    return "\n".join(header_lines)


def scan_rust_tests(root_dir):
    """Recursively scan all .rs files for test names and QA associations."""
    verified_ids = {}  # map q_id (int) to metadata

    # regex for explicit QA comments
    comment_pattern = re.compile(r"(?:QA|Rule|Ruling|Q&A|Rulings):\s*Q?(\d+)", re.I)

    for root, dirs, files in os.walk(root_dir):
        if "target" in dirs:
            dirs.remove("target")

        for file in files:
            if file.endswith(".rs"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()

                        rel_path = os.path.relpath(path, root_dir).replace("\\", "/")
                        for fn_name, start, end in extract_test_functions(lines):
                            body = "".join(lines[start : end + 1])
                            attached_above = extract_attached_comment_block_above(lines, start)
                            leading_comments = extract_leading_comment_block(lines, start, end)
                            q_ids = extract_q_ids(fn_name)
                            q_ids.update(extract_q_ids(attached_above))
                            q_ids.update(extract_q_ids(leading_comments))
                            q_ids.update(int(q_id) for q_id in comment_pattern.findall(attached_above))
                            q_ids.update(int(q_id) for q_id in comment_pattern.findall(leading_comments))

                            if not q_ids:
                                continue

                            score = score_test_body(body)
                            candidate = {
                                "test_name": fn_name,
                                "file_rel": rel_path,
                                "score": score,
                            }

                            for q_id in q_ids:
                                existing = verified_ids.get(q_id)
                                if existing is None or score > existing["score"]:
                                    verified_ids[q_id] = candidate

                except Exception as e:
                    print(f"Error scanning {path}: {e}")

    return {q_id: candidate for q_id, candidate in verified_ids.items() if candidate["score"] >= MIN_TEST_SCORE}


def generate_matrix():
    data_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\qa_data.json"
    rust_root = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src"
    output_paths = [
        r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\.agent\skills\qa_rule_verification\qa_test_matrix.md",
        r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\.kilocode\skills\qa_rule_verification\qa_test_matrix.md",
    ]

    if not os.path.exists(data_path):
        print(f"Data path not found: {data_path}")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        qa_data = json.load(f)

    # Scan all tests
    verified_ids = scan_rust_tests(rust_root)

    # Sort QA data by ID
    def get_id_num(item):
        m = re.search(r"\d+", item["id"])
        return int(m.group()) if m else 0

    qa_data.sort(key=get_id_num)

    # Calculate Stats
    total_items = len(qa_data)

    # Define SV IDs for stats consistency
    sv_ids = {1, 2, 8, 9, 10, 11, 12, 13, 3, 4, 5, 6, 7, 20, 21, 22}

    verified_and_sv_ids = set(verified_ids.keys()) | sv_ids
    verified_count = len(verified_and_sv_ids)
    coverage_pct = (verified_count / total_items) * 100 if total_items > 0 else 0

    engine_rule_gap_count = 0
    engine_card_gap_count = 0
    for item in qa_data:
        qid_int = get_id_num(item)
        is_verified = qid_int in verified_ids
        is_sv = qid_int in sv_ids
        is_card_specific = len(item.get("related_cards", [])) > 0
        if not is_verified and not is_sv:
            if is_card_specific:
                engine_card_gap_count += 1
            else:
                engine_rule_gap_count += 1

    lines = [
        "# Love Live! SIC Q&A Comprehensive Rule Matrix",
        "",
        "This matrix tracks the alignment of the LovecaSim engine with official Q&A rulings.",
        "Tests are counted only when the scanner finds a high-fidelity assertion path rather than placeholder or explicitly simplified coverage.",
        "",
        "## 📊 Coverage Summary",
        f"- **Total Rulings**: {total_items}",
        f"- **Verified (Automated)**: {verified_count}",
        f"- **Progress**: {coverage_pct:.1f}%",
        f"- **Unverified Engine (Rule)**: {engine_rule_gap_count}",
        f"- **Unverified Engine (Card-specific)**: {engine_card_gap_count}",
        "",
        "| ID | Status | Category | Question | Answer | Justification / Verification |",
        "| :--- | :---: | :--- | :--- | :--- | :--- |",
    ]

    for item in qa_data:
        qid_str = item["id"]
        qid_int = get_id_num(item)

        q_text = clean_text(item["question"])
        a_text = clean_text(item["answer"])

        # Scope Verification (SV) logic
        sv_ids_out_of_scope = {1, 2, 8, 9, 10, 11, 12, 13}
        sv_ids_pre_game = {3, 4, 5, 6, 7}
        sv_ids_meta_human = {20, 21, 22}
        sv_ids = sv_ids_out_of_scope | sv_ids_pre_game | sv_ids_meta_human

        is_verified = qid_int in verified_ids
        is_sv = qid_int in sv_ids
        status_icon = "✅" if (is_verified or is_sv) else "ℹ️"
        is_card_specific = len(item.get("related_cards", [])) > 0

        if is_sv:
            category = "Scope Verified"
        elif is_card_specific:
            category = "Engine (Card-specific)"
        else:
            category = "Engine (Rule)"

        justification = ""
        if is_verified:
            test_name = verified_ids[qid_int]["test_name"]
            file_rel = verified_ids[qid_int]["file_rel"]
            justification = f"`{test_name}` in `{file_rel}`"
        elif is_sv:
            if qid_int in sv_ids_out_of_scope:
                justification = "[SV] _General tournament/setup; outside engine scope._"
            elif qid_int in sv_ids_pre_game:
                justification = "[SV] _Pre-game/Deck validation; outside match engine._"
            elif qid_int in sv_ids_meta_human:
                justification = "[SV] _Meta-rule (human error protection); handle natively by engine._"
        else:
            if is_card_specific:
                card_refs = ", ".join([f"`{c['card_no']}`" for c in item["related_cards"]])
                justification = f"Card-specific ({card_refs}); no high-fidelity automated QA test selected yet."
            else:
                justification = "Engine (Rule) gap; no high-fidelity automated QA test selected yet."

        line = f"| **{qid_str}** | {status_icon} | {category} | {q_text} | {a_text} | {justification} |"
        lines.append(line)

    rendered = "\n".join(lines)
    written_paths = []
    for output_path in output_paths:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered)
        written_paths.append(output_path)

    for output_path in written_paths:
        print(f"Final Matrix generated at: {output_path}")
    print(f"Coverage: {verified_count}/{total_items} ({coverage_pct:.1f}%)")


if __name__ == "__main__":
    generate_matrix()
