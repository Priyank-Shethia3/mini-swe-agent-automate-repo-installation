#!/usr/bin/env python3
"""
Generate SWE-smith Profile from Existing Test Results

This script takes an existing result directory with:
- repo_metadata.json (from Stage 1: simple_repo_to_dockerfile.py)
- test_output.txt (from Stage 2: verify_dockerfile.py)
- parsed_test_status.json (from Stage 3: verify_testing.py)

And generates:
- Profile class code
- Integration metadata
- Integration instructions

Usage:
    python generate_profile_from_results.py agent-result/owner-repo
    python generate_profile_from_results.py agent-result/owner-repo --python-repo
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


def load_metadata(result_dir: Path) -> Optional[Dict[str, Any]]:
    """Load repo_metadata.json from result directory."""
    metadata_path = result_dir / "repo_metadata.json"

    if not metadata_path.exists():
        print(f"❌ repo_metadata.json not found at {metadata_path}")
        return None

    try:
        with open(metadata_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ Error reading repo_metadata.json: {e}")
        return None


def load_parsed_results(result_dir: Path) -> Optional[Dict[str, Any]]:
    """Load parsed_test_status.json from result directory."""
    parsed_path = result_dir / "parsed_test_status.json"

    if not parsed_path.exists():
        print(f"❌ parsed_test_status.json not found at {parsed_path}")
        return None

    try:
        with open(parsed_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ Error reading parsed_test_status.json: {e}")
        return None


def load_dockerfile(result_dir: Path) -> Optional[str]:
    """Load Dockerfile content from result directory."""
    dockerfile_path = result_dir / "Dockerfile"

    if not dockerfile_path.exists():
        return None

    try:
        with open(dockerfile_path, "r") as f:
            return f.read().strip()
    except IOError as e:
        print(f"⚠️  Error reading Dockerfile: {e}")
        return None


def load_install_script(result_dir: Path) -> Optional[str]:
    """Load conda installation script from result directory."""
    install_scripts = list(result_dir.glob("*_install.sh"))

    if not install_scripts:
        return None

    install_script = install_scripts[0]
    try:
        with open(install_script, "r") as f:
            return f.read().strip()
    except IOError as e:
        print(f"⚠️  Error reading installation script: {e}")
        return None


def create_class_name(owner: str, repo: str, commit: str) -> str:
    """Generate a valid Python class name following SWE-smith conventions."""
    clean_repo = re.sub(r"[^a-zA-Z0-9]", "", repo)

    if clean_repo:
        clean_repo = clean_repo[0].upper() + clean_repo[1:]

    commit_suffix = commit[:8] if commit and len(commit) >= 8 else "00000000"

    return f"{clean_repo}{commit_suffix}"


def generate_python_profile_class(
    owner: str,
    repo: str,
    metadata: Dict[str, Any],
    parsed_results: Optional[Dict[str, Any]],
    install_script: Optional[str],
) -> str:
    """Generate SWE-smith compatible Python profile class code."""
    class_name = create_class_name(owner, repo, metadata.get("commit_hash", ""))
    commit = metadata.get("commit_hash", "unknown")
    install_commands = metadata.get("install_commands", ["pip install -e ."])

    install_cmds_str = ",\n            ".join([f'"{cmd}"' for cmd in install_commands])

    header_comment = f"""# Auto-generated profile for {owner}/{repo}
# Commit: {commit}
# Generated: {datetime.now().isoformat()}
# Integration: Copy to swesmith/profiles/python.py
"""

    profile_code = f'''{header_comment}
@dataclass
class {class_name}(PythonProfile):
    owner: str = "{owner}"
    repo: str = "{repo}"
    commit: str = "{commit}"
    install_cmds: list = field(
        default_factory=lambda: [
            {install_cmds_str}
        ]
    )


'''

    return profile_code


def _template_dockerfile(dockerfile_content: str) -> str:
    """Convert agent's Dockerfile to use template variables."""
    dockerfile = dockerfile_content

    # Replace actual owner/repo with template variables
    dockerfile = re.sub(
        r"https://github\.com/[^/]+/[^/\s]+\.git",
        "https://github.com/{self.owner}/{self.repo}.git",
        dockerfile,
    )
    dockerfile = re.sub(
        r"git clone https://github\.com/[^/]+/[^\s]+",
        "git clone https://github.com/{self.owner}/{self.repo}.git",
        dockerfile,
    )

    # Replace WORKDIR /app with WORKDIR /testbed (SWE-smith convention)
    dockerfile = re.sub(r"WORKDIR /app\b", "WORKDIR /testbed", dockerfile)

    # Replace paths like /app/ with /testbed/
    dockerfile = dockerfile.replace("/app/", "/testbed/")

    # Replace paths like RUN git clone ... /app
    dockerfile = re.sub(r"(git clone [^\s]+ )/app\b", r"\1/testbed", dockerfile)

    # CRITICAL FIX for Modal compatibility:
    # Modal's legacy image builder skips WORKDIR, so we need to ensure
    # git clone CREATES /testbed explicitly, then WORKDIR sets it.
    # Change: "RUN git clone ... ." to "RUN git clone ... /testbed"
    # This must happen AFTER git is installed but BEFORE other commands

    # Pattern: Find "git clone ... ." and replace . with /testbed
    dockerfile = re.sub(r"(RUN git clone [^\n]+) \.", r"\1 /testbed", dockerfile)

    # CRITICAL FIX 2: Remove WORKDIR /testbed if it appears BEFORE git clone
    # because it creates an empty directory that git clone can't use
    # Pattern: Remove "WORKDIR /testbed" lines that appear before "RUN git clone"
    lines = dockerfile.split("\n")
    result_lines = []
    skip_workdir = False

    for i, line in enumerate(lines):
        # Check if this is a WORKDIR /testbed line
        if re.match(r"^\s*WORKDIR /testbed\s*$", line):
            # Look ahead to see if git clone comes after
            has_git_clone_after = False
            for j in range(i + 1, len(lines)):
                if "git clone" in lines[j] and "/testbed" in lines[j]:
                    has_git_clone_after = True
                    break
                # Stop looking if we hit another significant command
                if lines[j].strip().startswith("RUN") and "git clone" not in lines[j]:
                    break

            if has_git_clone_after:
                # Skip this WORKDIR line, we'll add it after git clone
                continue

        result_lines.append(line)

    # Now add WORKDIR /testbed after the git clone line if it's not already there
    # Also add git checkout {self.commit} after WORKDIR
    final_lines = []
    for i, line in enumerate(result_lines):
        final_lines.append(line)
        # If this is the git clone line, add WORKDIR after it
        if "git clone" in line and "/testbed" in line:
            # Check if next non-empty line is already WORKDIR
            next_is_workdir = False
            for j in range(i + 1, len(result_lines)):
                if result_lines[j].strip():
                    if "WORKDIR /testbed" in result_lines[j]:
                        next_is_workdir = True
                    break
            if not next_is_workdir:
                final_lines.append("WORKDIR /testbed")
                final_lines.append("RUN git checkout {self.commit}")
        # If this is a WORKDIR /testbed line that comes after git clone, add git checkout after it
        elif "WORKDIR /testbed" in line:
            # Check if this WORKDIR comes after a git clone
            has_git_clone_before = any(
                "git clone" in l for l in final_lines[: len(final_lines) - 1]
            )
            # Check if git checkout is already on the next line
            has_checkout_after = False
            if i + 1 < len(result_lines) and "git checkout" in result_lines[i + 1]:
                has_checkout_after = True
            if has_git_clone_before and not has_checkout_after:
                final_lines.append("RUN git checkout {self.commit}")

    return "\n".join(final_lines)


def _generate_log_parser(parser_name: str) -> str:
    """Generate log parser code based on test framework."""
    if parser_name == "gradle":
        return '''def log_parser(self, log: str) -> dict[str, str]:
        """Parse JUnit XML test results from Gradle output."""
        import re
        import xml.etree.ElementTree as ET
        
        test_status_map = {}
        xml_matches = re.findall(r'<\\?xml version.*?</testsuite>', log, re.DOTALL)
        
        for xml_content in xml_matches:
            try:
                root = ET.fromstring(xml_content)
                suite_classname = root.get('name', '')
                
                for testcase in root.findall('.//testcase'):
                    classname = testcase.get('classname', suite_classname)
                    methodname = testcase.get('name', '')
                    test_name = f"{classname}.{methodname}"
                    
                    if testcase.find('failure') is not None or testcase.find('error') is not None:
                        test_status_map[test_name] = TestStatus.FAILED.value
                    elif testcase.find('skipped') is not None:
                        test_status_map[test_name] = TestStatus.SKIPPED.value
                    else:
                        test_status_map[test_name] = TestStatus.PASSED.value
            except ET.ParseError:
                continue
        
        return test_status_map'''
    elif parser_name == "maven":
        return '''def log_parser(self, log: str) -> dict[str, str]:
        """Parse Maven Surefire text output with per-method granularity.
        
        Parses individual test methods from Maven Surefire output when using:
        mvn test -B -T 1C -Dsurefire.useFile=false -Dsurefire.printSummary=true -Dsurefire.reportFormat=plain
        """
        import re
        from swebench.harness.constants import TestStatus
        
        test_status_map = {}
        # Pattern matches: [INFO] testMethodName -- Time elapsed: 0.001 s
        # or: [ERROR] testMethodName -- Time elapsed: 0.001 s <<< FAILURE!
        pattern = r"^\\[(INFO|ERROR)\\]\\s+(.*?)\\s+--\\s+Time elapsed:\\s+([\\d.]+)\\s"
        
        for line in log.split("\\n"):
            if line.endswith("<<< FAILURE!") and line.startswith("[ERROR]"):
                test_name = re.match(pattern, line)
                if test_name is None:
                    continue
                test_status_map[test_name.group(2)] = TestStatus.FAILED.value
            elif (
                any([line.startswith(s) for s in ["[INFO]", "[ERROR]"]])
                and "Time elapsed:" in line
            ):
                test_name = re.match(pattern, line)
                if test_name is None:
                    continue
                test_status_map[test_name.group(2)] = TestStatus.PASSED.value
        return test_status_map'''
    else:
        return '''def log_parser(self, log: str) -> dict[str, str]:
        """Parse test output - customize for your framework."""
        return {}  # TODO: Implement parser'''


def generate_java_profile_class(
    owner: str,
    repo: str,
    metadata: Dict[str, Any],
    parsed_results: Optional[Dict[str, Any]],
    dockerfile_content: Optional[str],
) -> str:
    """Generate SWE-smith compatible Java profile class code."""
    if not dockerfile_content:
        raise ValueError(
            f"No Dockerfile found for {owner}/{repo}. Agent must generate Dockerfile first."
        )

    class_name = create_class_name(owner, repo, metadata.get("commit_hash", ""))
    commit = metadata.get("commit_hash", "unknown")
    test_commands = metadata.get("test_commands", ["./gradlew test"])
    test_cmd = test_commands[0] if test_commands else "./gradlew test"

    # Determine timeout based on build system
    is_maven = any("mvn" in cmd for cmd in test_commands)
    timeout = 400 if is_maven else 300
    build_tool = "Maven" if is_maven else "Gradle"

    # Use Maven parser if Maven detected, otherwise use parsed_results or default to gradle
    if is_maven:
        parser_name = "maven"
    else:
        parser_name = (
            parsed_results.get("parser", "gradle") if parsed_results else "gradle"
        )

    dockerfile_template = _template_dockerfile(dockerfile_content)
    log_parser_code = _generate_log_parser(parser_name)

    header_comment = f"""# Auto-generated profile for {owner}/{repo}
# Commit: {commit}
# Generated: {datetime.now().isoformat()}
# Integration: Copy to swesmith/profiles/java.py
"""

    profile_code = f'''{header_comment}
@dataclass
class {class_name}(JavaProfile):
    owner: str = "{owner}"
    repo: str = "{repo}"
    commit: str = "{commit}"
    test_cmd: str = "{test_cmd}"
    timeout: int = {timeout}  # {build_tool} tests can be slow

    @property
    def dockerfile(self):
        return f"""{dockerfile_template}"""

    {log_parser_code}


'''

    return profile_code


def generate_javascript_profile_class(
    owner: str,
    repo: str,
    metadata: Dict[str, Any],
    parsed_results: Optional[Dict[str, Any]],
    dockerfile_content: Optional[str],
) -> str:
    """Generate SWE-smith compatible JavaScript profile class code."""
    if not dockerfile_content:
        raise ValueError(
            f"No Dockerfile found for {owner}/{repo}. Agent must generate Dockerfile first."
        )

    class_name = create_class_name(owner, repo, metadata.get("commit_hash", ""))
    commit = metadata.get("commit_hash", "unknown")
    test_commands = metadata.get("test_commands", ["npm test"])
    test_cmd = test_commands[0] if test_commands else "npm test"

    parser_name = parsed_results.get("parser", "mocha") if parsed_results else "mocha"
    dockerfile_template = _template_dockerfile(dockerfile_content)

    header_comment = f"""# Auto-generated profile for {owner}/{repo}
# Commit: {commit}
# Generated: {datetime.now().isoformat()}
# Integration: Copy to swesmith/profiles/javascript.py
"""

    # Generate inline log parser for JS frameworks
    if parser_name == "jest":
        log_parser_code = _generate_log_parser("jest_unused")  # placeholder
    elif parser_name == "mocha":
        log_parser_code = _generate_log_parser("mocha_unused")  # placeholder
    else:
        log_parser_code = _generate_log_parser("unknown")

    profile_code = f'''{header_comment}
@dataclass
class {class_name}(JavaScriptProfile):
    owner: str = "{owner}"
    repo: str = "{repo}"
    commit: str = "{commit}"
    test_cmd: str = "{test_cmd}"

    @property
    def dockerfile(self):
        return f"""{dockerfile_template}"""

    {log_parser_code}


'''

    return profile_code


def generate_generic_profile_class(
    owner: str,
    repo: str,
    metadata: Dict[str, Any],
    parsed_results: Optional[Dict[str, Any]],
    dockerfile_content: Optional[str],
) -> str:
    """Generate SWE-smith compatible generic profile class code."""
    if not dockerfile_content:
        raise ValueError(
            f"No Dockerfile found for {owner}/{repo}. Agent must generate Dockerfile first."
        )

    class_name = create_class_name(owner, repo, metadata.get("commit_hash", ""))
    commit = metadata.get("commit_hash", "unknown")
    language = metadata.get("language", "unknown").lower()
    test_commands = metadata.get("test_commands", ["make test"])
    test_cmd = test_commands[0] if test_commands else "make test"

    parser_name = (
        parsed_results.get("parser", "unknown") if parsed_results else "unknown"
    )
    dockerfile_template = _template_dockerfile(dockerfile_content)
    log_parser_code = _generate_log_parser(parser_name)

    header_comment = f"""# Auto-generated profile for {owner}/{repo} ({language})
# Commit: {commit}
# Generated: {datetime.now().isoformat()}
# Integration: Copy to swesmith/profiles/{language}.py
"""

    profile_code = f'''{header_comment}
@dataclass
class {class_name}(RepoProfile):
    owner: str = "{owner}"
    repo: str = "{repo}"
    commit: str = "{commit}"
    test_cmd: str = "{test_cmd}"

    @property
    def dockerfile(self):
        return f"""{dockerfile_template}"""

    {log_parser_code}


'''

    return profile_code


def save_profile_class(
    result_dir: Path, profile_class_code: str, class_name: str
) -> Path:
    """Save the generated profile class to generated_profiles directory."""
    profiles_dir = result_dir / "generated_profiles"
    profiles_dir.mkdir(exist_ok=True)

    profile_file = profiles_dir / "profile_class.py"
    with open(profile_file, "w", encoding="utf-8") as f:
        f.write(profile_class_code)

    return profile_file


def save_integration_metadata(
    result_dir: Path,
    owner: str,
    repo: str,
    metadata: Dict[str, Any],
    parsed_results: Optional[Dict[str, Any]],
    is_python_repo: bool,
    class_name: str,
) -> Path:
    """Save integration metadata for SWE-smith."""
    profiles_dir = result_dir / "generated_profiles"
    profiles_dir.mkdir(exist_ok=True)

    if is_python_repo:
        language = "python"
        base_class = "PythonProfile"
        target_file = "swesmith/profiles/python.py"
    elif metadata.get("language", "").lower() == "javascript":
        language = "javascript"
        base_class = "JavaScriptProfile"
        target_file = "swesmith/profiles/javascript.py"
    elif metadata.get("language", "").lower() == "java":
        language = "java"
        base_class = "JavaProfile"
        target_file = "swesmith/profiles/java.py"
    else:
        language = metadata.get("language", "unknown").lower()
        base_class = "RepoProfile"
        language_files = {
            "go": "golang.py",
            "rust": "rust.py",
            "c": "c.py",
            "cpp": "cpp.py",
        }
        target_file = f"swesmith/profiles/{language_files.get(language, 'base.py')}"

    integration_metadata = {
        "profile_class_name": class_name,
        "target_file": target_file,
        "base_class": base_class,
        "language": language,
        "repository": f"{owner}/{repo}",
        "commit": metadata.get("commit_hash", "unknown"),
        "integration_ready": True,
        "generated_timestamp": datetime.now().isoformat(),
        "test_framework": parsed_results.get("parser", "unknown")
        if parsed_results
        else "unknown",
        "install_commands": metadata.get("install_commands", []),
        "test_commands": metadata.get("test_commands", []),
    }

    metadata_file = profiles_dir / "profile_metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(integration_metadata, f, indent=2)

    return metadata_file


def save_integration_instructions(
    result_dir: Path, owner: str, repo: str, class_name: str, target_file: str
) -> Path:
    """Generate integration instructions."""
    profiles_dir = result_dir / "generated_profiles"
    profiles_dir.mkdir(exist_ok=True)

    instructions = f"""# Integration Instructions

## Generated Profile: {class_name}
Repository: {owner}/{repo}

## Steps to integrate into SWE-smith:

1. **Copy the profile class:**
   ```bash
   cat {result_dir}/generated_profiles/profile_class.py >> /path/to/SWE-smith/{target_file}
   ```

2. **Verify the registration loop in the target file**

3. **Test the integration:**
   ```python
   from swesmith.profiles import registry
   profile = registry.get("{owner}/{repo}")
   print(f"Profile loaded: {{profile.__class__.__name__}}")
   ```

## Files generated:
- `profile_class.py` - The profile class to copy
- `profile_metadata.json` - Integration metadata
- `integration_instructions.md` - This file
"""

    instructions_file = profiles_dir / "integration_instructions.md"
    with open(instructions_file, "w", encoding="utf-8") as f:
        f.write(instructions)

    return instructions_file


def main():
    parser = argparse.ArgumentParser(
        description="Generate SWE-smith profile from existing test results"
    )
    parser.add_argument(
        "result_dir",
        type=Path,
        help="Path to result directory (e.g., agent-result/owner-repo)",
    )
    parser.add_argument(
        "--python-repo", action="store_true", help="Treat as Python repository"
    )

    args = parser.parse_args()

    result_dir = args.result_dir.resolve()

    if not result_dir.exists():
        print(f"❌ Result directory not found: {result_dir}")
        sys.exit(1)

    print(f"📂 Processing results from: {result_dir}")

    # Load metadata and parsed results
    metadata = load_metadata(result_dir)
    if not metadata:
        print("❌ Cannot generate profile without repo_metadata.json")
        sys.exit(1)

    parsed_results = load_parsed_results(result_dir)
    if not parsed_results:
        print("⚠️  No parsed_test_status.json found - profile may be incomplete")

    # Extract owner and repo from directory name or metadata
    if "owner" in metadata and "repo" in metadata:
        owner = metadata["owner"]
        repo = metadata["repo"]
    else:
        # Try to parse from directory name (e.g., "kaikramer-keystore-explorer")
        dir_name = result_dir.name
        if "-" in dir_name:
            parts = dir_name.split("-", 1)
            owner = parts[0]
            repo = parts[1]
        else:
            print("❌ Cannot determine owner/repo from directory name or metadata")
            sys.exit(1)

    print(f"✅ Repository: {owner}/{repo}")
    print(f"✅ Language: {metadata.get('language', 'unknown')}")
    if parsed_results:
        print(f"✅ Test framework: {parsed_results.get('parser', 'unknown')}")

    # Generate profile based on repository type
    if args.python_repo:
        install_script = load_install_script(result_dir)
        profile_code = generate_python_profile_class(
            owner, repo, metadata, parsed_results, install_script
        )
    elif metadata.get("language", "").lower() == "javascript":
        dockerfile_content = load_dockerfile(result_dir)
        profile_code = generate_javascript_profile_class(
            owner, repo, metadata, parsed_results, dockerfile_content
        )
    elif metadata.get("language", "").lower() == "java":
        dockerfile_content = load_dockerfile(result_dir)
        profile_code = generate_java_profile_class(
            owner, repo, metadata, parsed_results, dockerfile_content
        )
    else:
        dockerfile_content = load_dockerfile(result_dir)
        profile_code = generate_generic_profile_class(
            owner, repo, metadata, parsed_results, dockerfile_content
        )

    # Save profile files
    class_name = create_class_name(owner, repo, metadata.get("commit_hash", ""))

    profile_file = save_profile_class(result_dir, profile_code, class_name)
    print(f"✅ Profile class saved to: {profile_file}")

    metadata_file = save_integration_metadata(
        result_dir, owner, repo, metadata, parsed_results, args.python_repo, class_name
    )
    print(f"✅ Integration metadata saved to: {metadata_file}")

    # Load the metadata to get target file
    with open(metadata_file, "r") as f:
        integration_meta = json.load(f)

    instructions_file = save_integration_instructions(
        result_dir, owner, repo, class_name, integration_meta["target_file"]
    )
    print(f"✅ Integration instructions saved to: {instructions_file}")

    print("\n🎉 Profile generation completed!")
    print(f"   Class name: {class_name}")
    print(f"   Target file: {integration_meta['target_file']}")
    print("\n📋 Generated Profile:")
    print("-" * 60)
    print(profile_code)


if __name__ == "__main__":
    main()
