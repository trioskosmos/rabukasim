import inspect

from game.game_state import MemberCard

print(f"MemberCard definition: {MemberCard}")
print(
    f"Fields: {MemberCard.__dataclass_fields__.keys() if hasattr(MemberCard, '__dataclass_fields__') else 'Not a dataclass'}"
)
print(f"Init Signature: {inspect.signature(MemberCard.__init__)}")
