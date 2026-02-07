#!/usr/bin/env python3
"""Unit tests for C++ test parsers."""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from log_parser.parsers.ctest import parse_log_ctest
from log_parser.parsers.gtest import parse_log_gtest
from log_parser.parsers.catch2 import parse_log_catch2
from log_parser.parsers.boost_test import parse_log_boost_test
from log_parser.parsers.cppunit import parse_log_cppunit

# ============================================================================
# CTest Test Data (Real data from google-leveldb)
# ============================================================================

ctest_log_simple = """Test project /app/build
    Start 1: leveldb_tests
1/3 Test #1: leveldb_tests ....................   Passed   75.48 sec
    Start 2: c_test
2/3 Test #2: c_test ...........................   Passed    0.03 sec
    Start 3: env_posix_test
3/3 Test #3: env_posix_test ...................   Passed    1.95 sec

100% tests passed, 0 tests failed out of 3

Total Test time (real) =  77.46 sec
"""

# Real data from WerWolv-ImHex (verbose CTest output)
ctest_log_verbose = """UpdateCTestConfiguration  from :/app/build/DartConfiguration.tcl
Test project /app/build
test 1
      Start  1: Helpers/TestSucceeding
1: Test command: /app/build/helpers_test "TestSucceeding"
1: [20:41:20] [INFO]  [unit_tests | ???]           Success!
 1/5 Test  #1: Helpers/TestSucceeding ..............   Passed    0.01 sec
test 2
      Start  2: Helpers/TestFailing
2: Test command: /app/build/helpers_test "TestFailing"
2: [20:41:20] [INFO]  [unit_tests | ???]           Success!
 2/5 Test  #2: Helpers/TestFailing .................   Passed    0.01 sec
test 3
      Start  3: Algorithms/CRC32
3: Test command: /app/build/algorithms_test "CRC32"
3: [20:41:22] [INFO]  [unit_tests | ???]           Success!
 3/5 Test  #3: Algorithms/CRC32 ....................   Passed    0.01 sec
test 4
      Start  4: Algorithms/CRC16
4: Test command: /app/build/algorithms_test "CRC16"
4: [20:41:22] [INFO]  [unit_tests | ???]           Failed!
 4/5 Test  #4: Algorithms/CRC16 ....................   Failed    0.02 sec
test 5
      Start  5: Algorithms/md5
5: Test command: /app/build/algorithms_test "md5"
5: [20:41:22] [INFO]  [unit_tests | ???]           Success!
 5/5 Test  #5: Algorithms/md5 ......................   Passed    0.01 sec

80% tests passed, 1 test failed out of 5
"""

# ============================================================================
# Catch2 Test Data (Real data from duckdb-duckdb)
# ============================================================================

catch2_xml_log = """<?xml version="1.0" encoding="UTF-8"?>
<Catch name="unittest">
  <Group name="unittest">
    <TestCase name="ADBC - Select 42" tags="[adbc]" filename="/app/test/api/adbc/test_adbc.cpp" line="125">
      <OverallResult success="true"/>
    </TestCase>
    <TestCase name="ADBC - Test ingestion" tags="[adbc]" filename="/app/test/api/adbc/test_adbc.cpp" line="143">
      <OverallResult success="true"/>
    </TestCase>
    <TestCase name="ADBC - Test with error" tags="[adbc]" filename="/app/test/api/adbc/test_adbc.cpp" line="158">
      <OverallResult success="false"/>
    </TestCase>
    <TestCase name="Test Null Error" tags="[adbc]" filename="/app/test/api/adbc/test_adbc.cpp" line="515">
      <OverallResult success="true"/>
    </TestCase>
    <TestCase name="Test Invalid Path" tags="[adbc]" filename="/app/test/api/adbc/test_adbc.cpp" line="538">
      <OverallResult success="false"/>
    </TestCase>
  </Group>
</Catch>
"""

# Catch2 text format
catch2_text_log = """
All tests passed (1234 assertions in 50 test cases)
"""

# Catch2 summary format
catch2_summary_log = """
test cases: 150 | 145 passed | 5 failed
"""

# ============================================================================
# Google Test (GTest) Test Data (Synthetic but realistic)
# ============================================================================

gtest_log = """[==========] Running 8 tests from 3 test suites.
[----------] Global test environment set-up.
[----------] 3 tests from MathTest
[ RUN      ] MathTest.Addition
[       OK ] MathTest.Addition (0 ms)
[ RUN      ] MathTest.Multiplication
[  FAILED  ] MathTest.Multiplication (5 ms)
  Expected: 7
  Actual: 6
[ RUN      ] MathTest.Division
[       OK ] MathTest.Division (1 ms)
[----------] 3 tests from MathTest (6 ms total)

[----------] 3 tests from StringTest
[ RUN      ] StringTest.Concatenation
[       OK ] StringTest.Concatenation (0 ms)
[ RUN      ] StringTest.Comparison
[       OK ] StringTest.Comparison (0 ms)
[ RUN      ] StringTest.Length
[  FAILED  ] StringTest.Length (1 ms)
  Expected length: 10
  Actual length: 9
[----------] 3 tests from StringTest (1 ms total)

[----------] 2 tests from DatabaseTest
[ RUN      ] DatabaseTest.Connection
[       OK ] DatabaseTest.Connection (5 ms)
[ RUN      ] DatabaseTest.Query
[       OK ] DatabaseTest.Query (3 ms)
[----------] 2 tests from DatabaseTest (8 ms total)

[----------] Global test environment tear-down
[==========] 8 tests from 3 test suites ran. (15 ms total)
[  PASSED  ] 6 tests.
[  FAILED  ] 2 tests, listed below:
[  FAILED  ] MathTest.Multiplication
[  FAILED  ] StringTest.Length
"""

# GTest summary-only format (when individual tests aren't shown)
gtest_summary_log = """
[==========] Running 150 tests from 25 test suites.
[==========] 150 tests from 25 test suites ran. (500 ms total)
[  PASSED  ] 148 tests.
[  FAILED  ] 2 tests, listed below:
[  FAILED  ] SomeTest.Failed1
[  FAILED  ] SomeTest.Failed2

 2 FAILED TESTS
"""

# ============================================================================
# Boost.Test Test Data (Synthetic)
# ============================================================================

boost_test_success_log = """
Running 42 test cases...
Entering test suite "MasterTestSuite"
Entering test case "test_addition"
Leaving test case "test_addition"
Entering test case "test_subtraction"
Leaving test case "test_subtraction"
Entering test case "test_multiplication"
Leaving test case "test_multiplication"
Leaving test suite "MasterTestSuite"

*** No errors detected
"""

boost_test_failure_log = """
Running 5 test cases...
Entering test suite "MasterTestSuite"
Entering test case "test_addition"
Leaving test case "test_addition"
Entering test case "test_subtraction"
error in "test_subtraction": check x == y has failed [5 != 6]
Leaving test case "test_subtraction"
Entering test case "test_multiplication"
error in "test_multiplication": check result == expected has failed
Leaving test case "test_multiplication"
Entering test case "test_division"
Leaving test case "test_division"
Entering test case "test_modulo"
Leaving test case "test_modulo"
Leaving test suite "MasterTestSuite"

*** 2 failures detected in the test module "MathTests"
"""

boost_test_with_suites = """
Entering test suite "MathSuite/BasicOperations"
Entering test case "MathSuite/BasicOperations/test_add"
Leaving test case "MathSuite/BasicOperations/test_add"
Entering test case "MathSuite/BasicOperations/test_subtract"
error in "MathSuite/BasicOperations/test_subtract": check failed
Leaving test case "MathSuite/BasicOperations/test_subtract"
Leaving test suite "MathSuite/BasicOperations"

*** 1 failure detected
"""

# ============================================================================
# CppUnit Test Data (Synthetic)
# ============================================================================

cppunit_success_log = """
OK (150 tests)
"""

cppunit_failure_log = """
Test Results:
Run: 150  Failures: 2  Errors: 1

!!!FAILURES!!!
Test Results:
1) test: MathTest::testMultiplication (F) line: 123 src/test.cpp
   Expected: 7
   Actual: 6

2) test: StringTest::testConcatenation (F) line: 45 src/test.cpp
   Expected: "hello"
   Actual: "helo"

There were 2 failures:
1) MathTest::testMultiplication
2) StringTest::testConcatenation

There was 1 error:
1) DatabaseTest::testConnection
"""

cppunit_detailed_log = """
.....F..E.....

There were 2 failures:
1) Test name: MathTest::testDivision
   Assertion failed
   Expected: 5
   Actual: 4

2) Test name: StringTest::testReverse
   Assertion failed

There was 1 error:
1) Test name: DatabaseTest::testQuery
   SQLException: Connection timeout

Tests run: 15, Failures: 2, Errors: 1, Skipped: 0
"""


# ============================================================================
# Test Helper Function
# ============================================================================

def test_parser(name, parser_func, log_content, expected_total=None, 
                expected_passed=None, expected_failed=None, expected_skipped=None):
    """Test a parser and validate results."""
    print(f"\n{'=' * 60}")
    print(f"Testing {name} parser")
    print(f"{'=' * 60}")
    
    result = parser_func(log_content)
    
    # Validate result exists
    assert result is not None, f"{name} parser returned None"
    assert len(result) > 0, f"{name} parser returned empty dict"
    
    # Count statuses
    passed = sum(1 for s in result.values() if s == "PASSED")
    failed = sum(1 for s in result.values() if s == "FAILED")
    skipped = sum(1 for s in result.values() if s == "SKIPPED")
    
    print(f"  Total tests: {len(result)}")
    print(f"  PASSED: {passed}")
    print(f"  FAILED: {failed}")
    print(f"  SKIPPED: {skipped}")
    
    # Show sample results
    print("\n  Sample results:")
    for i, (test_name, status) in enumerate(list(result.items())[:5]):
        symbol = "✓" if status == "PASSED" else "✗" if status == "FAILED" else "○"
        print(f"    {symbol} {test_name}: {status}")
    
    if len(result) > 5:
        print(f"    ... and {len(result) - 5} more")
    
    # Validate against expected counts if provided
    if expected_total is not None:
        assert len(result) == expected_total, \
            f"Expected {expected_total} tests, got {len(result)}"
    if expected_passed is not None:
        assert passed == expected_passed, \
            f"Expected {expected_passed} passed, got {passed}"
    if expected_failed is not None:
        assert failed == expected_failed, \
            f"Expected {expected_failed} failed, got {failed}"
    if expected_skipped is not None:
        assert skipped == expected_skipped, \
            f"Expected {expected_skipped} skipped, got {skipped}"
    
    print(f"\n✓ {name} parser passed all validations")
    return result


# ============================================================================
# Main Test Execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("C++ TEST PARSER UNIT TESTS")
    print("=" * 60)
    print("\nTesting all C++ test parsers with real and synthetic data...")
    
    all_passed = True
    results = {}
    
    try:
        # CTest Parser Tests
        print("\n" + "=" * 60)
        print("CTEST PARSER TESTS")
        print("=" * 60)
        results["ctest_simple"] = test_parser(
            "CTest (simple)", parse_log_ctest, ctest_log_simple,
            expected_total=3, expected_passed=3, expected_failed=0
        )
        results["ctest_verbose"] = test_parser(
            "CTest (verbose)", parse_log_ctest, ctest_log_verbose,
            expected_total=5, expected_passed=4, expected_failed=1
        )
        
        # Catch2 Parser Tests
        print("\n" + "=" * 60)
        print("CATCH2 PARSER TESTS")
        print("=" * 60)
        results["catch2_xml"] = test_parser(
            "Catch2 (XML)", parse_log_catch2, catch2_xml_log,
            expected_total=5, expected_passed=3, expected_failed=2
        )
        results["catch2_text"] = test_parser(
            "Catch2 (text)", parse_log_catch2, catch2_text_log,
            expected_total=50, expected_passed=50, expected_failed=0
        )
        results["catch2_summary"] = test_parser(
            "Catch2 (summary)", parse_log_catch2, catch2_summary_log,
            expected_total=150, expected_passed=145, expected_failed=5
        )
        
        # GTest Parser Tests
        print("\n" + "=" * 60)
        print("GTEST PARSER TESTS")
        print("=" * 60)
        results["gtest_detailed"] = test_parser(
            "GTest (detailed)", parse_log_gtest, gtest_log,
            expected_failed=2  # At least verify we found the 2 failures
        )
        results["gtest_summary"] = test_parser(
            "GTest (summary)", parse_log_gtest, gtest_summary_log,
            expected_failed=2  # At least verify we found the 2 failures
        )
        
        # Boost.Test Parser Tests
        print("\n" + "=" * 60)
        print("BOOST.TEST PARSER TESTS")
        print("=" * 60)
        results["boost_success"] = test_parser(
            "Boost.Test (success)", parse_log_boost_test, boost_test_success_log,
            expected_failed=0
        )
        results["boost_failure"] = test_parser(
            "Boost.Test (failures)", parse_log_boost_test, boost_test_failure_log,
            expected_failed=2  # At least verify we found the 2 failures
        )
        results["boost_suites"] = test_parser(
            "Boost.Test (suites)", parse_log_boost_test, boost_test_with_suites,
            expected_failed=1  # At least verify we found the 1 failure
        )
        
        # CppUnit Parser Tests
        print("\n" + "=" * 60)
        print("CPPUNIT PARSER TESTS")
        print("=" * 60)
        results["cppunit_success"] = test_parser(
            "CppUnit (success)", parse_log_cppunit, cppunit_success_log,
            expected_total=150, expected_passed=150, expected_failed=0
        )
        results["cppunit_failure"] = test_parser(
            "CppUnit (failures)", parse_log_cppunit, cppunit_failure_log,
            expected_failed=2  # 2 explicit failures captured
        )
        results["cppunit_detailed"] = test_parser(
            "CppUnit (detailed)", parse_log_cppunit, cppunit_detailed_log,
            expected_failed=3  # At least verify we found the 3 failures/errors
        )
        
    except AssertionError as e:
        print(f"\n\n❌ TEST FAILED: {e}")
        all_passed = False
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # Final Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        if result:
            total = len(result)
            passed = sum(1 for s in result.values() if s == "PASSED")
            failed = sum(1 for s in result.values() if s == "FAILED")
            print(f"✓ {test_name:25s}: {total:3d} tests ({passed} passed, {failed} failed)")
        else:
            print(f"✗ {test_name:25s}: Failed to parse")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
    print("=" * 60)
    
    exit(0 if all_passed else 1)
