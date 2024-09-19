from functools import partial

def run_tests(func_list: list, tested_implementation: str) -> None:
    tests = [partial(func) for func in func_list]

    print(f'========== Tests for {tested_implementation} ==========')
    count = 1
    for test in tests:
        print(f'Test #{count}: ', end='')
        test()
        count += 1
        print("-" * 100)


