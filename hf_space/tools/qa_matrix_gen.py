import json
import os


def generate_matrix():
    path = "data/qa_data.json"
    if not os.path.exists(path):
        print(f"Error: {path} not found")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Sort by ID (numeric)
    data.sort(key=lambda x: int(x["id"].replace("Q", "")))

    matrix_file = "C:/Users/trios/.gemini/antigravity/brain/3184f098-63de-4eae-8ca5-1ec6244fd51d/qa_test_matrix.md"

    with open(matrix_file, "w", encoding="utf-8") as f:
        f.write("# Q&A Verification Matrix\n\n")
        f.write("This matrix tracks the testability and verification status of all official Q&A items.\n\n")
        f.write("| ID | Question Preview | Category | Status | Notes |\n")
        f.write("|---|---|---|---|---|\n")

        for item in data:
            qid = item["id"]
            question = item["question"].replace("\n", " ").strip()
            if len(question) > 60:
                question = question[:57] + "..."

            # Simple auto-categorization heuristic
            category = "Engine (Rule)"
            status = "[ ]"
            notes = ""

            if int(qid.replace("Q", "")) <= 15:
                category = "Tournament/Proc"
                status = "N/A"
            elif "スリーブ" in question or "シャッフル" in question:
                category = "Physical"
                status = "N/A"
            elif qid in ["Q166", "Q195", "Q206"]:
                status = "[x]"
                notes = "Verified"

            f.write(f"| {qid} | {question} | {category} | {status} | {notes} |\n")

        f.write("\n> [!NOTE]\n")
        f.write("> Status [x] indicates verified by Rust tests.\n")

    print(f"Matrix generated at {matrix_file}")


if __name__ == "__main__":
    generate_matrix()
