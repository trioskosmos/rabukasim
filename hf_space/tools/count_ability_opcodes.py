import json, re, sys
p = r"c:\\Users\\trios\\.gemini\\antigravity\\vscode\\loveca-copy\\data\\consolidated_abilities.json"
with open(p, 'r', encoding='utf-8') as f:
    data = json.load(f)

ability_count = len(data)

effect_ops = set()
condition_ops = set()
trigger_ops = set()

# helper to extract identifiers
ident_re = re.compile(r'[A-Z][A-Z0-9_]+')

for k,v in data.items():
    pc = v.get('pseudocode') or ''
    # split into sections by lines
    # find EFFECT: sections
    for m in re.finditer(r'EFFECT:\s*(.*)', pc):
        txt = m.group(1)
        # take until end of line or semicolon-separated statements
        # but also include following semicolon-separated parts on same line
        parts = re.split(r'[;\n]', txt)
        for part in parts:
            for idm in ident_re.findall(part):
                # skip common words that are not ops like "PLAYER", "SELF" etc
                if idm in ('PLAYER','SELF','TARGET','SUCCESS','OPTION','OPTIONAL','ZONE','MODE','FROM','TO','ALL','COUNT','VALUE'):
                    continue
                effect_ops.add(idm)
    for m in re.finditer(r'CONDITION:\s*(.*)', pc):
        txt = m.group(1)
        parts = re.split(r'[;\n]', txt)
        for part in parts:
            for idm in ident_re.findall(part):
                if idm in ('PLAYER','SELF','TARGET','SUCCESS','OPTION','OPTIONAL','ZONE','MODE','FROM','TO','ALL','COUNT','VALUE'):
                    continue
                condition_ops.add(idm)
    for m in re.finditer(r'TRIGGER:\s*(.*)', pc):
        txt = m.group(1)
        parts = re.split(r'[;\n]', txt)
        for part in parts:
            for idm in ident_re.findall(part):
                trigger_ops.add(idm)

# Additionally, scan for uppercase function-like tokens across pseudocode to capture ops not under EFFECT label
all_ops = set()
for v in data.values():
    pc = v.get('pseudocode') or ''
    for idm in ident_re.findall(pc):
        if idm in ('PLAYER','SELF','TARGET','SUCCESS','OPTION','OPTIONAL','ZONE','MODE','FROM','TO','ALL','COUNT','VALUE'):
            continue
        all_ops.add(idm)

# categorize remaining ops heuristically: if present in EFFECT lines earlier, it's effect; if in CONDITION lines, condition; else if in TRIGGER, trigger; else classify as effect by default
for op in list(all_ops):
    if op in effect_ops or op in condition_ops or op in trigger_ops:
        continue
    # heuristics: names containing DRAW, ADD, ACTIVATE, BOOST, RECOVER, MOVE, SET, REDUCE, TRANSFORM, PLACE, LOOK, PLAY, DISCARD, TAP, POSITION, CHOICE
    if re.search(r'DRAW|ADD|ACTIVATE|BOOST|RECOVER|MOVE|SET|REDUCE|TRANSFORM|PLACE|LOOK|PLAY|DISCARD|TAP|POSITION|CHOICE|HEART|BLADE|ENERGY', op):
        effect_ops.add(op)
    elif re.search(r'EQ|GT|LT|GE|LE|COUNT|HAS|IS|NOT|MIN|MAX|EXTRA|SUM', op):
        condition_ops.add(op)
    else:
        trigger_ops.add(op)

# remove common words if present
for s in ['EFFECT','CONDITION','TRIGGER']:
    effect_ops.discard(s)
    condition_ops.discard(s)
    trigger_ops.discard(s)

print('ability_count:', ability_count)
print('unique_effect_ops:', len(effect_ops))
print('unique_condition_ops:', len(condition_ops))
print('unique_trigger_flag_ops:', len(trigger_ops))

# Optionally list sorted small samples (first 40 each)
print('\nsample_effect_ops:', sorted(effect_ops)[:40])
print('\nsample_condition_ops:', sorted(condition_ops)[:40])
print('\nsample_trigger_ops:', sorted(trigger_ops)[:40])
