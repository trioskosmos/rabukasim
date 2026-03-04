# -*- coding: utf-8 -*-
"""Effect patterns.

Effects are the actions that occur when an ability activates.
Examples: DRAW, ADD_BLADES, RECOVER_MEMBER, etc.
"""

from .base import Pattern, PatternPhase

EFFECT_PATTERNS = [
    # ==========================================================================
    # Card manipulation effects
    # ==========================================================================
    Pattern(
        name="draw_cards",
        phase=PatternPhase.EFFECT,
        regex=r"カード.*?(\d+)枚.*?引",
        priority=20,
        excludes=["引き入れ"],  # "bring under" is not draw
        consumes=True,
        output_type="EffectType.DRAW",
    ),
    Pattern(
        name="draw_pseudocode",
        phase=PatternPhase.EFFECT,
        regex=r"DRAW\((.*?)\)",
        priority=5,
        consumes=True,
        output_type="EffectType.DRAW",
        extractor=lambda text, m: {
            "type": "EffectType.DRAW",
            "value": int(m.group(1)) if m.group(1).isdigit() else 0,
            "value_cond": m.group(1) if not m.group(1).isdigit() else None,
        },
    ),
    Pattern(
        name="select_cards_pseudocode",
        phase=PatternPhase.EFFECT,
        regex=r"SELECT_CARDS\((.*?)\)",
        priority=10,
        consumes=True,
        output_type="EffectType.SELECT_CARDS",
        extractor=lambda text, m: {
            "type": "EffectType.SELECT_CARDS",
            # Simple dict comprehension for params
            "params": {
                k.strip(): v.strip() for k, v in [p.strip().split("=") for p in m.group(1).split(",") if "=" in p]
            },
        },
    ),
    Pattern(
        name="tap_opponent_pseudocode",
        phase=PatternPhase.EFFECT,
        regex=r"TAP_OPPONENT\((\d+)\)",
        priority=5,
        consumes=True,
        output_type="EffectType.TAP_OPPONENT",
    ),
    Pattern(
        name="tap_member_pseudocode",
        phase=PatternPhase.EFFECT,
        regex=r"TAP_MEMBER\((.*?)\)",
        priority=5,
        consumes=True,
        output_type="EffectType.TAP_MEMBER",
        extractor=lambda text, m: {
            "type": "EffectType.TAP_MEMBER",
            "value": int(m.group(1)) if m.group(1).isdigit() else 1,
            "params": {"target": "targets"} if m.group(1) == "TARGETS" else {},
        },
    ),
    Pattern(
        name="draw_one",
        phase=PatternPhase.EFFECT,
        regex=r"引く",
        priority=50,
        excludes=["引き入れ", "置いた枚数分"],
        consumes=True,
        output_type="EffectType.DRAW",
        output_value=1,
    ),
    Pattern(
        name="look_deck_top",
        phase=PatternPhase.EFFECT,
        regex=r"(?:デッキ|山札)の一番上.*?見る",
        priority=19,
        output_type="EffectType.LOOK_DECK",
        output_value=1,
    ),
    Pattern(
        name="look_deck",
        phase=PatternPhase.EFFECT,
        regex=r"(?:デッキ|山札).*?(\d+)枚.*?(?:見る|見て)",
        priority=20,
        output_type="EffectType.LOOK_DECK",
    ),
    Pattern(
        name="search_deck",
        phase=PatternPhase.EFFECT,
        any_keywords=["探", "サーチ"],
        requires=["デッキ"],
        priority=30,
        output_type="EffectType.SEARCH_DECK",
        output_value=1,
    ),
    Pattern(
        name="search_deck_from",
        phase=PatternPhase.EFFECT,
        # "デッキから...手札に加える" (search deck for card, add to hand)
        regex=r"(?:デッキ|山札)から.*?手札に加",
        priority=5,  # Very high priority to catch before ADD_TO_HAND
        consumes=True,
        output_type="EffectType.SEARCH_DECK",
        output_value=1,
        output_params={"to": "hand"},
    ),
    Pattern(
        name="reveal_cards",
        phase=PatternPhase.EFFECT,
        regex=r"(\d+)枚.*?公開",
        priority=30,
        excludes=["エール"],  # Not cheer-based reveal
        output_type="EffectType.REVEAL_CARDS",
    ),
    Pattern(
        name="reveal_top",
        phase=PatternPhase.EFFECT,
        regex=r"デッキの一番上.*?公開",
        priority=20,
        output_type="EffectType.REVEAL_CARDS",
        output_value=1,
    ),
    Pattern(
        name="choose_heart_icons",
        phase=PatternPhase.EFFECT,
        regex=r"({{heart_.*?}}か{{heart_.*?}}).*?選ぶ",
        priority=15,
        output_type="EffectType.COLOR_SELECT",
    ),
    Pattern(
        name="return_discard_to_deck_bottom",
        phase=PatternPhase.EFFECT,
        regex=r"デッキの一番下に置く",
        priority=15,
        output_type="EffectType.MOVE_TO_DECK",
        output_params={"to": "deck_bottom"},
    ),
    Pattern(
        name="add_hearts_color_text",
        phase=PatternPhase.EFFECT,
        regex=r"［(赤|青|黄|緑|紫|桃)ハート］.*?得る",
        priority=15,
        output_type="EffectType.ADD_HEARTS",
        extractor=lambda text, m: {"type": "EffectType.ADD_HEARTS", "value": 1, "params": {"color_text": m.group(1)}},
    ),
    Pattern(
        name="look_and_choose_order",
        phase=PatternPhase.EFFECT,
        regex=r"LOOK_AND_CHOOSE_ORDER\((\d+)\)",
        priority=20,
        output_type="EffectType.ORDER_DECK",
        extractor=lambda text, m: {
            "type": "EffectType.ORDER_DECK",
            "value": int(m.group(1)),
        },
    ),
    Pattern(
        name="select_from_pool",
        phase=PatternPhase.EFFECT,
        regex=r"の中から.*?(\d+)?(枚|人).*?選ぶ",
        priority=20,
        output_type="EffectType.LOOK_AND_CHOOSE",
        extractor=lambda text, m: {
            "type": "EffectType.LOOK_AND_CHOOSE",
            "value": int(m.group(1)) if m.group(1) else 1,
        },
    ),
    # ==========================================================================
    # Recovery effects
    # ==========================================================================
    Pattern(
        name="add_self_to_hand",
        phase=PatternPhase.EFFECT,
        regex=r"この(カード|メンバー)を手札に加",
        priority=15,
        output_type="EffectType.ADD_TO_HAND",
        output_params={"target": "self", "to": "hand"},
    ),
    Pattern(
        name="place_member_to_hand",
        phase=PatternPhase.EFFECT,
        regex=r"メンバーを?.*?手札に加",
        priority=30,  # Lower precedence
        consumes=True,
        output_type="EffectType.ADD_TO_HAND",
        output_params={"to": "hand"},
    ),
    Pattern(
        name="recover_member",
        phase=PatternPhase.EFFECT,
        regex=r"控え室から.*?メンバーを?.*?手札に加",
        priority=10,  # High precedence to consume early
        consumes=True,
        output_type="EffectType.RECOVER_MEMBER",
        output_value=1,
        output_params={"from": "discard", "to": "hand"},
    ),
    Pattern(
        name="recover_from_success",
        phase=PatternPhase.EFFECT,
        regex=r"成功ライブカード(?:置き場)?[\s\S]*?手札に加",
        priority=20,
        output_type="EffectType.RECOVER_LIVE",
        output_value=1,
        output_params={"from": "success_zone", "to": "hand"},
    ),
    Pattern(
        name="recover_live",
        phase=PatternPhase.EFFECT,
        regex=r"控え室から.*?ライブカードを?.*?手札に加",
        priority=10,
        consumes=True,
        output_type="EffectType.RECOVER_LIVE",
        output_value=1,
        output_params={"from": "discard", "to": "hand"},
    ),
    Pattern(
        name="add_to_hand_from_deck",
        phase=PatternPhase.EFFECT,
        keywords=["デッキ", "手札に加え"],
        excludes=["見る", "選"],  # Not look and choose
        priority=25,
        consumes=True,
        output_type="EffectType.ADD_TO_HAND",
        output_params={"from": "deck"},
    ),
    Pattern(
        name="look_and_choose_reveal",
        phase=PatternPhase.EFFECT,
        regex=r"LOOK_AND_CHOOSE_REVEAL\((.*?)\)",
        priority=10,
        consumes=True,
        output_type="EffectType.LOOK_AND_CHOOSE",
        extractor=lambda text, m: {
            "type": "EffectType.LOOK_AND_CHOOSE",
            "value": int(m.group(1).split(",")[0].strip()),
            "params": {
                "choose_count": int(m.group(1).split("choose_count=")[1].split(",")[0].strip())
                if "choose_count=" in m.group(1)
                else 1,
                "source": "revealed",
            },
        },
    ),
    Pattern(
        name="look_and_choose",
        phase=PatternPhase.EFFECT,
        # Relaxed regex to allow filters between "look" and "choose"
        regex=r"(?:カードを?|[\{\[].*?[\}\]])?(\d+)枚(見て|見る).*?(?:その中から|その中にある|公開された).*?(?:カードを?)?(\d+)?(?:枚|つ)?.*?手札に加",
        priority=10,  # High priority to catch before LOOK_DECK
        consumes=True,
        output_type="EffectType.LOOK_AND_CHOOSE",
        extractor=lambda text, m: {
            "type": "EffectType.LOOK_AND_CHOOSE",
            "value": int(m.group(1)),
            "params": {"choose_count": int(m.group(3)) if m.group(3) else 1},
        },
    ),
    Pattern(
        name="discard_looked",
        phase=PatternPhase.EFFECT,
        # "そのカードを控え室に置く" (referring to looked card)
        regex=r"(?:その|公開した|見た)カードを?.*?控え室に置",
        priority=25,
        consumes=True,
        output_type="EffectType.LOOK_AND_CHOOSE",
        output_value=1,
        output_params={"look_count": 1, "destination": "discard"},
    ),
    Pattern(
        name="mill_to_discard",
        phase=PatternPhase.EFFECT,
        # "デッキの上からカードをX枚控え室に置く"
        regex=r"(?:デッキ|山札).*?(\d+)枚.*?控え室に置",
        priority=15,  # Higher priority than generic swap_to_discard
        consumes=True,
        output_type="EffectType.SWAP_CARDS",
        extractor=lambda text, m: {
            "type": "EffectType.SWAP_CARDS",
            "value": int(m.group(1)),
            "params": {"from": "deck", "target": "discard"},
        },
    ),
    Pattern(
        name="discard_remainder",
        phase=PatternPhase.EFFECT,
        regex=r"残りを?控え室に",
        priority=20,
        consumes=True,
        output_type="EffectType.SWAP_CARDS",
        output_params={"target": "discard"},
    ),
    Pattern(
        name="choose_player",
        phase=PatternPhase.EFFECT,
        regex=r"自分か相手を選",
        priority=5,  # Very high priority
        output_type="EffectType.META_RULE",
        output_params={"target": "PLAYER_SELECT"},
    ),
    # ==========================================================================
    # Stat modification effects
    # ==========================================================================
    Pattern(
        name="add_blades",
        phase=PatternPhase.EFFECT,
        regex=r"(?:{{icon_blade.*?}})?ブレード[^スコア場合]*?[+＋](\d+|１|２|３)",
        priority=20,
        output_type="EffectType.ADD_BLADES",
    ),
    Pattern(
        name="add_blades_gain",
        phase=PatternPhase.EFFECT,
        regex=r"(?:{{icon_blade.*?}})?ブレード.*?を得る",
        priority=30,
        output_type="EffectType.ADD_BLADES",
        output_value=1,
    ),
    Pattern(
        name="add_hearts",
        phase=PatternPhase.EFFECT,
        regex=r"ハート[^スコア場合]*?[+＋](\d+|１|２|３)",
        priority=20,
        output_type="EffectType.ADD_HEARTS",
    ),
    Pattern(
        name="add_hearts_gain",
        phase=PatternPhase.EFFECT,
        regex=r"(?:{{(?:heart_\d+|icon_heart).*?}})?ハートを?(\d+|１|２|３)?(つ|個|枚)?(を)?得る",
        priority=20,
        output_type="EffectType.ADD_HEARTS",
        extractor=lambda text, m: {
            "type": "EffectType.ADD_HEARTS",
            "value": int(m.group(1)) if m.group(1) else 1,
        },
    ),
    Pattern(
        name="add_hearts_icon",
        phase=PatternPhase.EFFECT,
        # Heart icons: {{heart_XX.png|heartXX}}を得る
        regex=r"({{heart_\d+\.png\|heart\d+}})+(を)?得る",
        priority=10,  # Very high priority
        consumes=True,
        output_type="EffectType.ADD_HEARTS",
        extractor=lambda text, m: {
            "type": "EffectType.ADD_HEARTS",
            "value": text[: m.end()].count("{{heart_"),  # Count heart icons
            "params": {},
        },
    ),
    Pattern(
        name="boost_score",
        phase=PatternPhase.EFFECT,
        regex=r"スコア.*?[+＋](\d+|１|２|３)",
        priority=20,
        output_type="EffectType.BOOST_SCORE",
    ),
    Pattern(
        name="reduce_heart_req",
        phase=PatternPhase.EFFECT,
        any_keywords=["必要ハート", "ハート条件"],
        requires=["減", "少なく"],
        priority=25,
        output_type="EffectType.REDUCE_HEART_REQ",
    ),
    # ==========================================================================
    # Energy effects
    # ==========================================================================
    Pattern(
        name="energy_charge",
        phase=PatternPhase.EFFECT,
        regex=r"エネルギー(?:カード)?を?(\d+)?枚.*?(?:置く|加える|チャージ)",
        priority=25,
        excludes=["控え室", "の上から", "を公開", "公開された"],
        output_type="EffectType.ENERGY_CHARGE",
    ),
    # ==========================================================================
    # Movement/Position effects
    # ==========================================================================
    Pattern(
        name="move_member",
        phase=PatternPhase.EFFECT,
        any_keywords=["ポジションチェンジ", "移動させ", "移動する", "場所を入れ替える"],
        priority=25,
        output_type="EffectType.MOVE_MEMBER",
        output_value=1,
    ),
    Pattern(
        name="tap_opponent",
        phase=PatternPhase.EFFECT,
        regex=r"相手.*?(\d+)?(?:人|枚)?(?:まで)?.*?(?:ウェイト|休み)",
        priority=15,
        consumes=True,
        output_type="EffectType.TAP_OPPONENT",
    ),
    Pattern(
        name="activate_member",
        phase=PatternPhase.EFFECT,
        keywords=["アクティブに"],
        excludes=["手札", "加え", "エネルギー"],  # Exclude energy here
        priority=25,
        output_type="EffectType.ACTIVATE_MEMBER",
        output_value=1,
    ),
    Pattern(
        name="activate_energy",
        phase=PatternPhase.EFFECT,
        regex=r"エネルギーを?(\d+)?枚?.*?アクティブに",
        priority=20,
        output_type="EffectType.ACTIVATE_ENERGY",
        extractor=lambda text, m: {
            "type": "EffectType.ACTIVATE_ENERGY",
            "value": int(m.group(1)) if m.group(1) else 1,
        },
    ),
    # ==========================================================================
    # Zone transfer effects
    # ==========================================================================
    Pattern(
        name="swap_to_discard",
        phase=PatternPhase.EFFECT,
        any_keywords=["控え室に置", "控え室に送"],
        priority=30,
        output_type="EffectType.SWAP_CARDS",
        output_params={"target": "discard"},
        extractor=lambda text, m: {
            "type": "EffectType.SWAP_CARDS",
            "params": {"target": "discard", "from": "deck" if "デッキ" in text or "山札" in text else "field"},
        },
    ),
    Pattern(
        name="move_to_deck",
        phase=PatternPhase.EFFECT,
        any_keywords=["デッキに戻す", "山札に置く"],
        priority=30,
        output_type="EffectType.MOVE_TO_DECK",
    ),
    Pattern(
        name="return_discard_to_deck",
        phase=PatternPhase.EFFECT,
        # "控え室にある...デッキの一番上に置く" (place from discard to top of deck)
        regex=r"控え室.*?(\d+)枚.*?(?:デッキ|山札).*?一番上に置",
        priority=15,
        consumes=True,
        output_type="EffectType.MOVE_TO_DECK",
        extractor=lambda text, m: {
            "type": "EffectType.MOVE_TO_DECK",
            "value": int(m.group(1)),
            "params": {"from": "discard", "to": "deck_top"},
        },
    ),
    Pattern(
        name="place_under",
        phase=PatternPhase.EFFECT,
        keywords=["の下に置"],
        excludes=["コスト", "払"],  # Not cost
        priority=30,
        output_type="EffectType.PLACE_UNDER",
    ),
    # ==========================================================================
    # Meta/Rule effects
    # ==========================================================================
    Pattern(
        name="select_mode",
        phase=PatternPhase.EFFECT,
        regex=r"(?:以下から|のうち、)(\d+|１|２|３)(つ|枚|回)?を選ぶ",
        priority=20,
        output_type="EffectType.SELECT_MODE",
    ),
    Pattern(
        name="color_select",
        phase=PatternPhase.EFFECT,
        any_keywords=["ハートの色を1つ指定", "好きなハートの色を"],
        priority=25,
        output_type="EffectType.COLOR_SELECT",
        output_value=1,
    ),
    Pattern(
        name="negate_effect",
        phase=PatternPhase.EFFECT,
        any_keywords=["無効", "キャンセル"],
        priority=25,
        output_type="EffectType.NEGATE_EFFECT",
        output_value=1,
    ),
    Pattern(
        name="shuffle_deck",
        phase=PatternPhase.EFFECT,
        keywords=["シャッフル"],
        priority=40,
        output_type="EffectType.META_RULE",
        output_params={"type": "shuffle", "deck": True},
    ),
    Pattern(
        name="play_member_from_hand",
        phase=PatternPhase.EFFECT,
        regex=r"手札から.*?登場させ",
        priority=15,
        output_type="EffectType.PLAY_MEMBER_FROM_HAND",
        output_value=1,
    ),
    Pattern(
        name="play_member_from_discard",
        phase=PatternPhase.EFFECT,
        regex=r"控え室から.*?登場させ",
        priority=15,
        output_type="EffectType.PLAY_MEMBER_FROM_DISCARD",
        output_value=1,
    ),
    Pattern(
        name="tap_self",
        phase=PatternPhase.EFFECT,
        regex=r"このメンバーをウェイトにする",
        priority=20,
        output_type="EffectType.TAP_MEMBER",
        output_params={"target": "self"},
    ),
    Pattern(
        name="card_selection",
        phase=PatternPhase.EFFECT,
        regex=r"(?:控え室にある|デッキにある|ステージにいる)?.*?(\d+)枚選ぶ",
        priority=50,  # Low priority
        output_type="EffectType.LOOK_AND_CHOOSE",
    ),
    # ==========================================================================
    # Cost/Constant modifiers parsed as effects
    # ==========================================================================
    Pattern(
        name="reduce_cost_self",
        phase=PatternPhase.EFFECT,
        # "コストは...X少なくなる" OR "コストはX減る" (cost is reduced by X)
        regex=r"コストは.*?(\d+)(?:少なく|減る|減)",
        priority=15,
        consumes=True,
        output_type="EffectType.REDUCE_COST",
    ),
    Pattern(
        name="reduce_cost_per_card",
        phase=PatternPhase.EFFECT,
        # "手札1枚につき、1少なくなる" (reduced by 1 per card in hand)
        regex=r"手札.*?(\d+)枚につき.*?(\d+)少なく",
        priority=10,  # Higher than reduce_cost_self
        consumes=True,
        output_type="EffectType.REDUCE_COST",
        extractor=lambda text, m: {
            "type": "EffectType.REDUCE_COST",
            "value": int(m.group(2)),
            "params": {"per_card": int(m.group(1)), "zone": "hand"},
        },
    ),
    Pattern(
        name="grant_ability",
        phase=PatternPhase.EFFECT,
        # Ability granting: "能力を得る" / "」を得る"
        regex=r"(?:」|{{.*?}}).*?を得る",
        priority=25,
        consumes=False,  # Allow inner effects to be parsed
        output_type="EffectType.BUFF_POWER",
        output_value=1,
    ),
    Pattern(
        name="grant_stat_buff",
        phase=PatternPhase.EFFECT,
        # "ブレード+X」を得る" / "ハート+X」を得る" (gain Blade+X / Heart+X)
        regex=r"(ブレード|ハート)[+＋](\d+)[」」].*?得る",
        priority=15,
        consumes=True,
        output_type="EffectType.BUFF_POWER",
        extractor=lambda text, m: {
            "type": "EffectType.BUFF_POWER" if "ブレード" in m.group(1) else "EffectType.ADD_HEARTS",
            "value": int(m.group(2)),
            "params": {"stat": "blade" if "ブレード" in m.group(1) else "heart"},
        },
    ),
    Pattern(
        name="tap_member_cost",
        phase=PatternPhase.EFFECT,
        # Tap member as cost/effect: "メンバーXをウェイトにしてもよい"
        regex=r"メンバー.*?(\d+)人?.*?ウェイトにして",
        priority=25,
        consumes=True,
        output_type="EffectType.TAP_MEMBER",
        extractor=lambda text, m: {"type": "EffectType.TAP_MEMBER", "value": int(m.group(1)), "params": {"cost": True}},
    ),
    Pattern(
        name="draw_equal_to_discarded",
        phase=PatternPhase.EFFECT,
        regex=r"置いた枚数分カードを引く",
        priority=15,
        consumes=True,
        output_type="EffectType.DRAW",
        output_params={"multiplier": "discarded_count"},
    ),
    Pattern(
        name="trigger_ability",
        phase=PatternPhase.EFFECT,
        regex=r"(能力1つ)?を?発動させる",
        priority=20,
        consumes=True,
        output_type="EffectType.TRIGGER_REMOTE",
    ),
    Pattern(
        name="treat_as_all_colors",
        phase=PatternPhase.EFFECT,
        regex=r"属性を全ての属性として扱う",
        priority=20,
        output_type="EffectType.META_RULE",
        output_params={"type": "all_colors"},
    ),
    Pattern(
        name="transform_base_hearts",
        phase=PatternPhase.EFFECT,
        regex=r"元々持つハートはすべて.*?({{heart_.*?}})?になる",
        priority=20,
        output_type="EffectType.TRANSFORM_COLOR",
        output_params={"target": "base_hearts"},
    ),
    Pattern(
        name="add_from_reveal_to_hand",
        phase=PatternPhase.EFFECT,
        regex=r"(?:公開された|公開される).*?手札に加",
        priority=20,
        output_type="EffectType.ADD_TO_HAND",
        output_params={"from": "reveal_zone", "to": "hand"},
    ),
    Pattern(
        name="recover_live_to_zone",
        phase=PatternPhase.EFFECT,
        regex=r"控え室からライブカードを.*?ライブカード置き場に置",
        priority=20,
        output_type="EffectType.PLAY_LIVE_FROM_DISCARD",
        output_value=1,
    ),
    Pattern(
        name="increase_cost",
        phase=PatternPhase.EFFECT,
        regex=r"コストを?[+＋](\d+)する",
        priority=20,
        output_type="EffectType.REDUCE_COST",  # Use negative for increase in engine or separate Opcode
        extractor=lambda text, m: {
            "type": "EffectType.REDUCE_COST",
            "value": -int(m.group(1)),
        },
    ),
    Pattern(
        name="increase_heart_req",
        phase=PatternPhase.EFFECT,
        regex=r"必要ハートが.*?多くなる",
        priority=20,
        output_type="EffectType.REDUCE_HEART_REQ",
        output_value=1,  # Default increase by 1 if value not specified
    ),
    Pattern(
        name="modify_cheer_count",
        phase=PatternPhase.EFFECT,
        regex=r"エールによって公開される.*?枚数が.*?(\d+)枚(減る|増える)",
        priority=20,
        output_type="EffectType.META_RULE",
        extractor=lambda text, m: {
            "type": "EffectType.META_RULE",
            "params": {"type": "cheer_mod"},
            "value": -int(m.group(1)) if m.group(2) == "減る" else int(m.group(1)),
        },
    ),
    Pattern(
        name="play_member_from_discard",
        phase=PatternPhase.EFFECT,
        regex=r"控え室(?:にある|から).*?登場させ",
        priority=15,
        output_type="EffectType.PLAY_MEMBER_FROM_DISCARD",
        output_value=1,
    ),
    Pattern(
        name="baton_touch_mod",
        phase=PatternPhase.EFFECT,
        regex=r"(\d+)人のメンバーとバトンタッチ",
        priority=20,
        output_type="EffectType.BATON_TOUCH_MOD",
        extractor=lambda text, m: {
            "type": "EffectType.BATON_TOUCH_MOD",
            "value": int(m.group(1)),
        },
    ),
    Pattern(
        name="rule_equivalence",
        phase=PatternPhase.EFFECT,
        regex=r"についても同じこと(として扱う|を行う)",
        priority=20,
        output_type="EffectType.META_RULE",
        output_params={"type": "rule_equivalence"},
    ),
    Pattern(
        name="restriction_no_live",
        phase=PatternPhase.EFFECT,
        regex=r"自分はライブ(できない|出来ません)",
        priority=20,
        output_type="EffectType.RESTRICTION",
        output_params={"type": "no_live"},
    ),
    Pattern(
        name="prevent_baton_touch",
        phase=PatternPhase.EFFECT,
        regex=r"バトンタッチで控え室に置けない",
        priority=10,
        output_type="EffectType.PREVENT_BATON_TOUCH",
        output_value=1,
    ),
    # ==========================================================================
    # New effects for BP05 and new card abilities
    # ==========================================================================
    Pattern(
        name="look_deck_dynamic_score",
        phase=PatternPhase.EFFECT,
        regex=r"デッキの上から.*?ライブの合計スコアに(\d+)を足した数に等しい枚数見る",
        priority=15,
        output_type="EffectType.LOOK_DECK_DYNAMIC",
        extractor=lambda text, m: {
            "type": "EffectType.LOOK_DECK_DYNAMIC",
            "value": 0,  # Dynamic value
            "params": {"value_source": "live_score", "modifier": int(m.group(1))},
        },
    ),
    Pattern(
        name="reduce_score",
        phase=PatternPhase.EFFECT,
        regex=r"ライブの合計スコアを[－−](\d+)する",
        priority=20,
        output_type="EffectType.REDUCE_SCORE",
        extractor=lambda text, m: {
            "type": "EffectType.REDUCE_SCORE",
            "value": int(m.group(1)),
        },
    ),
    Pattern(
        name="repeat_ability",
        phase=PatternPhase.EFFECT,
        regex=r"この手順をさらに(\d+)回まで繰り返してもよい",
        priority=15,
        output_type="EffectType.REPEAT_ABILITY",
        extractor=lambda text, m: {
            "type": "EffectType.REPEAT_ABILITY",
            "value": int(m.group(1)),
            "params": {"optional": True},
        },
    ),
    Pattern(
        name="lose_excess_hearts",
        phase=PatternPhase.EFFECT,
        regex=r"余剰ハートを(\d+)つ以上持っている場合、それらをすべて失い",
        priority=15,
        output_type="EffectType.LOSE_EXCESS_HEARTS",
        extractor=lambda text, m: {
            "type": "EffectType.LOSE_EXCESS_HEARTS",
            "value": int(m.group(1)),
            "params": {"lose_all": True},
        },
    ),
    Pattern(
        name="skip_activate_phase",
        phase=PatternPhase.EFFECT,
        regex=r"このメンバーは自分のアクティブフェイズにアクティブにしない",
        priority=20,
        output_type="EffectType.SKIP_ACTIVATE_PHASE",
        output_value=1,
    ),
    Pattern(
        name="pay_energy_dynamic_score",
        phase=PatternPhase.EFFECT,
        regex=r"そのカードのスコアに等しい数の{{icon_energy.*?}}を支払ってもよい",
        priority=15,
        output_type="EffectType.PAY_ENERGY_DYNAMIC",
        output_params={"value_source": "selected_card_score"},
    ),
    Pattern(
        name="place_energy_under_member",
        phase=PatternPhase.EFFECT,
        regex=r"エネルギー置き場にあるエネルギー(\d+)枚をこのメンバーの下に置く",
        priority=15,
        output_type="EffectType.PLACE_ENERGY_UNDER_MEMBER",
        extractor=lambda text, m: {
            "type": "EffectType.PLACE_ENERGY_UNDER_MEMBER",
            "value": int(m.group(1)),
            "params": {"target": "self"},
        },
    ),
]
