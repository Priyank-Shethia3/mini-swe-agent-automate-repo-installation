#!/usr/bin/env python3
"""Test script to verify verbose mode support in log parsers."""

from log_parser.parsers.pytest import parse_log_pytest
from log_parser.parsers.jest import parse_log_jest
from log_parser.parsers.mocha import parse_log_mocha
from log_parser.parsers.go_test import parse_log_go_test
from log_parser.parsers.cargo import parse_log_cargo
from log_parser.parsers.maven import parse_log_maven

# Test verbose pytest output
pytest_verbose_log = """
============================= test session starts ==============================
platform linux -- Python 3.9.0, pytest-7.0.0, pluggy-1.0.0 -- /usr/bin/python
cachedir: .pytest_cache
rootdir: /home/user/project
plugins: cov-4.0.0
collecting ... collected 5 items

tests/test_math.py::test_addition PASSED                                [ 20%]
tests/test_math.py::test_subtraction PASSED                             [ 40%]
tests/test_math.py::TestClass::test_multiplication FAILED               [ 60%]
tests/test_math.py::TestClass::test_division PASSED                     [ 80%]
tests/test_math.py::test_skip SKIPPED (unconditional skip)             [100%]

=================================== FAILURES ===================================
______________________ TestClass.test_multiplication _______________________

    def test_multiplication():
>       assert 2 * 3 == 7
E       assert 6 == 7

tests/test_math.py:15: AssertionError
=========================== short test summary info ============================
FAILED tests/test_math.py::TestClass::test_multiplication - assert 6 == 7
=================== 1 failed, 3 passed, 1 skipped in 0.12s ====================
"""

# Test verbose jest output
jest_verbose_log = """
 PASS  src/math.test.js
  Math operations
    ✓ should add numbers correctly (5 ms)
    ✓ should subtract numbers correctly (2 ms)
    ✕ should multiply numbers correctly (4 ms)
    ○ should divide numbers correctly

  ● Math operations › should multiply numbers correctly

    expect(received).toBe(expected) // Object.is equality

    Expected: 7
    Received: 6

      14 |   test('should multiply numbers correctly', () => {
      15 |     const result = multiply(2, 3);
    > 16 |     expect(result).toBe(7);
         |                    ^
      17 |   });

Test Suites: 1 passed, 1 total
Tests:       2 passed, 1 failed, 1 skipped, 4 total
"""

# Test verbose mocha output
mocha_verbose_log = """
  Math operations
    ✓ should add numbers correctly (42ms)
    ✓ should subtract numbers correctly
    1) should multiply numbers correctly
    - should divide numbers correctly

  Database operations
    ✔ should connect to database (120ms)
    2) should insert records
    ✓ should query records (85ms)

  3 passing (250ms)
  1 pending
  2 failing

  1) Math operations
       should multiply numbers correctly:
     AssertionError: expected 6 to equal 7
      at Context.<anonymous> (test/math.test.js:15:20)

  2) Database operations
       should insert records:
     Error: Connection timeout
      at Context.<anonymous> (test/db.test.js:25:15)
"""

# Test verbose go test output
go_verbose_log = """
=== RUN   TestAddition
--- PASS: TestAddition (0.00s)
=== RUN   TestSubtraction
--- PASS: TestSubtraction (0.00s)
=== RUN   TestMultiplication
    math_test.go:15: Expected 7, got 6
--- FAIL: TestMultiplication (0.00s)
=== RUN   TestDivision
--- SKIP: TestDivision (0.00s)
    math_test.go:20: Skipping division test
=== RUN   TestComplexOperations
=== RUN   TestComplexOperations/addition_with_negatives
--- PASS: TestComplexOperations/addition_with_negatives (0.00s)
=== RUN   TestComplexOperations/multiplication_with_zero
--- PASS: TestComplexOperations/multiplication_with_zero (0.00s)
=== RUN   TestComplexOperations/division_by_zero
--- FAIL: TestComplexOperations/division_by_zero (0.00s)
    math_test.go:35: Division by zero should return error
--- FAIL: TestComplexOperations (0.00s)
FAIL
exit status 1
FAIL    example.com/math    0.123s
"""

# Test verbose cargo test output
cargo_verbose_log = """
   Compiling math v0.1.0 (/home/user/project)
    Finished test [unoptimized + debuginfo] target(s) in 1.23s
     Running unittests src/lib.rs (target/debug/deps/math-1234567890abcdef)

running 5 tests
test tests::test_addition ... ok
test tests::test_subtraction ... ok
test tests::test_multiplication ... FAILED
test tests::test_division ... ignored
test tests::test_modulo ... ok

failures:

---- tests::test_multiplication stdout ----
thread 'tests::test_multiplication' panicked at 'assertion failed: `(left == right)`
  left: `6`,
 right: `7`', src/lib.rs:25:9

failures:
    tests::test_multiplication

test result: FAILED. 3 passed; 1 failed; 1 ignored; 0 measured; 0 filtered out; finished in 0.00s

   Doc-tests math

running 2 tests
test src/lib.rs - add (line 5) ... ok
test src/lib.rs - multiply (line 15) ... FAILED

failures:

---- src/lib.rs - multiply (line 15) stdout ----
Test executable failed.

failures:
    src/lib.rs - multiply (line 15)

test result: FAILED. 1 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.15s
"""

# Test verbose maven output
maven_verbose_log = """
-------------------------------------------------------
 T E S T S
-------------------------------------------------------
Running com.example.MathTest
testAddition(com.example.MathTest)  Time elapsed: 0.005 sec
testSubtraction(com.example.MathTest)  Time elapsed: 0.002 sec
testMultiplication(com.example.MathTest)  Time elapsed: 0.003 sec  <<< FAILURE!
java.lang.AssertionError: expected:<7> but was:<6>
	at org.junit.Assert.fail(Assert.java:88)
	at com.example.MathTest.testMultiplication(MathTest.java:25)

testDivision(com.example.MathTest)  Time elapsed: 0.001 sec
Tests run: 4, Failures: 1, Errors: 0, Skipped: 0, Time elapsed: 0.123 sec <<< FAILURE!

Running com.example.DatabaseTest
testConnection(com.example.DatabaseTest)  Time elapsed: 0.150 sec
testInsert(com.example.DatabaseTest)  Time elapsed: 0.045 sec  <<< ERROR!
java.sql.SQLException: Connection timeout
	at com.example.DatabaseTest.testInsert(DatabaseTest.java:35)

Tests run: 2, Failures: 0, Errors: 1, Skipped: 0, Time elapsed: 0.250 sec <<< FAILURE!

Results :

Failed tests:   testMultiplication(com.example.MathTest): expected:<7> but was:<6>

Tests in error: 
  testInsert(com.example.DatabaseTest): Connection timeout

Tests run: 6, Failures: 1, Errors: 1, Skipped: 0
"""

def test_parser(name, parser_func, log_content):
    """Test a parser and print results."""
    print(f"\n{'='*60}")
    print(f"Testing {name} parser with verbose output")
    print(f"{'='*60}")
    
    result = parser_func(log_content)
    
    if result:
        print(f"✓ Successfully parsed {len(result)} test cases")
        
        # Count statuses
        passed = sum(1 for status in result.values() if status == "PASSED")
        failed = sum(1 for status in result.values() if status == "FAILED")
        skipped = sum(1 for status in result.values() if status == "SKIPPED")
        
        print(f"  - PASSED: {passed}")
        print(f"  - FAILED: {failed}")
        print(f"  - SKIPPED: {skipped}")
        
        # Show sample results
        print("\nSample results:")
        for i, (test_name, status) in enumerate(list(result.items())[:5]):
            print(f"  {test_name}: {status}")
        
        if len(result) > 5:
            print(f"  ... and {len(result) - 5} more")
    else:
        print("✗ Failed to parse any test cases")
    
    return result

if __name__ == "__main__":
    print("Testing verbose mode support in log parsers")
    print("=" * 60)
    
    # Run all tests
    results = {}
    
    results['pytest'] = test_parser('pytest', parse_log_pytest, pytest_verbose_log)
    results['jest'] = test_parser('jest', parse_log_jest, jest_verbose_log)
    results['mocha'] = test_parser('mocha', parse_log_mocha, mocha_verbose_log)
    results['go_test'] = test_parser('go_test', parse_log_go_test, go_verbose_log)
    results['cargo'] = test_parser('cargo', parse_log_cargo, cargo_verbose_log)
    results['maven'] = test_parser('maven', parse_log_maven, maven_verbose_log)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    for parser_name, result in results.items():
        if result:
            print(f"✓ {parser_name}: Successfully parsed {len(result)} test cases")
        else:
            print(f"✗ {parser_name}: Failed to parse")