import sys
import re
from enum import IntEnum

# --- Mappings (Extracted from engine_rust_src and engine/models) ---

class Opcode(IntEnum):
    NOP = 0
    RETURN = 1
    JUMP = 2
    JUMP_IF_FALSE = 3
    DRAW = 10
    ADD_BLADES = 11
    ADD_HEARTS = 12
    REDUCE_COST = 13
    LOOK_DECK = 14
    RECOVER_LIVE = 15
    BOOST_SCORE = 16
    RECOVER_MEMBER = 17
    BUFF_POWER = 18
    IMMUNITY = 19
    MOVE_MEMBER = 20
    SWAP_CARDS = 21
    SEARCH_DECK = 22
    ENERGY_CHARGE = 23
    SET_BLADES = 24
    SET_HEARTS = 25
    FORMATION_CHANGE = 26
    NEGATE_EFFECT = 27
    ORDER_DECK = 28
    META_RULE = 29
    SELECT_MODE = 30
    MOVE_TO_DECK = 31
    TAP_OPPONENT = 32
    PLACE_UNDER = 33
    FLAVOR_ACTION = 34
    RESTRICTION = 35
    BATON_TOUCH_MOD = 36
    SET_SCORE = 37
    SWAP_ZONE = 38
    TRANSFORM_COLOR = 39
    REVEAL_CARDS = 40
    LOOK_AND_CHOOSE = 41
    CHEER_REVEAL = 42
    ACTIVATE_MEMBER = 43
    ADD_TO_HAND = 44
    COLOR_SELECT = 45
    REPLACE_EFFECT = 46
    TRIGGER_REMOTE = 47
    REDUCE_HEART_REQ = 48
    MODIFY_SCORE_RULE = 49
    TAP_MEMBER = 53
    PLAY_MEMBER_FROM_HAND = 57
    MOVE_TO_DISCARD = 58
    GRANT_ABILITY = 60
    INCREASE_HEART_COST = 61
    REDUCE_YELL_COUNT = 62
    PLAY_MEMBER_FROM_DISCARD = 63
    PAY_ENERGY = 64
    SELECT_MEMBER = 65
    DRAW_UNTIL = 66
    SELECT_PLAYER = 67
    SELECT_LIVE = 68
    REVEAL_UNTIL = 69
    INCREASE_COST = 70
    PREVENT_PLAY_TO_SLOT = 71
    SWAP_AREA = 72
    TRANSFORM_HEART = 73
    SELECT_CARDS = 74
    OPPONENT_CHOOSE = 75
    PLAY_LIVE_FROM_DISCARD = 76
    REDUCE_LIVE_SET_LIMIT = 77
    PREVENT_ACTIVATE = 82
    ACTIVATE_ENERGY = 81
    PREVENT_SET_TO_SUCCESS_PILE = 80
    PREVENT_BATON_TOUCH = 90
    SET_TARGET_SELF = 100
    SET_TARGET_PLAYER = 101
    SET_TARGET_OPPONENT = 102
    SET_TARGET_ALL_PLAYERS = 103
    SET_TARGET_MEMBER_SELF = 104
    SET_TARGET_MEMBER_OTHER = 105
    SET_TARGET_CARD_HAND = 106
    SET_TARGET_CARD_DISCARD = 107
    SET_TARGET_CARD_DECK_TOP = 108
    SET_TARGET_OPPONENT_HAND = 109
    SET_TARGET_MEMBER_SELECT = 110
    SET_TARGET_MEMBER_NAMED = 111

    # Condition Checks (Pre-defined for decoding)
    CHECK_TURN_1 = 200
    CHECK_HAS_MEMBER = 201
    CHECK_HAS_COLOR = 202
    CHECK_COUNT_STAGE = 203
    CHECK_COUNT_HAND = 204
    CHECK_COUNT_DISCARD = 205
    CHECK_IS_CENTER = 206
    CHECK_LIFE_LEAD = 207
    CHECK_COUNT_GROUP = 208
    CHECK_GROUP_FILTER = 209
    CHECK_OPPONENT_HAS = 210
    CHECK_SELF_IS_GROUP = 211
    CHECK_MODAL_ANSWER = 212
    CHECK_COUNT_ENERGY = 213
    CHECK_HAS_LIVE_CARD = 214
    CHECK_COST_CHECK = 215
    CHECK_RARITY_CHECK = 216
    CHECK_HAND_HAS_NO_LIVE = 217
    CHECK_COUNT_SUCCESS_LIVE = 218
    CHECK_OPPONENT_HAND_DIFF = 219
    CHECK_SCORE_COMPARE = 220
    CHECK_HAS_CHOICE = 221
    CHECK_OPPONENT_CHOICE = 222
    CHECK_COUNT_HEARTS = 223
    CHECK_COUNT_BLADES = 224
    CHECK_OPPONENT_ENERGY_DIFF = 225
    CHECK_HAS_KEYWORD = 226
    CHECK_DECK_REFRESHED = 227
    CHECK_HAS_MOVED = 228
    CHECK_HAND_INCREASED = 229
    CHECK_COUNT_LIVE_ZONE = 230
    CHECK_BATON = 231
    CHECK_TYPE_CHECK = 232
    CHECK_IS_IN_DISCARD = 233
    CHECK_AREA_CHECK = 234

class TriggerType(IntEnum):
    NONE = 0
    ON_PLAY = 1
    ON_LIVE_START = 2
    ON_LIVE_SUCCESS = 3
    TURN_START = 4
    TURN_END = 5
    CONSTANT = 6
    ACTIVATED = 7
    ON_LEAVES = 8
    ON_REVEAL = 9
    ON_POSITION_CHANGE = 10

def decode_filter(f):
    if f == 0: return "None"
    parts = []
    
    # Optional flags
    if f & 0x02: parts.append("Optional(0x02)")
    
    # ALL flag
    if f & 0x80000000: parts.append("ALL")
    
    # Type Filter
    type_f = (f >> 2) & 0x03
    if type_f == 1: parts.append("Type:Member")
    elif type_f == 2: parts.append("Type:Live")
    
    # Group Filter
    if f & 0x10:
        group_id = (f >> 5) & 0x7F
        parts.append(f"Group:{group_id}")
        
    # Unit Filter
    if f & 0x10000:
        unit_id = (f >> 17) & 0x7F
        parts.append(f"Unit:{unit_id}")
        
    # Cost Filter
    if f & 0x01000000:
        threshold = (f >> 25) & 0x1F
        is_le = (f & 0x40000000) != 0
        op = "<=" if is_le else ">="
        parts.append(f"Cost/Hearts {op} {threshold}")
        
    if not parts:
        return f"Unknown({f})"
    return " | ".join(parts)

# --- Legends (For human-readable decoding) ---

ZONES = {
    0: "Deck",
    1: "Deck Top",
    2: "Deck Bottom",
    3: "Energy Zone",
    4: "Stage",
    6: "Hand",
    7: "Discard",
    8: "Deck (Generic)",
    13: "Success Live Pile",
    15: "Yell Cards",
}

SLOTS = {
    0: "Left Slot",
    1: "Center Slot",
    2: "Right Slot",
    4: "Context Area",
    6: "Hand (Generic)",
    7: "Discard (Generic)",
    10: "Choice Target",
}

COMPARISONS = {
    0: "GE (>=)",
    1: "LE (<=)",
    2: "GT (>)",
    3: "LT (<)",
    4: "EQ (==)",
}

def get_legend_str():
    lines = ["\n--- BYTECODE LEGEND ---"]
    lines.append("Zones: " + ", ".join([f"{k}:{v}" for k, v in ZONES.items()]))
    lines.append("Slots: " + ", ".join([f"{k}:{v}" for k, v in SLOTS.items()]))
    lines.append("Comparisons: " + ", ".join([f"{k}:{v}" for k, v in COMPARISONS.items()]))
    return "\n".join(lines)

def decode_chunk(chunk):
    op, v, a_low, a_high, s = chunk
    a = ((a_high & 0xFFFFFFFF) << 32) | (a_low & 0xFFFFFFFF)
    is_negated = False
    base_op = op
    if op >= 1000 and op < 1300:
        is_negated = True
        base_op = op - 1000
    
    try:
        op_name = Opcode(base_op).name
    except ValueError:
        op_name = f"OP_{base_op}"
        
    if is_negated:
        op_name = f"NOT {op_name}"
        
    # Standard fallback
    params = f"v={v}, a={a}, s={s}"
    
    if base_op == Opcode.LOOK_AND_CHOOSE:
        # v = look_count | pick_count<<8, a = filter/source, s = target/remainder
        src_val = (a >> 12) & 0x0F
        src_zone_id = src_val if src_val != 0 else 8
        src_zone = ZONES.get(src_zone_id, f"Zone_{src_zone_id}")
        target_id = s & 0xFF
        target = SLOTS.get(target_id, f"Slot_{target_id}")
        params = f"v(Reveal):{v&0xFF}, v(Pick):{(v>>8)&0xFF}, a(Filter):[{decode_filter(a)}], a(Source):{src_zone}, s(Target):{target}"
    elif base_op == Opcode.BUFF_POWER:
        params = f"v(Value):{v}, a(Attr):{a}, s(Slot):{SLOTS.get(s, s)}"
    elif base_op == Opcode.RECOVER_MEMBER or base_op == Opcode.RECOVER_LIVE:
        src_val = (s >> 16) & 0xFF
        src_zone_id = src_val if src_val != 0 else 7 # Default recovery to discard
        params = f"v(Count):{v}, a(Filter):[{decode_filter(a)}], s(Source):{ZONES.get(src_zone_id, src_zone_id)}, s(Dest):{SLOTS.get(s & 0xFF, s & 0xFF)}"
    elif base_op == Opcode.DRAW or base_op == Opcode.MOVE_TO_DISCARD or base_op == Opcode.ADD_HEARTS or base_op == Opcode.ADD_BLADES:
        src_val = (s >> 16) & 0xFF
        if base_op == Opcode.MOVE_TO_DISCARD and src_val != 0:
             params = f"v(Count):{v}, a(Filter):[{decode_filter(a)}], s(Source):{ZONES.get(src_val, src_val)}, s(Target):{SLOTS.get(s & 0xFF, s & 0xFF)}"
        else:
             params = f"v(Count):{v}, a(Attr/Source):{a}, s(Slot/Target):{SLOTS.get(s & 0xFF, s & 0xFF)}"
    elif base_op == Opcode.PAY_ENERGY:
        params = f"v(Cost):{v}, a(Optional):{a}, s(Type):{s}"
    elif base_op == Opcode.SELECT_MEMBER:
        params = f"v(Unused):{v}, a(Filter):[{decode_filter(a)}], s(Target_Slot):{SLOTS.get(s, s)}"
    elif base_op == Opcode.GRANT_ABILITY:
        params = f"v(Unused):{v}, a(Source_CID):{a}, s(Target_Slot):{SLOTS.get(s, s)}"
    elif base_op == Opcode.MOVE_MEMBER:
        params = f"v(From):{SLOTS.get(v, v)}, a(To):{SLOTS.get(a, a)}, s(Unused):{s}"
    elif base_op >= 100 and base_op < 200:
        params = f"v={v}, a={a}, s={s}" # Target setters
    elif base_op >= 200 and base_op < 300:
        # Comparison logic for conditions
        comp_val = (s >> 4) & 0x0F
        slot = s & 0x0F
        comp_map = COMPARISONS
        comp = comp_map.get(comp_val, f"C_{comp_val}")
        params = f"v(Val):{v}, a(Attr):{a}, s(Comp):{comp}, s(Slot):{SLOTS.get(slot, slot)}"
        
    return f"{op_name:<20} | {params}"

def decode_bytecode(bytecode):
    if not bytecode:
        return "None"
    
    chunks = [bytecode[i:i+5] for i in range(0, len(bytecode), 5)]
    lines = []
    for i, chunk in enumerate(chunks):
        if len(chunk) < 5:
            chunk = chunk + [0] * (5 - len(chunk))
        lines.append(f"  {i*5:02d}: {decode_chunk(chunk)}")
    
    # Add Legend to the end
    lines.append(get_legend_str())
    return "\n".join(lines)

if __name__ == "__main__":
    # Standardized UTF-8 Handling
    if sys.stdout.encoding.lower() != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    if len(sys.argv) < 2:
        print("Usage: python bytecode_decoder.py \"[41, 3, 385876097, 0, 1, 0, 0, 0]\"")
        sys.exit(1)
        
    raw = sys.argv[1]
    # Clean up input if it's bracketed
    raw = raw.strip('[] ')
    try:
        data = [int(x.strip()) for x in raw.split(',')]
        print(decode_bytecode(data))
    except Exception as e:
        print(f"Error decoding: {e}")
