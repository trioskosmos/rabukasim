import sys
sys.path.append('.')
from engine.models.ability import Ability
from engine.models.generated_enums import TriggerType

ab = Ability("", TriggerType.CONSTANT, [])
attr = ab._pack_filter_attr({"filter":"NAME_IN=高坂穂乃果,絢瀬絵里"})
print(hex(attr))
import pprint
pprint.pprint(ab.filters[-1])
