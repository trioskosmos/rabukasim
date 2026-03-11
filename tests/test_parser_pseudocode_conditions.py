import os
import sys


sys.path.append(os.getcwd())

from compiler.parser_v2 import AbilityParserV2
from engine.models.generated_enums import ConditionType


def test_count_success_live_merges_multiple_brace_blocks():
    parser = AbilityParserV2()

    conditions = parser._parse_pseudocode_conditions(
        'COUNT_SUCCESS_LIVE(PLAYER) {FILTER="GROUP_ID=0"} {MIN=2}'
    )

    assert len(conditions) == 1

    condition = conditions[0]
    assert condition.type == ConditionType.COUNT_SUCCESS_LIVE
    assert condition.params["target"] == "self"
    assert condition.params["FILTER"] == "GROUP_ID=0"
    assert condition.params["MIN"] == 2
    assert condition.params["raw_cond"] == "COUNT_SUCCESS_LIVE"
    assert "val" not in condition.params