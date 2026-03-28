import sys
import time
import cProfile
import pstats
import io

sys.path.insert(0, '.')

def profile_single_card():
    from compiler.main import _process_card_worker, _init_worker, _ABILITY_COMPILATION_CACHE, _sparse_manager
    
    # Initialize
    _init_worker(_ABILITY_COMPILATION_CACHE, _sparse_manager.mapping, {})
    
    # Test card data
    test_card_no = 'LL-bp1-001-R+'
    test_data = {
        'type': 'メンバー',
        'name': '高坂穂乃果',
        'ability': '{{ON_PLAY}} {{Activated}} 手札から「μ\'s」のメンバーを1枚選び、ステージに登場させる。',
        'rare': 'R+',
        'series': 'μ\'s',
        'cost': 2,
    }
    
    # Profile single card compilation
    pr = cProfile.Profile()
    pr.enable()
    
    start = time.time()
    for _ in range(10):  # Run 10 times for better measurement
        result = _process_card_worker((test_card_no, test_data, 'full', 9, 9, 0))
    elapsed = time.time() - start
    
    pr.disable()
    
    # Print stats
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)
    
    print(f"\nTotal time for 10 runs: {elapsed:.3f}s ({elapsed/10:.3f}s per card)")
    print("\nTop 20 functions by cumulative time:")
    print(s.getvalue())

if __name__ == "__main__":
    profile_single_card()
