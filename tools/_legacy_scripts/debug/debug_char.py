from pydantic import TypeAdapter

from engine.models.card import LiveCard
from engine.models.enums import Group


def test():
    # Test 1: Enum comparison
    target = Group.MUSE
    groups = [0]
    print(f"Group.MUSE in [0]: {target in groups}")
    groups_enum = [Group.MUSE]
    print(f"Group.MUSE in [Group.MUSE]: {target in groups_enum}")

    # Test 2: Pydantic Dataclass validation
    data = {
        "card_id": 1019,
        "card_no": "TEST",
        "name": "TEST",
        "score": 10,
        "required_hearts": [1, 0, 0, 0, 0, 0, 0],
        "groups": [0],
    }
    adapter = TypeAdapter(LiveCard)
    card = adapter.validate_python(data)
    print(f"Card groups: {card.groups} type: {type(card.groups[0])}")
    print(f"Group.MUSE in card.groups: {Group.MUSE in card.groups}")


if __name__ == "__main__":
    test()
