#!/usr/bin/env python3
"""Test edge cases and additional verbose formats."""

from log_parser.parsers.pytest import parse_log_pytest
from log_parser.parsers.jest import parse_log_jest
from log_parser.parsers.mocha import parse_log_mocha
from log_parser.parsers.go_test import parse_log_go_test
from log_parser.parsers.cargo import parse_log_cargo
from log_parser.parsers.maven import parse_log_maven

# Pytest with -vv (extra verbose)
pytest_vv_log = """
============================= test session starts ==============================
platform darwin -- Python 3.11.5, pytest-7.4.3, pluggy-1.3.0 -- /usr/local/bin/python3
cachedir: .pytest_cache
rootdir: /Users/user/project
configfile: pytest.ini
plugins: asyncio-0.21.1, cov-4.1.0
collected 10 items

tests/unit/test_auth.py::test_login_success PASSED                      [ 10%]
tests/unit/test_auth.py::test_login_invalid_password FAILED             [ 20%]
tests/unit/test_auth.py::TestUserManagement::test_create_user PASSED    [ 30%]
tests/unit/test_auth.py::TestUserManagement::test_delete_user SKIPPED   [ 40%]
tests/integration/test_api.py::test_get_endpoint PASSED                 [ 50%]
tests/integration/test_api.py::test_post_endpoint ERROR                 [ 60%]
tests/e2e/test_workflow.py::test_full_workflow[chrome] PASSED           [ 70%]
tests/e2e/test_workflow.py::test_full_workflow[firefox] FAILED          [ 80%]
tests/e2e/test_workflow.py::test_full_workflow[safari] SKIPPED          [ 90%]
tests/performance/test_load.py::test_concurrent_requests PASSED         [100%]

=================================== FAILURES ===================================
_________________________ test_login_invalid_password __________________________
"""

# Jest with --verbose and custom reporters
jest_custom_log = """
PASS src/components/Button.test.tsx (2.341 s)
  Button Component
    Rendering
      ✓ renders with default props (45 ms)
      ✓ renders with custom className (12 ms)
    Interactions
      ✓ calls onClick handler when clicked (23 ms)
      ✕ disables button when loading (15 ms)
      ○ shows loading spinner

FAIL src/utils/validation.test.js
  Validation Utils
    Email validation
      ✓ accepts valid email addresses (2 ms)
      ✕ rejects invalid email addresses (3 ms)
    Phone validation
      ✓ accepts valid phone numbers (1 ms)
      ○ validates international formats

Test Suites: 1 failed, 1 passed, 2 total
Tests:       5 passed, 2 failed, 2 skipped, 9 total
"""

# Mocha with different reporters (spec, tap, json)
mocha_tap_log = """
TAP version 13
ok 1 Math utilities should add two numbers
ok 2 Math utilities should subtract two numbers
not ok 3 Math utilities should multiply two numbers
  ---
  message: 'expected 6 to equal 7'
  severity: fail
  ...
ok 4 Math utilities should divide two numbers # SKIP
ok 5 String utilities should capitalize first letter
not ok 6 String utilities should trim whitespace
ok 7 Array utilities should filter items
1..7
# tests 7
# pass 4
# fail 2
# skip 1
"""

# Go test with -v and benchmarks
go_benchmark_log = """
=== RUN   TestStringConcat
--- PASS: TestStringConcat (0.00s)
=== RUN   TestStringBuilder
--- PASS: TestStringBuilder (0.00s)
=== RUN   TestParseJSON
    parse_test.go:25: Testing JSON parsing
=== RUN   TestParseJSON/valid_json
--- PASS: TestParseJSON/valid_json (0.00s)
=== RUN   TestParseJSON/invalid_json
    parse_test.go:35: Expected error for invalid JSON
--- FAIL: TestParseJSON/invalid_json (0.00s)
--- FAIL: TestParseJSON (0.00s)
=== RUN   TestTimeout
--- SKIP: TestTimeout (0.00s)
    timeout_test.go:10: Skipping timeout test in CI
BenchmarkStringConcat-8     1000000      1052 ns/op
BenchmarkStringBuilder-8   5000000       234 ns/op
PASS
ok      example.com/perf    3.456s
"""

# Cargo test with --nocapture and doc tests
cargo_nocapture_log = """
running 10 tests
test core::tests::test_config_load ... ok
test core::tests::test_config_save ... ok
test core::tests::test_config_validate ... FAILED
test utils::string::tests::test_trim ... ok
test utils::string::tests::test_split ... ignored
test utils::math::tests::test_factorial ... ok
test utils::math::tests::test_fibonacci ... FAILED
test integration::test_full_flow ... ok
test benchmarks::bench_parse ... ignored
test benchmarks::bench_serialize ... ok

failures:

---- core::tests::test_config_validate stdout ----
Validation should have failed for invalid config
thread 'core::tests::test_config_validate' panicked at 'assertion failed'

---- utils::math::tests::test_fibonacci stdout ----
Expected: [1, 1, 2, 3, 5, 8]
Got: [1, 1, 2, 3, 5, 7]

failures:
    core::tests::test_config_validate
    utils::math::tests::test_fibonacci

test result: FAILED. 6 passed; 2 failed; 2 ignored; 0 measured; 0 filtered out

   Doc-tests mylib

running 5 tests
test src/lib.rs - (line 10) ... ok
test src/utils.rs - trim_string (line 25) ... ok
test src/utils.rs - parse_int (line 45) ... FAILED
test src/config.rs - Config::new (line 15) ... ok
test src/config.rs - Config::validate (line 30) ... ignored
"""

# Maven with TestNG and parameterized tests
maven_testng_log = """
-------------------------------------------------------
 T E S T S
-------------------------------------------------------
Running TestSuite
Configuring TestNG with: org.apache.maven.surefire.testng.conf.TestNG652Configurator@4b1210ee
testLogin[admin,password123](com.example.AuthTest)  Time elapsed: 0.125 sec
testLogin[user,pass456](com.example.AuthTest)  Time elapsed: 0.089 sec  <<< FAILURE!
java.lang.AssertionError: Login failed for user
	at com.example.AuthTest.testLogin(AuthTest.java:45)

testDataProcessing[dataset1](com.example.DataTest)  Time elapsed: 1.234 sec
testDataProcessing[dataset2](com.example.DataTest)  Time elapsed: 0.987 sec
testDataProcessing[dataset3](com.example.DataTest)  Time elapsed: 2.456 sec  <<< ERROR!
java.io.IOException: File not found: dataset3.csv
	at com.example.DataTest.testDataProcessing(DataTest.java:78)

Tests run: 5, Failures: 1, Errors: 1, Skipped: 0, Time elapsed: 4.891 sec <<< FAILURE!

Running com.example.IntegrationTest
testApiEndpoint(com.example.IntegrationTest)  Time elapsed: 0.543 sec
testDatabaseConnection(com.example.IntegrationTest)  Time elapsed: 0.234 sec
testCacheInvalidation(com.example.IntegrationTest)  Time elapsed: 0.156 sec  <<< FAILURE!

Tests run: 3, Failures: 1, Errors: 0, Skipped: 0, Time elapsed: 0.933 sec <<< FAILURE!
"""

def test_edge_cases():
    """Test edge cases and additional verbose formats."""
    
    print("Testing edge cases and additional verbose formats")
    print("=" * 60)
    
    # Test pytest with extra verbose
    print("\n1. Testing pytest with -vv output")
    result = parse_log_pytest(pytest_vv_log)
    if result:
        print(f"   ✓ Parsed {len(result)} tests")
        # Check for parametrized tests
        if any('[' in name for name in result.keys()):
            print("   ✓ Correctly handled parametrized tests")
    else:
        print("   ✗ Failed to parse")
    
    # Test jest with custom output
    print("\n2. Testing jest with custom reporter output")
    result = parse_log_jest(jest_custom_log)
    if result:
        print(f"   ✓ Parsed {len(result)} tests")
        # Check for nested describe blocks
        nested_count = sum(1 for name in result.keys() if len(name) > 20)
        if nested_count > 0:
            print(f"   ✓ Handled nested describe blocks")
    else:
        print("   ✗ Failed to parse")
    
    # Test mocha with TAP output
    print("\n3. Testing mocha with TAP format")
    result = parse_log_mocha(mocha_tap_log)
    if result:
        print(f"   ✓ Parsed {len(result)} tests from TAP format")
    else:
        print("   ✗ Failed to parse TAP format")
    
    # Test go with benchmarks
    print("\n4. Testing go test with benchmarks")
    result = parse_log_go_test(go_benchmark_log)
    if result:
        print(f"   ✓ Parsed {len(result)} tests")
        # Check for subtests
        if any('.' in name for name in result.keys()):
            print("   ✓ Correctly handled subtests")
    else:
        print("   ✗ Failed to parse")
    
    # Test cargo with doc tests
    print("\n5. Testing cargo with --nocapture and doc tests")
    result = parse_log_cargo(cargo_nocapture_log)
    if result:
        print(f"   ✓ Parsed {len(result)} tests")
        # Check for doc tests
        doc_test_count = sum(1 for name in result.keys() if 'doctest' in name)
        if doc_test_count > 0:
            print(f"   ✓ Parsed {doc_test_count} doc tests")
    else:
        print("   ✗ Failed to parse")
    
    # Test maven with TestNG
    print("\n6. Testing maven with TestNG and parameterized tests")  
    result = parse_log_maven(maven_testng_log)
    if result:
        print(f"   ✓ Parsed {len(result)} tests")
        # Check for parameterized tests
        param_count = sum(1 for name in result.keys() if '[' in name or ']' in name)
        if param_count > 0:
            print(f"   ✓ Handled {param_count} parameterized tests")
    else:
        print("   ✗ Failed to parse")

if __name__ == "__main__":
    test_edge_cases()