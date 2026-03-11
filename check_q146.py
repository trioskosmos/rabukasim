import json

with open('data/qa_data.json', 'r', encoding='utf-8-sig') as f:
    qa_data = json.load(f)

# qa_data is a list
for qa in qa_data:
    if qa.get('id') == 'Q146':
        print(f"Q146: {qa.get('question')}")
        print(f"A146: {qa.get('answer')}")
        print(f"Full Q146: {json.dumps(qa, indent=2, ensure_ascii=False)}")
        break
