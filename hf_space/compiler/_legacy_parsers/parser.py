import re
from typing import List

from engine.models.ability import (
    Ability,
    AbilityCostType,
    Condition,
    ConditionType,
    Cost,
    Effect,
    EffectType,
    TargetType,
    TriggerType,
)


class AbilityParser:
    @staticmethod
    def parse_ability_text(text: str) -> List[Ability]:
        abilities = []

        # Split by newlines (blocks) - handle both literal and escaped newlines, and <br>

        text = text.replace("<br>", "\n")

        blocks = re.split(r"\\n|\n", text)

        last_ability = None

        for block in blocks:
            block = block.strip()

            if not block:
                continue

            # Split block into sentences. Standard Japanese uses '。' as period.

            # We split on '。' and optional space.

            sentences = [s.strip() for s in re.split(r"。\s*", block) if s.strip()]

            parenthesis_stack = 0

            for i, line in enumerate(sentences):
                line = line.strip()

                if not line:
                    continue

                if not line:
                    continue

                # Track parenthesis nesting across the block

                open_parens = line.count("（") + line.count("(")

                close_parens = line.count("）") + line.count(")")

                # Identify if this is a continuation of the previous ability

                starts_with_continuation = (
                    line.startswith("・")
                    or line.startswith("-")
                    or line.startswith("－")
                    or any(
                        line.startswith(kw)
                        for kw in [
                            "回答が",
                            "選んだ場合",
                            "条件が",
                            "それ以外",
                            "その",
                            "それら",
                            "残り",
                            "そし",
                            "その後",
                            "そこから",
                            "もよい",
                            "を自分",
                            "ライブ終了時まで",
                            "この能力",
                            "この効果",
                            "（",
                            "(",
                            "そうした場合",
                            # NOTE: Removed "この" as it's too aggressive - blocks valid first-sentence
                            # triggers like "このメンバーが登場したとき". More specific "この効果" and
                            # "この能力" cover the actual continuation cases.
                            "ただし",  # However
                            "かつ",  # And
                            "または",  # Or
                            "もしくは",
                            "および",
                            "代わりに",
                            "このメンバー",
                            "そのメンバー",
                            "選んだ",
                            "選んだエリア",
                            "」",
                            "）」",
                        ]
                    )
                )

                # Logic: If it starts with a continuation keyword OR we are currently inside an open parenthesis from previous sentence

                is_continuation = starts_with_continuation or (i > 0 and parenthesis_stack > 0)

                parenthesis_stack += open_parens - close_parens

                trigger = TriggerType.NONE

                if not is_continuation:
                    # --- Trigger Parsing ---

                    triggers = []

                    line_lower = line.lower()

                    # Robust Trigger Identification with Tiered Priority

                    # Tier 1: Explicit Icons (filenames) - Strongest

                    # Tier 2: Specific Phrases - Medium

                    # Tier 3: Generic Kanji - Weakest (prevent false positives from description text)

                    matches = []  # List of (index, priority, TriggerType)

                    # --- Tier 1: Icons ---

                    if "toujyou" in line_lower:
                        matches.append((line_lower.find("toujyou"), 1, TriggerType.ON_PLAY))

                    if "live_start" in line_lower:
                        matches.append((line_lower.find("live_start"), 1, TriggerType.ON_LIVE_START))

                    if "live_success" in line_lower:
                        # Special check for "only activates when"

                        has_only_activates_when = "この能力は" in line and "のみ発動する" in line and "公開" in line

                        if not has_only_activates_when:
                            matches.append((line_lower.find("live_success"), 1, TriggerType.ON_LIVE_SUCCESS))

                    # --- Tier 2: Specific Phrases ---

                    if "エールにより公開" in line or "エールで公開" in line:
                        matches.append((line.find("公開"), 2, TriggerType.ON_REVEAL))

                    # --- Tier 3: Kanji / Keywords ---

                    # Only add if not found via icon to avoid duplicates, or just add and let sorting handle it

                    if "登場" in line:
                        matches.append((line.find("登場"), 3, TriggerType.ON_PLAY))

                    if "ライブ開始" in line:
                        matches.append((line.find("ライブ開始"), 3, TriggerType.ON_LIVE_START))

                    if "ライブの開始" in line:
                        matches.append((line.find("ライブの開始"), 3, TriggerType.ON_LIVE_START))

                    if "ライブ成功" in line:
                        matches.append((line.find("ライブ成功"), 3, TriggerType.ON_LIVE_SUCCESS))

                    if "kidou" in line_lower:
                        matches.append((line_lower.find("kidou"), 1, TriggerType.ACTIVATED))

                    elif "起動" in line:
                        matches.append((line.find("起動"), 3, TriggerType.ACTIVATED))

                    if "jyouji" in line_lower:
                        matches.append((line_lower.find("jyouji"), 1, TriggerType.CONSTANT))

                    elif "常時" in line:
                        matches.append((line.find("常時"), 3, TriggerType.CONSTANT))

                    if "エールで出た" in line:
                        matches.append((line.find("エールで出た"), 2, TriggerType.CONSTANT))

                    if "jidou" in line_lower:
                        matches.append((line_lower.find("jidou"), 1, TriggerType.ON_LEAVES))

                    elif "自動" in line:
                        matches.append((line.find("自動"), 3, TriggerType.ON_LEAVES))

                    if "ターン開始" in line:
                        matches.append((line.find("ターン開始"), 3, TriggerType.TURN_START))

                    if "ターン終了" in line:
                        matches.append((line.find("ターン終了"), 3, TriggerType.TURN_END))

                    elif "live_end" in line_lower:
                        matches.append((line_lower.find("live_end"), 1, TriggerType.TURN_END))

                    elif "ライブ終了" in line:
                        matches.append((line.find("ライブ終了"), 3, TriggerType.TURN_END))

                    # Filter Logic

                    # 1. Look Ahead filtering (ignore "Has [Start] Ability")

                    valid_matches = []

                    for idx, tier, t_type in matches:
                        if idx == -1:
                            continue

                        look_ahead = line[idx : idx + 20]

                        if any(kw in look_ahead for kw in ["能力", "スキル", "を持つ", "を持たない", "がない"]):
                            continue

                        valid_matches.append((idx, tier, t_type))

                    if valid_matches:
                        # 2. Find best tier

                        best_tier = min(m[1] for m in valid_matches)

                        # 3. Filter to only matches of best tier

                        best_matches = [m for m in valid_matches if m[1] == best_tier]

                        # 4. Sort by index (Earliest Wins)

                        best_matches.sort(key=lambda x: x[0])

                        trigger = best_matches[0][2]

                        # Priority Override: Event Triggers > Constant (Refined)

                        # If we have ON_LIVE_SUCCESS/START/PLAY mixed with CONSTANT, prefer the Event Trigger

                        event_triggers = {
                            TriggerType.ON_LIVE_SUCCESS,
                            TriggerType.ON_LIVE_START,
                            TriggerType.ON_PLAY,
                            TriggerType.ON_REVEAL,
                            TriggerType.ON_LEAVES,
                            TriggerType.TURN_START,
                            TriggerType.TURN_END,
                        }

                        has_event = any(m[2] in event_triggers for m in best_matches)

                        has_constant = any(m[2] == TriggerType.CONSTANT for m in best_matches)

                        if has_event and has_constant:
                            # Pick the first event trigger

                            trigger = next(m[2] for m in best_matches if m[2] in event_triggers)

                    elif i == 0 and not is_continuation:
                        # Fallback for first sentence without icon: only if it contains action keywords

                        if any(
                            kw in line
                            for kw in [
                                "引",
                                "スコア",
                                "プラス",
                                "＋",
                                "ブレード",
                                "ハート",
                                "控",
                                "戻",
                                "エネ",
                                "デッキ",
                                "山札",
                                "見る",
                                "公開",
                                "選ぶ",
                                "選び",
                                "選ぶ。",
                            ]
                        ):
                            trigger = TriggerType.ACTIVATED

                conditions = []

                effects = []

                costs = []

                # --- Split into Cost and effect early to find colon index ---

                full_content = re.sub(r"（.*?）|\(.*?\)", "", line)

                colon_idx = full_content.find("：")

                if colon_idx == -1:
                    colon_idx = full_content.find(":")

                cost_part = full_content[:colon_idx] if colon_idx != -1 else None

                content = full_content  # Use full content for condition parsing initially

                # We will truncate 'content' later specifically for effects.

                # --- Once per turn ---

                is_once_per_turn = any(
                    kw in line
                    for kw in [
                        "1ターンに1回",
                        "ターン終了時まで1回",
                        "に限る",
                        "ターン1回",
                        "［ターン1回］",
                        "【ターン1回】",
                    ]
                )

                if "[Turn 1]" in line or "ターン1" in line:
                    conditions.append(Condition(ConditionType.TURN_1, {"turn": 1}))

                # --- Zone Context ---

                context_zone = None

                zone_map = {
                    "右サイドエリア": "RIGHT_STAGE",
                    "左サイドエリア": "LEFT_STAGE",
                    "センターエリア": "CENTER_STAGE",
                    "成功ライブカード置き場": "SUCCESS_LIVE",
                    "ライブ成功カード置き場": "SUCCESS_LIVE",
                    "ライブ成功": "SUCCESS_LIVE",
                    "エネルギー置き場": "ENERGY",
                    "エネルギーデッキ": "ENERGY_DECK",
                    "ライブカード置き場": "LIVE_ZONE",
                    "ライブエリア": "LIVE_AREA",
                    "控え室": "DISCARD",
                    "手札": "HAND",
                    "ステージ": "STAGE",
                    "山札": "DECK",
                    "デッキ": "DECK",
                    "ライブ中": "LIVE_ZONE",
                }

                # Enhanced zone detection with keyword proximity

                best_zone_idx = -1

                for keyword, zone_id in zone_map.items():
                    idx = content.find(keyword)

                    if idx != -1:
                        if best_zone_idx == -1 or idx < best_zone_idx:
                            best_zone_idx = idx

                            context_zone = zone_id

                if context_zone:
                    # Look for "相手" (opponent) near the zone keyword

                    # "相手のセンターエリア" vs "自分のセンターエリア"

                    prefix_text = content[max(0, best_zone_idx - 8) : best_zone_idx]

                    if "相手" in prefix_text:
                        context_zone = "OPPONENT_" + context_zone

                    elif "自分" in prefix_text:
                        # Explicitly yours, keep as is

                        pass

                    elif "相手" in content and best_zone_idx > content.find("相手"):
                        # Fallback: if opponent is mentioned before the zone keyword

                        context_zone = "OPPONENT_" + context_zone

                # Success Live Count: 成功ライブカード置き場にカードがX枚以上ある場合

                if "成功ライブカード置き場" in content and "枚以上" in content:
                    match = re.search(r"(\d+)枚以上", content)

                    if match:
                        conditions.append(Condition(ConditionType.COUNT_SUCCESS_LIVE, {"min": int(match.group(1))}))

                # Live Zone Count: ライブ中のカードがX枚以上ある場合

                if "ライブ中のカード" in content and "枚以上" in content:
                    match = re.search(r"(\d+)枚以上", content)

                    if match:
                        conditions.append(Condition(ConditionType.COUNT_LIVE_ZONE, {"min": int(match.group(1))}))

                # Heart Comparison (Opponent)

                if "ハートの総数" in content and "相手" in content and any(kw in content for kw in ["多い", "少ない"]):
                    comp = "GT" if "多い" in content else "LT"

                    conditions.append(
                        Condition(
                            ConditionType.SCORE_COMPARE, {"comparison": comp, "target": "opponent", "type": "heart"}
                        )
                    )

                # Cheer Count Comparison (Opponent)

                if "エール" in content and "枚数" in content and "相手" in content:
                    conditions.append(
                        Condition(ConditionType.SCORE_COMPARE, {"target": "opponent", "type": "cheer_count"})
                    )

                # Heart Inclusion (Specific Colors)

                if "ハートの中に" in content and "がある場合" in content:
                    conditions.append(
                        Condition(
                            ConditionType.HAS_KEYWORD, {"keyword": "Specific Heart", "context": "heart_inclusion"}
                        )
                    )

                # Opponent Hand Diff: 相手の手札の枚数が自分よりX枚以上多い場合

                if match := re.search(r"相手の手札の枚数が自分より(\d+)枚以上多い場合", content):
                    conditions.append(Condition(ConditionType.OPPONENT_HAND_DIFF, {"diff": int(match.group(1))}))

                # Opponent Energy Diff: 相手のエネルギーが自分よりX枚以上多い場合 or just 多い場合

                if match := re.search(r"相手のエネルギーが自分より(\d+)枚以上多い場合", content):
                    conditions.append(Condition(ConditionType.OPPONENT_ENERGY_DIFF, {"diff": int(match.group(1))}))

                elif "相手のエネルギーが自分より多い場合" in content:
                    conditions.append(Condition(ConditionType.OPPONENT_ENERGY_DIFF, {"diff": 1}))

                # ALL Blade Rule (Meta Rule)

                if "ALLブレード" in content and any(
                    kw in content for kw in ["ハートとして扱う", "ハートとして内容を確認", "いずれかの色のハート"]
                ):
                    trigger = TriggerType.CONSTANT

                    effects.append(
                        Effect(EffectType.META_RULE, target=TargetType.PLAYER, params={"type": "heart_rule"})
                    )

                # --- Condition Parsing ---

                # Detect group filters early for propagation

                sentence_groups = re.findall(r"『(.*?)』", content)

                # Issue Gap-1: Has Moved (Standalone check - must be separate to capture alongside group conditions)

                if "移動している場合" in content:
                    if not any(c.type == ConditionType.HAS_MOVED for c in conditions):
                        conditions.append(Condition(ConditionType.HAS_MOVED))

                # Group count

                if match := re.search(r"『(.*?)』.*?(\d+)(枚|人)以上", content):
                    params = {"group": match.group(1), "min": int(match.group(2))}

                    if context_zone:
                        params["zone"] = context_zone

                    conditions.append(Condition(ConditionType.COUNT_GROUP, params))

                # Issue 541: Opponent Hand > Self

                elif match := re.search(
                    r"相手の手札(の枚数)?が自分(の手札)?より(多い|少ない|(\d+)枚以上多い)", content
                ):
                    diff = 1

                    comp = "GT" if "多い" in content else "LT"

                    if match.group(4):
                        diff = int(match.group(4))

                    conditions.append(Condition(ConditionType.OPPONENT_HAND_DIFF, {"diff": diff, "comparison": comp}))

                # Issue 177: Hand Increased

                elif match := re.search(r"このターンに自分の手札が(\d+)枚以上増えている", content):
                    conditions.append(Condition(ConditionType.HAND_INCREASED, {"min": int(match.group(1))}))

                # Issue 541: Opponent Hand > Self (Enhanced - separate to avoid overlap)

                elif match := re.search(r"相手の手札(?:の枚数)?が自分(?:の手札)?より(\d+)枚以上多い場合", content):
                    if not any(c.type == ConditionType.OPPONENT_HAND_DIFF for c in conditions):
                        conditions.append(
                            Condition(
                                ConditionType.OPPONENT_HAND_DIFF, {"diff": int(match.group(1)), "comparison": "GE"}
                            )
                        )

                # Issue 269: Live Zone Group Check (Zone count part)

                elif (
                    context_zone
                    and context_zone != "SUCCESS_LIVE"
                    and (match := re.search(r"(\d+)(枚|人)以上", content))
                ):
                    params = {"count": int(match.group(1)), "zone": context_zone}

                    conditions.append(
                        Condition(
                            ConditionType.COUNT_DISCARD if context_zone == "DISCARD" else ConditionType.COUNT_STAGE,
                            params,
                        )
                    )

                # Issue 558: Energy Count Check (Moved Up)

                if match := re.search(r"エネルギーが(\d+)枚以上", content):
                    conditions.append(Condition(ConditionType.COUNT_ENERGY, {"min": int(match.group(1))}))

                # Generic count (STAGE fallback)

                if (
                    (match := re.search(r"(\d+)枚以上ある場合", content))
                    and not conditions
                    and "エネルギー" not in content
                ):
                    params = {"min": int(match.group(1))}

                    if context_zone:
                        params["zone"] = context_zone

                    conditions.append(Condition(ConditionType.COUNT_STAGE, params))

                # "If all are X"

                if match := re.search(r"(?:それらが|カードが)?すべて(.*?)の場合", content):
                    conditions.append(
                        Condition(ConditionType.GROUP_FILTER, {"group": match.group(1).strip(), "context": "revealed"})
                    )

                # Group filter 『...』

                for g in sentence_groups:
                    if not any(c.type == ConditionType.COUNT_GROUP and c.params.get("group") == g for c in conditions):
                        params = {"group": g}

                        if "名前の異なる" in content:
                            params["distinct_names"] = True

                        if context_zone:
                            params["zone"] = context_zone

                        if match := re.search(rf"『{re.escape(g)}』.*?(\d+)(人|枚)以上", content):
                            params["count"] = int(match.group(1))

                            conditions.append(Condition(ConditionType.COUNT_GROUP, params))

                        elif any(
                            kw in content
                            for kw in ["場合", "なら", "に限る", "ないかぎり", "のメンバーがいる", "がいるとき"]
                        ):
                            if "ほかの" in content or "他の" in content:
                                params["exclude_self"] = True

                            conditions.append(Condition(ConditionType.GROUP_FILTER, params))

                        # Issue 269: "その中に『...』がある場合" (referencing previous zone check)

                        elif "その中に" in content and "がある場合" in content:
                            params = {
                                "group": g,
                                "context": "live_zone"
                                if "ライブ中" in content
                                or "live" in content
                                or any(
                                    c.type == ConditionType.COUNT_STAGE and c.params.get("zone") == "LIVE_ZONE"
                                    for c in conditions
                                )
                                else "stage",
                            }

                            conditions.append(Condition(ConditionType.GROUP_FILTER, params))

                # Specific Member names 「...」

                if any(kw in content for kw in ["がある場合", "がいる場合", "登場している場合"]):
                    found_names = set()

                    for area_name, member_name in re.findall(r"([左中右センター].*?エリア)に「(.*?)」", content):
                        area_id = (
                            "LEFT_STAGE"
                            if "左" in area_name
                            else "RIGHT_STAGE"
                            if "右" in area_name
                            else "CENTER_STAGE"
                        )

                        conditions.append(
                            Condition(ConditionType.HAS_MEMBER, {"name": member_name, "area": area_id, "zone": "STAGE"})
                        )

                        found_names.add(member_name)

                    for n in re.findall(r"「(.*?)」", content):
                        if n not in found_names:
                            params = {"name": n}

                            if context_zone:
                                params["zone"] = context_zone

                            conditions.append(Condition(ConditionType.HAS_MEMBER, params))

                # Negation

                if any(kw in content for kw in ["以外", "でない場合", "ではない場合"]) and conditions:
                    conditions[-1].is_negated = True

                # Center Area specific

                if "センターエリア" in content and "場合" in content:
                    if not any(c.type == ConditionType.IS_CENTER for c in conditions):
                        conditions.append(Condition(ConditionType.IS_CENTER))

                # Multiplier Factor (1枚につき... / 人につき...)

                if match := re.search(r"(?:(\d+)枚|(\d+)人)につき", content):
                    mult = int(match.group(1) or match.group(2))

                    # Propagate to future effects in this sentence

                    current_multiplier = mult

                else:
                    current_multiplier = None

                # center, life lead, score lead, opponent has, modal answer

                if (
                    "センターエリア" in content
                    and "場合" in content
                    and not any(c.params.get("area") == "CENTER_STAGE" for c in conditions)
                ):
                    conditions.append(Condition(ConditionType.IS_CENTER))

                if any(kw in content for kw in ["ライフが相手より多い", "ライフが相手より少ない"]):
                    conditions.append(Condition(ConditionType.LIFE_LEAD))

                if "ブレードハートを持つ" in content:
                    conditions.append(Condition(ConditionType.HAS_KEYWORD, {"keyword": "Blade Heart"}))

                # Score/Cost Interaction/Comparison (Enhanced)

                if any(kw in content for kw in ["スコア", "ライブの合計", "コストの合計", "コスト"]):
                    # print(f"DEBUG: Found score/cost keyword in {content}")

                    if any(
                        re.search(p, content)
                        for p in [
                            r"相手.*?より高い",
                            r"相手.*?同じか高い",
                            r"自分.*?同じか高い",
                            r"相手.*?より低い",
                            r"相手.*?同じか低い",
                            r"自分.*?同じか低い",
                            r"相手.*?より多い",
                            r"相手.*?同じか多い",
                            r"自分.*?同じか多い",
                            r"相手.*?より少ない",
                            r"相手.*?同じか少ない",
                            r"自分.*?同じか少ない",
                            r"相手.*?と同じ",
                            r"自分.*?と同じ",
                            r"相手.*?より高く",
                            r"相手.*?より低く",
                        ]
                    ):
                        comp = (
                            "GE"
                            if re.search(r"同じか高い|以上|高ければ", content)
                            else "LE"
                            if re.search(r"同じか低い|以下|低ければ", content)
                            else "GT"
                            if re.search(r"高い|高く|多い", content)
                            else "LT"
                            if re.search(r"低い|低く|少ない", content)
                            else "EQ"
                        )

                        # Prioritize score if both are present but score is closer to comparison

                        if "スコア" in content and "コスト" in content:
                            ctype = (
                                "score" if re.search(r"スコア.*?同じ|スコア.*?高い|スコア.*?低い", content) else "cost"
                            )

                        else:
                            ctype = "cost" if "コスト" in content else "score"

                        # print(f"DEBUG: Added SCORE_COMPARE {ctype} {comp}")

                        params = {"comparison": comp, "target": "opponent", "type": ctype}

                        if context_zone:
                            params["zone"] = context_zone

                        conditions.append(Condition(ConditionType.SCORE_COMPARE, params))

                    elif match := re.search(
                        r"(?:スコア|コスト)(?:が|の合計が|の合計|の数)?.*?(\d+|１|２|３|４|５|６|７|８|９|０|[一二三四五六七八九〇])(つ|個|枚|人)?(以上|以下)",
                        content,
                    ):
                        val_str = match.group(1)

                        val_map = {
                            "１": 1,
                            "２": 2,
                            "３": 3,
                            "４": 4,
                            "５": 5,
                            "６": 6,
                            "７": 7,
                            "８": 8,
                            "９": 9,
                            "０": 0,
                            "一": 1,
                            "二": 2,
                            "三": 3,
                            "四": 4,
                            "五": 5,
                            "六": 6,
                            "七": 7,
                            "八": 8,
                            "九": 9,
                            "〇": 0,
                        }

                        val = int(val_map.get(val_str, val_str)) if not val_str.isdigit() else int(val_str)

                        ctype = "cost" if "コスト" in content else "score"

                        conditions.append(
                            Condition(
                                ConditionType.SCORE_COMPARE,
                                {"comparison": "GE" if match.group(3) == "以上" else "LE", "value": val, "type": ctype},
                            )
                        )

                    elif "同じ場合" in content or "スコアが同じ" in content:
                        conditions.append(
                            Condition(ConditionType.SCORE_COMPARE, {"comparison": "EQ", "target": "opponent"})
                        )

                if "相手" in content and any(kw in content for kw in ["ある場合", "いる場合", "のとき"]):
                    conditions.append(Condition(ConditionType.OPPONENT_HAS))

                is_modal_answer_branch = False

                if match := re.search(r"回答が(.*?)の場合", content):
                    is_modal_answer_branch = True

                    # Do not add condition, instead we treat this as a branch for SELECT_MODE

                # Opponent Choice Detection (opponent makes a decision)

                if "相手" in content and any(kw in content for kw in ["選ぶ", "選び", "選んで"]):
                    conditions.append(Condition(ConditionType.OPPONENT_CHOICE, {"type": "select"}))

                elif "相手" in content and "控え室に置いてもよい" in content:
                    conditions.append(Condition(ConditionType.OPPONENT_CHOICE, {"type": "discard_optional"}))

                elif "相手" in content and any(kw in content for kw in ["手札から", "捨てる", "選ばせる"]):
                    conditions.append(Condition(ConditionType.OPPONENT_CHOICE, {"type": "discard"}))

                # Enhanced Choice Detection (player chooses)

                choice_patterns = [
                    r"1つを選ぶ",
                    r"のうち.*?選ぶ",
                    r"どちらか.*?選ぶ",
                    r"選んでもよい",
                    r"好きな.*?選",
                    r"以下から.*?選ぶ",
                    r"か.*?か.*?のうち",
                    r"[一二三123]つを選ぶ",
                    r"メンバー(\d+)人を?選ぶ",
                    r"を(\d+)枚選ぶ",
                ]

                if any(re.search(p, content) for p in choice_patterns):
                    conditions.append(Condition(ConditionType.HAS_CHOICE))

                elif "1枚選ぶ" in content and any(kw in content for kw in ["控え室", "登場", "デッキ", "山札"]):
                    conditions.append(Condition(ConditionType.HAS_CHOICE))

                # Cost/Blade filter: コスト(\d+)(以下|以上), ブレード(の数)?が(\d+)(以下|以上)

                if match := re.search(
                    r"(?:コスト|ブレード(?:の数)?)(?:が)?.*?(\d+|１|２|３|４|５|６|７|８|９|０|[一二三四五六七八九〇])(つ|個|枚|人)?(以下|以上)",
                    content,
                ):
                    val_str = match.group(1)

                    val_map = {
                        "１": 1,
                        "２": 2,
                        "３": 3,
                        "４": 4,
                        "５": 5,
                        "６": 6,
                        "７": 7,
                        "８": 8,
                        "９": 9,
                        "０": 0,
                        "一": 1,
                        "二": 2,
                        "三": 3,
                        "四": 4,
                        "五": 5,
                        "六": 6,
                        "七": 7,
                        "八": 8,
                        "九": 9,
                        "〇": 0,
                    }

                    val = int(val_map.get(val_str, val_str)) if not val_str.isdigit() else int(val_str)

                    ctype = "blade" if "ブレード" in content else "cost"

                    conditions.append(
                        Condition(
                            ConditionType.COST_CHECK if ctype == "cost" else ConditionType.COUNT_BLADES,
                            {
                                "value" if ctype == "cost" else "min": val,
                                "comparison": "LE" if match.group(3) == "以下" else "GE",
                            },
                        )
                    )

                if "余剰ハート" in content:
                    is_neg = any(kw in content for kw in ["持たない", "ない場合", "でない場合"])

                    params = {"context": "excess"}

                    if is_neg:
                        params["min"] = 1

                    conditions.append(Condition(ConditionType.COUNT_HEARTS, params, is_negated=is_neg))

                if "デッキの上から" in content and "公開" in content:
                    context_zone = "DECK"

                # --- Split content for effect parsing ---

                if colon_idx != -1:
                    content = content[colon_idx + 1 :]

                if cost_part:
                    cost_is_optional = any(kw in cost_part for kw in ["もよい", "支払うことで", "支払えば"])

                    if "このメンバーをウェイトにし" in cost_part or "このメンバーをウェイトにする" in cost_part:
                        costs.append(Cost(AbilityCostType.TAP_SELF, is_optional=cost_is_optional))
                    elif "相手" in cost_part and "ウェイト" in cost_part:
                        costs.append(
                            Cost(
                                AbilityCostType.TAP_MEMBER,
                                1,
                                params={"target": "opponent"},
                                is_optional=cost_is_optional,
                            )
                        )

                    # Discard Hand Cost
                    if any(kw in cost_part for kw in ["控え室に置", "捨て"]) and "手札" in cost_part:
                        count_discard = 1
                        if match := re.search(r"(\d+)枚", cost_part):
                            count_discard = int(match.group(1))
                        elif "すべて" in cost_part or "全て" in cost_part:
                            count_discard = 99
                        costs.append(Cost(AbilityCostType.DISCARD_HAND, count_discard, is_optional=cost_is_optional))

                    if "手札をすべて公開する" in cost_part:
                        costs.append(Cost(AbilityCostType.REVEAL_HAND_ALL, is_optional=cost_is_optional))

                    if "このメンバー" in cost_part and ("控え室に置" in cost_part or "捨て" in cost_part):
                        costs.append(Cost(AbilityCostType.SACRIFICE_SELF, is_optional=cost_is_optional))

                    if "下に置かれているカードを" in cost_part and "控え室に置く" in cost_part:
                        costs.append(Cost(AbilityCostType.SACRIFICE_UNDER, is_optional=cost_is_optional))

                    if "エネルギーを" in cost_part and "控え室に置く" in cost_part:
                        costs.append(Cost(AbilityCostType.DISCARD_ENERGY, 1, is_optional=cost_is_optional))

                    if "手札に戻す" in cost_part and "このメンバー" in cost_part:
                        costs.append(Cost(AbilityCostType.RETURN_HAND, is_optional=cost_is_optional))

                    # Parse "Return Discard to Deck" cost
                    if (
                        "控え室" in cost_part
                        and ("デッキ" in cost_part or "山札" in cost_part)
                        and ("下に置" in cost_part or "戻" in cost_part)
                    ):
                        cost_type = AbilityCostType.RETURN_DISCARD_TO_DECK
                        if "ライブカード" in cost_part:
                            cost_type = (
                                AbilityCostType.RETURN_LIVE_TO_DECK
                            )  # Or Discard with filter? Using 29 for now as it maps semantically
                        elif "メンバー" in cost_part:
                            cost_type = AbilityCostType.RETURN_MEMBER_TO_DECK

                        count_deck = 1
                        if match := re.search(r"(\d+)枚", cost_part):
                            count_deck = int(match.group(1))
                        costs.append(Cost(cost_type, count_deck, is_optional=cost_is_optional))

                    # Generic Tap Member Cost (e.g. choose other member to tap)
                    if "ウェイト" in cost_part and "このメンバー" not in cost_part and "相手" not in cost_part:
                        count_tap = 1
                        if match := re.search(r"(\d+)枚|(\d+)人", cost_part):
                            count_tap = int(match.group(1) or match.group(2))
                        costs.append(Cost(AbilityCostType.TAP_MEMBER, count_tap, is_optional=cost_is_optional))

                    if energy_icons := len(re.findall(r"\{\{icon_energy.*?\}\}", cost_part)):
                        costs.append(Cost(AbilityCostType.ENERGY, energy_icons, is_optional=cost_is_optional))

                # Checks that can look at full content but result in Conditions/Costs

                # (COUNT_ENERGY check moved up to line 266 region)

                # Live card present condition: ライブカードがある場合

                if "ライブカードがある場合" in content:
                    conditions.append(Condition(ConditionType.HAS_LIVE_CARD))

                # Hand check: 公開した手札の中にライブカードがない場合

                if "公開した手札" in content and "ライブカードがない" in content:
                    conditions.append(Condition(ConditionType.HAND_HAS_NO_LIVE))

                # --- Effect Parsing ---

                # Gap Closure 2: Flavor Action (e.g. 何が好き？と聞く)

                if "何が好き？" in content or "何が好き" in content:
                    effects.append(Effect(EffectType.FLAVOR_ACTION, params={"question": "What do you like?"}))

                # Gap Closure 3: Set Blades (e.g. 元々持つ...数は3つになる)

                if match := re.search(
                    r"元々持つ(?:{{icon_blade.png\|ブレード}}|ブレード)(?:の数)?は(\d+)つになる", content
                ):
                    effects.append(Effect(EffectType.SET_BLADES, int(match.group(1))))

                # Gap Closure 1: Draw per Energy (e.g. エネルギー6枚につき、カードを1枚引く)

                if "エネルギー" in content and "につき" in content and "引く" in content:
                    match = re.search(r"エネルギー(\d+)枚につき.*?(\d+)枚", content)

                    req = int(match.group(1)) if match else 1

                    draw_amt = int(match.group(2)) if match else 1

                    effects.append(
                        Effect(EffectType.DRAW, draw_amt, params={"multiplier": "energy", "req_per_unit": req})
                    )

                    # Consumed '枚' and '引く', so prevent generic parsing below

                    content = content.replace("枚", "").replace("引く", "").replace("につき", "")

                # Gap Closure 2: Re-Cheer / Lose Blade Heart (e.g. ブレードハートを失い、もう一度エールを行う)

                if "ブレードハート" in content and "失い" in content:
                    effects.append(Effect(EffectType.META_RULE, 1, params={"type": "lose_blade_heart"}))

                if "もう一度エール" in content:
                    effects.append(Effect(EffectType.META_RULE, 1, params={"type": "re_cheer"}))

                # Gap Closure 3: Deck Refresh Condition (e.g. デッキがリフレッシュしていた場合)

                if "デッキ" in content and "リフレッシュ" in content:
                    conditions.append(Condition(ConditionType.DECK_REFRESHED, {}))

                # Gap Closure 4: Cheer Count Modifier (e.g. エールによって公開される...枚数が...減る)

                if "公開" in content and "枚数" in content and ("減る" in content or "増える" in content):
                    match = re.search(r"(\d+)枚(減る|増える)", content)

                    val = int(match.group(1)) if match else 0

                    if "減る" in content:
                        val = -val

                    effects.append(Effect(EffectType.META_RULE, val, params={"type": "cheer_mod"}))

                # Flavor Actions (Questions)

                if "?" in content and any(kw in content for kw in ["聞く", "質問"]):
                    effects.append(Effect(EffectType.FLAVOR_ACTION, 1))

                # Gap Closure 5: Heart Req Increase/Decrease (多くなる/少なくなる)

                if "必要ハート" in content and ("多くなる" in content or "少なくなる" in content):
                    # Usually "heart0多くなる" -> +1? Or just "多くなる" = +1 default

                    val = 1

                    if "少なくなる" in content:
                        val = -1

                    target = TargetType.OPPONENT if "相手" in content else TargetType.PLAYER

                    effects.append(Effect(EffectType.REDUCE_HEART_REQ, val, target=target))

                # Gap Closure 6: Score Limit Filter (e.g. スコア3以下の)

                score_filter = None

                if "スコア" in content and "以下" in content:
                    if match := re.search(r"スコア(\d+)以下", content):
                        score_filter = int(match.group(1))

                # Refined DRAW: Prioritize "カードをX枚" to avoid catching condition values (e.g. Energy 7)

                # Also exclude "引き入れる" which means "bring in/under" not "draw"

                if "引き入れ" not in content:  # Exclude "bring in under" pattern
                    if match := re.search(r"カードを\s*(\d+)枚[^。]*?引", content):
                        effects.append(
                            Effect(EffectType.DRAW, int(match.group(1)), TargetType.PLAYER, params={"from": "deck"})
                        )

                    elif match := re.search(r"(\d+)枚[^。]*?引", content):
                        # Check if the number before "枚" isn't part of a known condition like "Energy X"

                        is_valid_draw = True

                        if "エネルギー" in content:
                            # If energy count is right before 枚, it's likely the energy count, not draw count

                            if re.search(rf"エネルギー\s*{match.group(1)}枚", content):
                                is_valid_draw = False

                        if is_valid_draw:
                            effects.append(
                                Effect(EffectType.DRAW, int(match.group(1)), TargetType.PLAYER, params={"from": "deck"})
                            )

                    elif "引く" in content and "置いた枚数分" not in content:
                        effects.append(Effect(EffectType.DRAW, 1, TargetType.PLAYER, params={"from": "deck"}))

                # --- Discard up to X, Draw X (SELECT_MODE) ---

                if match := re.search(r"手札を(\d+)枚まで控え室に置いてもよい.*?置いた枚数分カードを引く", line):
                    max_discard = int(match.group(1))

                    # Create Modal Options for 0 to Max

                    modal_options = []

                    # Option 0: Do nothing

                    modal_options.append(
                        [Effect(EffectType.META_RULE, 0, TargetType.PLAYER, params={"message": "キャンセル (0枚)"})]
                    )

                    for i in range(1, max_discard + 1):
                        opts = []

                        # Discard i cards (Using SWAP_CARDS 11 logic or DISCARD effect if available)

                        # Based on effect_mixin, usually DISCARD is a COST.

                        # But here it's an effect choice.

                        # Using EffectType.SWAP_CARDS (11) as observed in other cards

                        opts.append(
                            Effect(
                                EffectType.SWAP_CARDS,
                                i,
                                TargetType.CARD_HAND,
                                params={"target": "discard", "from": "hand", "count": i},
                            )
                        )

                        # Draw i cards

                        opts.append(Effect(EffectType.DRAW, i, TargetType.PLAYER))

                        modal_options.append(opts)

                    effects.append(Effect(EffectType.SELECT_MODE, 1, TargetType.PLAYER, modal_options=modal_options))

                    # Construct Ability immediately and stop processing to avoid phantom effects

                    abilities.append(
                        Ability(
                            raw_text=line.strip(),
                            trigger=trigger,
                            effects=effects,
                            conditions=conditions,
                            costs=costs,
                            is_once_per_turn=is_once_per_turn,
                        )
                    )

                    continue

                # DEBUG: Trace LOOK_DECK check
                if "見る" in content or "デッキ" in content:
                    print(f"DEBUG: Checking LOOK_DECK on: '{content}'")

                if match := re.search(r"(?:デッキ|山札).*?(\d+)枚.*?(?:見る|見て)", content):
                    print(f"DEBUG: MATCHED LOOK_DECK! Count={match.group(1)}")
                    effects.append(Effect(EffectType.LOOK_DECK, int(match.group(1))))

                has_look_and_choose = False

                if any(kw in content for kw in ["その中から", "その中"]):
                    params = {"source": "looked"}

                    # Capture filters for choice

                    if match := re.search(r"『(.*?)』", content):
                        params["group"] = match.group(1)

                    if match := re.search(r"コスト(\d+)以下", content):
                        params["cost_max"] = int(match.group(1))

                    if "ライブカード" in content:
                        params["filter"] = "live"

                    elif "メンバー" in content:
                        params["filter"] = "member"

                    if "控え室に置く" in content or "残りを控え室" in content:
                        params["on_fail"] = "discard"

                    # "好きな枚数を好きな順番でデッキの上に置き" = Put any number on top in any order

                    if (
                        "好きな枚数" in content
                        and any(kw in content for kw in ["デッキの上", "山札の上"])
                        and any(kw in content for kw in ["置", "戻"])
                    ):
                        params["destination"] = "deck_top"

                        params["any_number"] = True

                        params["reorder"] = True

                    # Extract look count

                    if match := re.search(r"(\d+)枚.*?見て", content):
                        effects.append(Effect(EffectType.LOOK_DECK, int(match.group(1))))

                    effects.append(Effect(EffectType.LOOK_AND_CHOOSE, 1, params=params))

                    has_look_and_choose = True

                if match := re.search(r"(\d+)枚.*?公開", content):
                    if not has_look_and_choose:
                        params = {}

                        if "デッキ" in content:
                            params["from"] = "deck"

                        effects.append(Effect(EffectType.REVEAL_CARDS, int(match.group(1)), params=params))

                elif "公開" in content and "エール" not in content:
                    if not has_look_and_choose:
                        params = {}

                        if "デッキ" in content:
                            params["from"] = "deck"

                        effects.append(Effect(EffectType.REVEAL_CARDS, 1, params=params))

                # Optionality

                if "てもよい" in content and effects:
                    effects[-1].is_optional = True

                # Recovery/Add

                if "控え室" in content and ("手札に加え" in content or "手札に戻" in content):
                    filters = {}

                    if match := re.search(r"コスト(\d+)以下", content):
                        filters["cost_max"] = int(match.group(1))

                    if score_filter:
                        filters["score_max"] = score_filter

                    eff_type = EffectType.RECOVER_LIVE if "ライブカード" in content else EffectType.RECOVER_MEMBER

                    # Ensure it's not a live card if "member card" is specified

                    if "メンバーカード" in content:
                        eff_type = EffectType.RECOVER_MEMBER

                    # Explicitly set from zone to discard - overrides any context_zone
                    from_zone = "opponent_discard" if "相手" in content else "discard"
                    effects.append(
                        Effect(
                            eff_type, 1, TargetType.CARD_DISCARD, params={"to": "hand", "from": from_zone, **filters}
                        )
                    )

                    if any(kw in content for kw in ["ハート", "heart"]):
                        effects[-1].params["filter"] = "heart_req"

                    # Capture specific group filter if explicitly mentioned near recover target

                    if match := re.search(r"『(.*?)』", content):
                        effects[-1].params["group"] = match.group(1)

                    # Check for ability filter (e.g. "「アクティブにする」を持つ")
                    if "アクティブにする" in content or "【起動】" in content:
                        effects[-1].params["has_ability"] = "active"

                elif "手札に加え" in content and not any(
                    e.effect_type in (EffectType.RECOVER_LIVE, EffectType.RECOVER_MEMBER) for e in effects
                ):
                    # Skip if LOOK_AND_CHOOSE already covers the "add to hand" semantic

                    has_look_and_choose = any(e.effect_type == EffectType.LOOK_AND_CHOOSE for e in effects)

                    if not has_look_and_choose:
                        params = {"to": "hand"}

                        if any(kw in content for kw in ["デッキ", "山札"]):
                            params["from"] = "deck"

                        elif "成功ライブカード" in content:
                            params["from"] = "success_live"

                        elif "ライブカード置き場" in content:
                            params["from"] = "live_zone"

                        elif "控え室" in content:
                            params["from"] = (
                                "opponent_discard" if "相手" in content and "自身" in content else "discard"
                            )

                        elif "自身" in content and "控え室" in content:
                            params["from"] = "discard"

                        # Filter extraction

                        if "アクティブにする" in content or "【起動】" in content:
                            params["has_ability"] = "active"

                        if "ライブカード" in content:
                            effects.append(Effect(EffectType.RECOVER_LIVE, 1, params=params))

                        else:
                            if match := re.search(r"コスト(\d+)以下", content):
                                params["cost_max"] = int(match.group(1))

                            if score_filter:
                                params["score_max"] = score_filter

                            effects.append(Effect(EffectType.ADD_TO_HAND, 1, params=params))

                if any(kw in content for kw in ["エールにより公開", "エールで公開"]) and not any(
                    kw in content for kw in ["場合", "なら", "とき"]
                ):
                    effects.append(Effect(EffectType.CHEER_REVEAL, 1))

                if "デッキ" in content and any(kw in content for kw in ["探", "サーチ"]):
                    effects.append(Effect(EffectType.SEARCH_DECK, 1))

                # Buffs

                # Target identification (PLAYER vs OPPONENT vs ALL)

                # For ADD_TO_HAND/RECOVER_MEMBER, if "自分は" is present, target is PLAYER even if "相手" is mentioned as source.

                target = TargetType.MEMBER_NAMED if (match := re.search(r" 「(.*?)」.*?は", content)) else None

                if not target:
                    if any(kw in content for kw in ["自分と相手", "自分も相手も", "全員", "自分および相手"]):
                        target = TargetType.ALL_PLAYERS

                    elif "自分は" in content and "手札に加え" in content:
                        target = TargetType.PLAYER

                    elif "相手は" in content and not any(kw in content for kw in ["自分は", "自分を"]):
                        target = TargetType.OPPONENT

                    elif "相手" in content and any(kw in content for kw in ["ウェイト", "させる", "選ばせる"]):
                        target = TargetType.OPPONENT

                    elif "相手" in content:
                        target = TargetType.OPPONENT

                    else:
                        target = TargetType.MEMBER_SELF

                target_params = {"target_name": match.group(1)} if target == TargetType.MEMBER_NAMED else {}

                if "ブレード" in content and "得る" in content:
                    icon_count = len(re.findall(r"icon_blade\.png", content))

                    count = (
                        int(match.group(1)) if (match := re.search(r"ブレード.*?(\d+)", content)) else icon_count or 1
                    )

                    if "ALLブレード" in content:
                        target_params["all_blade"] = True

                    effects.append(Effect(EffectType.ADD_BLADES, count, target, params=target_params))

                # Blade counting condition (ブレードがX以上)

                if match := re.search(r"ブレード.*?(\d+)(つ|個)以上", content):
                    conditions.append(Condition(ConditionType.COUNT_BLADES, {"min": int(match.group(1))}))

                elif "ブレード" in content and "合計" in content and (match := re.search(r"合計.*?(\d+)", content)):
                    conditions.append(Condition(ConditionType.COUNT_BLADES, {"min": int(match.group(1))}))

                if any(kw in content for kw in ["ハート", "heart", "heart_"]) and any(
                    kw in content for kw in ["得る", "加える", "増える"]
                ):
                    params = target_params.copy()

                    if "icon_all.png" in content or "icon_heart_all.png" in content or "all.png" in content:
                        params["color"] = 6

                        count = len(re.findall(r"icon_all\.png|icon_heart_all\.png|all\.png", content)) or 1

                    else:
                        count = (
                            int(match.group(1))
                            if (match := re.search(r"[+＋](\d+)", content))
                            else len(re.findall(r"heart_\d+\.png", content)) or 1
                        )

                        # Try to find specific color

                        if color_match := re.search(r"heart_(\d+)\.png", content):
                            params["color"] = int(color_match.group(1))

                    effects.append(Effect(EffectType.ADD_HEARTS, count, target, params=params))

                # Heart counting condition (ハートが合計X個以上 / ハートに...X個以上持つ)

                heart_match = re.search(r"(?:ハート|heart).*?(\d+)(つ|個)以上", full_content)

                if heart_match or (
                    "ハート" in full_content
                    and "合計" in full_content
                    and (heart_match := re.search(r"(?:合計|持ち).*?(\d+)(つ|個|枚)?", full_content))
                ):
                    heart_color = None

                    if (
                        "icon_all.png" in full_content
                        or "icon_heart_all.png" in full_content
                        or "all.png" in full_content
                    ):
                        heart_color = 6

                    else:
                        # Search for color icon BEFORE the count match if possible, or anywhere in full_content

                        search_limit = heart_match.start()

                        preceding_text = full_content[:search_limit]

                        color_icons = re.findall(r"heart_(\d+)\.png", preceding_text)

                        if not color_icons:
                            color_icons = re.findall(r"heart_(\d+)\.png", full_content)

                        if color_icons:
                            heart_color = int(color_icons[0]) - 1

                    is_gating = colon_idx == -1 or heart_match.start() < colon_idx

                    if "heart" in full_content or "ハート" in full_content:
                        print(
                            f"DEBUG: {full_content[:40]}... | colon={colon_idx} | heart={heart_match.start()} | gating={is_gating}"
                        )

                    conditions.append(
                        Condition(
                            ConditionType.COUNT_HEARTS,
                            {"min": int(heart_match.group(1)), "color": heart_color, "gating": is_gating},
                        )
                    )

                if any(kw in content for kw in ["必要ハート", "heart"]):
                    is_increase = any(kw in content for kw in ["増やす", "増える", "増加"])

                    is_decrease = any(kw in content for kw in ["減らす", "少なくなる", "減る", "マイナス", "－"])

                    if is_increase or is_decrease:
                        # Prioritize counting heart images for requirement effects

                        # We use heart_00\.png or just heart_.*?\.png since for requirement it's usually any/white

                        heart_images = len(re.findall(r"heart_.*?\.png", content))

                        if heart_images > 0:
                            count = heart_images

                        else:
                            # Try to find a count, but avoid "枚" and skip previous score buffs (+2)

                            # Focus on numbers close to the increase keywords

                            count_match = re.search(r"(\d+)(増やす|増える|減らす|減る)", content)

                            if count_match:
                                count = int(count_match.group(1))

                            else:
                                # Fallback to latest digit before images or keywords, ignoring "枚"

                                count_matches = re.findall(r"(\d+)(?!枚|人)", content)

                                if count_matches:
                                    count = int(count_matches[-1])

                                else:
                                    count = 1

                        if is_increase:
                            count = -count

                        effects.append(
                            Effect(EffectType.REDUCE_HEART_REQ, count, TargetType.PLAYER, params=target_params)
                        )

                if "エネルギー" in content and any(kw in content for kw in ["置く", "加える", "チャージ", "し"]):
                    if "デッキ" in content or "山札" in content:
                        # Handled by MOVE_TO_DECK below

                        pass

                    else:
                        target_e = TargetType.OPPONENT if "相手" in content else TargetType.PLAYER

                        count = 1

                        if match := re.search(r"エネルギーを(\d+)枚", content):
                            count = int(match.group(1))

                        effects.append(Effect(EffectType.ENERGY_CHARGE, count, target_e, params={}))

                # Exclude "好きな枚数" (any number) from multiplier detection to avoid false positives

                if any(kw in content for kw in ["につき", "1人につき", "人につき"]) or (
                    "枚数" in content and "好きな枚数" not in content
                ):
                    eff_params = {"multiplier": True}

                    if "成功ライブカード" in content or "ライブカード" in content:
                        eff_params["per_live"] = True

                    elif "エネ" in content:
                        eff_params["per_energy"] = True

                    elif "自分と相手" in content and ("メンバー" in content or "人につき" in content):
                        eff_params["per_member_all"] = True
                    elif "メンバー" in content or "人につき" in content:
                        eff_params["per_member"] = True

                    # Attach to the LAST effect if applicable

                    if effects and effects[-1].effect_type in (
                        EffectType.ADD_BLADES,
                        EffectType.ADD_HEARTS,
                        EffectType.BUFF_POWER,
                    ):
                        effects[-1].params.update(eff_params)

                    else:
                        effects.append(Effect(EffectType.BUFF_POWER, 1, params=eff_params))

                # Implicit/Generic Buff (only if explicit keywords like Blade/Heart/Score are NOT preventing it)

                elif (match := re.search(r"[+＋](\d+)", content)) and not any(
                    kw in content for kw in ["ブレード", "ハート", "スコア"]
                ):
                    effects.append(Effect(EffectType.BUFF_POWER, int(match.group(1))))

                if (
                    ("ポジションチェンジ" in content)
                    or ("エリア" in content and "移動" in content)
                    or ("場所を入れ替える" in content)
                    or ("移動させ" in content)
                ):
                    if any(kw in content for kw in ["場合", "なら", "とき"]) and "ポジションチェンジ" not in content:
                        # Check if HAS_MOVED condition already exists to avoid duplicates

                        if not any(c.type == ConditionType.HAS_MOVED for c in conditions):
                            conditions.append(Condition(ConditionType.HAS_MOVED))

                    else:
                        effects.append(Effect(EffectType.MOVE_MEMBER, 1))

                if "シャッフル" in content:
                    target_s = TargetType.OPPONENT if "相手" in content else TargetType.PLAYER

                    effects.append(Effect(EffectType.META_RULE, 0, target_s, params={"type": "shuffle", "deck": True}))

                if (
                    any(kw in content for kw in ["デッキ", "山札"])
                    and any(kw in content for kw in ["戻す", "置く", "置き"])
                    and not any(e.effect_type == EffectType.LOOK_AND_CHOOSE for e in effects)
                ):
                    # If it's "Place in discard", it's SWAP_CARDS (Target: Discard), not MOVE_TO_DECK

                    is_discard_dest = "控え室に" in content and "控え室から" not in content

                    if not is_discard_dest:
                        pos = "bottom" if "下" in content else "top" if "上" in content else "any"

                        to_energy = "エネルギーデッキ" in content

                        params = {"position": pos}

                        if to_energy:
                            params["to_energy_deck"] = True

                        if "控え室" in content:
                            params["from"] = "discard"

                        elif "ステージ" in content:
                            params["from"] = "stage"

                        effects.append(Effect(EffectType.MOVE_TO_DECK, 1, params=params))

                if "アクティブに" in content and not ("手札" in content and "加え" in content):
                    count = int(match.group(1)) if (match := re.search(r"(\d+)枚", content)) else 1

                    target_type = TargetType.MEMBER_SELF if "このメンバー" in content else TargetType.MEMBER_SELECT

                    effects.append(
                        Effect(
                            EffectType.ACTIVATE_MEMBER,
                            count,
                            target_type,
                            params={"target": "energy"} if "エネルギー" in content else {},
                        )
                    )

                # Duration

                dur = (
                    {"until": "live_end"}
                    if "ライブ終了時まで" in content
                    else {"until": "turn_end"}
                    if any(kw in content for kw in ["ターン終了まで", "終了時まで"])
                    else {}
                )

                if dur:
                    if not effects:
                        effects.append(Effect(EffectType.BUFF_POWER, 1, params={**dur, "temporary": True}))

                    else:
                        for eff in effects:
                            eff.params.update(dur)

                if any(kw in content for kw in ["必要ハート", "ハート条件", "heart"]) and any(
                    kw in content for kw in ["扱う", "確認", "する"]
                ):
                    src = "all_blade" if "ALLブレード" in content else "blade" if "ブレード" in content else None

                    if "オール" in content:
                        src = "all"

                    effects.append(
                        Effect(EffectType.META_RULE, 0, params={"type": "heart_rule", "live": True, "source": src})
                    )

                if "スコア" in content and any(kw in content for kw in ["加算", "合算"]):
                    effects.append(Effect(EffectType.BOOST_SCORE, 1, params={"type": "score_rule", "live": True}))

                if "ライブカード" in content and not effects:
                    # Catch-all for live interaction if no other effect parsed

                    effects.append(Effect(EffectType.META_RULE, 0, params={"live": True}))

                if any(kw in content for kw in ["選ばれない", "選べない", "置けない"]):
                    effects.append(Effect(EffectType.IMMUNITY, 1))

                if "として扱う" in content and "すべての領域" in content:
                    # Group Alias / Multi-Group
                    groups = []
                    for m in re.finditer(r"『(.*?)』", content):
                        groups.append(m.group(1))
                    if groups:
                        effects.append(
                            Effect(EffectType.META_RULE, 1, params={"type": "group_alias", "groups": groups})
                        )

                if "登場させる" in content:
                    count = int(match.group(1)) if (match := re.search(r"(\d+)枚", content)) else 1

                    src = "hand" if "手札" in content else "discard"

                    effects.append(
                        Effect(
                            EffectType.RECOVER_MEMBER,
                            count,
                            TargetType.CARD_DISCARD,
                            {"auto_play": True, "from": src, **({"score_max": score_filter} if score_filter else {})},
                        )
                    )

                # Cluster 5: Remote Ability Triggering

                if "能力" in content and any(kw in content for kw in ["発動させる", "発動する"]):
                    if "この能力は" in content:
                        # This is a condition on the current ability, not triggering another

                        if "エールによって公開されている" in content:
                            conditions.append(Condition(ConditionType.HAS_KEYWORD, {"keyword": "Revealed by Cheer"}))

                    else:
                        zone = "discard" if "控え室" in content else "stage"

                        if zone == "stage" and "控え室" in text and "そのカード" in content:
                            zone = "discard"

                        if zone == "stage" and context_zone:
                            zone = context_zone.lower()

                        # Remote trigger almost always implies choosing a target

                        if not any(c.type == ConditionType.HAS_CHOICE for c in conditions):
                            conditions.append(Condition(ConditionType.HAS_CHOICE))

                        effects.append(Effect(EffectType.TRIGGER_REMOTE, 1, params={"from": zone}))

                        effects.append(Effect(EffectType.TRIGGER_REMOTE, 1, params={"from": zone}))

                # Effect: Place Under (Stacking)
                # Matches "Under X" or "Place under this member" but NOT "Place under deck"
                if (
                    "の下に置" in content
                    and "コスト" not in content
                    and "払" not in content
                    and "代わり" not in content
                ):
                    count_pu = 1
                    if match := re.search(r"(\d+)枚", content):
                        count_pu = int(match.group(1))

                    target_pu = TargetType.MEMBER_SELECT
                    if "このメンバー" in content:
                        target_pu = TargetType.MEMBER_SELF

                    params_pu = {}
                    if "エネルギー" in content:
                        params_pu["from"] = "energy"
                    elif "手札" in content:
                        params_pu["from"] = "hand"
                    elif "控え室" in content:
                        params_pu["from"] = "discard"

                    # If the text implies putting a card under *this* member
                    if "このメンバーの下" in content:
                        target_pu = TargetType.MEMBER_SELF

                    effects.append(Effect(EffectType.PLACE_UNDER, count_pu, target_pu, params=params_pu))

                # Final pass: Apply optionality to effects in this sentence if "may" is present
                if "てもよい" in full_content:
                    for eff in effects:
                        eff.is_optional = True

                if "控" in content and any(kw in content for kw in ["置", "送"]):
                    # Retroactive fix for "Discard Remaining" appearing in a separate sentence

                    if "残り" in content and last_ability and last_ability.effects:
                        last_eff = last_ability.effects[-1]

                        if last_eff.effect_type == EffectType.LOOK_AND_CHOOSE:
                            last_eff.params["on_fail"] = "discard"

                            # We can skip parsing this as a new effect since we attached it to the previous one

                            continue

                    # Prevent parsing "Sacrifice Self" or "Cost Discard" as generic discard effect

                    # Also skip if LOOK_AND_CHOOSE with on_fail:discard already handles remaining cards

                    has_look_and_choose_discard = any(
                        e.effect_type == EffectType.LOOK_AND_CHOOSE and e.params.get("on_fail") == "discard"
                        for e in effects
                    ) or (
                        last_ability
                        and any(
                            e.effect_type == EffectType.LOOK_AND_CHOOSE and e.params.get("on_fail") == "discard"
                            for e in last_ability.effects
                        )
                    )

                    has_discard_cost = any(c.type == AbilityCostType.DISCARD_HAND for c in costs)

                    skip_swap = (
                        "このメンバー" in content
                        or (has_look_and_choose_discard and "残り" in content)
                        or (has_discard_cost and "手札" in content and "てもよい" in content)  # Cost pattern
                        or any(e.effect_type in (EffectType.RECOVER_LIVE, EffectType.RECOVER_MEMBER) for e in effects)
                    )

                    if not skip_swap:
                        count = (
                            int(match.group(1))
                            if (match := re.search(r"(?:手札|から).*?(\d+)枚", content))
                            else int(match.group(1))
                            if (match := re.search(r"(\d+)枚", content))
                            else 1
                        )

                        src = "deck" if "デッキ" in content else "hand" if "手札" in content else None

                        if not src and "控え室" in content:
                            src = "discard"

                        # Determine card type filter for discard

                        swap_params = {"target": "discard"}

                        if src:
                            swap_params["from"] = src

                        if "ライブカード" in content or "ライブ" in content:
                            swap_params["filter"] = "live"

                        elif "メンバーカード" in content or "メンバー" in content:
                            swap_params["filter"] = "member"

                        effects.append(Effect(EffectType.SWAP_CARDS, count, params=swap_params))

                if any(kw in content for kw in ["ウェイトにする", "ウェイト状態にする", "休み"]):
                    # If this is "Tap Self" effect but we already have a "Tap Self" cost, skip it

                    # (unless it's explicitly an effect that also taps the opponent)

                    is_tap_self = "このメンバー" in content and "相手" not in content

                    if is_tap_self and any(c.type == AbilityCostType.TAP_SELF for c in costs):
                        pass

                    else:
                        count = (
                            int(match.group(1)) if (match := re.search(r"(\d+|１|２|３|[一二三])人", content)) else 1
                        )

                    # Full-width mapping if needed

                    val_map = {"１": 1, "２": 2, "３": 3, "一": 1, "二": 2, "三": 3}

                    if match and match.group(1) in val_map:
                        count = val_map[match.group(1)]

                    target_tap = TargetType.OPPONENT if "相手" in content else TargetType.PLAYER

                    effects.append(
                        Effect(
                            EffectType.TAP_OPPONENT if target_tap == TargetType.OPPONENT else EffectType.TAP_MEMBER,
                            count,
                            target_tap,
                            {"all": True} if "すべて" in content else {},
                        )
                    )

                if match := re.search(r"スコア.*?[+＋](\d+|１|２|３|[一二三])", content):
                    val_str = match.group(1)

                    val_map = {"１": 1, "２": 2, "３": 3, "一": 1, "二": 2, "三": 3}

                    val = int(val_map.get(val_str, val_str)) if not val_str.isdigit() else int(val_str)

                    if "として扱う" in content or re.search(r"スコア[^、。]*?を得る", content):
                        effects.append(Effect(EffectType.MODIFY_SCORE_RULE, val, params={"until": "live_end"}))

                    else:
                        effects.append(Effect(EffectType.BOOST_SCORE, val))

                elif "スコア" in content and any(kw in content for kw in ["得る", "＋", "プラス"]):
                    if "として扱う" in content or re.search(r"スコア[^、。]*?を得る", content):
                        effects.append(Effect(EffectType.MODIFY_SCORE_RULE, 1, params={"until": "live_end"}))

                    else:
                        effects.append(Effect(EffectType.BOOST_SCORE, 1))

                # Yell Score Modifier rule

                if "スコア" in content and "加算" in content and "エールで出た" in content:
                    match = re.search(r"スコアの合計に(\d+)を加算", content)

                    val = int(match.group(1)) if match else 1

                    effects.append(
                        Effect(EffectType.MODIFY_SCORE_RULE, val, params={"multiplier_source": "yell_score_icon"})
                    )

                    trigger = TriggerType.CONSTANT

                if "コスト" in content and any(kw in content for kw in ["減", "-"]):
                    effects.append(Effect(EffectType.REDUCE_COST, 1))

                if match := re.search(r"ハートの必要数を([＋\+]?|－|-|ー)(\d+)する", content):
                    op = match.group(1)

                    val = int(match.group(2))

                    if "－" in op or "-" in op or "ー" in op:
                        val = -val

                    effects.append(Effect(EffectType.REDUCE_HEART_REQ, val))

                if any(kw in content for kw in ["必要ハート", "必要なハート"]) and any(
                    kw in content for kw in ["なる", "扱う", "置く"]
                ):
                    effects.append(Effect(EffectType.REDUCE_HEART_REQ, 1))

                if "なる" in content and "ハート" in content:
                    effects.append(Effect(EffectType.TRANSFORM_COLOR, 1, params={"target": "heart"}))

                if (match := re.search(r"ブレード[^スコア場合]*?[+＋](\d+|１|２|３|[一二三])", content)) or (
                    "ブレード" in content and any(kw in content for kw in ["得る", "得る。"]) and "持つ" not in content
                ):
                    val = 1

                    if match:
                        val_str = match.group(1)

                        val_map = {"１": 1, "２": 2, "３": 3, "一": 1, "二": 2, "三": 3}

                        val = int(val_map.get(val_str, val_str)) if not val_str.isdigit() else int(val_str)

                    elif match_v := re.search(r"(\d+|１|２|３|[一二三])(?:つ|個).*?ブレード", content):
                        val_str = match_v.group(1)

                        val_map = {"１": 1, "２": 2, "３": 3, "一": 1, "二": 2, "三": 3}

                        val = int(val_map.get(val_str, val_str)) if not val_str.isdigit() else int(val_str)

                    if not any(e.effect_type == EffectType.ADD_BLADES for e in effects):
                        effects.append(Effect(EffectType.ADD_BLADES, val))

                # Separately check for Hearts (Buffs or Add Hearts)

                # "Heart +1" or "Gain Heart" -> Type 2 (ADD_HEARTS)

                if (match := re.search(r"ハート[^スコア場合]*?[+＋](\d+|１|２|３|[一二三])", content)) or (
                    "ハート" in content and any(kw in content for kw in ["得る", "得る。"]) and "持つ" not in content
                ):
                    val = 1

                    if match:
                        val_str = match.group(1)

                        val_map = {"１": 1, "２": 2, "３": 3, "一": 1, "二": 2, "三": 3}

                        val = int(val_map.get(val_str, val_str)) if not val_str.isdigit() else int(val_str)

                    elif match_v := re.search(r"(\d+|１|２|３|[一二三])(?:つ|個).*?ハート", content):
                        val_str = match_v.group(1)

                        val_map = {"１": 1, "２": 2, "３": 3, "一": 1, "二": 2, "三": 3}

                        val = int(val_map.get(val_str, val_str)) if not val_str.isdigit() else int(val_str)

                    if not any(e.effect_type == EffectType.ADD_HEARTS for e in effects):
                        effects.append(Effect(EffectType.ADD_HEARTS, val))

                if any(kw in content for kw in ["無効", "キャンセル"]):
                    effects.append(Effect(EffectType.NEGATE_EFFECT, 1))

                if "デッキ" in content:
                    if "順番" in content and not any(
                        e.effect_type == EffectType.LOOK_AND_CHOOSE and e.params.get("reorder") for e in effects
                    ):
                        effects.append(Effect(EffectType.ORDER_DECK, 1))

                    elif ("一番上" in content or "一番下" in content) and "シャッフル" in content and "合計" in content:
                        count = int(match.group(1)) if (match := re.search(r"合計(\d+)枚", content)) else 0

                        params = {
                            "shuffle": True,
                            "position": "bottom" if "一番下" in content else "top",
                            "target_zone": "discard" if "控え室" in content else None,
                        }

                        if names := re.findall(r"「(.*?)」", content):
                            params["target_names"] = names

                        effects.append(Effect(EffectType.ORDER_DECK, count, params=params))

                    elif "一番上" in content:
                        effects.append(Effect(EffectType.MOVE_TO_DECK, 1, params={"position": "top"}))

                    elif "一番下" in content:
                        effects.append(Effect(EffectType.MOVE_TO_DECK, 1, params={"position": "bottom"}))

                if "登場させ" in content:
                    val = 1

                    if match := re.search(r"(\d+)人", content):
                        val = int(match.group(1))

                    params = {"is_optional": "もよい" in content}

                    if match := re.search(
                        r"コスト(\d+|１|２|３|４|５|６|７|８|９|０|[一二三四五六七八九〇])以下", content
                    ):
                        val_map = {
                            "１": 1,
                            "２": 2,
                            "３": 3,
                            "４": 4,
                            "５": 5,
                            "６": 6,
                            "７": 7,
                            "８": 8,
                            "９": 9,
                            "０": 0,
                            "一": 1,
                            "二": 2,
                            "三": 3,
                            "四": 4,
                            "五": 5,
                            "六": 6,
                            "七": 7,
                            "八": 8,
                            "九": 9,
                            "〇": 0,
                        }

                        params["cost_max"] = int(val_map.get(match.group(1), match.group(1)))

                    if sentence_groups:
                        params["group"] = sentence_groups[0]

                    effects.append(Effect(EffectType.PLAY_MEMBER_FROM_HAND, val, params=params))

                    if effects and effects[-1].effect_type in (
                        EffectType.ORDER_DECK,
                        EffectType.LOOK_AND_CHOOSE,
                        EffectType.MOVE_TO_DECK,
                        EffectType.ADD_TO_HAND,
                        EffectType.RECOVER_MEMBER,
                        EffectType.RECOVER_LIVE,
                        EffectType.SWAP_CARDS,
                    ):
                        if "ライブ" in content:
                            effects[-1].params["filter"] = "live"

                            if effects[-1].effect_type == EffectType.RECOVER_MEMBER:
                                effects[-1].effect_type = EffectType.RECOVER_LIVE

                        elif "メンバー" in content:
                            effects[-1].params["filter"] = "member"

                        if "エネルギー" in content:
                            effects[-1].params["filter"] = "energy"

                if match := re.search(
                    r"(?:以下から|のうち、)(\d+|１|２|３|４|５|一|二|三|四|五)(つ|枚|回|個)?を選ぶ", content
                ):
                    val_str = match.group(1)

                    # Simple mapping for common Japanese numerals

                    val_map = {"１": 1, "２": 2, "３": 3, "４": 4, "５": 5, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5}

                    val = int(val_map.get(val_str, val_str)) if not val_str.isdigit() else int(val_str)

                    effects.append(Effect(EffectType.SELECT_MODE, val))

                elif "以下から1つを選ぶ" in content:
                    effects.append(Effect(EffectType.SELECT_MODE, 1))

                if any(kw in content for kw in ["ハートの色を1つ指定", "好きなハートの色を"]):
                    effects.append(Effect(EffectType.COLOR_SELECT, 1))

                if "必要ハート" in content and "選んだ1つ" in content:
                    effects.append(Effect(EffectType.REDUCE_HEART_REQ, 0, params={"mode": "select_requirement"}))

                if "メンバーの下に" in content and "置" in content:
                    params = {}

                    if "エネルギー" in content:
                        params["type"] = "energy"

                    effects.append(Effect(EffectType.PLACE_UNDER, 1, params=params))

                if "聞く" in content:
                    effects.append(Effect(EffectType.FLAVOR_ACTION, 1))

                if "ライブできない" in content:
                    effects.append(Effect(EffectType.RESTRICTION, 1, params={"type": "live"}))

                if "置くことができない" in content:
                    effects.append(Effect(EffectType.RESTRICTION, 1, params={"type": "placement"}))

                if (
                    "なる" in content
                    and "すべて" in content
                    and (match := re.search(r"すべて\[(.*?)\]になる", content))
                ):
                    effects.append(Effect(EffectType.TRANSFORM_COLOR, 1, params={"target_color": match.group(1)}))

                if "バトンタッチ" in content and "2人" in content:
                    effects.append(Effect(EffectType.BATON_TOUCH_MOD, 2))

                if match := re.search(r"スコアは([0123456789０１２３４５６７８９]+)になる", content):
                    effects.append(Effect(EffectType.SET_SCORE, int(match.group(1).replace("４", "4"))))

                if (
                    "公開" in content
                    and any(kw in content for kw in ["置き場", "加える"])
                    and not any(e.effect_type == EffectType.LOOK_AND_CHOOSE for e in effects)
                ):
                    effects.append(Effect(EffectType.SWAP_ZONE, 1))

                if ("手札に加える" in content or "引く" in content) and not effects:
                    # Check if it mentions "Live card" or "Member card"

                    params = {"generic_add": True}

                    if "ライブ" in content:
                        params["filter"] = "live"

                    elif "メンバー" in content:
                        params["filter"] = "member"

                    if "枚数分" in content:
                        params["multiplier"] = "count"

                    effects.append(Effect(EffectType.DRAW, 1, params=params))

                # Replacement Effects (代わりに - Cluster 4)

                if "代わりに" in content:
                    # Find the replacement value (e.g., 'スコアを＋２' -> 2)

                    match = re.search(r"代わりに.*?[+＋](\d+)", content)

                    if match:
                        effects.append(
                            Effect(EffectType.REPLACE_EFFECT, int(match.group(1)), params={"replaces": "score_boost"})
                        )

                if (content.startswith("（") and content.endswith("）")) or (
                    content.startswith("(") and content.endswith(")")
                ):
                    # If the whole sentence is in parens, it's often reminder text

                    if not effects:
                        params = {}

                        if "対戦相手" in content and any(kw in content for kw in ["発動", "能力"]):
                            params["type"] = "opponent_trigger_allowed"

                        effects.append(Effect(EffectType.META_RULE, 1, params=params))

                        trigger = TriggerType.CONSTANT

                    else:
                        # Ensure reminder text within a block doesn't add accidental effects

                        pass

                # Explicit check for Opponent Interaction text (robust against splitting)

                if "対戦相手のカードの効果でも発動する" in content:
                    effects.append(Effect(EffectType.META_RULE, 1, params={"type": "opponent_trigger_allowed"}))

                    # Also propagate flag to the last ability if this is a continuation
                    if last_ability:
                        # Add condition to mark it can trigger from opponent effects
                        last_ability.conditions.append(
                            Condition(ConditionType.OPPONENT_HAS, {"opponent_trigger_allowed": True})
                        )

                    # If we just added this effect and no other trigger, set constant

                    if trigger == TriggerType.NONE:
                        trigger = TriggerType.CONSTANT

                # Final touches

                is_opt = (
                    "てよい" in content or "てもよい" in content or "。その後。" in content
                )  # Heuristic for optional continuations

                is_glob = "すべての" in content

                is_opp_hand = "相手の手札" in content

                for eff in effects:
                    eff.is_optional = is_opt

                    if is_glob:
                        eff.params["all"] = True

                    if is_opp_hand or "自分と相手" in content:
                        eff.target = TargetType.OPPONENT_HAND if is_opp_hand else TargetType.OPPONENT

                        if "自分と相手" in content:
                            eff.params["both_players"] = True

                    if eff.effect_type in (
                        EffectType.RECOVER_MEMBER,
                        EffectType.RECOVER_LIVE,
                        EffectType.ADD_TO_HAND,
                        EffectType.DRAW,
                        EffectType.SWAP_CARDS,
                    ):
                        if eff.target == TargetType.SELF:
                            eff.target = TargetType.PLAYER

                    if current_multiplier and "multiplier" not in eff.params:
                        eff.params["multiplier"] = current_multiplier

                    # Group Propagation: If sentence has a group in 『』, apply it to effects that might need it

                    if sentence_groups:
                        # Apply to effects that don't already have a more specific group

                        if eff.effect_type in [
                            EffectType.ADD_BLADES,
                            EffectType.ADD_HEARTS,
                            EffectType.BUFF_POWER,
                            EffectType.RECOVER_MEMBER,
                            EffectType.RECOVER_LIVE,
                            EffectType.ADD_TO_HAND,
                            EffectType.SEARCH_DECK,
                            EffectType.LOOK_AND_CHOOSE,
                        ]:
                            if "group" not in eff.params:
                                eff.params["group"] = sentence_groups[0]

                    # Zone Propagation

                    if context_zone:
                        if "from" not in eff.params:
                            eff.params["from"] = context_zone.lower()

                            # Marker for master_validator to see this zone is accounted for

                            eff.params["zone_accounted"] = True

                        if context_zone == "Discard":
                            eff.params["discard_interaction"] = True

                        if context_zone == "SUCCESS_LIVE":
                            eff.params["live_interaction"] = True

                    # Target selection filter migration:

                    # If this effect is a choice or play, and we have conditions that look like filters, move them.

                    if eff.effect_type in (
                        EffectType.PLAY_MEMBER_FROM_HAND,
                        EffectType.RECOVER_MEMBER,
                        EffectType.RECOVER_LIVE,
                        EffectType.ADD_TO_HAND,
                        EffectType.SEARCH_DECK,
                        EffectType.LOOK_AND_CHOOSE,
                        EffectType.TAP_OPPONENT,
                        EffectType.TAP_MEMBER,
                    ):
                        for cond in list(conditions):
                            if cond.type == ConditionType.COST_CHECK:
                                eff.params["cost_max" if cond.params.get("comparison") == "LE" else "cost_min"] = (
                                    cond.params.get("value")
                                )

                                conditions.remove(cond)

                            elif cond.type == ConditionType.COUNT_GROUP:
                                eff.params["group"] = cond.params.get("group")

                                # Don't remove COUNT_GROUP as it might also be a global requirement

                if (
                    any(kw in content for kw in ["ライブカードがある場合", "ライブカードが含まれる場合"])
                    and "その中に" in content
                ):
                    for eff in effects:
                        if eff.effect_type == EffectType.DRAW:
                            eff.params["condition"] = "has_live_in_looked"

                # Also mark costs as optional when pattern detected

                for cost in costs:
                    if is_opt:
                        cost.is_optional = True

                # --- Construct Ability ---

                if trigger != TriggerType.NONE:
                    # Handle multiple triggers (lazy way: create one ability, caller might need to dup if we want perfection,

                    # but actually we can just return a list of abilities from this function, so we can append multiple)

                    # For now, let's keep it simple: if we detected the slash, we append multiple

                    base_ability = Ability(
                        raw_text=line.strip(),
                        trigger=trigger,
                        effects=effects,
                        conditions=conditions,
                        costs=costs,
                        is_once_per_turn=is_once_per_turn,
                    )

                    # print(f"DEBUG: Created Ability: Trigger={trigger}, Effects={[e.effect_type for e in effects]}")

                    abilities.append(base_ability)

                    last_ability = base_ability

                    # Dual trigger hack for PL!-PR-009-PR

                    if "toujyou" in line and (("live_start" in line) or ("live_success" in line)) and "/" in line:
                        second_trigger = (
                            TriggerType.ON_LIVE_START if "live_start" in line else TriggerType.ON_LIVE_SUCCESS
                        )

                        # Clone it effectively

                        abilities.append(
                            Ability(
                                raw_text=content.strip(),
                                trigger=second_trigger,
                                effects=[
                                    Effect(e.effect_type, e.value, e.target, e.params.copy(), e.is_optional)
                                    for e in effects
                                ],
                                conditions=[Condition(c.type, c.params.copy(), c.is_negated) for c in conditions],
                                costs=[Cost(c.type, c.value, c.params.copy(), c.is_optional) for c in costs],
                                is_once_per_turn=base_ability.is_once_per_turn,
                            )
                        )

                elif effects or conditions or costs:
                    if last_ability and is_continuation:
                        # Check for Modal Answer Branching first

                        if is_modal_answer_branch:
                            # Find or create SELECT_MODE effect for modal answers

                            select_eff = None

                            if last_ability.effects and last_ability.effects[-1].effect_type == EffectType.SELECT_MODE:
                                if last_ability.effects[-1].params.get("type") == "modal_answer":
                                    select_eff = last_ability.effects[-1]

                            if not select_eff:
                                # Create new SELECT_MODE effect

                                # Assuming 3 options usually, but value doesn't strictly matter for VM if modal_options list is used

                                select_eff = Effect(
                                    EffectType.SELECT_MODE, 1, TargetType.PLAYER, params={"type": "modal_answer"}
                                )

                                select_eff.modal_options = []

                                last_ability.effects.append(select_eff)

                            # Append current branch effects

                            select_eff.modal_options.append(effects)

                            # Do NOT extend main effects/conditions

                        elif (
                            line.startswith("・")
                            or line.startswith("-")
                            or line.startswith("－")
                            or re.match(r"^[\(\（]\d+[\)\）]", line)
                        ) and any(e.effect_type == EffectType.SELECT_MODE for e in last_ability.effects):
                            last_ability.modal_options.append(effects)

                        else:
                            last_ability.effects.extend(effects)

                            # Only add conditions if they are not already present to avoid duplicates

                            for cond in conditions:
                                if cond not in last_ability.conditions:
                                    last_ability.conditions.append(cond)

                            last_ability.costs.extend(costs)

                            last_ability.raw_text += " " + line.strip()

                        if is_once_per_turn:
                            last_ability.is_once_per_turn = True

                    elif not is_continuation:
                        # Only default to CONSTANT if we have some indicators of an ability
                        # (to avoid splitting errors defaulting to Constant)
                        has_ability_indicators = any(
                            kw in line
                            for kw in [
                                "引",
                                "スコア",
                                "プラス",
                                "＋",
                                "ブレード",
                                "ハート",
                                "控",
                                "戻",
                                "エネ",
                                "デッキ",
                                "山札",
                                "見る",
                                "公開",
                                "選ぶ",
                                "扱",
                                "得る",
                                "移動",
                            ]
                        )
                        if has_ability_indicators:
                            last_ability = Ability(
                                raw_text=content.strip(),
                                trigger=TriggerType.CONSTANT,
                                effects=effects,
                                conditions=conditions,
                                costs=costs,
                                is_once_per_turn=is_once_per_turn,
                            )
                            abilities.append(last_ability)
                        else:
                            # If no indicators and not a continuation, maybe it's an error?
                            # For robustness, we'll log it if we were in a logger-enabled mode
                            # but here we just avoid creating a bogus Constant ability.
                            pass

        return abilities

    def parse(self, text: str) -> List[Ability]:
        """Alias for parse_ability_text for consistency."""

        return self.parse_ability_text(text)
