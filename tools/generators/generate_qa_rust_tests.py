import json
import re

def generate_rust_tests():
    try:
        with open("data/qa_data.json", "r", encoding="utf-8") as f:
            qa_data = json.load(f)
    except FileNotFoundError:
        print("data/qa_data.json not found.")
        return

    # Extract already implemented tests
    try:
        with open("engine_rust_src/src/qa_verification_tests.rs", "r", encoding="utf-8") as f:
            existing_tests = f.read()
    except FileNotFoundError:
        existing_tests = ""

    # Collect existing Q numbers (e.g. Q103, Q55)
    implemented_qs = set()
    for match in re.finditer(r"q(\d+)", existing_tests.lower()):
        implemented_qs.add(f"Q{match.group(1)}")

    # Generate new tests
    test_content = """use crate::core::logic::*;
use crate::test_helpers::*;

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_db() -> CardDatabase {
        CardDatabase::default()
    }

    fn create_test_state() -> GameState {
        GameState::default()
    }

"""

    # Sort by Q number numerically
    qa_data.sort(key=lambda x: int(x["id"].replace("Q", "")) if x["id"].startswith("Q") else 9999)

    for item in qa_data:
        qid = item["id"]

        if qid in implemented_qs:
            continue

        question = item.get("question", "").replace('\n', ' ')
        answer = item.get("answer", "").replace('\n', ' ')

        q_num = qid.replace('Q', '').zfill(3)

        test_content += f"""    // QA: {qid}
    // Question: {question}
    // Answer: {answer}
    #[test]
    #[ignore = "Generated placeholder"]
    fn test_qa_{q_num}_placeholder() {{
        // TODO: Implement test for {qid}
        let db = load_real_db();
        let mut state = create_test_state();

        // 1. Setup State

        // 2. Perform Action

        // 3. Verify Result
        assert!(false, "Test not implemented yet");
    }}

"""

    test_content += "}\n"

    with open("engine_rust_src/src/qa_missing_tests.rs", "w", encoding="utf-8") as f:
        f.write(test_content)
    print(f"Generated engine_rust_src/src/qa_missing_tests.rs")

if __name__ == "__main__":
    generate_rust_tests()
