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
        with open(metadata_path, 'r') as f:
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
        with open(parsed_path, 'r') as f:
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
        with open(dockerfile_path, 'r') as f:
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
        with open(install_script, 'r') as f:
            return f.read().strip()
    except IOError as e:
        print(f"⚠️  Error reading installation script: {e}")
        return None


def create_class_name(owner: str, repo: str, commit: str) -> str:
    """Generate a valid Python class name following SWE-smith conventions."""
    clean_repo = re.sub(r'[^a-zA-Z0-9]', '', repo)

    if clean_repo:
        clean_repo = clean_repo[0].upper() + clean_repo[1:]

    commit_suffix = commit[:8] if commit and len(commit) >= 8 else "00000000"

    return f"{clean_repo}{commit_suffix}"


def generate_python_profile_class(owner: str, repo: str, metadata: Dict[str, Any],
                                 parsed_results: Optional[Dict[str, Any]],
                                 install_script: Optional[str]) -> str:
    """Generate SWE-smith compatible Python profile class code."""
    class_name = create_class_name(owner, repo, metadata.get('commit_hash', ''))
    commit = metadata.get('commit_hash', 'unknown')
    install_commands = metadata.get('install_commands', ['pip install -e .'])

    install_cmds_str = ',\n            '.join([f'"{cmd}"' for cmd in install_commands])

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


def generate_java_profile_class(owner: str, repo: str, metadata: Dict[str, Any],
                               parsed_results: Optional[Dict[str, Any]],
                               dockerfile_content: Optional[str]) -> str:
    """Generate SWE-smith compatible Java profile class code."""
    class_name = create_class_name(owner, repo, metadata.get('commit_hash', ''))
    commit = metadata.get('commit_hash', 'unknown')
    test_commands = metadata.get('test_commands', ['./gradlew test'])
    
    parser_name = parsed_results.get('parser', 'gradle') if parsed_results else 'gradle'
    
    # Determine if this is Gradle or Maven
    is_gradle = any('gradlew' in cmd for cmd in test_commands)
    is_maven = any('mvn' in cmd for cmd in test_commands)
    
    # For Gradle/Maven, we need to combine test execution + XML extraction
    # The log parser expects XML content in the output
    # CRITICAL: Use `;` not `&&` so XML extraction runs even if tests fail
    if len(test_commands) > 1:
        # Combine all commands (typically: run tests + extract XML)
        # Clean up first command (remove || true)
        first_cmd = test_commands[0]
        if ' || true' in first_cmd:
            first_cmd = first_cmd.split(' || true')[0].strip()
        
        # Add flags for better test execution
        if is_gradle and '--continue' not in first_cmd:
            first_cmd = first_cmd.replace('test', 'test --continue')
        
        # Combine with XML extraction using `;` not `&&`
        # Escape the semicolon in -exec: `\;` instead of `;`
        remaining_cmds = test_commands[1:]
        xml_extraction = remaining_cmds[0] if remaining_cmds else ''
        
        # Fix the find command: escape semicolon and escape quotes around glob
        if 'find' in xml_extraction and '-exec cat {}' in xml_extraction:
            xml_extraction = xml_extraction.replace('-exec cat {} ;', '-exec cat {} \\\\;')
            # Use escaped quotes so they don't break the Python string
            xml_extraction = xml_extraction.replace('TEST-*.xml', '\\"TEST-*.xml\\"')
        
        # Use `;` to ensure XML extraction always runs
        combined_cmd = f"{first_cmd} || true; {xml_extraction}"
        test_cmd = f"/bin/bash -c '{combined_cmd}'"
    else:
        test_cmd = test_commands[0] if test_commands else './gradlew test'
        # Clean up and add flags
        if ' || true' in test_cmd:
            test_cmd = test_cmd.split(' || true')[0].strip()
        if is_gradle and '--continue' not in test_cmd:
            test_cmd = test_cmd.replace('test', 'test --continue')

    header_comment = f"""# Auto-generated profile for {owner}/{repo}
# Commit: {commit}
# Generated: {datetime.now().isoformat()}
# Integration: Copy to swesmith/profiles/java.py
"""

    # Generate inline log parser based on detected framework
    # Note: Parser logic must be inline since profiles will be copy-pasted
    if parser_name == 'gradle':
        log_parser_code = '''def log_parser(self, log: str) -> dict[str, str]:
        """Parse JUnit XML test results from Gradle output."""
        import re
        import xml.etree.ElementTree as ET
        
        test_status_map = {}
        
        # Extract XML content from the log
        xml_matches = re.findall(r'<\\?xml version.*?</testsuite>', log, re.DOTALL)
        
        for xml_content in xml_matches:
            try:
                root = ET.fromstring(xml_content)
                suite_classname = root.get('name', '')
                
                # Parse each testcase
                for testcase in root.findall('.//testcase'):
                    classname = testcase.get('classname', suite_classname)
                    methodname = testcase.get('name', '')
                    test_name = f"{classname}.{methodname}"
                    
                    # Check for failure, error, or skipped
                    if testcase.find('failure') is not None or testcase.find('error') is not None:
                        test_status_map[test_name] = TestStatus.FAILED.value
                    elif testcase.find('skipped') is not None:
                        test_status_map[test_name] = TestStatus.SKIPPED.value
                    else:
                        test_status_map[test_name] = TestStatus.PASSED.value
            except ET.ParseError:
                continue
        
        return test_status_map'''
    elif parser_name == 'maven':
        log_parser_code = '''def log_parser(self, log: str) -> dict[str, str]:
        """Parse Maven Surefire test output."""
        import re
        
        test_status_map = {}
        pattern = r"^\\[(INFO|ERROR)\\]\\s+(.*?)\\s+--\\s+Time elapsed:\\s+([\\d.]+)\\s"
        
        for line in log.split("\\n"):
            if line.endswith("<<< FAILURE!") and line.startswith("[ERROR]"):
                test_name = re.match(pattern, line)
                if test_name:
                    test_status_map[test_name.group(2)] = TestStatus.FAILED.value
            elif any([line.startswith(s) for s in ["[INFO]", "[ERROR]"]]) and "Time elapsed:" in line:
                test_name = re.match(pattern, line)
                if test_name:
                    test_status_map[test_name.group(2)] = TestStatus.PASSED.value
        
        return test_status_map'''
    else:
        log_parser_code = '''def log_parser(self, log: str) -> dict[str, str]:
        """Parse test output - TODO: Implement parser for this framework."""
        return {}  # TODO: Implement parser'''

    # Set appropriate timeout based on build system
    if is_gradle:
        timeout = 300  # Gradle: dependency resolution + compilation is slow
        build_tool = "Gradle"
    elif is_maven:
        timeout = 400  # Maven: multi-threaded builds are very slow
        build_tool = "Maven"
    else:
        timeout = 180
        build_tool = "Java"
    
    # Generate appropriate Dockerfile based on build system
    if is_gradle:
        # Read install commands to determine base image and build command
        install_commands = metadata.get('install_commands', [])
        
        # Extract base image from Dockerfile or use default
        base_image = "eclipse-temurin:17-jdk"  # default
        java_version = "17"
        if dockerfile_content:
            import re
            # Extract FROM line (e.g., "FROM eclipse-temurin:17-jdk")
            from_match = re.search(r'FROM\s+([^\s]+)', dockerfile_content)
            if from_match:
                base_image = from_match.group(1)
                # Extract version number
                version_match = re.search(r':(\d+)', base_image)
                if version_match:
                    java_version = version_match.group(1)
        
        # Check if there's a subdirectory structure (like kse/ for keystore-explorer)
        # Look for multiple WORKDIR commands in the existing Dockerfile
        workdir_path = "/testbed"
        subdirectory = ""
        if dockerfile_content:
            import re
            workdir_matches = re.findall(r'WORKDIR\s+(.+)', dockerfile_content)
            if len(workdir_matches) > 1:
                # Extract the subdirectory from the last WORKDIR
                # e.g., /app/kse -> kse, /testbed/kse -> kse
                last_workdir = workdir_matches[-1].strip()
                subdirectory = last_workdir.split('/')[-1]
                if subdirectory:
                    workdir_path = f"/testbed/{subdirectory}"
        
        # Get the build command from install_commands
        build_cmd = "./gradlew clean build -x test || true"
        if install_commands:
            for cmd in install_commands:
                if 'gradlew' in cmd and 'build' in cmd:
                    build_cmd = cmd
                    if ' || true' not in build_cmd:
                        build_cmd += " || true"
                    break
        
        # Generate Dockerfile with proper subdirectory handling
        if workdir_path != "/testbed":
            dockerfile_template = f'''FROM {base_image}
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/{{self.mirror_name}} /testbed
WORKDIR {workdir_path}
RUN chmod +x gradlew
RUN {build_cmd}
'''
        else:
            dockerfile_template = f'''FROM {base_image}
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/{{self.mirror_name}} /testbed
WORKDIR /testbed
RUN chmod +x gradlew
RUN {build_cmd}
'''
    elif is_maven:
        # Maven Dockerfile
        java_version = "11"  # Maven projects often use Java 11
        if dockerfile_content and 'openjdk-' in dockerfile_content:
            import re
            match = re.search(r'openjdk-(\d+)', dockerfile_content)
            if match:
                java_version = match.group(1)
        
        dockerfile_template = f'''FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
RUN apt-get update && apt-get install -y git openjdk-{java_version}-jdk maven
RUN git clone https://github.com/{{self.mirror_name}} /testbed
WORKDIR /testbed
RUN mvn clean install -B -q -DskipTests -am || true
'''
    else:
        # Generic Java Dockerfile
        dockerfile_template = '''FROM openjdk:17-jdk-slim
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/{self.mirror_name} /testbed
WORKDIR /testbed
'''

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


def generate_javascript_profile_class(owner: str, repo: str, metadata: Dict[str, Any],
                                    parsed_results: Optional[Dict[str, Any]],
                                    dockerfile_content: Optional[str]) -> str:
    """Generate SWE-smith compatible JavaScript profile class code."""
    class_name = create_class_name(owner, repo, metadata.get('commit_hash', ''))
    commit = metadata.get('commit_hash', 'unknown')
    test_commands = metadata.get('test_commands', ['npm test'])
    test_cmd = test_commands[0] if test_commands else 'npm test'

    parser_name = parsed_results.get('parser', 'mocha') if parsed_results else 'mocha'

    header_comment = f"""# Auto-generated profile for {owner}/{repo}
# Commit: {commit}
# Generated: {datetime.now().isoformat()}
# Integration: Copy to swesmith/profiles/javascript.py
"""

    # Generate inline log parser
    if parser_name == 'jest':
        log_parser_code = '''def log_parser(self, log: str) -> dict[str, str]:
        """Parse Jest test output."""
        import re
        test_status_map = {}
        
        for line in log.split("\\n"):
            match = re.match(r'^\\s*(PASS|FAIL)\\s+(.+?)\\s*$', line.strip())
            if match:
                status, test_file = match.groups()
                test_status_map[test_file] = TestStatus.PASSED.value if status == "PASS" else TestStatus.FAILED.value
        
        return test_status_map'''
    elif parser_name == 'mocha':
        log_parser_code = '''def log_parser(self, log: str) -> dict[str, str]:
        """Parse Mocha test output."""
        import re
        test_status_map = {}
        
        for line in log.split("\\n"):
            if re.match(r'^\\s*✓', line):
                test_name = line.strip()[2:].strip()
                test_status_map[test_name] = TestStatus.PASSED.value
            elif re.match(r'^\\s*\\d+\\)', line):
                test_name = line.split(')', 1)[1].strip()
                test_status_map[test_name] = TestStatus.FAILED.value
        
        return test_status_map'''
    else:
        log_parser_code = '''def log_parser(self, log: str) -> dict[str, str]:
        """Parse Mocha test output (default fallback)."""
        import re
        test_status_map = {}
        
        for line in log.split("\\n"):
            if re.match(r'^\\s*✓', line):
                test_name = line.strip()[2:].strip()
                test_status_map[test_name] = TestStatus.PASSED.value
            elif re.match(r'^\\s*\\d+\\)', line):
                test_name = line.split(')', 1)[1].strip()
                test_status_map[test_name] = TestStatus.FAILED.value
        
        return test_status_map'''

    profile_code = f'''{header_comment}
@dataclass
class {class_name}(JavaScriptProfile):
    owner: str = "{owner}"
    repo: str = "{repo}"
    commit: str = "{commit}"
    test_cmd: str = "{test_cmd}"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim
RUN apt-get update && apt-get install -y git
RUN git clone https://github.com/{self.mirror_name} /testbed
WORKDIR /testbed
RUN npm install
"""

    {log_parser_code}


'''

    return profile_code


def generate_generic_profile_class(owner: str, repo: str, metadata: Dict[str, Any],
                                 parsed_results: Optional[Dict[str, Any]],
                                 dockerfile_content: Optional[str]) -> str:
    """Generate SWE-smith compatible generic profile class code."""
    class_name = create_class_name(owner, repo, metadata.get('commit_hash', ''))
    commit = metadata.get('commit_hash', 'unknown')
    language = metadata.get('language', 'unknown').lower()
    test_commands = metadata.get('test_commands', ['make test'])
    test_cmd = test_commands[0] if test_commands else 'make test'

    parser_name = parsed_results.get('parser', 'unknown') if parsed_results else 'unknown'

    base_image = {
        'go': 'golang:1.21',
        'rust': 'rust:latest',
        'c': 'gcc:latest',
        'cpp': 'gcc:latest',
    }.get(language, 'ubuntu:22.04')

    header_comment = f"""# Auto-generated profile for {owner}/{repo} ({language})
# Commit: {commit}
# Generated: {datetime.now().isoformat()}
# Integration: Copy to swesmith/profiles/{language}.py
"""

    # Generate inline log parser
    if parser_name == 'go_test':
        log_parser_code = '''def log_parser(self, log: str) -> dict[str, str]:
        """Parse Go test output."""
        import re
        test_status_map = {}
        
        for line in log.split("\\n"):
            match = re.match(r'^---\\s+(PASS|FAIL|SKIP):\\s+(.+?)\\s+\\(', line)
            if match:
                status, test_name = match.groups()
                if status == "PASS":
                    test_status_map[test_name] = TestStatus.PASSED.value
                elif status == "FAIL":
                    test_status_map[test_name] = TestStatus.FAILED.value
                elif status == "SKIP":
                    test_status_map[test_name] = TestStatus.SKIPPED.value
        
        return test_status_map'''
    elif parser_name == 'cargo':
        log_parser_code = '''def log_parser(self, log: str) -> dict[str, str]:
        """Parse Cargo test output."""
        import re
        test_status_map = {}
        
        for line in log.split("\\n"):
            match = re.match(r'^test\\s+(.+?)\\s+\\.\\.\\.\\s+(ok|FAILED|ignored)', line)
            if match:
                test_name, status = match.groups()
                if status == "ok":
                    test_status_map[test_name] = TestStatus.PASSED.value
                elif status == "FAILED":
                    test_status_map[test_name] = TestStatus.FAILED.value
                elif status == "ignored":
                    test_status_map[test_name] = TestStatus.SKIPPED.value
        
        return test_status_map'''
    else:
        log_parser_code = '''def log_parser(self, log: str) -> dict[str, str]:
        """Generic parser - customize based on your test framework."""
        test_status_map = {}
        
        for line in log.split("\\n"):
            if "PASS" in line or "passed" in line.lower():
                test_status_map[line.strip()] = TestStatus.PASSED.value
            elif "FAIL" in line or "failed" in line.lower():
                test_status_map[line.strip()] = TestStatus.FAILED.value
        
        return test_status_map'''

    profile_code = f'''{header_comment}
@dataclass
class {class_name}(RepoProfile):
    owner: str = "{owner}"
    repo: str = "{repo}"
    commit: str = "{commit}"
    test_cmd: str = "{test_cmd}"

    @property
    def dockerfile(self):
        return f"""FROM {base_image}
RUN apt-get update && apt-get install -y git
RUN git clone https://github.com/{self.mirror_name} /testbed
WORKDIR /testbed
"""

    {log_parser_code}


'''

    return profile_code


def save_profile_class(result_dir: Path, profile_class_code: str, class_name: str) -> Path:
    """Save the generated profile class to generated_profiles directory."""
    profiles_dir = result_dir / "generated_profiles"
    profiles_dir.mkdir(exist_ok=True)

    profile_file = profiles_dir / "profile_class.py"
    with open(profile_file, 'w', encoding='utf-8') as f:
        f.write(profile_class_code)

    return profile_file


def save_integration_metadata(result_dir: Path, owner: str, repo: str,
                            metadata: Dict[str, Any], parsed_results: Optional[Dict[str, Any]],
                            is_python_repo: bool, class_name: str) -> Path:
    """Save integration metadata for SWE-smith."""
    profiles_dir = result_dir / "generated_profiles"
    profiles_dir.mkdir(exist_ok=True)

    if is_python_repo:
        language = "python"
        base_class = "PythonProfile"
        target_file = "swesmith/profiles/python.py"
    elif metadata.get('language', '').lower() == 'javascript':
        language = "javascript"
        base_class = "JavaScriptProfile"
        target_file = "swesmith/profiles/javascript.py"
    elif metadata.get('language', '').lower() == 'java':
        language = "java"
        base_class = "JavaProfile"
        target_file = "swesmith/profiles/java.py"
    else:
        language = metadata.get('language', 'unknown').lower()
        base_class = "RepoProfile"
        language_files = {
            'go': 'golang.py',
            'rust': 'rust.py',
            'c': 'c.py',
            'cpp': 'cpp.py',
        }
        target_file = f"swesmith/profiles/{language_files.get(language, 'base.py')}"

    integration_metadata = {
        "profile_class_name": class_name,
        "target_file": target_file,
        "base_class": base_class,
        "language": language,
        "repository": f"{owner}/{repo}",
        "commit": metadata.get('commit_hash', 'unknown'),
        "integration_ready": True,
        "generated_timestamp": datetime.now().isoformat(),
        "test_framework": parsed_results.get('parser', 'unknown') if parsed_results else 'unknown',
        "install_commands": metadata.get('install_commands', []),
        "test_commands": metadata.get('test_commands', []),
    }

    metadata_file = profiles_dir / "profile_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(integration_metadata, f, indent=2)

    return metadata_file


def save_integration_instructions(result_dir: Path, owner: str, repo: str,
                                 class_name: str, target_file: str) -> Path:
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
    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write(instructions)

    return instructions_file


def main():
    parser = argparse.ArgumentParser(
        description="Generate SWE-smith profile from existing test results"
    )
    parser.add_argument(
        "result_dir",
        type=Path,
        help="Path to result directory (e.g., agent-result/owner-repo)"
    )
    parser.add_argument(
        "--python-repo",
        action="store_true",
        help="Treat as Python repository"
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
    if 'owner' in metadata and 'repo' in metadata:
        owner = metadata['owner']
        repo = metadata['repo']
    else:
        # Try to parse from directory name (e.g., "kaikramer-keystore-explorer")
        dir_name = result_dir.name
        if '-' in dir_name:
            parts = dir_name.split('-', 1)
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
        profile_code = generate_python_profile_class(owner, repo, metadata, parsed_results, install_script)
    elif metadata.get('language', '').lower() == 'javascript':
        dockerfile_content = load_dockerfile(result_dir)
        profile_code = generate_javascript_profile_class(owner, repo, metadata, parsed_results, dockerfile_content)
    elif metadata.get('language', '').lower() == 'java':
        dockerfile_content = load_dockerfile(result_dir)
        profile_code = generate_java_profile_class(owner, repo, metadata, parsed_results, dockerfile_content)
    else:
        dockerfile_content = load_dockerfile(result_dir)
        profile_code = generate_generic_profile_class(owner, repo, metadata, parsed_results, dockerfile_content)

    # Save profile files
    class_name = create_class_name(owner, repo, metadata.get('commit_hash', ''))

    profile_file = save_profile_class(result_dir, profile_code, class_name)
    print(f"✅ Profile class saved to: {profile_file}")

    metadata_file = save_integration_metadata(
        result_dir, owner, repo, metadata, parsed_results,
        args.python_repo, class_name
    )
    print(f"✅ Integration metadata saved to: {metadata_file}")

    # Load the metadata to get target file
    with open(metadata_file, 'r') as f:
        integration_meta = json.load(f)

    instructions_file = save_integration_instructions(
        result_dir, owner, repo, class_name, integration_meta['target_file']
    )
    print(f"✅ Integration instructions saved to: {instructions_file}")

    print(f"\n🎉 Profile generation completed!")
    print(f"   Class name: {class_name}")
    print(f"   Target file: {integration_meta['target_file']}")
    print(f"\n📋 Generated Profile:")
    print("-" * 60)
    print(profile_code)


if __name__ == "__main__":
    main()

