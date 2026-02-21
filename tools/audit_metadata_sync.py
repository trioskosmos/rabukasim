import json
import re
from pathlib import Path

def load_json(path):
    if not Path(path).exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def audit():
    metadata = load_json('data/metadata.json')
    manual_pseudocode = load_json('data/manual_pseudocode.json')
    
    # Read ability_translator.js to find mapping keys
    translator_path = 'frontend/web_ui/js/ability_translator.js'
    translator_text = open(translator_path, 'r', encoding='utf-8').read()
    
    # Extract string keys from Translations.jp.opcodes
    string_keys = set(re.findall(r'"(\w+)":', translator_text))
    
    # Extract symbolic keys
    symbolic_keys = set(re.findall(r'\[EffectType\.(\w+)\]', translator_text))
    symbolic_check_keys = set(re.findall(r'\[ConditionCheck\.(\w+)\]', translator_text))
    trigger_symbolic = set(re.findall(r'\[TriggerType\.(\w+)\]', translator_text))
    
    report = []
    report.append("# Metadata vs Translator vs Pseudocode Audit Report\n")
    
    # 1. Opcodes (10-90)
    report.append("## Opcodes (Effects)")
    report.append("| Opcode | Name | Status | Details |")
    report.append("|---|---|---|---|")
    for name, op in metadata['opcodes'].items():
        if name in ["NOP", "RETURN", "JUMP", "JUMP_IF_FALSE"]: continue
        found = name in string_keys or name in symbolic_keys
        status = "✅ OK" if found else "❌ MISSING"
        details = "Found in JS" if found else "Not mapped in translator.js"
        report.append(f"| {op} | {name} | {status} | {details} |")
            
    # 2. Conditions (200+)
    report.append("\n## Conditions")
    report.append("| Opcode | Name | Status | Details |")
    report.append("|---|---|---|---|")
    for name, op in metadata['conditions'].items():
        found = name in string_keys or name in symbolic_keys or name in symbolic_check_keys
        status = "✅ OK" if found else "❌ MISSING"
        details = "Mapped correctly" if found else "Not found in translator.js"
        report.append(f"| {op} | {name} | {status} | {details} |")

    # 3. Costs
    report.append("\n## Costs")
    report.append("| Opcode | Name | Status |")
    report.append("|---|---|---|")
    for name, op in metadata['costs'].items():
        if name == "NONE": continue
        found = name in string_keys
        status = "✅ OK" if found else "❌ MISSING"
        report.append(f"| {op} | {name} | {status} |")

    # 4. Triggers
    report.append("\n## Triggers")
    report.append("| Opcode | Name | Status |")
    report.append("|---|---|---|")
    for name, op in metadata['triggers'].items():
        if name == "NONE": continue
        found = name in trigger_symbolic
        status = "✅ OK" if found else "❌ MISSING"
        report.append(f"| {op} | {name} | {status} |")

    # 5. Pseudocode Audit
    report.append("\n## Pseudocode Tokens Audit")
    report.append("> [!NOTE]")
    report.append("> Tokens are categorized as **UNKNOWN** if they are not in `metadata.json` and not recognized as valid DSL parameters (like `COLOR_PINK`).\n")
    
    all_tokens = {}
    
    # Categorize tokens
    master_names = set(metadata['opcodes'].keys()) | set(metadata['conditions'].keys()) | \
                   set(metadata['costs'].keys()) | set(metadata['triggers'].keys())
    
    # Valid structural keywords
    dsl_keywords = {
        "SELECT_MODE", "OPTION", "PLAYER", "OPPONENT", "OTHER_MEMBER", "SELF", 
        "CARD_HAND", "TARGET_MEMBER", "VARIABLE", "TARGET", "FILTER", "PER_CARD",
        "NAME", "NAMES", "ZONE", "DISPLAY", "KEYWORD", "UNIT", "NAMES", "ANY", "ALL", "NONE",
        "TRIGGER", "EFFECT", "COST", "CONDITION", "OPTIONAL", "ONCE_PER_TURN",
        "DURATION", "UNTIL", "FROM", "TO", "LIST", "OPTIONS", "OR", "AND", "NOT",
        "EQUALS", "GREATER_THAN", "LESS_THAN", "LE", "GE", "MAX", "MIN", "BASE",
        "VARIABLE", "MULTIPLIER", "PER_ENERGY", "PER_HAND", "PER_MEMBER"
    }
    
    # Valid mechanical values and parameters
    dsl_params = {
        "COLOR_PINK", "COLOR_RED", "COLOR_YELLOW", "COLOR_GREEN", "COLOR_BLUE", "COLOR_PURPLE",
        "BLUE", "PINK", "RED", "YELLOW", "GREEN", "PURPLE", "COST", "HEART", "BLADE",
        "OPPONENT_WAIT", "MY_STAGE", "MY_HAND", "MY_DISCARD", "OPPONENT_STAGE",
        "REVEALED", "DISCARD", "HAND", "ENERGY", "BOTTOM", "TOP", "SUCCESS_PILE",
        "CENTER", "CENTER_ONLY", "OUT_OF_CENTER", "ADD_TAG", "AREA_IN", "BATON_PASS", 
        "BATON_TOUCH", "MEMBER_AT_SLOT", "POSITION_CHANGE", "HAND_SIZE", "SCORE_LEAD", 
        "ENERGY_LEAD", "HEART_LEAD", "COST_LEAD", "WAIT", "MIRAKURA", "DOLLCHESTRA", 
        "KALEIDOSCORE", "SYNCRISE", "CATCHU", "BIBI", "PRINTEMPS", "LILY_WHITE", "MUSE", 
        "HASU", "DOLL", "CERISE", "SCORE", "ENERGY", "HEARTS", "BLADES", "MEMBER", "MEMBERS",
        "LIVE_CARD", "LIVE_AREA", "SUCCESS_LIVE", "SUCCESS_LIVES", "LIVE_ZONE", "DECK",
        "ALL_MEMBERS", "ALL_AREAS", "ALL_ENERGY_ACTIVE", "ANY_STAGE", "UNIT_BIBI", "UNIT_CATCHU",
        "OTHER", "OTHER_MEMBER", "SAME_NAME", "SAME_UNIT", "SAME_SLOT", "SAME_NAME_AS",
        "NEXT_TURN", "UNTIL_LIVE_END", "LIVE_END", "DID_ACTIVATE_ENERGY_THIS_TURN",
        "DID_ACTIVATE_MEMBER_THIS_TURN", "MOVED_THIS_TURN", "REVEALED_THIS", "PLAYED",
        "DISCARDED", "REMAINDER", "DESTINATION", "DURATION", "MULTIPLIER", "POSITION_CHANGE",
        "HEART_COLORS", "HEART_TYPE", "HEART_LIST", "ZONE", "DISPLAY", "KEYWORD", "UNIT",
        "COUNT_PER", "COUNT_ACTIVATED", "COUNT_PER", "COUNT_UNIQUE_NAMES", "COUNT_REVEALED",
        "ACTIVATE_AND_SELF", "SUCCESS_LIVES_CONTAINS", "UNIQUE_NAMES", "PLAYER_SELECT",
        "MEMBER_SELECT", "TARGET_FILTER", "TARGET_PLAYER", "SUM_COST", "SUM_HEARTS", "SUM_SCORE",
        "SUM_ENERGY", "SUM_SUCCESS_LIVE", "MATCH_COST", "MATCH_HEART", "MATCH_COUNT",
        "MATCH_BASE_BLADE", "MATCH_PREVIOUS", "MATCH_RECOVERED", "HAND_SIZE_DIFF",
        "HIGHEST_COST_ON_STAGE", "OPPONENT_LIVE", "OPPONENT_EXTRA_HEARTS", "EXTRA_HEARTS",
        "RECOVER_REVEALED", "TOTAL_BLADES", "TOTAL_COST_LE", "UNIQUE_NAME", "YELL_REVEALED"
    }

    known_aliases = {
        "ON_MEMBER_DISCARD", "ON_PLAY", "ACTIVATED", "ON_REMOVE", "ON_LEAVES", "TURN_1",
        "ADD", "BASE", "BOTH", "BOTH_PLAYERS", "COUNT", "EFFECT", "GRANT_HEARTS", 
        "SCORE", "STAGE", "TRIGGER", "TRUE", "FALSE", "MULLIGAN", "WAIT", "NAMES",
        "NOT", "MODE", "AREA", "LIST", "TYPE", "DIVE", "CYCLE", "EMOTION", "WAIT",
        "TONIGHT", "OR", "EQUALS", "MAX", "MIN", "GROUP", "GROUP_ID", "SLOT", "LIVE",
        "SELF_SLOT", "LEFT", "RIGHT", "LEFT_SIDE", "RIGHT_SIDE", "SIDE"
    }

    for card_no, data in manual_pseudocode.items():
        pseudo = data.get('pseudocode', '')
        # 1. Strip OPTION labels (content before |)
        lines = []
        for line in pseudo.split('\n'):
            if "OPTION:" in line and "|" in line:
                label, code = line.split("|", 1)
                lines.append(code)
            else:
                lines.append(line)
        
        stripped_pseudo = "\n".join(lines)
        
        # 2. Extract SHOUTY_CASE tokens
        tokens = re.findall(r'\b[A-Z_][A-Z0-9_]+\b', stripped_pseudo)
        for t in tokens:
            if t not in all_tokens:
                all_tokens[t] = []
            if card_no not in all_tokens[t]:
                all_tokens[t].append(card_no)

    report.append("| Token | Status | Sample Card |")
    report.append("|---|---|---|")
    
    sorted_tokens = sorted(all_tokens.keys())
    orphans = []
    
    # Regex for common comparison parameters like COST_LE_4, HEARTS_GE_3
    comp_pattern = re.compile(r'^[A-Z_]+_(?:GE|LE|GT|LT|EQ)(?:_[0-9A-Z_]+)?$')
    # Regex for common prefix-based logic
    prefix_pattern = re.compile(r'^(?:HAS|COUNT|MATCH|SUM|PER|NOT|ON|DECK|TOTAL|REDUCE|IS|PLAY|DISCARD|REMOVE|RESET|REVEALED|LOOK|OTHER|NEXT|PREVENT|SET|UNIQUE|TYPE|HAND|MOVE|BATON|SCORE|ENERGY|HEART|BLADE|ALL|ANY|BASE|OPPONENT|TRIGGER|NO|CHARGED|FIXED)_')
    
    for token in sorted_tokens:
        if token.isdigit(): continue
        
        status = ""
        if token in master_names:
            status = "✅ MASTER"
        elif token in dsl_keywords:
            status = "⚙️ KEYWORD"
        elif token in dsl_params:
            status = "🎨 PARAM"
        elif token in known_aliases:
            status = "📎 ALIAS"
        elif token.startswith("CHECK_") and token[6:] in metadata['conditions']:
            status = "📎 ALIAS"
        elif comp_pattern.match(token):
            status = "🎨 PARAM"
        elif prefix_pattern.match(token):
            status = "⚙️ LOGIC"
        elif token.startswith("UNIT_") or token.startswith("HEART_") or token.startswith("NAME_") or token.startswith("TARGET_"):
            status = "🎨 PARAM"
        elif "_OR_" in token or "_AND_" in token or "_FROM_" in token or "_TO_" in token or "_ON_" in token or "_IN_" in token or "_AS_" in token:
            status = "⚙️ LOGIC"
        elif "_THIS_TURN" in token or "_THIS" in token:
            status = "⚙️ LOGIC"
        elif token in ["TAPPED", "REVERSED", "SUB_GROUP", "TARGETS", "O_TARGET", "MAIN_PHASE"]:
            status = "⚙️ LOGIC"
        else:
            status = "❓ UNKNOWN"
            orphans.append(token)
            
        if status == "❓ UNKNOWN":
            report.append(f"| {token} | {status} | {all_tokens[token][0]} |")

    if not orphans:
        report.append("| (None) | ✅ All Tokens Categorized | - |")

    # Final count of categories (Optional)
    
    Path('reports').mkdir(exist_ok=True)
    with open('reports/audit_detailed.md', 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
    
    print("Report generated: reports/audit_detailed.md")

if __name__ == "__main__":
    audit()
