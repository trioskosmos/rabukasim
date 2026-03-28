import sys
import time
import cProfile
import pstats
import io

sys.path.insert(0, '.')

def profile_compile():
    from compiler.main import compile_cards
    
    # Profile the compilation
    pr = cProfile.Profile()
    pr.enable()
    
    start = time.time()
    compile_cards('data/cards.json', 'data/cards_compiled_profiled.json', quiet=True)
    elapsed = time.time() - start
    
    pr.disable()
    
    # Print stats
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(30)
    
    print(f"\nTotal time: {elapsed:.2f}s")
    print("\nTop 30 functions by cumulative time:")
    print(s.getvalue())

if __name__ == "__main__":
    profile_compile()
