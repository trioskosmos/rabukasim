import json

def summarize_issues():
    with open('qa/text_issues_categorized.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open('qa/text_issues_summary.txt', 'w', encoding='utf-8') as f:
        for item in data:
            f.write(f"[{item['type']}] ({item['count']}) \"{item['text']}\"\n")
            if item['count'] > 1:
                f.write(f"   Example Cards: {', '.join(item['example_cards'][:3])}\n")
            f.write("\n")

if __name__ == "__main__":
    summarize_issues()
