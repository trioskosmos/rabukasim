import requests
import json
import re
import time
from bs4 import BeautifulSoup

# Constants
BASE_URL = "https://llofficial-cardgame.com"
INITIAL_URL = f"{BASE_URL}/question/searchresults/?keyword=&keyword_type%5B%5D=all&search_type=and&title=&card_kind=&work_title="
EX_URL_TEMPLATE = f"{BASE_URL}/question/search_ex?keyword=&keyword_type%5B0%5D=all&search_type=and&title=&card_kind=&work_title=&page={{page}}&t={{timestamp}}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_text(element):
    """Helper to replace <img> tags with their alt text and clean whitespace."""
    if not element:
        return ""
    
    # Clone the element to avoid modifying the original soup
    import copy
    element_copy = copy.copy(element)
    
    # Replace all <img> tags with {{alt}}
    for img in element_copy.find_all("img"):
        alt = img.get("alt", "")
        # Try to match the format in cards.json: {{src|alt}}
        src = img.get("src", "").split("/")[-1]
        if alt:
            img.replace_with(f"{{{{{src}|{alt}}}}}")
        else:
            img.replace_with(f"{{{{{src}}}}}")
            
    text = element_copy.get_text(separator="\n", strip=True)
    
    # Remove repetitive sections split by ---------------------
    if "---------------------" in text:
        parts = text.split("---------------------")
        # Often the first part is a preview and the second is the full question
        # We want the combined context usually, but sometimes it repeats.
        # For now, let's keep it but clean up duplicates within the parts.
        text = "\n---\n".join(part.strip() for part in parts if part.strip())

    # Final cleanup of excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def parse_qa_item(item):
    """Parses a single Q&A item from BeautifulSoup object."""
    heading_el = item.find("h2", class_="faq-Heading")
    heading = heading_el.get_text(strip=True) if heading_el else ""
    
    # Match "Q206 (2025.12.17)"
    match = re.match(r"(Q\d+)\s*\((.*?)\)", heading)
    qa_id = match.group(1) if match else heading
    date = match.group(2) if match else ""
    
    question_el = item.find("p", class_="question-Detail")
    answer_el = item.find("p", class_="answer-Detail")
    
    question = clean_text(question_el)
    answer = clean_text(answer_el)
    
    related_cards = []
    relation_div = item.find("div", class_="relation-Detail")
    if relation_div:
        relation_text_el = relation_div.find("p", class_="relation-Text")
        if relation_text_el:
            relation_text = relation_text_el.get_text(strip=True)
            # Match [ID : Name]
            card_matches = re.findall(r"\[(.*?)\s*：\s*(.*?)\]", relation_text)
            for card_no, name in card_matches:
                related_cards.append({
                    "card_no": card_no.strip(),
                    "name": name.strip()
                })
            
    return {
        "id": qa_id,
        "date": date,
        "question": question,
        "answer": answer,
        "related_cards": related_cards
    }

def main():
    all_qa = []
    
    print(f"Fetching Page 1...")
    response = requests.get(INITIAL_URL, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch initial page: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Get max_page from script tag if possible
    # var max_page = 14;
    max_page = 14 # Default from analysis
    script_text = soup.find("script", text=re.compile("max_page"))
    if script_text:
        match = re.search(r"max_page\s*=\s*(\d+)", script_text.string)
        if match:
            max_page = int(match.group(1))
            print(f"Detected max_page: {max_page}")

    items = soup.find_all("div", class_="qa-Item")
    print(f"Found {len(items)} items on Page 1")
    for item in items:
        all_qa.append(parse_qa_item(item))
        
    for page in range(2, max_page + 1):
        print(f"Fetching Page {page}...")
        timestamp = int(time.time() * 1000)
        url = EX_URL_TEMPLATE.format(page=page, timestamp=timestamp)
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Failed to fetch Page {page}: {response.status_code}")
            continue
            
        # The search_ex endpoint returns raw HTML snippets of the items
        snippet_soup = BeautifulSoup(response.text, 'html.parser')
        items = snippet_soup.find_all("div", class_="qa-Item")
        print(f"Found {len(items)} items on Page {page}")
        for item in items:
            all_qa.append(parse_qa_item(item))
            
        time.sleep(1) # Be nice to the server
        
    # Sort by ID (numerical) descending
    try:
        all_qa.sort(key=lambda x: int(x['id'][1:]), reverse=True)
    except:
        pass
        
    output_path = "data/qa_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_qa, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully saved {len(all_qa)} items to {output_path}")

if __name__ == "__main__":
    main()
