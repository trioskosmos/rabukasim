import sys
import traceback
import os
os.environ['LOVECA_COMPILER_WORKERS'] = '1'  # Force single worker for clearer errors
sys.path.insert(0, '.')

from compiler.main import (
    _init_worker, _process_card_worker, _ABILITY_COMPILATION_CACHE, 
    _sparse_manager, _manual_translations_en, _instruction_compile_errors
)

# Clear any previous errors
_instruction_compile_errors.clear()

# Initialize
_init_worker(_ABILITY_COMPILATION_CACHE, _sparse_manager.mapping, {})

# Try to compile one specific card that's failing
test_card_no = 'LL-bp1-001-R+'
test_data = {
    'type': 'メンバー',
    'name': '高坂穂乃果',
    'ability': '{{ON_PLAY}} {{Activated}} 手札から「μ\'s」のメンバーを1枚選び、ステージに登場させる。',
    'rare': 'R+',
    'series': 'μ\'s',
    'cost': 2,
}

print(f"Testing card: {test_card_no}")
try:
    result = _process_card_worker((test_card_no, test_data, 'full', 9, 9, 0))
    print('Result type:', result[0])
    print('Result pk:', result[1])
    if result[3]:
        print('ERROR:', result[3])
except Exception as e:
    print('EXCEPTION:', e)
    traceback.print_exc()
