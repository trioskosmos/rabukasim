from engine.models.ability import Ability, Condition, ConditionType, Effect, EffectType, TriggerType
from engine.models.opcodes import Opcode


def test_compile():
    cond = Condition(
        ConditionType.SCORE_COMPARE,
        {"comparison": "GT", "target": "opponent", "type": "cost", "zone": "OPPONENT_CENTER_STAGE"},
    )
    abi = Ability(
        raw_text="test",
        trigger=TriggerType.ON_LIVE_START,
        effects=[Effect(EffectType.BOOST_SCORE, 1)],
        conditions=[cond],
    )

    print(f"Condition Type: {cond.type} (name: {cond.type.name})")
    op_name = f"CHECK_{cond.type.name}"
    print(f"Opcode name: {op_name}")
    print(f"Has Opcode: {hasattr(Opcode, op_name)}")

    bytecode = abi.compile()
    print(f"Bytecode: {bytecode}")

    # Check if 220 is in bytecode
    if any(x == 220 for x in bytecode):
        print("Success: CHECK_SCORE_COMPARE (220) found in bytecode")
    else:
        print("Failure: CHECK_SCORE_COMPARE (220) NOT found in bytecode")


if __name__ == "__main__":
    test_compile()
