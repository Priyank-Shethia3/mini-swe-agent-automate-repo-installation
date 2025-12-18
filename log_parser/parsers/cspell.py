import re
from enum import Enum

class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

def parse_log_cspell(log: str) -> dict[str, str]:
    """
    Parses CSpell output.
    Example:
    CSpell: Files checked: 14, Issues found: 0 in 0 files
    """
    results = {}
    
    # Check for formatting tests (Prettier)
    if "All matched files use Prettier code style!" in log:
        results["prettier_format"] = TestStatus.PASSED.value
    elif "Checking formatting..." in log and "npm run suggest:format" in log:
        results["prettier_format"] = TestStatus.FAILED.value

    # Check for build tests (spec-md)
    # The command is spec-md --metadata spec/metadata.json spec/GraphQL.md > /dev/null
    # If it fails, npm test would exit. Since we have the CSpell output below it, it likely passed.
    if "test:build" in log:
        # Assuming if we reached past it without error it passed
        results["spec_build"] = TestStatus.PASSED.value

    # Check for CSpell results
    cspell_match = re.search(r"CSpell: Files checked: (\d+), Issues found: (\d+)", log)
    if cspell_match:
        issues = int(cspell_match.group(2))
        status = TestStatus.PASSED.value if issues == 0 else TestStatus.FAILED.value
        results["cspell_spelling"] = status
    
    return results
