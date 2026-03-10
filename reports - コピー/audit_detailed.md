# Metadata vs Translator vs Pseudocode Audit Report

## Opcodes (Effects)
| Opcode | Name | Status | Details |
|---|---|---|---|
| 10 | DRAW | ✅ OK | Found in JS |
| 11 | ADD_BLADES | ✅ OK | Found in JS |
| 12 | ADD_HEARTS | ✅ OK | Found in JS |
| 13 | REDUCE_COST | ✅ OK | Found in JS |
| 14 | LOOK_DECK | ✅ OK | Found in JS |
| 15 | RECOVER_LIVE | ✅ OK | Found in JS |
| 16 | BOOST_SCORE | ✅ OK | Found in JS |
| 17 | RECOVER_MEMBER | ✅ OK | Found in JS |
| 18 | BUFF_POWER | ✅ OK | Found in JS |
| 19 | IMMUNITY | ✅ OK | Found in JS |
| 20 | MOVE_MEMBER | ✅ OK | Found in JS |
| 21 | SWAP_CARDS | ✅ OK | Found in JS |
| 22 | SEARCH_DECK | ✅ OK | Found in JS |
| 23 | ENERGY_CHARGE | ✅ OK | Found in JS |
| 24 | SET_BLADES | ✅ OK | Found in JS |
| 25 | SET_HEARTS | ✅ OK | Found in JS |
| 26 | FORMATION_CHANGE | ✅ OK | Found in JS |
| 27 | NEGATE_EFFECT | ✅ OK | Found in JS |
| 28 | ORDER_DECK | ✅ OK | Found in JS |
| 29 | META_RULE | ✅ OK | Found in JS |
| 30 | SELECT_MODE | ✅ OK | Found in JS |
| 31 | MOVE_TO_DECK | ✅ OK | Found in JS |
| 32 | TAP_OPPONENT | ✅ OK | Found in JS |
| 33 | PLACE_UNDER | ✅ OK | Found in JS |
| 35 | RESTRICTION | ✅ OK | Found in JS |
| 36 | BATON_TOUCH_MOD | ✅ OK | Found in JS |
| 37 | SET_SCORE | ✅ OK | Found in JS |
| 38 | SWAP_ZONE | ✅ OK | Found in JS |
| 39 | TRANSFORM_COLOR | ✅ OK | Found in JS |
| 40 | REVEAL_CARDS | ✅ OK | Found in JS |
| 41 | LOOK_AND_CHOOSE | ✅ OK | Found in JS |
| 42 | CHEER_REVEAL | ✅ OK | Found in JS |
| 43 | ACTIVATE_MEMBER | ✅ OK | Found in JS |
| 44 | ADD_TO_HAND | ✅ OK | Found in JS |
| 45 | COLOR_SELECT | ✅ OK | Found in JS |
| 46 | REPLACE_EFFECT | ✅ OK | Found in JS |
| 47 | TRIGGER_REMOTE | ✅ OK | Found in JS |
| 48 | REDUCE_HEART_REQ | ✅ OK | Found in JS |
| 49 | MODIFY_SCORE_RULE | ✅ OK | Found in JS |
| 50 | ADD_STAGE_ENERGY | ✅ OK | Found in JS |
| 51 | SET_TAPPED | ✅ OK | Found in JS |
| 52 | ADD_CONTINUOUS | ✅ OK | Found in JS |
| 53 | TAP_MEMBER | ✅ OK | Found in JS |
| 34 | FLAVOR | ✅ OK | Found in JS |
| 57 | PLAY_MEMBER_FROM_HAND | ✅ OK | Found in JS |
| 83 | SET_HEART_COST | ✅ OK | Found in JS |
| 58 | MOVE_TO_DISCARD | ✅ OK | Found in JS |
| 60 | GRANT_ABILITY | ✅ OK | Found in JS |
| 61 | INCREASE_HEART_COST | ✅ OK | Found in JS |
| 62 | REDUCE_YELL_COUNT | ✅ OK | Found in JS |
| 63 | PLAY_MEMBER_FROM_DISCARD | ✅ OK | Found in JS |
| 64 | PAY_ENERGY | ✅ OK | Found in JS |
| 65 | SELECT_MEMBER | ✅ OK | Found in JS |
| 66 | DRAW_UNTIL | ✅ OK | Found in JS |
| 67 | SELECT_PLAYER | ✅ OK | Found in JS |
| 68 | SELECT_LIVE | ✅ OK | Found in JS |
| 69 | REVEAL_UNTIL | ✅ OK | Found in JS |
| 70 | INCREASE_COST | ✅ OK | Found in JS |
| 71 | PREVENT_PLAY_TO_SLOT | ✅ OK | Found in JS |
| 72 | SWAP_AREA | ✅ OK | Found in JS |
| 73 | TRANSFORM_HEART | ✅ OK | Found in JS |
| 74 | SELECT_CARDS | ✅ OK | Found in JS |
| 75 | OPPONENT_CHOOSE | ✅ OK | Found in JS |
| 76 | PLAY_LIVE_FROM_DISCARD | ✅ OK | Found in JS |
| 77 | REDUCE_LIVE_SET_LIMIT | ✅ OK | Found in JS |
| 82 | PREVENT_ACTIVATE | ✅ OK | Found in JS |
| 81 | ACTIVATE_ENERGY | ✅ OK | Found in JS |
| 80 | PREVENT_SET_TO_SUCCESS_PILE | ✅ OK | Found in JS |
| 90 | PREVENT_BATON_TOUCH | ✅ OK | Found in JS |

## Conditions
| Opcode | Name | Status | Details |
|---|---|---|---|
| 200 | TURN_1 | ✅ OK | Mapped correctly |
| 201 | HAS_MEMBER | ✅ OK | Mapped correctly |
| 202 | HAS_COLOR | ✅ OK | Mapped correctly |
| 203 | COUNT_STAGE | ✅ OK | Mapped correctly |
| 204 | COUNT_HAND | ✅ OK | Mapped correctly |
| 205 | COUNT_DISCARD | ✅ OK | Mapped correctly |
| 206 | IS_CENTER | ✅ OK | Mapped correctly |
| 207 | LIFE_LEAD | ✅ OK | Mapped correctly |
| 208 | COUNT_GROUP | ✅ OK | Mapped correctly |
| 209 | GROUP_FILTER | ✅ OK | Mapped correctly |
| 210 | OPPONENT_HAS | ✅ OK | Mapped correctly |
| 211 | SELF_IS_GROUP | ✅ OK | Mapped correctly |
| 212 | MODAL_ANSWER | ✅ OK | Mapped correctly |
| 213 | COUNT_ENERGY | ✅ OK | Mapped correctly |
| 214 | HAS_LIVE_CARD | ✅ OK | Mapped correctly |
| 215 | COST_CHECK | ✅ OK | Mapped correctly |
| 216 | RARITY_CHECK | ✅ OK | Mapped correctly |
| 217 | HAND_HAS_NO_LIVE | ✅ OK | Mapped correctly |
| 218 | COUNT_SUCCESS_LIVE | ✅ OK | Mapped correctly |
| 219 | OPPONENT_HAND_DIFF | ✅ OK | Mapped correctly |
| 220 | SCORE_COMPARE | ✅ OK | Mapped correctly |
| 221 | HAS_CHOICE | ✅ OK | Mapped correctly |
| 222 | OPPONENT_CHOICE | ✅ OK | Mapped correctly |
| 223 | COUNT_HEARTS | ✅ OK | Mapped correctly |
| 224 | COUNT_BLADES | ✅ OK | Mapped correctly |
| 225 | OPPONENT_ENERGY_DIFF | ✅ OK | Mapped correctly |
| 226 | HAS_KEYWORD | ✅ OK | Mapped correctly |
| 227 | DECK_REFRESHED | ✅ OK | Mapped correctly |
| 228 | HAS_MOVED | ✅ OK | Mapped correctly |
| 229 | HAND_INCREASED | ✅ OK | Mapped correctly |
| 230 | COUNT_LIVE_ZONE | ✅ OK | Mapped correctly |
| 231 | BATON | ✅ OK | Mapped correctly |
| 232 | TYPE_CHECK | ✅ OK | Mapped correctly |
| 233 | IS_IN_DISCARD | ✅ OK | Mapped correctly |
| 234 | AREA_CHECK | ✅ OK | Mapped correctly |

## Costs
| Opcode | Name | Status |
|---|---|---|
| 1 | ENERGY | ✅ OK |
| 2 | TAP_SELF | ✅ OK |
| 3 | DISCARD_HAND | ✅ OK |
| 4 | RETURN_HAND | ✅ OK |
| 5 | SACRIFICE_SELF | ✅ OK |
| 6 | REVEAL_HAND_ALL | ✅ OK |
| 7 | SACRIFICE_UNDER | ✅ OK |
| 8 | DISCARD_ENERGY | ✅ OK |
| 9 | REVEAL_HAND | ✅ OK |
| 20 | TAP_MEMBER | ✅ OK |
| 21 | TAP_ENERGY | ✅ OK |
| 22 | REST_MEMBER | ✅ OK |
| 23 | RETURN_MEMBER_TO_HAND | ✅ OK |
| 24 | DISCARD_MEMBER | ✅ OK |
| 25 | DISCARD_LIVE | ✅ OK |
| 26 | REMOVE_LIVE | ✅ OK |
| 27 | REMOVE_MEMBER | ✅ OK |
| 28 | RETURN_LIVE_TO_HAND | ✅ OK |
| 29 | RETURN_LIVE_TO_DECK | ✅ OK |
| 30 | RETURN_MEMBER_TO_DECK | ✅ OK |
| 31 | PLACE_MEMBER_FROM_HAND | ✅ OK |
| 32 | PLACE_LIVE_FROM_HAND | ✅ OK |
| 33 | PLACE_ENERGY_FROM_HAND | ✅ OK |
| 34 | PLACE_MEMBER_FROM_DISCARD | ✅ OK |
| 35 | PLACE_LIVE_FROM_DISCARD | ✅ OK |
| 36 | PLACE_ENERGY_FROM_DISCARD | ✅ OK |
| 37 | PLACE_MEMBER_FROM_DECK | ✅ OK |
| 38 | PLACE_LIVE_FROM_DECK | ✅ OK |
| 39 | PLACE_ENERGY_FROM_DECK | ✅ OK |
| 41 | SHUFFLE_DECK | ✅ OK |
| 42 | DRAW_CARD | ✅ OK |
| 43 | DISCARD_TOP_DECK | ✅ OK |
| 44 | REMOVE_TOP_DECK | ✅ OK |
| 45 | RETURN_DISCARD_TO_DECK | ✅ OK |
| 46 | RETURN_REMOVED_TO_DECK | ✅ OK |
| 47 | RETURN_REMOVED_TO_HAND | ✅ OK |
| 48 | RETURN_REMOVED_TO_DISCARD | ✅ OK |
| 49 | PLACE_ENERGY_FROM_SUCCESS | ✅ OK |
| 50 | DISCARD_SUCCESS_LIVE | ✅ OK |
| 51 | REMOVE_SUCCESS_LIVE | ✅ OK |
| 52 | RETURN_SUCCESS_LIVE_TO_HAND | ✅ OK |
| 53 | RETURN_SUCCESS_LIVE_TO_INDEX | ✅ OK |
| 54 | RETURN_SUCCESS_LIVE_TO_DISCARD | ✅ OK |
| 55 | PLACE_MEMBER_FROM_SUCCESS | ✅ OK |
| 56 | PLACE_LIVE_FROM_SUCCESS | ✅ OK |
| 57 | PLACE_ENERGY_FROM_REMOVED | ✅ OK |
| 58 | PLACE_MEMBER_FROM_REMOVED | ✅ OK |
| 59 | PLACE_LIVE_FROM_REMOVED | ✅ OK |
| 60 | RETURN_ENERGY_TO_DECK | ✅ OK |
| 61 | RETURN_ENERGY_TO_HAND | ✅ OK |
| 62 | REMOVE_ENERGY | ✅ OK |
| 63 | RETURN_STAGE_ENERGY_TO_DECK | ✅ OK |
| 64 | RETURN_STAGE_ENERGY_TO_HAND | ✅ OK |
| 65 | DISCARD_STAGE_ENERGY | ✅ OK |
| 66 | REMOVE_STAGE_ENERGY | ✅ OK |
| 67 | PLACE_ENERGY_FROM_STAGE_ENERGY | ✅ OK |
| 68 | PLACE_MEMBER_FROM_STAGE_ENERGY | ✅ OK |
| 69 | PLACE_LIVE_FROM_STAGE_ENERGY | ✅ OK |
| 70 | PLACE_ENERGY_FROM_HAND_TO_STAGE_ENERGY | ✅ OK |
| 71 | PLACE_MEMBER_FROM_HAND_TO_STAGE_ENERGY | ✅ OK |
| 72 | PLACE_LIVE_FROM_HAND_TO_STAGE_ENERGY | ✅ OK |
| 73 | PLACE_ENERGY_FROM_DISCARD_TO_STAGE_ENERGY | ✅ OK |
| 74 | PLACE_MEMBER_FROM_DISCARD_TO_STAGE_ENERGY | ✅ OK |
| 75 | PLACE_LIVE_FROM_DISCARD_TO_STAGE_ENERGY | ✅ OK |
| 76 | PLACE_ENERGY_FROM_DECK_TO_STAGE_ENERGY | ✅ OK |
| 77 | PLACE_MEMBER_FROM_DECK_TO_STAGE_ENERGY | ✅ OK |
| 78 | PLACE_LIVE_FROM_DECK_TO_STAGE_ENERGY | ✅ OK |
| 79 | PLACE_ENERGY_FROM_SUCCESS_TO_STAGE_ENERGY | ✅ OK |
| 80 | PLACE_MEMBER_FROM_SUCCESS_TO_STAGE_ENERGY | ✅ OK |
| 81 | PLACE_LIVE_FROM_SUCCESS_TO_STAGE_ENERGY | ✅ OK |
| 82 | PLACE_ENERGY_FROM_REMOVED_TO_STAGE_ENERGY | ✅ OK |
| 83 | PLACE_MEMBER_FROM_REMOVED_TO_STAGE_ENERGY | ✅ OK |
| 84 | PLACE_LIVE_FROM_REMOVED_TO_STAGE_ENERGY | ✅ OK |
| 85 | RETURN_LIVE_TO_DISCARD | ✅ OK |
| 86 | RETURN_LIVE_TO_REMOVED | ✅ OK |
| 87 | RETURN_LIVE_TO_SUCCESS | ✅ OK |
| 88 | RETURN_MEMBER_TO_DISCARD | ✅ OK |
| 89 | RETURN_MEMBER_TO_REMOVED | ✅ OK |
| 90 | RETURN_MEMBER_TO_SUCCESS | ✅ OK |
| 91 | RETURN_ENERGY_TO_DISCARD | ✅ OK |
| 92 | RETURN_ENERGY_TO_REMOVED | ✅ OK |
| 93 | RETURN_ENERGY_TO_SUCCESS | ✅ OK |
| 94 | RETURN_SUCCESS_LIVE_TO_REMOVED | ✅ OK |
| 95 | RETURN_REMOVED_SUCCESS | ✅ OK |
| 96 | RETURN_STAGE_ENERGY_TO_DISCARD | ✅ OK |
| 97 | RETURN_STAGE_ENERGY_TO_REMOVED | ✅ OK |
| 98 | RETURN_STAGE_ENERGY_TO_SUCCESS | ✅ OK |
| 99 | RETURN_DISCARD_TO_HAND | ✅ OK |
| 100 | RETURN_DISCARD_TO_REMOVED | ✅ OK |

## Triggers
| Opcode | Name | Status |
|---|---|---|
| 1 | ON_PLAY | ✅ OK |
| 2 | ON_LIVE_START | ✅ OK |
| 3 | ON_LIVE_SUCCESS | ✅ OK |
| 4 | TURN_START | ✅ OK |
| 5 | TURN_END | ✅ OK |
| 6 | CONSTANT | ✅ OK |
| 7 | ACTIVATED | ✅ OK |
| 8 | ON_LEAVES | ✅ OK |
| 9 | ON_REVEAL | ✅ OK |
| 10 | ON_POSITION_CHANGE | ✅ OK |

## Pseudocode Tokens Audit
> [!NOTE]
> Tokens are categorized as **UNKNOWN** if they are not in `metadata.json` and not recognized as valid DSL parameters (like `COLOR_PINK`).

| Token | Status | Sample Card |
|---|---|---|
| (None) | ✅ All Tokens Categorized | - |
