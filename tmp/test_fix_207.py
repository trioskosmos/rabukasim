import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.models.ability import Ability

def test_filter_compilation():
    ab = Ability()
    
    # Revision 5 BIT LAYOUT:
    # Bit 4: Group Enable
    # Bits 5-11: Group ID

    def check_filter(filter_str, expected_group_id):
        attr = ab._pack_filter_attr({"filter": filter_str})
        group_id = (attr >> 5) & 0x7F
        group_enabled = (attr >> 4) & 1
        print(f"Filter '{filter_str}': attr={attr}, group_id={group_id}, group_enabled={group_enabled}")
        if group_id != expected_group_id:
            print(f"ERROR: Expected group_id {expected_group_id}, got {group_id}")
            return False
        if group_enabled != 1:
            print(f"ERROR: Expected group_enabled 1, got {group_enabled}")
            return False
        return True

    results = []
    results.append(check_filter("UNIT_HASU", 4))
    results.append(check_filter("UNIT_HASUNOSORA", 4))
    results.append(check_filter("UNIT_NIJIGASAKI", 2))
    results.append(check_filter("UNIT_NIJI", 2))
    results.append(check_filter("UNIT_AQOURS", 1))
    results.append(check_filter("UNIT_AQUOURS", 1)) # Typo check
    results.append(check_filter("UNIT_MUSE", 0))
    results.append(check_filter("UNIT_MUS", 0))
    results.append(check_filter("UNIT_μ'S", 0))

    if all(results):
        print("All tests passed!")
        sys.exit(0)
    else:
        print("Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    test_filter_compilation()
