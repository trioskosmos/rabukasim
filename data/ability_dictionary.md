# Ability Dictionary

Comparison symbols:

- `GE` -> `>=`
- `GT` -> `>`
- `LE` -> `<=`
- `LT` -> `<`
- `EQ` -> `==`
- `NE` -> `!=`

Families:
- `activation`: 7 opcodes
- `condition`: 37 opcodes
- `control`: 8 opcodes
- `draw`: 2 opcodes
- `movement`: 11 opcodes
- `recovery`: 3 opcodes
- `resource`: 18 opcodes
- `search`: 7 opcodes
- `selection`: 7 opcodes
- `targeting`: 3 opcodes
- `transform`: 3 opcodes

Common forms:
- `draw {value}` -> `DRAW`
- `count(stage) >= {value}` -> `COUNT_STAGE`
- `count(energy) >= {value}` -> `COUNT_ENERGY`
- `select mode {option_names}` -> `SELECT_MODE`
- `look {value}, choose {choose_count}` -> `LOOK_AND_CHOOSE`
- `move {value} from {source_zone} to discard` -> `MOVE_TO_DISCARD`
- `recover live {value}` -> `RECOVER_LIVE`
- `activate member {value}` -> `ACTIVATE_MEMBER`
- `activate energy {value}` -> `ACTIVATE_ENERGY`
- `boost score {value}` -> `BOOST_SCORE`
- `add hearts {value}` -> `ADD_HEARTS`
- `add blades {value}` -> `ADD_BLADES`

## Activation

- `ACTIVATE_ENERGY`
  - template: `activate energy {value}`
  - value role: `count`
  - kind: `effect`
  - count: `22`
  - triggers: `ON_PLAY`, `ACTIVATED`, `ON_LIVE_START`, `ON_LEAVES`, `LIVE_START`
  - attr keys: `compare_accumulated`
  - slot keys: `target_slot`
  - example: ability 32, trigger ON_PLAY, frame ACTIVATE_ENERGY

- `TAP_OPPONENT`
  - template: `tap opponent`
  - value role: `count`
  - kind: `effect`
  - count: `19`
  - triggers: `ON_PLAY`, `ON_LIVE_START`, `ON_POSITION_CHANGE`
  - attr keys: `target_player`, `value_enabled`, `value_threshold`, `is_le`, `is_cost_type`
  - slot keys: `target_slot`, `source_zone`
  - params keys: `filter`
  - example: ability 25, trigger ON_PLAY, frame TAP_OPPONENT

- `SET_TAPPED`
  - template: `tap / set tapped`
  - value role: `state`
  - kind: `effect`
  - count: `17`
  - triggers: `ON_PLAY`, `LIVE_START`, `ON_LIVE_START`, `ACTIVATED`
  - attr keys: `is_optional`
  - slot keys: `target_slot`
  - example: ability 17, trigger LIVE_START, frame SET_TAPPED

- `ACTIVATE_MEMBER`
  - template: `activate member {value}`
  - value role: `count`
  - kind: `effect`
  - count: `12`
  - triggers: `ON_LIVE_START`, `ON_PLAY`, `ACTIVATED`, `ON_LEAVES`
  - attr keys: `is_optional`, `target_player`, `group_enabled`, `group_id`, `unit_enabled`
  - slot keys: `target_slot`
  - example: ability 123, trigger ON_PLAY, frame ACTIVATE_MEMBER

- `BATON_TOUCH_MOD`
  - template: `modify baton touch`
  - value role: `none`
  - kind: `effect`
  - count: `1`
  - triggers: `CONSTANT`
  - attr keys: `is_optional`
  - slot keys: `target_slot`
  - example: ability 477, trigger CONSTANT, frame BATON_TOUCH_MOD

- `FORMATION_CHANGE`
  - template: `formation change`
  - value role: `none`
  - kind: `effect`
  - count: `1`
  - triggers: `ON_LIVE_SUCCESS`
  - attr keys: `target_player`, `is_optional`
  - slot keys: `target_slot`
  - example: ability 431, trigger ON_LIVE_SUCCESS, frame FORMATION_CHANGE

- `PREVENT_BATON_TOUCH`
  - template: `prevent baton touch`
  - value role: `none`
  - kind: `condition`
  - count: `1`
  - triggers: `CONSTANT`
  - slot keys: `target_slot`
  - example: ability 504, trigger CONSTANT, frame PREVENT_BATON_TOUCH

## Condition

- `SUM_VALUE`
  - template: `sum value`
  - value role: `math`
  - kind: `condition`
  - count: `81`
  - triggers: `ON_LIVE_START`, `ACTIVATED`, `ON_PLAY`, `ON_LIVE_SUCCESS`, `ON_LEAVES`
  - attr keys: `once_per_turn`
  - slot keys: `target_slot`, `comparison`
  - example: ability 19, trigger ON_PLAY, frame SUM_VALUE

- `COUNT_STAGE`
  - template: `count(stage) {comparison} {value}`
  - value role: `threshold`
  - kind: `condition`
  - count: `49`
  - triggers: `ON_LIVE_START`, `ON_PLAY`, `ON_LIVE_SUCCESS`, `CONSTANT`, `ACTIVATED`
  - attr keys: `group_enabled`, `group_id`, `unit_enabled`, `unit_id`, `target_player`, `special_id`, `char_id_1`, `is_tapped`
  - slot keys: `target_slot`, `comparison`
  - params keys: `raw_cond`, `MIN`
  - example: ability 38, trigger ON_PLAY, frame COUNT_STAGE

- `COUNT_ENERGY`
  - template: `count(energy) {comparison} {value}`
  - value role: `threshold`
  - kind: `condition`
  - count: `24`
  - triggers: `CONSTANT`, `ON_PLAY`, `ON_LIVE_START`, `ACTIVATED`, `LIVE_START`
  - attr keys: `once_per_turn`
  - slot keys: `target_slot`, `comparison`
  - example: ability 31, trigger LIVE_START, frame COUNT_ENERGY

- `GROUP_FILTER`
  - template: `group filter`
  - value role: `none`
  - kind: `condition`
  - count: `22`
  - triggers: `ON_LIVE_START`, `ON_PLAY`, `ON_LIVE_SUCCESS`, `ACTIVATED`, `ON_REVEAL`
  - attr keys: `card_type`, `group_enabled`, `group_id`, `zone_mask`, `char_id_1`, `once_per_turn`, `unit_enabled`, `unit_id`
  - slot keys: `target_slot`, `comparison`
  - example: ability 76, trigger ON_PLAY, frame GROUP_FILTER

- `BATON`
  - template: `baton`
  - value role: `none`
  - kind: `condition`
  - count: `19`
  - triggers: `ON_PLAY`, `CONSTANT`, `ON_LEAVES`, `LIVE_START`
  - attr keys: `group_enabled`, `group_id`, `unit_enabled`, `unit_id`, `value_enabled`, `value_threshold`, `is_cost_type`, `not_has_blade_heart`
  - example: ability 27, trigger ON_PLAY, frame BATON

- `COUNT_SUCCESS_LIVE`
  - template: `count(success_live) {comparison} {value}`
  - value role: `threshold`
  - kind: `condition`
  - count: `19`
  - triggers: `ON_LIVE_START`, `ON_LIVE_SUCCESS`, `ON_PLAY`, `CONSTANT`
  - attr keys: `group_enabled`, `group_id`
  - slot keys: `target_slot`, `comparison`
  - example: ability 145, trigger ON_PLAY, frame COUNT_SUCCESS_LIVE

- `HAS_KEYWORD`
  - template: `has keyword {keyword}`
  - value role: `none`
  - kind: `condition`
  - count: `19`
  - triggers: `ON_LIVE_START`, `ON_REVEAL`, `ON_PLAY`, `ON_LIVE_SUCCESS`, `ACTIVATED`
  - attr keys: `char_id_1`, `once_per_turn`, `group_enabled`, `group_id`, `keyword_energy`, `keyword_member`
  - slot keys: `target_slot`, `comparison`
  - example: ability 24, trigger ON_PLAY, frame HAS_KEYWORD

- `HAS_MEMBER`
  - template: `has member`
  - value role: `none`
  - kind: `condition`
  - count: `16`
  - triggers: `ON_LIVE_START`, `ON_PLAY`, `ON_LIVE_SUCCESS`
  - attr keys: `group_enabled`, `group_id`, `char_id_1`, `value_enabled`, `value_threshold`, `is_cost_type`, `special_id`, `unit_enabled`
  - slot keys: `target_slot`, `comparison`, `area_idx`
  - example: ability 102, trigger ON_PLAY, frame HAS_MEMBER

- `DISCARDED_CARDS`
  - template: `discarded cards`
  - value role: `threshold`
  - kind: `condition`
  - count: `11`
  - triggers: `ON_LIVE_START`, `ACTIVATED`, `ON_PLAY`, `LIVE_START`
  - attr keys: `card_type`, `has_blade_heart`, `zone_mask`, `group_enabled`, `group_id`
  - slot keys: `target_slot`, `comparison`
  - example: ability 47, trigger ON_PLAY, frame DISCARDED_CARDS

- `COUNT_HEARTS`
  - template: `count(hearts) {comparison} {value}`
  - value role: `threshold`
  - kind: `condition`
  - count: `10`
  - triggers: `ON_LIVE_SUCCESS`, `ON_LIVE_START`, `ON_PLAY`
  - attr keys: `group_enabled`, `group_id`
  - slot keys: `target_slot`, `comparison`
  - example: ability 173, trigger ON_PLAY, frame COUNT_HEARTS

- `SCORE_COMPARE`
  - template: `compare score`
  - value role: `threshold`
  - kind: `condition`
  - count: `10`
  - triggers: `ON_LIVE_SUCCESS`, `ON_LIVE_START`, `ON_PLAY`, `ACTIVATED`
  - attr keys: `once_per_turn`
  - slot keys: `target_slot`, `comparison`
  - example: ability 144, trigger ON_PLAY, frame SCORE_COMPARE

- `IS_CENTER`
  - template: `is center`
  - value role: `none`
  - kind: `condition`
  - count: `7`
  - triggers: `ACTIVATED`, `ON_PLAY`, `ON_LIVE_START`
  - attr keys: `once_per_turn`
  - slot keys: `target_slot`, `comparison`
  - example: ability 77, trigger ON_PLAY, frame IS_CENTER

- `SCORE_TOTAL_CHECK`
  - template: `score total check`
  - value role: `threshold`
  - kind: `condition`
  - count: `7`
  - triggers: `ON_PLAY`, `ON_LIVE_START`, `CONSTANT`
  - slot keys: `target_slot`, `comparison`
  - example: ability 74, trigger ON_PLAY, frame SCORE_TOTAL_CHECK

- `COUNT_DISCARD`
  - template: `count(discard) {comparison} {value}`
  - value role: `threshold`
  - kind: `condition`
  - count: `5`
  - triggers: `ON_LIVE_START`, `ON_PLAY`
  - attr keys: `card_type`, `group_enabled`, `group_id`, `unique_names`, `has_blade_heart`, `unit_enabled`, `unit_id`
  - slot keys: `target_slot`, `comparison`
  - example: ability 187, trigger ON_PLAY, frame COUNT_DISCARD

- `COUNT_GROUP`
  - template: `count(group) {comparison} {value}`
  - value role: `threshold`
  - kind: `condition`
  - count: `4`
  - triggers: `ON_LIVE_START`, `ON_PLAY`
  - attr keys: `unique_names`, `unit_enabled`, `unit_id`, `group_enabled`, `group_id`, `zone_mask`
  - slot keys: `target_slot`, `comparison`
  - params keys: `raw_cond`, `MIN`
  - example: ability 132, trigger ON_PLAY, frame COUNT_GROUP

- `COUNT_SUCCESS`
  - template: `count(success) {comparison} {value}`
  - value role: `threshold`
  - kind: `condition`
  - count: `3`
  - triggers: `CONSTANT`
  - attr keys: `target_player`, `is_ge`, `is_eq`
  - slot keys: `target_slot`
  - example: ability 452, trigger CONSTANT, frame COUNT_SUCCESS

- `IS_SELF_MOVE`
  - template: `is self move`
  - value role: `none`
  - kind: `condition`
  - count: `3`
  - triggers: `ON_POSITION_CHANGE`
  - attr keys: `once_per_turn`
  - slot keys: `target_slot`, `comparison`
  - example: ability 597, trigger ON_POSITION_CHANGE, frame IS_SELF_MOVE

- `MAIN_PHASE`
  - template: `main phase`
  - value role: `none`
  - kind: `condition`
  - count: `3`
  - triggers: `ON_POSITION_CHANGE`, `ON_MOVE_TO_DISCARD`, `ON_MEMBER_TAP`
  - attr keys: `once_per_turn`
  - slot keys: `target_slot`, `comparison`
  - example: ability 606, trigger ON_POSITION_CHANGE, frame MAIN_PHASE

- `SUCCESS_PILE_COUNT`
  - template: `success pile count`
  - value role: `threshold`
  - kind: `condition`
  - count: `3`
  - triggers: `ON_PLAY`, `ON_LIVE_START`
  - attr keys: `group_enabled`, `target_player`, `group_id`, `card_type`, `special_id`
  - slot keys: `target_slot`, `comparison`
  - example: ability 79, trigger ON_PLAY, frame SUCCESS_PILE_COUNT

- `COUNT_BLADE_HEART_TYPES`
  - template: `count(blade_heart_types) {comparison} {value}`
  - value role: `threshold`
  - kind: `condition`
  - count: `2`
  - triggers: `ON_REVEAL`
  - attr keys: `once_per_turn`
  - slot keys: `target_slot`, `comparison`
  - example: ability 586, trigger ON_REVEAL, frame COUNT_BLADE_HEART_TYPES

- `COUNT_HAND`
  - template: `count(hand) {comparison} {value}`
  - value role: `threshold`
  - kind: `condition`
  - count: `2`
  - triggers: `ON_LIVE_START`, `ON_LIVE_SUCCESS`
  - slot keys: `target_slot`, `comparison`
  - example: ability 203, trigger ON_LIVE_START, frame COUNT_HAND

- `COUNT_LIVE_ZONE`
  - template: `count(live_zone) {comparison} {value}`
  - value role: `threshold`
  - kind: `condition`
  - count: `2`
  - triggers: `ON_LIVE_START`, `ON_LIVE_SUCCESS`
  - attr keys: `group_enabled`, `group_id`, `special_id`, `zone_mask`
  - slot keys: `target_slot`, `comparison`
  - example: ability 346, trigger ON_LIVE_START, frame COUNT_LIVE_ZONE

- `COUNT_SUCCESS_LIVE_SCORE`
  - template: `count(success_live_score) {comparison} {value}`
  - value role: `threshold`
  - kind: `condition`
  - count: `2`
  - triggers: `ON_LIVE_START`
  - slot keys: `target_slot`, `comparison`
  - example: ability 361, trigger ON_LIVE_START, frame COUNT_SUCCESS_LIVE_SCORE

- `SYNC_COST`
  - template: `sync cost`
  - value role: `none`
  - kind: `condition`
  - count: `2`
  - triggers: `ON_LIVE_START`
  - attr keys: `group_enabled`, `group_id`
  - slot keys: `target_slot`, `comparison`, `area_idx`
  - example: ability 195, trigger ON_LIVE_START, frame SYNC_COST

- `TOTAL_BLADES`
  - template: `total blades`
  - value role: `none`
  - kind: `condition`
  - count: `2`
  - triggers: `ON_LIVE_START`
  - slot keys: `target_slot`, `comparison`
  - example: ability 324, trigger ON_LIVE_START, frame TOTAL_BLADES

- `AREA_CHECK`
  - template: `area check`
  - value role: `none`
  - kind: `condition`
  - count: `1`
  - triggers: `ON_PLAY`
  - example: ability 87, trigger ON_PLAY, frame AREA_CHECK

- `CHECK_ALL_MEMBERS`
  - template: `check all members`
  - value role: `none`
  - kind: `condition`
  - count: `1`
  - triggers: `LIVE_START`
  - example: ability 6, trigger LIVE_START, frame CHECK_ALL_MEMBERS

- `COUNT_BLADES`
  - template: `count(blades) {comparison} {value}`
  - value role: `threshold`
  - kind: `condition`
  - count: `1`
  - triggers: `ON_LIVE_START`
  - attr keys: `target_player`
  - slot keys: `target_slot`, `comparison`
  - example: ability 253, trigger ON_LIVE_START, frame COUNT_BLADES

- `COUNT_ENERGY_EXACT`
  - template: `count(energy_exact) {comparison} {value}`
  - value role: `threshold`
  - kind: `condition`
  - count: `1`
  - triggers: `ON_LIVE_START`
  - slot keys: `target_slot`
  - example: ability 336, trigger ON_LIVE_START, frame COUNT_ENERGY_EXACT

- `COUNT_LIVE_HEARTS`
  - template: `count(live_hearts) {comparison} {value}`
  - value role: `threshold`
  - kind: `condition`
  - count: `1`
  - triggers: `LIVE_START`
  - attr keys: `card_type`, `color_mask`
  - slot keys: `target_slot`, `comparison`
  - example: ability 2, trigger LIVE_START, frame COUNT_LIVE_HEARTS

- `DECK_REFRESHED`
  - template: `deck refreshed`
  - value role: `none`
  - kind: `condition`
  - count: `1`
  - triggers: `ON_LIVE_SUCCESS`
  - slot keys: `target_slot`, `comparison`
  - example: ability 403, trigger ON_LIVE_SUCCESS, frame DECK_REFRESHED

- `HAS_EXCESS_HEART`
  - template: `has excess heart`
  - value role: `none`
  - kind: `condition`
  - count: `1`
  - triggers: `ON_LIVE_SUCCESS`
  - slot keys: `target_slot`, `comparison`
  - example: ability 420, trigger ON_LIVE_SUCCESS, frame HAS_EXCESS_HEART

- `HEART_LEAD`
  - template: `heart lead`
  - value role: `none`
  - kind: `condition`
  - count: `1`
  - triggers: `ON_LIVE_SUCCESS`
  - slot keys: `target_slot`, `comparison`
  - example: ability 432, trigger ON_LIVE_SUCCESS, frame HEART_LEAD

- `NOT_HAS_EXCESS_HEART`
  - template: `does not have excess heart`
  - value role: `none`
  - kind: `condition`
  - count: `1`
  - triggers: `ON_LIVE_SUCCESS`
  - attr keys: `target_player`
  - slot keys: `target_slot`, `comparison`
  - example: ability 429, trigger ON_LIVE_SUCCESS, frame NOT_HAS_EXCESS_HEART

- `OPPONENT_ENERGY_DIFF`
  - template: `opponent energy difference`
  - value role: `threshold`
  - kind: `condition`
  - count: `1`
  - triggers: `ON_LIVE_SUCCESS`
  - slot keys: `target_slot`, `comparison`
  - example: ability 395, trigger ON_LIVE_SUCCESS, frame OPPONENT_ENERGY_DIFF

- `TARGET_MEMBER_HAS_NO_HEARTS`
  - template: `target member has no hearts`
  - value role: `none`
  - kind: `condition`
  - count: `1`
  - triggers: `ON_ABILITY_RESOLVE`
  - slot keys: `target_slot`, `comparison`
  - example: ability 607, trigger ON_ABILITY_RESOLVE, frame TARGET_MEMBER_HAS_NO_HEARTS

- `TYPE_CHECK`
  - template: `type check`
  - value role: `none`
  - kind: `condition`
  - count: `1`
  - triggers: `ACTIVATED`
  - example: ability 560, trigger ACTIVATED, frame TYPE_CHECK

## Control

- `RETURN`
  - template: `end ability`
  - value role: `none`
  - kind: `control`
  - count: `612`
  - triggers: `ON_LIVE_START`, `ON_PLAY`, `CONSTANT`, `ON_LIVE_SUCCESS`, `ACTIVATED`
  - attr keys: `once_per_turn`
  - example: ability 0, trigger ON_REVEAL, frame RETURN

- `JUMP_IF_FALSE`
  - template: `if check fails, jump +{value}`
  - value role: `offset`
  - kind: `control`
  - count: `482`
  - triggers: `ON_LIVE_START`, `ON_PLAY`, `ON_LIVE_SUCCESS`, `CONSTANT`, `ACTIVATED`
  - example: ability 2, trigger LIVE_START, frame JUMP_IF_FALSE

- `JUMP`
  - template: `jump +{value}`
  - value role: `offset`
  - kind: `control`
  - count: `112`
  - triggers: `ON_LIVE_START`, `ON_PLAY`, `ACTIVATED`, `ON_LIVE_SUCCESS`, `ON_POSITION_CHANGE`
  - example: ability 25, trigger ON_PLAY, frame JUMP

- `NOP`
  - template: `no-op`
  - value role: `none`
  - kind: `control`
  - count: `71`
  - triggers: `ON_LIVE_START`, `ON_LIVE_SUCCESS`, `ON_PLAY`, `CONSTANT`, `ACTIVATED`
  - attr keys: `group_enabled`, `group_id`, `unit_enabled`, `unit_id`, `card_type`, `unique_names`, `once_per_turn`, `special_id`
  - slot keys: `target_slot`, `comparison`
  - params keys: `raw_cond`, `MIN`, `LESS_THAN`, `AREA`
  - example: ability 25, trigger ON_PLAY, frame NOP

- `PREVENT_PLAY_TO_SLOT`
  - template: `prevent play to slot`
  - value role: `none`
  - kind: `condition`
  - count: `2`
  - triggers: `ON_PLAY`
  - slot keys: `target_slot`
  - example: ability 120, trigger ON_PLAY, frame PREVENT_PLAY_TO_SLOT

- `PREVENT_SET_TO_SUCCESS_PILE`
  - template: `prevent set to success pile`
  - value role: `none`
  - kind: `condition`
  - count: `2`
  - triggers: `ON_LIVE_SUCCESS`, `CONSTANT`
  - slot keys: `target_slot`
  - example: ability 388, trigger ON_LIVE_SUCCESS, frame PREVENT_SET_TO_SUCCESS_PILE

- `NEGATE_EFFECT`
  - template: `negate effect`
  - value role: `none`
  - kind: `effect`
  - count: `1`
  - triggers: `ON_PLAY`
  - slot keys: `target_slot`
  - example: ability 44, trigger ON_PLAY, frame NEGATE_EFFECT

- `RESTRICTION`
  - template: `apply restriction`
  - value role: `none`
  - kind: `effect`
  - count: `1`
  - triggers: `ON_PLAY`
  - slot keys: `target_slot`
  - example: ability 156, trigger ON_PLAY, frame RESTRICTION

## Draw

- `DRAW`
  - template: `draw {value}`
  - value role: `count`
  - kind: `effect`
  - count: `88`
  - triggers: `ON_PLAY`, `ON_LIVE_SUCCESS`, `ON_LIVE_START`, `ACTIVATED`, `ON_LEAVES`
  - attr keys: `is_optional`, `once_per_turn`, `compare_accumulated`, `target_player`, `group_enabled`, `group_id`
  - slot keys: `target_slot`, `remainder_zone`, `is_dynamic`
  - params keys: `scalar_dynamic`, `per_card`
  - example: ability 1, trigger ON_PLAY, frame DRAW

- `DRAW_UNTIL`
  - template: `draw until {value}`
  - value role: `target`
  - kind: `effect`
  - count: `1`
  - triggers: `ON_PLAY`
  - slot keys: `target_slot`
  - example: ability 24, trigger ON_PLAY, frame DRAW_UNTIL

## Movement

- `MOVE_TO_DISCARD`
  - template: `move {value} from {source_zone} to discard`
  - value role: `count`
  - kind: `effect`
  - count: `164`
  - triggers: `ON_PLAY`, `ON_LIVE_START`, `ACTIVATED`, `ON_LIVE_SUCCESS`, `LIVE_START`
  - attr keys: `is_optional`, `target_player`, `zone_mask`, `once_per_turn`, `group_enabled`, `group_id`, `card_type`, `has_blade_heart`
  - slot keys: `target_slot`, `source_zone`, `dest_zone`, `remainder_zone`, `is_dynamic`
  - params keys: `same_unit_discard`, `scalar_dynamic`
  - example: ability 1, trigger ON_PLAY, frame MOVE_TO_DISCARD

- `MOVE_MEMBER`
  - template: `move member {value}`
  - value role: `count`
  - kind: `effect`
  - count: `29`
  - triggers: `ON_PLAY`, `ON_LIVE_START`, `ACTIVATED`, `LIVE_START`, `ON_LEAVES`
  - attr keys: `target_player`, `is_optional`, `group_id`, `unit_enabled`, `unit_id`, `once_per_turn`
  - slot keys: `target_slot`, `is_wait`, `source_zone`, `params`
  - params keys: `destination`
  - example: ability 17, trigger LIVE_START, frame MOVE_MEMBER

- `MOVE_TO_DECK`
  - template: `move {value} to deck`
  - value role: `count`
  - kind: `effect`
  - count: `14`
  - triggers: `ON_LIVE_START`, `ON_PLAY`, `ON_LIVE_SUCCESS`
  - attr keys: `is_optional`
  - slot keys: `dest_zone`, `remainder_zone`, `target_slot`, `source_zone`
  - example: ability 15, trigger ON_PLAY, frame MOVE_TO_DECK

- `ADD_TO_HAND`
  - template: `add {value} to hand`
  - value role: `count`
  - kind: `effect`
  - count: `13`
  - triggers: `ON_PLAY`, `ON_LIVE_SUCCESS`, `ON_LIVE_START`
  - attr keys: `is_optional`, `target_player`, `card_type`, `zone_mask`
  - slot keys: `target_slot`
  - example: ability 100, trigger ON_PLAY, frame ADD_TO_HAND

- `PLAY_MEMBER_FROM_DISCARD`
  - template: `play member from discard {value}`
  - value role: `count`
  - kind: `effect`
  - count: `9`
  - triggers: `ON_PLAY`, `ACTIVATED`, `ON_LIVE_START`
  - attr keys: `target_player`, `value_enabled`, `value_threshold`, `is_le`, `is_cost_type`, `group_enabled`, `group_id`, `is_tapped`
  - slot keys: `target_slot`, `source_zone`, `is_reveal_until_live`, `is_baton_slot`, `is_empty_slot`
  - example: ability 27, trigger ON_PLAY, frame PLAY_MEMBER_FROM_DISCARD

- `PLAY_MEMBER_FROM_HAND`
  - template: `play member from hand {value}`
  - value role: `count`
  - kind: `effect`
  - count: `7`
  - triggers: `ON_PLAY`
  - attr keys: `target_player`, `card_type`, `group_enabled`, `group_id`, `value_enabled`, `value_threshold`, `is_le`, `is_cost_type`
  - slot keys: `target_slot`, `is_empty_slot`
  - example: ability 10, trigger ON_PLAY, frame PLAY_MEMBER_FROM_HAND

- `PLACE_ENERGY_UNDER_MEMBER`
  - template: `place energy under member {value}`
  - value role: `count`
  - kind: `effect`
  - count: `4`
  - triggers: `ON_PLAY`, `ON_LIVE_START`, `ACTIVATED`
  - attr keys: `is_optional`, `once_per_turn`
  - slot keys: `source_zone`
  - example: ability 122, trigger ON_PLAY, frame PLACE_ENERGY_UNDER_MEMBER

- `MOVE_TO_HAND`
  - template: `move {value} to hand`
  - value role: `count`
  - kind: `effect`
  - count: `3`
  - triggers: `ON_PLAY`, `LIVE_START`
  - slot keys: `target_slot`, `source_zone`
  - example: ability 58, trigger LIVE_START, frame MOVE_TO_HAND

- `PLAY_LIVE_FROM_DISCARD`
  - template: `play live from discard {value}`
  - value role: `count`
  - kind: `effect`
  - count: `2`
  - triggers: `ACTIVATED`, `ON_POSITION_CHANGE`
  - attr keys: `target_player`, `zone_mask`
  - slot keys: `target_slot`, `source_zone`
  - example: ability 577, trigger ACTIVATED, frame PLAY_LIVE_FROM_DISCARD

- `SWAP_AREA`
  - template: `swap areas`
  - value role: `none`
  - kind: `effect`
  - count: `2`
  - triggers: `ON_PLAY`
  - slot keys: `target_slot`
  - example: ability 95, trigger ON_PLAY, frame SWAP_AREA

- `SWAP_ZONE`
  - template: `swap zones`
  - value role: `none`
  - kind: `effect`
  - count: `2`
  - triggers: `ON_PLAY`
  - attr keys: `target_player`, `group_enabled`, `group_id`, `card_type`, `zone_mask`, `is_optional`
  - slot keys: `target_slot`, `source_zone`, `dest_zone`
  - example: ability 48, trigger ON_PLAY, frame SWAP_ZONE

## Recovery

- `RECOVER_LIVE`
  - template: `recover live {value}`
  - value role: `count`
  - kind: `effect`
  - count: `44`
  - triggers: `ACTIVATED`, `ON_PLAY`, `ON_LIVE_SUCCESS`, `LIVE_START`, `ON_LIVE_START`
  - attr keys: `zone_mask`, `group_enabled`, `group_id`, `is_optional`, `target_player`, `value_enabled`, `value_threshold`, `heart_type`
  - slot keys: `target_slot`, `source_zone`
  - example: ability 7, trigger ACTIVATED, frame RECOVER_LIVE

- `RECOVER_MEMBER`
  - template: `recover member {value}`
  - value role: `count`
  - kind: `effect`
  - count: `28`
  - triggers: `ON_PLAY`, `ACTIVATED`, `ON_LIVE_START`, `ON_LIVE_SUCCESS`, `ON_MOVE_TO_DISCARD`
  - attr keys: `zone_mask`, `group_enabled`, `group_id`, `is_optional`, `value_enabled`, `is_cost_type`, `value_threshold`, `is_le`
  - slot keys: `target_slot`, `source_zone`
  - example: ability 36, trigger ON_PLAY, frame RECOVER_MEMBER

- `GRANT_ABILITY`
  - template: `grant ability`
  - value role: `none`
  - kind: `effect`
  - count: `11`
  - triggers: `ON_PLAY`, `ON_LIVE_START`, `ACTIVATED`, `ON_REVEAL`
  - slot keys: `target_slot`
  - example: ability 79, trigger ON_PLAY, frame GRANT_ABILITY

## Resource

- `ADD_BLADES`
  - template: `add blades {value}`
  - value role: `count`
  - kind: `effect`
  - count: `91`
  - triggers: `ON_LIVE_START`, `CONSTANT`, `ON_PLAY`, `ACTIVATED`, `ON_POSITION_CHANGE`
  - attr keys: `target_player`, `compare_accumulated`, `group_enabled`, `is_optional`, `group_id`, `duration`, `once_per_turn`
  - slot keys: `target_slot`, `remainder_zone`, `is_dynamic`
  - params keys: `scalar_dynamic`
  - example: ability 6, trigger LIVE_START, frame ADD_BLADES

- `ADD_HEARTS`
  - template: `add hearts {value}`
  - value role: `count`
  - kind: `effect`
  - count: `82`
  - triggers: `ON_LIVE_START`, `CONSTANT`, `ON_REVEAL`, `ON_PLAY`, `ACTIVATED`
  - attr keys: `target_player`, `card_type`, `compare_accumulated`, `is_optional`, `group_enabled`, `group_id`, `keyword`, `is_tapped`
  - slot keys: `target_slot`, `remainder_zone`, `is_dynamic`
  - params keys: `heart_type`, `all`, `scalar_dynamic`
  - example: ability 2, trigger LIVE_START, frame ADD_HEARTS

- `BOOST_SCORE`
  - template: `boost score {value}`
  - value role: `count`
  - kind: `effect`
  - count: `81`
  - triggers: `ON_LIVE_START`, `ON_LIVE_SUCCESS`, `CONSTANT`
  - attr keys: `target_player`, `compare_accumulated`, `group_enabled`, `group_id`, `unique_names`, `is_tapped`, `once_per_turn`
  - slot keys: `target_slot`, `remainder_zone`, `is_dynamic`
  - params keys: `scalar_dynamic`
  - example: ability 200, trigger ON_LIVE_START, frame BOOST_SCORE

- `PAY_ENERGY`
  - template: `pay energy {value}`
  - value role: `count`
  - kind: `effect`
  - count: `65`
  - triggers: `ON_LIVE_START`, `ACTIVATED`, `ON_PLAY`, `ON_LIVE_SUCCESS`, `ON_MOVE_TO_DISCARD`
  - attr keys: `is_optional`, `once_per_turn`, `target_player`
  - slot keys: `target_slot`
  - example: ability 7, trigger ACTIVATED, frame PAY_ENERGY

- `ENERGY_CHARGE`
  - template: `charge energy {value}`
  - value role: `count`
  - kind: `effect`
  - count: `26`
  - triggers: `ON_LIVE_SUCCESS`, `ON_PLAY`, `CONSTANT`, `ACTIVATED`, `ON_LIVE_START`
  - attr keys: `is_optional`, `once_per_turn`
  - slot keys: `target_slot`, `is_wait`
  - example: ability 19, trigger ON_PLAY, frame ENERGY_CHARGE

- `REDUCE_HEART_REQ`
  - template: `reduce heart requirement {value}`
  - value role: `count`
  - kind: `effect`
  - count: `14`
  - triggers: `ON_LIVE_START`
  - attr keys: `target_player`, `compare_accumulated`, `group_enabled`, `group_id`, `special_id`
  - slot keys: `target_slot`, `remainder_zone`, `is_dynamic`
  - params keys: `scalar_dynamic`
  - example: ability 222, trigger ON_LIVE_START, frame REDUCE_HEART_REQ

- `REDUCE_COST`
  - template: `reduce cost {value}`
  - value role: `count`
  - kind: `effect`
  - count: `8`
  - triggers: `CONSTANT`, `ACTIVATED`
  - attr keys: `target_player`, `group_enabled`, `group_id`, `special_id`, `compare_accumulated`, `unique_names`
  - slot keys: `target_slot`, `source_zone`, `remainder_zone`, `is_dynamic`
  - params keys: `per_card`
  - example: ability 478, trigger CONSTANT, frame REDUCE_COST

- `INCREASE_COST`
  - template: `increase cost {value}`
  - value role: `count`
  - kind: `effect`
  - count: `4`
  - triggers: `CONSTANT`, `ACTIVATED`
  - attr keys: `target_player`, `compare_accumulated`
  - slot keys: `target_slot`, `remainder_zone`, `is_dynamic`
  - params keys: `scalar_dynamic`
  - example: ability 496, trigger CONSTANT, frame INCREASE_COST

- `SET_HEART_COST`
  - template: `set heart cost {value}`
  - value role: `count`
  - kind: `effect`
  - count: `4`
  - triggers: `ON_LIVE_START`
  - slot keys: `target_slot`
  - example: ability 304, trigger ON_LIVE_START, frame SET_HEART_COST

- `INCREASE_HEART_COST`
  - template: `increase heart cost {value}`
  - value role: `count`
  - kind: `effect`
  - count: `2`
  - triggers: `ON_LIVE_START`, `CONSTANT`
  - slot keys: `target_slot`
  - example: ability 357, trigger ON_LIVE_START, frame INCREASE_HEART_COST

- `REDUCE_LIVE_SET_LIMIT`
  - template: `reduce live set limit {value}`
  - value role: `count`
  - kind: `effect`
  - count: `2`
  - triggers: `ACTIVATED`, `ON_POSITION_CHANGE`
  - slot keys: `target_slot`
  - example: ability 577, trigger ACTIVATED, frame REDUCE_LIVE_SET_LIMIT

- `CALC_SUM_COST`
  - template: `calculate sum cost`
  - value role: `none`
  - kind: `effect`
  - count: `1`
  - triggers: `ON_LIVE_START`
  - example: ability 211, trigger ON_LIVE_START, frame CALC_SUM_COST

- `DIV_VALUE`
  - template: `divide value`
  - value role: `count`
  - kind: `effect`
  - count: `1`
  - triggers: `ON_LIVE_START`
  - example: ability 203, trigger ON_LIVE_START, frame DIV_VALUE

- `INCREASE_HEART_REQ`
  - template: `increase heart requirement {value}`
  - value role: `count`
  - kind: `effect`
  - count: `1`
  - triggers: `ON_LIVE_START`
  - attr keys: `target_player`, `compare_accumulated`
  - slot keys: `remainder_zone`, `is_dynamic`
  - params keys: `scalar_dynamic`
  - example: ability 354, trigger ON_LIVE_START, frame INCREASE_HEART_REQ

- `IN_SUCCESS_PILE`
  - template: `put in success pile`
  - value role: `none`
  - kind: `effect`
  - count: `1`
  - triggers: `CONSTANT`
  - slot keys: `target_slot`
  - example: ability 492, trigger CONSTANT, frame IN_SUCCESS_PILE

- `PAY_ENERGY_DYNAMIC`
  - template: `pay dynamic energy {value}`
  - value role: `count`
  - kind: `effect`
  - count: `1`
  - triggers: `ACTIVATED`
  - attr keys: `is_optional`
  - params keys: `source`
  - example: ability 552, trigger ACTIVATED, frame PAY_ENERGY_DYNAMIC

- `REDUCE_YELL_COUNT`
  - template: `reduce yell count {value}`
  - value role: `count`
  - kind: `effect`
  - count: `1`
  - triggers: `ON_LIVE_START`
  - slot keys: `target_slot`
  - example: ability 215, trigger ON_LIVE_START, frame REDUCE_YELL_COUNT

- `SET_SCORE`
  - template: `set score {value}`
  - value role: `value`
  - kind: `effect`
  - count: `1`
  - triggers: `ON_LIVE_SUCCESS`
  - slot keys: `target_slot`
  - example: ability 401, trigger ON_LIVE_SUCCESS, frame SET_SCORE

## Search

- `LOOK_AND_CHOOSE`
  - template: `look {value}, choose {choose_count}`
  - value role: `count`
  - kind: `effect`
  - count: `44`
  - triggers: `ON_PLAY`, `LIVE_START`, `ACTIVATED`, `ON_LEAVES`, `ON_LIVE_START`
  - attr keys: `is_optional`, `target_player`, `card_type`, `group_enabled`, `group_id`, `value_enabled`, `value_threshold`, `is_cost_type`
  - slot keys: `target_slot`, `source_zone`, `remainder_zone`
  - params keys: `count`, `choose_count`
  - example: ability 3, trigger ON_PLAY, frame LOOK_AND_CHOOSE

- `LOOK_DECK`
  - template: `look at top {value} of deck`
  - value role: `count`
  - kind: `effect`
  - count: `11`
  - triggers: `ON_PLAY`, `ON_LIVE_START`, `ON_LIVE_SUCCESS`
  - attr keys: `target_player`, `card_type`, `group_enabled`, `group_id`, `has_blade_heart`
  - slot keys: `target_slot`
  - example: ability 14, trigger ON_PLAY, frame LOOK_DECK

- `LOOK_REORDER_DISCARD`
  - template: `look top {value} of deck, reorder and discard the rest`
  - value role: `count`
  - kind: `effect`
  - count: `5`
  - triggers: `ON_LIVE_START`, `LIVE_START`, `ON_PLAY`
  - slot keys: `target_slot`
  - example: ability 20, trigger LIVE_START, frame LOOK_REORDER_DISCARD

- `REVEAL_CARDS`
  - template: `reveal {value} cards`
  - value role: `count`
  - kind: `effect`
  - count: `3`
  - triggers: `ON_PLAY`, `ON_LIVE_START`, `ACTIVATED`
  - attr keys: `is_optional`, `card_type`, `group_enabled`, `group_id`
  - slot keys: `target_slot`
  - example: ability 160, trigger ON_PLAY, frame REVEAL_CARDS

- `REVEAL_UNTIL`
  - template: `reveal until {value}`
  - value role: `count`
  - kind: `effect`
  - count: `3`
  - triggers: `ACTIVATED`, `ON_PLAY`
  - attr keys: `target_player`, `is_optional`, `card_type`
  - slot keys: `target_slot`, `is_reveal_until_live`, `is_baton_slot`
  - example: ability 100, trigger ON_PLAY, frame REVEAL_UNTIL

- `ORDER_DECK`
  - template: `order deck`
  - value role: `mode`
  - kind: `effect`
  - count: `2`
  - triggers: `ON_PLAY`, `ON_LIVE_SUCCESS`
  - example: ability 14, trigger ON_PLAY, frame ORDER_DECK

- `BOTTOM_DECK`
  - template: `put to bottom of deck`
  - value role: `none`
  - kind: `effect`
  - count: `1`
  - triggers: `ON_PLAY`
  - slot keys: `target_slot`
  - example: ability 8, trigger ON_PLAY, frame BOTTOM_DECK

## Selection

- `SELECT_MEMBER`
  - template: `select member {value}`
  - value role: `count`
  - kind: `condition`
  - count: `74`
  - triggers: `ON_LIVE_START`, `ON_PLAY`, `ACTIVATED`, `LIVE_START`, `ON_LIVE_SUCCESS`
  - attr keys: `target_player`, `group_enabled`, `group_id`, `value_enabled`, `value_threshold`, `is_le`, `is_cost_type`, `is_optional`
  - slot keys: `target_slot`, `source_zone`, `area_idx`, `comparison`
  - params keys: `filter`
  - example: ability 10, trigger ON_PLAY, frame SELECT_MEMBER

- `SELECT_MODE`
  - template: `choose mode {option_names}`
  - value role: `branch_count`
  - kind: `effect`
  - count: `25`
  - triggers: `ON_LIVE_START`, `ON_PLAY`, `ACTIVATED`, `ON_LIVE_SUCCESS`
  - attr keys: `once_per_turn`
  - slot keys: `is_opponent`, `target_slot`
  - example: ability 26, trigger ON_PLAY, frame SELECT_MODE

- `SELECT_CARDS`
  - template: `select cards {value}`
  - value role: `count`
  - kind: `effect`
  - count: `24`
  - triggers: `ON_LIVE_START`, `ON_PLAY`, `ACTIVATED`, `ON_LIVE_SUCCESS`
  - attr keys: `is_optional`, `target_player`, `card_type`, `group_enabled`, `group_id`, `value_enabled`, `value_threshold`, `is_le`
  - slot keys: `target_slot`, `source_zone`, `dest_zone`, `remainder_zone`
  - example: ability 15, trigger ON_PLAY, frame SELECT_CARDS

- `COLOR_SELECT`
  - template: `choose color`
  - value role: `count`
  - kind: `effect`
  - count: `11`
  - triggers: `ON_LIVE_START`
  - attr keys: `target_player`, `color_mask`, `is_optional`
  - slot keys: `target_slot`
  - example: ability 190, trigger ON_LIVE_START, frame COLOR_SELECT

- `OPPONENT_CHOOSE`
  - template: `opponent chooses`
  - value role: `none`
  - kind: `effect`
  - count: `1`
  - triggers: `ON_PLAY`
  - slot keys: `target_slot`
  - example: ability 147, trigger ON_PLAY, frame OPPONENT_CHOOSE

- `SELECT_LIVE`
  - template: `select live {value}`
  - value role: `count`
  - kind: `effect`
  - count: `1`
  - triggers: `ON_LIVE_START`
  - attr keys: `target_player`, `group_enabled`, `group_id`, `card_type`
  - slot keys: `target_slot`, `source_zone`
  - example: ability 216, trigger ON_LIVE_START, frame SELECT_LIVE

- `SELECT_PLAYER`
  - template: `select player`
  - value role: `count`
  - kind: `effect`
  - count: `1`
  - triggers: `ACTIVATED`
  - attr keys: `once_per_turn`
  - slot keys: `target_slot`
  - example: ability 564, trigger ACTIVATED, frame SELECT_PLAYER

## Targeting

- `SET_TARGET_SELF`
  - template: `set target self`
  - value role: `none`
  - kind: `effect`
  - count: `3`
  - triggers: `ON_LIVE_START`, `ON_PLAY`
  - example: ability 55, trigger ON_PLAY, frame SET_TARGET_SELF

- `SET_TARGET_OPPONENT`
  - template: `set target opponent`
  - value role: `none`
  - kind: `effect`
  - count: `2`
  - triggers: `ON_PLAY`, `ON_LIVE_START`
  - example: ability 55, trigger ON_PLAY, frame SET_TARGET_OPPONENT

- `TRIGGER_REMOTE`
  - template: `trigger remote ability`
  - value role: `count`
  - kind: `effect`
  - count: `2`
  - triggers: `ON_PLAY`, `ACTIVATED`
  - attr keys: `target_player`, `card_type`, `group_enabled`, `group_id`, `value_enabled`, `value_threshold`, `is_le`, `is_cost_type`
  - slot keys: `target_slot`
  - example: ability 148, trigger ON_PLAY, frame TRIGGER_REMOTE

## Transform

- `TRANSFORM_COLOR`
  - template: `transform color`
  - value role: `none`
  - kind: `effect`
  - count: `3`
  - triggers: `ON_LIVE_START`, `ON_LIVE_SUCCESS`
  - attr keys: `target_player`, `is_optional`
  - slot keys: `target_slot`
  - example: ability 280, trigger ON_LIVE_START, frame TRANSFORM_COLOR

- `TRANSFORM_HEART`
  - template: `transform heart`
  - value role: `none`
  - kind: `effect`
  - count: `2`
  - triggers: `ON_LIVE_START`
  - attr keys: `target_player`, `color_mask`
  - slot keys: `target_slot`
  - example: ability 232, trigger ON_LIVE_START, frame TRANSFORM_HEART

- `TRANSFORM_BLADES`
  - template: `transform blades`
  - value role: `none`
  - kind: `effect`
  - count: `1`
  - triggers: `ON_LIVE_START`
  - slot keys: `target_slot`
  - example: ability 288, trigger ON_LIVE_START, frame TRANSFORM_BLADES
