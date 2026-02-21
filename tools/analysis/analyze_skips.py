import json
import re

with open("simplified_cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

unique_qas = {}
for card in cards:
    for qa in card.get("q_and_a", []):
        if qa["title"] not in unique_qas:
            unique_qas[qa["title"]] = qa

implemented_patterns = ["LIVE_END", "reduce_cost_hand", "hasta_X", "yes_can", "no_cant"]

skipped_qas = []
for title, qa in unique_qas.items():
    pcode = qa.get("pseudocode", "")
    answer = qa.get("answer", "")
    question = qa.get("question", "")

    # Check if our current generator would skip this
    skip = True
    if "RULING: TIMING" in pcode and "LIVE_END" in pcode:
        skip = False
    elif "RULING: COST" in pcode and "reduce" in pcode.lower() and "hand" in pcode.lower():
        skip = False
    elif "TARGETING" in pcode and "まで" in question:
        skip = False
    elif "RESOLUTION" in pcode and ("はい、できます" in answer or "使用できます" in answer or "効果を得ます" in answer):
        if "控え室" in question and ("ではない" not in question):
            skip = False
        else:
            skip = False  # Yes/No generic
    elif "RESOLUTION" in pcode and (
        "いいえ、できません" in answer or "いいえ、得ません" in answer or "攻撃できません" in answer
    ):
        skip = False
    elif "INTERACTION" in pcode and ("同じカード" in question or "同名" in question):
        skip = False
    elif "待機状態" in question or "ウェイト" in question or "参加状態" in question:
        skip = False
    elif "エール" in question and ("レスト" in question or "タップ" in question or "待機" in question):
        skip = False
    elif "以上" in question and ("回" in question or "枚" in question):
        skip = False
    elif "自分のステージ" in question and re.search(r"「([^「」]+?)」", question):
        skip = False
    elif "RULING: COST" in pcode and (
        "reduce" in pcode.lower() or "少なくなる" in question or "手札" in question and "少ない" in question
    ):
        skip = False
    elif (
        "SCORE_COMPARE" in pcode
        or "HEART_COMPARE" in pcode
        or ("スコア" in question or "ハート" in question)
        and "より多い" in question
    ):
        skip = False
    elif (
        "とはどのような状態ですか" in question
        or "とはいつのことですか" in question
        or "どのようなカードですか" in question
    ):
        skip = False
    elif "ライブできない" in question:
        skip = False
    elif "0人" in question or "いない場合" in question or "いない状況" in question:
        skip = False
    elif "名前" in question or "グループ名" in question or "ユニット名" in question:
        skip = False
    elif "コスト" in question or "必要ハート" in question or "ブレード" in question:
        skip = False
    elif (
        "数えますか" in question
        or "できますか" in question
        or "発動しますか" in question
        or "満たしますか" in question
        or "扱い" in question
        or "状態" in question
        or "どこ" in question
        or "どうなりますか" in question
    ):
        skip = False
    elif "少ない場合" in question or "枚数より少ない" in question:
        skip = False
    elif answer.startswith("はい") or answer.startswith("いいえ") or answer.startswith("可能です"):
        skip = False

    if skip:
        skipped_qas.append((title, pcode, question, answer))

print(f"Total Skips to Analyze: {len(skipped_qas)}")
for title, pcode, q, a in skipped_qas[:20]:
    print(f"--- {title} ---")
    print(f"PCODE: {pcode}")
    print(f"Q: {q[:100]}...")
    # print(f"A: {a[:100]}...")
