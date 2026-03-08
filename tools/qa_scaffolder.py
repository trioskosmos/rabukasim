import json
import os
import sys
import re

def clean_text(text):
    if not text:
        return ""
    return text.strip()

def get_scaffold(qid):
    qa_data_path = r"data/qa_data.json"
    cards_path = r"data/cards.json"
    
    if not os.path.exists(qa_data_path):
        return f"Error: {qa_data_path} not found"
    if not os.path.exists(cards_path):
        return f"Error: {cards_path} not found"
        
    with open(qa_data_path, "r", encoding="utf-8") as f:
        qa_data = json.load(f)
        
    with open(cards_path, "r", encoding="utf-8") as f:
        cards_data = json.load(f)
        
    # Standardize QID (e.g., 195 -> Q195)
    if isinstance(qid, int) or qid.isdigit():
        qid = f"Q{qid}"
        
    target_qa = next((item for item in qa_data if item["id"].upper() == qid.upper()), None)
    
    if not target_qa:
        return f"Error: QA ID {qid} not found in {qa_data_path}"
    
    qid_num = re.search(r"\d+", target_qa["id"]).group()
    
    question = target_qa["question"]
    answer = target_qa["answer"]
    related_cards = target_qa.get("related_cards", [])
    
    card_info = []
    for rc in related_cards:
        card_no = rc["card_no"]
        card = cards_data.get(card_no)
        if card:
            ability = card.get("ability", "No ability text found.")
            card_info.append(f"        - {card_no} ({card['name']}): {ability}")
        else:
            card_info.append(f"        - {card_no}: [Card not found in database]")
            
    card_info_str = "\n".join(card_info)
    
    scaffold = f"""
    #[test]
    fn scaffold_q{qid_num}_todo() {{
        /*
        // PENDING QA: Q{qid_num}
        Question: {question}
        Answer: {answer}
        
        Card Abilities:
{card_info_str}
        */
        let db = load_real_db();
        let mut state = create_test_state();
        state.ui.silent = true; // Recommendation for tests
        
        // TODO: Implement verification logic for Q{qid_num}
        // Use db.id_by_no("CARD_NO") to get engine IDs
        
        panic!("Test skeleton for Q{qid_num} not implemented yet");
    }}
"""
    return scaffold

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/qa_scaffolder.py <QID>")
        sys.exit(1)
        
    # Ensure UTF-8 output even on Windows
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        
    qid_input = sys.argv[1]
    scaffold = get_scaffold(qid_input)
    
    # Automatically append to drafts.rs if it exists
    target_file = r"engine_rust_src/src/qa/drafts.rs"
    if os.path.exists(target_file):
        with open(target_file, "a", encoding="utf-8") as f:
            f.write("\n" + scaffold + "\n")
        print(f"Scaffold for {qid_input} appended to {target_file}")
    else:
        print(scaffold)
