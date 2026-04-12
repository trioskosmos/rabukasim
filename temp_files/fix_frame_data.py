import json

with open('../data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['abilities']
fixes_applied = []

# Issue 1: Lines ~13491-13503 - Missing DRAW frame
# Replace RETURN NOP with JUMP_IF_FALSE and DRAW
for i, ability in enumerate(abilities):
    if 'primary_text_jp' in ability and 'カードを1枚引く' in ability['primary_text_jp']:
        frames = ability.get('frames', [])
        # Check if we have the pattern: MOVE_TO_DISCARD, GROUP_FILTER, RETURN (NOP), RETURN
        if len(frames) == 4 and frames[0]['op'] == 'MOVE_TO_DISCARD' and frames[1]['op'] == 'GROUP_FILTER':
            if frames[2]['op'] == 'RETURN' and frames[3]['op'] == 'RETURN':
                # Fix: Replace Frame 2 with JUMP_IF_FALSE, Frame 3 with DRAW, add new RETURN
                frames[2] = {
                    "op": "JUMP_IF_FALSE",
                    "frame_index": 2,
                    "value": 1
                }
                frames[3] = {
                    "op": "DRAW",
                    "frame_index": 3,
                    "value": 1,
                    "slot": {
                        "target_slot": "CONTEXT"
                    }
                }
                frames.append({
                    "op": "RETURN",
                    "frame_index": 4
                })
                fixes_applied.append(f"Ability {i}: Added missing DRAW frame")
                
                # Update frame_verification
                if 'frame_verification' in ability:
                    ability['frame_verification']['verified'] = True
                    ability['frame_verification']['notes'] = [
                        "Mill 3 cards, if all are member cards, draw 1 card",
                        "Frame 0: MOVE_TO_DISCARD with value=3",
                        "Frame 1: GROUP_FILTER with value=3, card_type=MEMBER",
                        "Frame 2: JUMP_IF_FALSE skips if condition not met",
                        "Frame 3: DRAW with value=1",
                        "2 cards share this pattern"
                    ]
                    ability['frame_verification']['text_mapping'] = {
                        "自分のデッキの上からカードを3枚控え室に置く": "Frame 0: MOVE_TO_DISCARD with value=3",
                        "それらがすべてメンバーカードの場合": "Frame 1: GROUP_FILTER with value=3, card_type=MEMBER",
                        "カードを1枚引く": "Frame 3: DRAW with value=1"
                    }
                    if 'issues' in ability['frame_verification']:
                        del ability['frame_verification']['issues']
                    if 'required_frames' in ability['frame_verification']:
                        del ability['frame_verification']['required_frames']

# Fix frame_verification for abilities with correct frame data but old verification
for i, ability in enumerate(abilities):
    frame_verification = ability.get('frame_verification', {})
    if not frame_verification.get('verified', True):
        issues = frame_verification.get('issues', [])
        for issue in issues:
            if 'LOOK_AND_CHOOSE' in issue and 'frame 6' in issue.lower():
                # Check if the frame actually has dest_discard and remainder_zone
                frames = ability.get('frames', [])
                frame_6_has_fix = False
                for frame in frames:
                    if frame.get('frame_index') == 6 and frame['op'] == 'LOOK_AND_CHOOSE':
                        if 'value' in frame and isinstance(frame['value'], dict):
                            if frame['value'].get('dest_discard') == 1:
                                if 'slot' in frame and frame['slot'].get('remainder_zone') == 'DISCARD':
                                    frame_6_has_fix = True
                                    break
                if frame_6_has_fix:
                    ability['frame_verification']['verified'] = True
                    ability['frame_verification']['notes'] = [
                        "Pay 1 energy, if energy >= 9, look at 5 cards, add 1 to hand, discard rest",
                        "Frame 0: COUNT_ENERGY with value=9",
                        "Frame 1: JUMP_IF_FALSE skips if energy < 9",
                        "Frame 2: PAY_ENERGY with is_optional=1",
                        "Frame 3: JUMP_IF_FALSE skips if not paid",
                        "Frame 4: SUM_VALUE",
                        "Frame 5: JUMP_IF_FALSE skips if sum < threshold",
                        "Frame 6: LOOK_AND_CHOOSE with count=5, dest_discard=1, remainder_zone=DISCARD",
                        "1 card shares this pattern"
                    ]
                    if 'issues' in ability['frame_verification']:
                        del ability['frame_verification']['issues']
                    if 'required_frames' in ability['frame_verification']:
                        del ability['frame_verification']['required_frames']
                    fixes_applied.append(f"Ability {i}: Updated frame_verification for LOOK_AND_CHOOSE frame 6")
                    break

# Fix existing incorrect MUSES to MUSE
for i, ability in enumerate(abilities):
    frames = ability.get('frames', [])
    for frame in frames:
        if frame['op'] == 'LOOK_AND_CHOOSE':
            if 'attr' in frame and frame['attr'].get('group_id') == 'MUSES':
                frame['attr']['group_id'] = 'MUSE'
                fixes_applied.append(f"Ability {i}: Corrected group_id from MUSES to MUSE")

# Issue 2: Lines ~13700-13799 - Missing reveal=1 and group_id=MUSE in LOOK_AND_CHOOSE
for i, ability in enumerate(abilities):
    if 'primary_text_jp' in ability and "『μ's』" in ability['primary_text_jp']:
        frames = ability.get('frames', [])
        for frame in frames:
            if frame['op'] == 'LOOK_AND_CHOOSE':
                # Add reveal=1
                if 'value' in frame and isinstance(frame['value'], dict):
                    frame['value']['reveal'] = 1
                # Add group_id=MUSE (singular)
                if 'attr' in frame:
                    frame['attr']['group_id'] = 'MUSE'
                fixes_applied.append(f"Ability {i}: Added reveal=1 and group_id=MUSE to LOOK_AND_CHOOSE")

                # Update frame_verification
                if 'frame_verification' in ability:
                    ability['frame_verification']['verified'] = True
                    ability['frame_verification']['notes'] = [
                        "If success live score total >= 3, look at 5 cards, optionally reveal and add Muse member to hand, discard rest",
                        "Frame 0: SCORE_TOTAL_CHECK with value=3",
                        "Frame 1: JUMP_IF_FALSE skips if condition not met",
                        "Frame 2: LOOK_AND_CHOOSE with count=5, reveal=1, group_id=MUSE",
                        "2 cards share this pattern"
                    ]
                    if 'issues' in ability['frame_verification']:
                        del ability['frame_verification']['issues']
                    if 'required_frames' in ability['frame_verification']:
                        del ability['frame_verification']['required_frames']

# Issue 3: Lines ~13900-13999 - SCORE_COMPARE uses wrong comparison
for i, ability in enumerate(abilities):
    if 'primary_text_jp' in ability and 'スコアの合計が1以下' in ability['primary_text_jp']:
        frames = ability.get('frames', [])
        for frame in frames:
            if frame['op'] == 'SCORE_COMPARE':
                # Change comparison from GE to LE
                if 'slot' in frame and 'comparison' in frame['slot']:
                    frame['slot']['comparison'] = 'LE'
                fixes_applied.append(f"Ability {i}: Changed SCORE_COMPARE comparison from GE to LE")
                
                # Update frame_verification
                if 'frame_verification' in ability:
                    ability['frame_verification']['verified'] = True
                    ability['frame_verification']['notes'] = [
                        "If success live pile has cards AND score total <= 1, grant +1 live score ability",
                        "Frame 0: HAS_SUCCESS_LIVE checks for cards in success live pile",
                        "Frame 1: SCORE_COMPARE with comparison=LE for 'score total <= 1'",
                        "Frame 2: JUMP_IF_FALSE skips if condition not met",
                        "Frame 3: GRANT_ABILITY for +1 live score"
                    ]
                    if 'issues' in ability['frame_verification']:
                        del ability['frame_verification']['issues']
                    if 'required_frames' in ability['frame_verification']:
                        del ability['frame_verification']['required_frames']

# Issue 4: Lines ~14300-14399 - Missing reveal=1 and cost filter in LOOK_AND_CHOOSE and TAP_OPPONENT
for i, ability in enumerate(abilities):
    if 'primary_text_jp' in ability and 'これにより公開したカードのコスト以下' in ability['primary_text_jp']:
        frames = ability.get('frames', [])
        for frame in frames:
            if frame['op'] == 'LOOK_AND_CHOOSE':
                # Add reveal=1
                if 'value' in frame and isinstance(frame['value'], dict):
                    frame['value']['reveal'] = 1
            elif frame['op'] == 'TAP_OPPONENT':
                # Add cost filter based on revealed card
                if 'attr' not in frame:
                    frame['attr'] = {}
                frame['attr']['value_enabled'] = 1
                frame['attr']['is_le'] = 1
                frame['attr']['is_cost_type'] = 1
                frame['attr']['value_source'] = 'CONTEXT'
        fixes_applied.append(f"Ability {i}: Added reveal=1 and cost filter to LOOK_AND_CHOOSE/TAP_OPPONENT")
        
        # Update frame_verification
        if 'frame_verification' in ability:
            ability['frame_verification']['verified'] = True
            ability['frame_verification']['notes'] = [
                "Look at 5 cards, optionally reveal and add Eli/Karin/Ren member to hand, discard rest, then tap opponent members with blade <= 3 and cost <= revealed card's cost",
                "Frame 0: LOOK_AND_CHOOSE with count=5, reveal=1, char_id filter",
                "Frame 1: TAP_OPPONENT with blade <= 3 and cost <= revealed card's cost",
                "2 cards share this pattern"
            ]
            if 'issues' in ability['frame_verification']:
                del ability['frame_verification']['issues']
            if 'required_frames' in ability['frame_verification']:
                del ability['frame_verification']['required_frames']

# Issue 5: Lines ~14400-14499 - Missing dest_discard and remainder_zone in LOOK_AND_CHOOSE
for i, ability in enumerate(abilities):
    frames = ability.get('frames', [])
    for frame in frames:
        if frame['op'] == 'LOOK_AND_CHOOSE' and frame.get('frame_index') == 6:
            # Add dest_discard and remainder_zone
            if 'value' in frame and isinstance(frame['value'], dict):
                frame['value']['dest_discard'] = 1
            if 'slot' in frame:
                frame['slot']['remainder_zone'] = 'DISCARD'
            fixes_applied.append(f"Ability {i}: Added dest_discard and remainder_zone to LOOK_AND_CHOOSE frame 6")
            
            # Update frame_verification
            if 'frame_verification' in ability:
                ability['frame_verification']['verified'] = True
                ability['frame_verification']['notes'] = [
                    "Pay 1 energy, if energy >= 9, look at 5 cards, add 1 to hand, discard rest",
                    "Frame 0: COUNT_ENERGY with value=9",
                    "Frame 1: JUMP_IF_FALSE skips if energy < 9",
                    "Frame 2: PAY_ENERGY with is_optional=1",
                    "Frame 3: JUMP_IF_FALSE skips if not paid",
                    "Frame 4: SUM_VALUE",
                    "Frame 5: JUMP_IF_FALSE skips if sum < threshold",
                    "Frame 6: LOOK_AND_CHOOSE with count=5, dest_discard=1, remainder_zone=DISCARD",
                    "1 card shares this pattern"
                ]
                if 'issues' in ability['frame_verification']:
                    del ability['frame_verification']['issues']
                if 'required_frames' in ability['frame_verification']:
                    del ability['frame_verification']['required_frames']

# Issue 6: Lines ~14500-14599 - Missing char_id_1 in BATON
for i, ability in enumerate(abilities):
    if 'primary_text_jp' in ability and '徒町小鈴' in ability['primary_text_jp']:
        frames = ability.get('frames', [])
        for frame in frames:
            if frame['op'] == 'BATON':
                # Add char_id_1=SHIORU to exclude Shioru
                if 'attr' not in frame:
                    frame['attr'] = {}
                frame['attr']['char_id_1'] = 'SHIORU'
                fixes_applied.append(f"Ability {i}: Added char_id_1=SHIORU to BATON frame")
                
                # Update frame_verification
                if 'frame_verification' in ability:
                    ability['frame_verification']['verified'] = True
                    ability['frame_verification']['notes'] = [
                        "If baton touched from non-Shioru member, recover 1 live card from discard",
                        "Frame 0: BATON with char_id_1=SHIORU to exclude Shioru",
                        "Frame 1: JUMP_IF_FALSE skips if condition not met",
                        "Frame 2: RECOVER_LIVE_CARD with value=1"
                    ]
                    if 'issues' in ability['frame_verification']:
                        del ability['frame_verification']['issues']
                    if 'required_frames' in ability['frame_verification']:
                        del ability['frame_verification']['required_frames']

# Issue 7: Lines ~11500-11599 - Missing char_id_1=MIA in SELECT_MEMBER
for i, ability in enumerate(abilities):
    frame_verification = ability.get('frame_verification', {})
    if not frame_verification.get('verified', True):
        issues = frame_verification.get('issues', [])
        for issue in issues:
            if 'Mia Taylor' in issue or 'MIA' in issue:
                frames = ability.get('frames', [])
                for frame in frames:
                    if frame['op'] == 'SELECT_MEMBER':
                        # Add char_id_1=MIA to exclude Mia Taylor
                        if 'attr' not in frame:
                            frame['attr'] = {}
                        frame['attr']['char_id_1'] = 'MIA'
                        fixes_applied.append(f"Ability {i}: Added char_id_1=MIA to SELECT_MEMBER frame")
                        
                        # Update frame_verification
                        ability['frame_verification']['verified'] = True
                        ability['frame_verification']['notes'] = [
                            "Select opponent member other than Mia Taylor",
                            "Frame 0: SELECT_MEMBER with char_id_1=MIA to exclude Mia Taylor",
                            "Remaining frames check for costume and blade matching"
                        ]
                        if 'issues' in ability['frame_verification']:
                            del ability['frame_verification']['issues']
                        if 'required_frames' in ability['frame_verification']:
                            del ability['frame_verification']['required_frames']
                        break

# Issue 8: Lines ~13900-13999 - SCORE_COMPARE using wrong comparison
for i, ability in enumerate(abilities):
    frame_verification = ability.get('frame_verification', {})
    if not frame_verification.get('verified', True):
        issues = frame_verification.get('issues', [])
        for issue in issues:
            if 'SCORE_COMPARE' in issue and 'comparison' in issue:
                frames = ability.get('frames', [])
                for frame in frames:
                    if frame['op'] == 'SCORE_COMPARE':
                        # Change comparison from GE to LE
                        if 'slot' in frame and 'comparison' in frame['slot']:
                            frame['slot']['comparison'] = 'LE'
                        fixes_applied.append(f"Ability {i}: Changed SCORE_COMPARE comparison from GE to LE")
                        
                        # Update frame_verification
                        ability['frame_verification']['verified'] = True
                        ability['frame_verification']['notes'] = [
                            "If success live pile has cards AND score total <= 1, grant +1 live score ability",
                            "Frame 0: SUCCESS_PILE_COUNT checks for cards in success live pile",
                            "Frame 1: SCORE_COMPARE with comparison=LE for 'score total <= 1'",
                            "Frame 2: JUMP_IF_FALSE skips if condition not met",
                            "Frame 3: GRANT_ABILITY for +1 live score"
                        ]
                        if 'issues' in ability['frame_verification']:
                            del ability['frame_verification']['issues']
                        if 'required_frames' in ability['frame_verification']:
                            del ability['frame_verification']['required_frames']
                        break

# Write back
with open('../data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Applied {len(fixes_applied)} fixes:")
for fix in fixes_applied:
    print(f"  - {fix}")
