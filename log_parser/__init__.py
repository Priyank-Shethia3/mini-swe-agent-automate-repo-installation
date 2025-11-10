"""
Simplified test log parser system.

This module provides a simple, regex-based parsing system for test output logs.
Each test framework has its own dedicated parser class.
"""

from .parsers.jest import parse_log_jest
from .parsers.mocha import parse_log_mocha
from .parsers.pytest import parse_log_pytest
from .parsers.go_test import parse_log_go_test
from .parsers.cargo import parse_log_cargo
from .parsers.maven import parse_log_maven

__all__ = [
    'parse_log_jest',
    'parse_log_mocha', 
    'parse_log_pytest',
    'parse_log_go_test',
    'parse_log_cargo',
    'parse_log_maven'
]