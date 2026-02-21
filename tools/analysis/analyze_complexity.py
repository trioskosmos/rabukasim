import os
import sys

sys.path.append(os.getcwd())

from game.ability import ConditionType, EffectType, TriggerType
from game.data_loader import CardDataLoader


def calculate_complexity(card):
    score = 0

    # Base complexity for having abilities
    if not card.abilities:
        return 0

    for ability in card.abilities:
        score += 1

        # Trigger Complexity
        if ability.trigger == TriggerType.CONSTANT:
            score += 2
        elif ability.trigger == TriggerType.ACTIVATED:
            score += 2

        # Condition Complexity
        for condition in ability.conditions:
            if condition.type in [ConditionType.COUNT_GROUP, ConditionType.GROUP_FILTER]:
                score += 2
            elif condition.type in [ConditionType.OPPONENT_HAS, ConditionType.IS_CENTER]:
                score += 3
            elif condition.type == ConditionType.SELF_IS_GROUP:
                score += 4
            elif condition.type == ConditionType.MODAL_ANSWER:
                score += 12  # Hard to map semantically

        # Effect Complexity (Based on "How hard it was to implement/parse")
        for effect in ability.effects:
            etype = effect.effect_type

            # Tier 1: The Basics (Simple Regex)
            if etype in [EffectType.DRAW, EffectType.BUFF_POWER, EffectType.ADD_HEARTS, EffectType.RECOVER_LIVE]:
                score += 1

            # Tier 2: Specific Logic (Targeting, Searching)
            elif etype in [
                EffectType.LOOK_DECK,
                EffectType.SEARCH_DECK,
                EffectType.RECOVER_MEMBER,
                EffectType.ENERGY_CHARGE,
            ]:
                score += 3

            # Tier 3: Advanced Logic (Immunity, Moving things)
            elif etype in [EffectType.IMMUNITY, EffectType.MOVE_MEMBER, EffectType.REDUCE_COST, EffectType.BOOST_SCORE]:
                score += 5

            # Tier 4: The Tricky Ones (Negation, Swapping)
            elif etype in [EffectType.SWAP_CARDS, EffectType.NEGATE_EFFECT, EffectType.SWAP_ZONE]:
                score += 8

            # Tier 5: The "Final Bosses" (Added at 95% -> 100%)
            elif etype in [
                EffectType.ORDER_DECK,
                EffectType.TAP_OPPONENT,
                EffectType.SELECT_MODE,
                EffectType.RESTRICTION,
                EffectType.BATON_TOUCH_MOD,
                EffectType.PLACE_UNDER,
            ]:
                score += 15

            # Special: Meta Rules (Hard to find, easy to implement)
            elif etype == EffectType.META_RULE:
                score += 5

            # Special: Flavor (Ambiguous text)
            elif etype == EffectType.FLAVOR_ACTION:
                score += 10

        # Multi-line/Continuation Complexity
        # If the raw text has multiple sentences/lines but one trigger
        lines = ability.raw_text.split("/")  # My parser joins with ' / ' for continuation
        if len(lines) > 1:
            score += (len(lines) - 1) * 10  # 10 point penalty per continuation line

    # FAQ Complexity (Ambiguity requiring clarification)
    if hasattr(card, "faq") and card.faq:
        score += len(card.faq) * 5  # 5 points per FAQ entry

    return score


def main():
    print("Loading Cards...")
    json_path = os.path.join(os.getcwd(), "data", "cards.json")
    loader = CardDataLoader(json_path)
    # unpack load result tuple: members, lives, energy
    members, lives, _ = loader.load()

    # Combine members and lives for full analysis
    all_cards = list(members.values()) + list(lives.values())

    card_scores = []

    for card in all_cards:
        # Skip cards with no abilities if desired, but 0 complexity is valid
        score = calculate_complexity(card)
        if score > 0:
            card_scores.append((score, card))

    # Sort by score descending
    card_scores.sort(key=lambda x: x[0], reverse=True)

    # Calculate Statistics
    import statistics

    scores = [s for s, c in card_scores]
    mean_score = statistics.mean(scores)
    stdev_score = statistics.stdev(scores)

    print(f"Stats: Mean={mean_score:.2f}, StdDev={stdev_score:.2f}, Max={max(scores) if scores else 0}")

    # Dynamic Tiers
    tiers = [
        ("SSS Tier (Universe > +3σ)", mean_score + 3 * stdev_score),
        ("SS Tier (God > +2σ)", mean_score + 2 * stdev_score),
        ("S Tier (Final Boss > +1σ)", mean_score + 1 * stdev_score),
        ("A Tier (Complex > Mean)", mean_score),
        ("B Tier (Advanced > -0.5σ)", mean_score - 0.5 * stdev_score),
        ("C Tier (Standard > -1σ)", mean_score - 1 * stdev_score),
        ("D Tier (Basic < -1σ)", -1),  # Catch all remaining
    ]

    # Generate Report
    with open("card_complexity_tiers.md", "w", encoding="utf-8") as f:
        f.write("# Card Complexity Analysis (Statistical)\n")
        f.write(
            f"**Statistics**: Mean: {mean_score:.2f} | StdDev: {stdev_score:.2f} | Max: {max(scores) if scores else 0}\n\n"
        )

        for i in range(len(tiers) - 1):
            tier_name, threshold = tiers[i]
            next_threshold = tiers[i + 1][1] if i + 1 < len(tiers) else -999

            # Filter cards in this band
            # For the last defined tier (D), we just take everything below C
            if i == len(tiers) - 1:
                tier_cards = [(s, c) for s, c in card_scores if s < threshold]
            else:
                # Check if this is the last band in our loop (D Tier logic handled by falling through?)
                # Actually strictly:
                # SSS: >= mean + 3std
                # SS: < 3std AND >= 2std
                # ...
                tier_cards = [(s, c) for s, c in card_scores if s >= threshold and (i == 0 or s < tiers[i - 1][1])]

            # Since we iterate from top (SSS) down, we just need s >= threshold and s < previous_threshold
            # But simpler: just process list and remove? No, repeated iteration is fine.

            # Correct logic:
            # SSS: s >= T_SSS
            # SS:  T_SS <= s < T_SSS

            upper_bound = 9999 if i == 0 else tiers[i - 1][1]
            current_cards = [(s, c) for s, c in card_scores if threshold <= s < upper_bound]

            f.write(f"## {tier_name} (Range: {threshold:.1f} - {upper_bound:.1f})\n")
            f.write(f"Count: {len(current_cards)}\n\n")

            f.write("| Card Name | Score | FAQ | Key Mechanics |\n")
            f.write("|---|---|---|---|\n")
            for score, card in current_cards[:30]:  # Top 30 per tier
                mechanics = []
                for ab in card.abilities:
                    for eff in ab.effects:
                        mechanics.append(eff.effect_type.name)
                mechanics_str = ", ".join(set(mechanics))
                faq_count = len(card.faq) if hasattr(card, "faq") else 0
                f.write(f"| {card.name} | {score} | {faq_count} | {mechanics_str} |\n")
            f.write("\n")

    print("Report generated: card_complexity_tiers.md")


if __name__ == "__main__":
    main()
