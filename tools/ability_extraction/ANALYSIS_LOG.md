# Ability Extraction Analysis Log

This document tracks analysis of failing tests following the workflow:
1. View a test
2. Identify the main card and ability being tested
3. Compare authored, converted, and semantic representations
4. Fix parser/translator as necessary
5. Document findings

---

## Test: test_card_693 (PL!N-bp5-001-AR ab#0)

**Card:** PL!N-bp5-001-AR | 上原歩夢 (Ayumu)
**Ability Index:** 0
**Trigger:** 自動 (ON_LEAVES)

### Semantic Data
```json
{
  "triggers": "自動",
  "use_limit": 1,
  "effect": {
    "condition": {
      "text": "自分がエールしたとき",
      "type": "cheer_action",
      "target": "self"
    },
    "action": {
      "condition": {
        "text": "エールにより公開された自分のカードが持つブレードハートの中に3種類以上ある場合",
        "type": "blade_heart_presence",
        "location": "cheer_revealed",
        "presence": "present"
      },
      "action": {
        "resource": "heart",
        "heart_types": ["01"],
        "actions": [
          {"duration": "until_end_of_live"},
          {"action": "gain_resource", "resource": "heart", "heart_types": ["01"]}
        ]
      },
      "furthermore_action": {
        "action": "gain_ability",
        "ability": "{{jyouji.png|常時}}ライブの合計スコアを+１する。"
      }
    }
  }
}
```

### Authored Frames
```json
[
  {
    "op": "COUNT_LIVE_HEARTS",
    "frame_index": 0,
    "value": 0,
    "attr": {"target_player": "SELF"},
    "slot": {"target_slot": "CONTEXT", "comparison": "GE"}
  },
  {
    "op": "JUMP_IF_FALSE",
    "frame_index": 1,
    "value": 1
  },
  {
    "op": "RETURN",
    "frame_index": 2
  }
]
```

### Converted Frames
Same as authored (incomplete stub)

### Analysis
**Issue:** The authored frames are an incomplete stub. They only contain COUNT_LIVE_HEARTS with value=0 and RETURN, which is clearly incorrect for the actual ability which should:
1. Check for cheer_action trigger
2. Check blade_heart_presence condition (3+ types)
3. Add heart01
4. Furthermore: check for 6+ types and grant constant +1 score ability

**Root Cause:** The authored frames for this card are incomplete/incorrect. The semantic data has the correct structure with blade_heart_presence condition and furthermore_action, but the converter is not generating the correct frames because the authored frames are a stub.

**Required Fix:** This requires fixing the authored frames in the source data, not the converter/parser. The converter is correctly generating the same frames as authored (both are incomplete stubs).

**Status:** Cannot fix via converter/parser - requires authored frame correction.

---

## Current Status

**Test Failures:** 107 failed (down from 109 initially)

**Successful Converter Fixes:**
1. Added SELECT_MEMBER for blade_count_at_least with group (109→108)
2. Fixed effect-level condition+action structure with correct JUMP distances (108→107)
3. Fixed heart_type preservation for ADD_HEARTS (preserving HEART03 instead of converting to GREEN)

**User-Added Fixes:**
1. area_move with group filter handler (didn't change failures)
2. REDUCE_HEART_REQ compare_accumulated for group conditions (didn't change failures)

**Remaining Issues:**
- Many authored frames are incomplete stubs (like PL!N-bp5-001-AR)
- Parser improvements needed for: SELECT_MODE, BATON conditions, DISCARDED_CARDS, META_RULE, group conditions with full text

---

## Failed Test Cards Analysis

Total failed tests: 51
Unique card IDs extracted: 32
Cards matched in cards.json: 31

### 1. PL!-PR-004-PR | 園田海未

**Ability Text:**
```
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から必要ハートに{{heart_01.png|heart01}}を3以上含むライブカードを1枚手札に加える。
```

**Authored Frames:**
- Frame 0: MOVE_TO_DISCARD | value=2 | attr={'target_player': 'SELF', 'once_per_turn': 1} | slot={'target_slot': 'STAGE_1', 'source_zone': 'HAND', 'dest_zone': 'DISCARD'}
- Frame 1: RECOVER_LIVE | value=1 | attr={'zone_mask': 'ALL', 'value_enabled': 1, 'value_threshold': 3, 'heart_type': 1} | slot={'target_slot': 'HAND', 'source_zone': 'DISCARD'}

**Converted Frames:**
- Frame 0: MOVE_TO_DISCARD | value=2 | attr={'target_player': 'SELF'} | slot={'source_zone': 'HAND', 'dest_zone': 'DISCARD', 'target_slot': 'CONTEXT'}
- Frame 1: RECOVER_LIVE | value=1 | attr={'zone_mask': 'ALL'} | slot={'source_zone': 'DISCARD', 'target_slot': 'HAND'}

**Issues:**
- Missing once_per_turn in MOVE_TO_DISCARD
- Missing value_enabled, value_threshold, heart_type in RECOVER_LIVE
- target_slot mismatch (STAGE_1 vs CONTEXT)

**Root Cause:** Parser not extracting "ターン1回" as use_limit and not extracting heart threshold "heart01を3以上含む"

### 2. PL!-bp3-012-RM | 南 ことり

**Ability Text:**
```
{{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、自分の成功ライブカード置き場にあるカード1枚につき、選んだハートを1つ得る。
```

**Authored Frames:**
- Frame 0: COLOR_SELECT | value=1 | attr={'target_player': 'SELF', 'color_mask': 'RED|GREEN|ANY'} | slot={'target_slot': 'CONTEXT'}
- Frame 1: ADD_HEARTS | value=1 | attr={'target_player': 'SELF', 'compare_accumulated': 1} | slot={'remainder_zone': 'SUCCESS_PILE', 'is_dynamic': 1}

**Converted Frames:**
- Frame 0: COLOR_SELECT | value=1 | attr={'target_player': 'SELF', 'color_mask': 'RED|GREEN|ANY'} | slot={'target_slot': 'CONTEXT'}
- Frame 1: ADD_HEARTS | value=1 | attr={'target_player': 'SELF', 'compare_accumulated': 1, 'remainder_zone': 'SUCCESS_PILE', 'is_dynamic': 1, 'heart_type': 'SELECTED'} | slot={'target_slot': 'CONTEXT'}

**Issues:**
- Extra heart_type='SELECTED' in ADD_HEARTS attr
- remainder_zone and is_dynamic in attr instead of slot

**Root Cause:** Converter placing remainder_zone/is_dynamic in wrong location

### 3. PL!-pb1-030-L | Cutie Panther

**Ability Text:**
```
{{live_start.png|ライブ開始時}}相手のステージにウェイト状態のメンバーがいる場合、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}{{heart_00.png|heart0}}減らす。
```

**Authored Frames:**
- Frame 0: SELECT_MEMBER | value=1 | attr={'target_player': 'OPPONENT', 'is_tapped': 1} | slot={'target_slot': 'STAGE_0', 'comparison': 'GE'}
- Frame 1: JUMP_IF_FALSE | value=1
- Frame 2: REDUCE_HEART_REQ | value=2

**Converted Frames:**
- Frame 0: REDUCE_HEART_REQ | value=1 | attr={'target_player': 'SELF', 'heart_types_count': 2}

**Issues:**
- Missing SELECT_MEMBER for tapped opponent member condition
- Wrong REDUCE_HEART_REQ attributes

**Root Cause:** Parser not extracting "ウェイト状態のメンバー" as tapped condition

### 4. PL!HS-bp1-003-P | 乙宗 梢

**Ability Text:**
```
{{jyouji.png|常時}}自分のステージのエリアすべてに『蓮ノ空』のメンバーが登場しており、かつ名前が異なる場合、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。
```

**Authored Frames:**
- Frame 0: COUNT_STAGE | value=None | attr={'group_enabled': 1, 'group_id': 'HASUNOSORA', 'unique_names': 1, 'all_areas': 1} | slot={'target_slot': 'STAGE_0', 'comparison': 'GE'}

**Converted Frames:**
- Frame 0: COUNT_GROUP | value=蓮ノ空 | attr={'target_player': 'SELF', 'unit_enabled': 1, 'unit_id': 'HASUNOSORA'} | slot={'target_slot': 'CONTEXT', 'comparison': 'GE'}

**Issues:**
- COUNT_GROUP vs COUNT_STAGE
- Missing all_areas and unique_names

**Root Cause:** Converter not handling all_areas condition type correctly

---

## Test: test_card_628 (PL!SP-bp5-009-AR ab#0)

**Card:** PL!SP-bp5-009-AR | 鬼塚夏美 (Natsumi Onitsuka)
**Ability Index:** 0
**Trigger:** ライブ開始時 (LIVE_START)

### Semantic Data
```json
{
  "triggers": "ライブ開始時",
  "effect": {
    "payment": {
      "action": "discard_to_waitroom",
      "source": "deck_top",
      "count": 1,
      "optional": true
    },
    "condition": {
      "text": "自分のデッキの一番上のカードを控え室に置いてもよい。そうした場合",
      "type": "raw"
    },
    "action": {
      "condition": {
        "text": "ライブ終了時まで、ブレードを得る。これにより控え室に置いたカードがライブカードの場合",
        "type": "raw"
      },
      "action": {
        "action": "member_to_wait",
        "target": "self",
        "source": "stage"
      }
    }
  }
}
```

### Authored Frames
```json
[
  {
    "op": "SET_TAPPED",
    "frame_index": 0,
    "value": 0,
    "attr": {"target_player": "SELF"},
    "slot": {"source_zone": "STAGE", "target_slot": "CONTEXT"}
  },
  {
    "op": "RETURN",
    "frame_index": 1
  }
]
```

### Converted Frames
Same as authored (incomplete stub)

### Analysis
**Issue:** The authored frames are an incomplete stub. They only contain SET_TAPPED with value=0 and RETURN, which is clearly incorrect for the actual ability which should:
1. Optional cost: discard top deck card
2. If done: add blade until end of live
3. If discarded card is live: tap self
4. Repeat up to 4 times

**Root Cause:** The authored frames for this card are incomplete/incorrect. The semantic data has the correct structure with payment, condition, and action, but the converter is not generating the correct frames because the authored frames are a stub.

**Status:** Cannot fix via converter/parser - requires authored frame correction.

**Note:** PL!SP-bp5-009 has 3 variants (R, P, AR) in cards.json, but none have abilities listed in cards.json. Only 1 ability is found in both semantic data and authored frames, which is the incomplete stub analyzed above.

---

## Workflow Improvements (2026-04-18)

### Added Semantic Data to Frame Comparison

Updated `tools/compare_ability_frames_detailed.py` to include semantic data from `abilities_extracted_from_cards.json`. This helps identify what the parser extracted vs what the converter generated.

**Changes:**
1. Load `unique_abilities` from semantic data file (key is `unique_abilities`, not `abilities`)
2. Match abilities by card number (e.g., `PL!SP-pb1-023-L`) and ability index
3. Display: Trigger, Use Limit, Cost, Effect

**Usage:**
```powershell
cd C:\Users\trios\.gemini\antigravity\vscode\loveca-copy
python tools\compare_ability_frames_detailed.py
# View data\frame_comparison_detailed.txt
```

### Fix: count_group → COUNT_STAGE

**Issue:** The semantic condition `count_group` was being converted to `COUNT_GROUP` opcode, but should use `COUNT_STAGE` with `group_enabled` and `group_id` attributes.

**Fix:** Changed 4 occurrences in `semantic_to_frame_converter.py`:
- Line 1409: `member_count_at_least` with group
- Line 1492: group with threshold
- Line 1500: group with numeric value
- Line 1503: group without numeric value

All now use `COUNT_STAGE` with `group_enabled` and `group_id` attributes instead of `COUNT_GROUP`.

**Verification:**
- Automated frames: 0 occurrences of `COUNT_GROUP`
- Authored frames: 14 occurrences of `COUNT_GROUP` (manual, needs separate review)

### Debugging Workflow

1. Run `cargo test` to get failing tests
2. Identify card from test name or comments
3. Look up card ID in `data/cards_compiled.json` if needed
4. Check `data/frame_comparison_detailed.txt` for the card's:
   - Authored frames (expected behavior)
   - Automated frames (actual converter output)
   - Semantic data (what the parser extracted)
5. Compare to identify missing/wrong details
6. Fix parser in `tools/ability_extraction/` or translator in `semantic_to_frame_converter.py`
7. Regenerate frames and rerun tests

### Key Files

| File | Purpose |
|------|---------|
| `tools/semantic_to_frame_converter.py` | Converts semantic actions to frame opcodes |
| `tools/ability_extraction/condition_parser.py` | Parses condition text into semantic structures |
| `data/frame_comparison_detailed.txt` | Side-by-side comparison with semantic data |
| `data/abilities_extracted_from_cards.json` | Semantic extraction output (source: unique_abilities) |
| `data/ability_frame_source.json` | Automated frame output |
| `data/ability_frame_source_authored.json` | Manual frame definitions |

---

### Current Test Status

After COUNT_GROUP fix:
- ~199 tests still failing
- Many failures likely due to structural frame differences (e.g., `target_slot` vs `source_zone` placement, `is_cost` flags, `choose_count` params)
- Need to analyze patterns in `frame_comparison_detailed.txt` to identify common conversion issues

---

## Analysis: PL!-bp5-024-L (Private Wars) - Card 47

**Issue:** Test `test_card_47_live_start_*_mode` fails because converter doesn't handle group presence conditions or SELECT_MODE actions.

### Semantic Data
```json
{
  "condition": {
    "type": "member_presence",
    "group": "A-RISE",
    "group_type": "unit"
  },
  "action": {
    "actions": [
      {"action": "activate_member", "source_state": "wait"},
      {"action": "member_to_wait", "target": "opponent", ...}
    ]
  }
}
```

### Authored Frames (Correct)
- Condition: `COUNT_STAGE` with `group_enabled: 1`, `group_id: "ARISE"`
- Action: `SELECT_MODE` with 2 options, `JUMP` logic, `SELECT_MEMBER`, `ACTIVATE_MEMBER`, `ADD_BLADES`, `TAP_OPPONENT`

### Automated Frames (Before Fix)
- Condition: `HAS_MEMBER` with `card_type: "MEMBER"` (wrong - ignores A-RISE requirement)
- Action: Just `ACTIVATE_MEMBER` (missing SELECT_MODE entirely)

### Fix Applied
**File:** `semantic_to_frame_converter.py` lines 1418-1427

Added group handling to `member_presence` condition:
```python
if group:
    # Use COUNT_STAGE with group filtering
    group_type = condition_data.get("group_type")
    extra_attr = {"group_enabled": 1, "group_id": _group_or_char_id(group, group_type)}
    if "opponent" in condition_data.get("target", ""):
        extra_attr["target_player"] = "OPPONENT"
    else:
        extra_attr["target_player"] = "SELF"
    frames, idx = append_count("COUNT_STAGE", extra_attr=extra_attr)
```

**Result:** Condition now correctly uses `COUNT_STAGE` with A-RISE group check.

### Remaining Issue
The action part still fails because the parser doesn't extract "以下から1つを選ぶ" (choose one from below) as a SELECT_MODE structure. The semantic shows flat actions instead of a choice between two modes.

**Status:** Partial fix - condition works, SELECT_MODE action handling needs parser work.
