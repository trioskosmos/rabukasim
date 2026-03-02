"""Trigger detection patterns.

Triggers determine WHEN an ability activates:
- ON_PLAY: When member enters the stage
- ON_LIVE_START: When a live begins
- ON_LIVE_SUCCESS: When a live succeeds
- ACTIVATED: Manual activation
- CONSTANT: Always active
- etc.

Patterns are organized in tiers:
- Tier 1 (priority 10-19): Icon filenames (most reliable)
- Tier 2 (priority 20-29): Specific phrases
- Tier 3 (priority 30-39): Generic kanji keywords
"""

from .base import Pattern, PatternPhase

TRIGGER_PATTERNS = [
    # ==========================================================================
    # TIER 1: Icon-based triggers (Medium priority)
    # ==========================================================================
    Pattern(
        name="on_play_icon",
        phase=PatternPhase.TRIGGER,
        regex=r"toujyou",
        priority=25,  # Was 10
        output_type="TriggerType.ON_PLAY",
    ),
    Pattern(
        name="on_live_start_icon",
        phase=PatternPhase.TRIGGER,
        regex=r"live_start",
        priority=25,  # Was 10
        output_type="TriggerType.ON_LIVE_START",
    ),
    Pattern(
        name="on_live_success_icon",
        phase=PatternPhase.TRIGGER,
        regex=r"live_success",
        priority=25,  # Was 10
        # Skip if "この能力は...のみ発動する" (activation restriction, not trigger)
        excludes=["この能力は"],
        output_type="TriggerType.ON_LIVE_SUCCESS",
    ),
    Pattern(
        name="activated_icon",
        phase=PatternPhase.TRIGGER,
        regex=r"kidou",
        priority=25,  # Was 10
        output_type="TriggerType.ACTIVATED",
    ),
    Pattern(
        name="constant_icon",
        phase=PatternPhase.TRIGGER,
        regex=r"jyouji",
        priority=25,  # Was 10
        output_type="TriggerType.CONSTANT",
    ),
    Pattern(
        name="on_leaves_icon",
        phase=PatternPhase.TRIGGER,
        regex=r"jidou",
        priority=25,
        output_type="TriggerType.ON_LEAVES",
    ),
    # ==========================================================================
    # TIER 1.5: Composite/Contextual triggers (High priority)
    # These override the generic jidou icon if specific text follows it
    # ==========================================================================
    Pattern(
        name="on_reveal_after_jidou",
        phase=PatternPhase.TRIGGER,
        regex=r"jidou.*?エール(により|で)?公開",
        priority=15,  # Higher than Tier 1/2 generic icons
        output_type="TriggerType.ON_REVEAL",
    ),
    Pattern(
        name="on_leaves_after_jidou",
        phase=PatternPhase.TRIGGER,
        regex=r"jidou.*?(ステージから|が)?(控え室|場外)に置かれた",
        priority=15,
        output_type="TriggerType.ON_LEAVES",
    ),
    Pattern(
        name="on_move_after_jidou",
        phase=PatternPhase.TRIGGER,
        regex=r"jidou.*?(配置|ポジション)を変更",
        priority=15,
        output_type="TriggerType.ON_POSITION_CHANGE",
    ),
    Pattern(
        name="live_end_icon",
        phase=PatternPhase.TRIGGER,
        regex=r"live_end",
        priority=25,  # Was 10
        output_type="TriggerType.TURN_END",
    ),
    # ==========================================================================
    # TIER 2: Specific phrase triggers
    # ==========================================================================
    Pattern(
        name="on_reveal_cheer",
        phase=PatternPhase.TRIGGER,
        regex=r"エールにより公開|エールで公開",
        priority=20,
        output_type="TriggerType.ON_REVEAL",
    ),
    Pattern(
        name="constant_yell_reveal",
        phase=PatternPhase.TRIGGER,
        keywords=["エールで出た"],
        priority=20,
        output_type="TriggerType.CONSTANT",
    ),
    # ==========================================================================
    # TIER 3: Kanji keyword triggers
    # ==========================================================================
    Pattern(
        name="on_play_kanji",
        phase=PatternPhase.TRIGGER,
        regex=r"登場",
        priority=30,
        # Filter: Not when describing "has [Play] ability" etc
        look_ahead_excludes=["能力", "スキル", "を持つ", "を持たない", "がない"],
        output_type="TriggerType.ON_PLAY",
    ),
    Pattern(
        name="on_live_start_kanji",
        phase=PatternPhase.TRIGGER,
        regex=r"ライブ開始|ライブの開始",
        priority=30,
        look_ahead_excludes=["能力", "スキル", "を持つ"],
        output_type="TriggerType.ON_LIVE_START",
    ),
    Pattern(
        name="on_live_success_kanji",
        phase=PatternPhase.TRIGGER,
        regex=r"ライブ成功",
        priority=30,
        look_ahead_excludes=["能力", "スキル", "を持つ"],
        output_type="TriggerType.ON_LIVE_SUCCESS",
    ),
    Pattern(
        name="activated_kanji",
        phase=PatternPhase.TRIGGER,
        keywords=["起動"],
        priority=30,
        look_ahead_excludes=["能力", "スキル", "を持つ"],
        output_type="TriggerType.ACTIVATED",
    ),
    Pattern(
        name="constant_kanji",
        phase=PatternPhase.TRIGGER,
        keywords=["常時"],
        priority=30,
        look_ahead_excludes=["能力", "スキル", "を持つ"],
        output_type="TriggerType.CONSTANT",
    ),
    Pattern(
        name="on_leaves_kanji",
        phase=PatternPhase.TRIGGER,
        keywords=["自動"],
        priority=30,
        look_ahead_excludes=["能力", "スキル", "を持つ"],
        output_type="TriggerType.ON_LEAVES",
    ),
    Pattern(
        name="turn_start",
        phase=PatternPhase.TRIGGER,
        keywords=["ターン開始"],
        priority=30,
        output_type="TriggerType.TURN_START",
    ),
    Pattern(
        name="turn_end_kanji",
        phase=PatternPhase.TRIGGER,
        regex=r"ターン終了|ライブ終了",
        priority=30,
        look_ahead_excludes=["まで"],  # "Until end of turn" is duration, not trigger
        output_type="TriggerType.TURN_END",
    ),
]
