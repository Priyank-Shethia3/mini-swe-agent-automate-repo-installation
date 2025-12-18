#!/usr/bin/env python3
"""
End-to-End Repository Profile Generation

This script orchestrates the complete 3-stage pipeline to generate repository profiles:
1. simple_repo_to_dockerfile.py - Generate Dockerfile/conda script + metadata
2. verify_dockerfile.py - Run tests and capture output
3. verify_testing.py - Parse test output and identify parser

Produces a profile class ready for integration into the profile registry.

Usage:
    python generate_profile.py owner/repo --python-repo  # For Python repos
    python generate_profile.py owner/repo               # For non-Python repos
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import textwrap
import io
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
import json


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
                            is_python_repo: bool, class_name: str,
                            pipeline_results: Dict[str, Any]) -> Path:
    """Save integration metadata for SWE-smith."""
    profiles_dir = result_dir / "generated_profiles"
    profiles_dir.mkdir(exist_ok=True)

    # Determine language and target file
    if is_python_repo:
        language = "python"
        base_class = "PythonProfile"
        target_file = "swesmith/profiles/python.py"
    elif metadata.get('language', '').lower() == 'javascript':
        language = "javascript"
        base_class = "JavaScriptProfile"
        target_file = "swesmith/profiles/javascript.py"
    else:
        language = metadata.get('language', 'unknown').lower()
        base_class = "RepoProfile"
        # Map common languages to their profile files
        language_files = {
            'go': 'golang.py',
            'rust': 'rust.py',
            'java': 'java.py',
            'c': 'c.py',
            'cpp': 'cpp.py',
            'csharp': 'csharp.py',
            'php': 'php.py'
        }
        target_file = f"swesmith/profiles/{language_files.get(language, 'base.py')}"

    # Count successful stages
    successful_stages = sum(1 for stage in pipeline_results['stages'].values() if stage['success'])

    integration_metadata = {
        "profile_class_name": class_name,
        "target_file": target_file,
        "base_class": base_class,
        "language": language,
        "repository": f"{owner}/{repo}",
        "commit": metadata.get('commit_hash', 'unknown') if metadata else 'unknown',
        "integration_ready": successful_stages >= 2,  # Stages 1&2 must succeed for profile generation
        "generated_timestamp": datetime.now().isoformat(),
        "pipeline_stages_successful": successful_stages,
        "requires_manual_review": successful_stages < 3 or parsed_results is None,
        "test_framework": parsed_results.get('parser', 'unknown') if parsed_results else 'unknown',
        "install_commands": metadata.get('install_commands', []) if metadata else [],
        "test_commands": metadata.get('test_commands', []) if metadata else [],
        "profile_generation_requirements": "Stages 1&2 must succeed - Stage 1 for analysis, Stage 2 for verification"
    }

    metadata_file = profiles_dir / "profile_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(integration_metadata, f, indent=2)

    return metadata_file


def generate_integration_instructions(result_dir: Path, owner: str, repo: str,
                                    class_name: str, target_file: str) -> Path:
    """Generate integration instructions for manual copying to SWE-smith."""
    profiles_dir = result_dir / "generated_profiles"
    profiles_dir.mkdir(exist_ok=True)

    instructions = f"""# Integration Instructions

## Generated Profile: {class_name}
Repository: {owner}/{repo}

## Steps to integrate into SWE-smith:

1. **Copy the profile class:**
   ```bash
   # Copy the generated profile class
   cat {result_dir}/generated_profiles/profile_class.py >> /path/to/SWE-smith/{target_file}
   ```

2. **Verify the registration loop:**
   Ensure the target file has a registration loop at the end:
   ```python
   # Register all profiles with the global registry
   for name, obj in list(globals().items()):
       if (
           isinstance(obj, type)
           and issubclass(obj, BaseProfileClass)
           and obj.__name__ != "BaseProfileClass"
       ):
           registry.register_profile(obj)
   ```

3. **Test the integration:**
   ```python
   from swesmith.profiles import registry
   profile = registry.get("{owner}/{repo}")
   print(f"Profile loaded: {{profile.__class__.__name__}}")
   ```

4. **Commit the changes:**
   ```bash
   cd /path/to/SWE-smith
   git add {target_file}
   git commit -m "Add auto-generated profile for {owner}/{repo}"
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


class OutputCapture:
    """Captures stdout/stderr while still displaying to console."""

    def __init__(self):
        self.captured_output = []
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def write(self, text):
        """Write to both console and capture buffer."""
        self.captured_output.append(text)
        self.original_stdout.write(text)

    def flush(self):
        """Flush console output."""
        self.original_stdout.flush()

    def get_captured_output(self) -> str:
        """Get all captured output as a single string."""
        return ''.join(self.captured_output)


def run_pipeline_command(cmd: list, description: str, timeout: int = 1800, livestream: bool = True) -> Tuple[int, str]:
    """Run a pipeline command with timeout and optionally livestream output."""
    print(f"🚀 {description}...")
    print(f"   Command: {' '.join(cmd)}")
    print("   " + "-" * 50)

    try:
        if livestream:
            # Run with real-time output streaming
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            output_lines = []
            print("📄 Live Output:")

            try:
                # Stream output line by line
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        line = line.rstrip('\n')
                        output_lines.append(line)
                        print(f"   {line}")

                # Wait for process to complete with timeout
                try:
                    returncode = process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    timeout_msg = f"Command timed out after {timeout} seconds"
                    print(f"⏰ {timeout_msg}")
                    print("   " + "-" * 50)
                    return -1, timeout_msg

                full_output = '\n'.join(output_lines)

            except Exception as e:
                process.kill()
                process.wait()
                raise e

        else:
            # Run with captured output (original behavior for stages 2&3)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            full_output = result.stdout + result.stderr
            returncode = result.returncode

            if full_output.strip():
                print("📄 Command Output:")
                # Print output with indentation for readability
                for line in full_output.strip().split('\n'):
                    print(f"   {line}")
            else:
                print("   (No output)")

        print("   " + "-" * 50)

        if returncode == 0:
            print(f"✅ Command completed successfully (exit code 0)")
        else:
            print(f"❌ Command failed (exit code {returncode})")

        return returncode, full_output

    except subprocess.TimeoutExpired:
        timeout_msg = f"Command timed out after {timeout} seconds"
        print(f"⏰ {timeout_msg}")
        print("   " + "-" * 50)
        return -1, timeout_msg
    except Exception as e:
        error_msg = f"Error running command: {e}"
        print(f"💥 {error_msg}")
        print("   " + "-" * 50)
        return -1, error_msg


def validate_repo_name(repo_name: str) -> Tuple[str, str]:
    """Validate and parse repository name."""
    if '/' not in repo_name:
        raise ValueError("Repository name must be in format 'owner/repo'")

    parts = repo_name.split('/')
    if len(parts) != 2:
        raise ValueError("Repository name must be in format 'owner/repo'")

    owner, repo = parts
    if not owner or not repo:
        raise ValueError("Owner and repo names cannot be empty")

    return owner, repo


def create_class_name(owner: str, repo: str, commit: str) -> str:
    """Generate a valid Python class name following SWE-smith conventions."""
    # Clean repo name: remove non-alphanumeric chars and capitalize
    # Handle common patterns: "pytest-practice" -> "PytestPractice"
    clean_repo = re.sub(r'[^a-zA-Z0-9]', '', repo)

    # Capitalize first letter and keep the rest as-is (to preserve camelCase if present)
    if clean_repo:
        clean_repo = clean_repo[0].upper() + clean_repo[1:]

    # Use first 8 characters of commit hash
    commit_suffix = commit[:8] if commit and len(commit) >= 8 else "00000000"

    return f"{clean_repo}{commit_suffix}"


def load_metadata(result_dir: Path) -> Optional[Dict[str, Any]]:
    """Load repo_metadata.json from result directory."""
    metadata_path = result_dir / "repo_metadata.json"

    if not metadata_path.exists():
        print(f"⚠️  repo_metadata.json not found at {metadata_path}")
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
        print(f"⚠️  parsed_test_status.json not found at {parsed_path}")
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
    # Find installation script
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


def get_parser_import_code(parser_name: str) -> str:
    """Generate the import statement for the parser."""
    parser_imports = {
        'jest': 'from log_parser.parsers.jest import parse_log_jest',
        'mocha': 'from log_parser.parsers.mocha import parse_log_mocha',
        'pytest': 'from log_parser.parsers.pytest import parse_log_pytest',
        'go_test': 'from log_parser.parsers.go_test import parse_log_go_test',
        'cargo': 'from log_parser.parsers.cargo import parse_log_cargo',
        'maven': 'from log_parser.parsers.maven import parse_log_maven',
    }
    return parser_imports.get(parser_name, f'# Unknown parser: {parser_name}')


def get_parser_function_call(parser_name: str) -> str:
    """Generate the parser function call."""
    parser_functions = {
        'jest': 'parse_log_jest(log)',
        'mocha': 'parse_log_mocha(log)',
        'pytest': 'parse_log_pytest(log)',
        'go_test': 'parse_log_go_test(log)',
        'cargo': 'parse_log_cargo(log)',
        'maven': 'parse_log_maven(log)',
    }
    return parser_functions.get(parser_name, 'return {}  # Unknown parser')


def _template_dockerfile(dockerfile_content: str) -> str:
    """Convert agent's Dockerfile to use template variables."""
    dockerfile = dockerfile_content
    
    # Replace actual owner/repo with template variables
    dockerfile = re.sub(r'https://github\.com/[^/]+/[^/\s]+\.git',
                       'https://github.com/{self.owner}/{self.repo}.git',
                       dockerfile)
    dockerfile = re.sub(r'git clone https://github\.com/[^/]+/[^\s]+',
                       'git clone https://github.com/{self.owner}/{self.repo}.git',
                       dockerfile)
    
    # Replace WORKDIR /app with WORKDIR /testbed (SWE-smith convention)
    dockerfile = re.sub(r'WORKDIR /app\b', 'WORKDIR /testbed', dockerfile)
    
    # Replace paths like /app/ with /testbed/
    dockerfile = dockerfile.replace('/app/', '/testbed/')
    
    # Replace paths like RUN git clone ... /app
    dockerfile = re.sub(r'(git clone [^\s]+ )/app\b', r'\1/testbed', dockerfile)
    
    # CRITICAL FIX for Modal compatibility:
    # Modal's legacy image builder skips WORKDIR, so we need to ensure
    # git clone CREATES /testbed explicitly, then WORKDIR sets it.
    # Change: "RUN git clone ... ." to "RUN git clone ... /testbed"
    # This must happen AFTER git is installed but BEFORE other commands
    
    # Pattern: Find "git clone ... ." and replace . with /testbed
    dockerfile = re.sub(
        r'(RUN git clone [^\n]+) \.',
        r'\1 /testbed',
        dockerfile
    )
    
    # CRITICAL FIX 2: Remove WORKDIR /testbed if it appears BEFORE git clone
    # because it creates an empty directory that git clone can't use
    # Pattern: Remove "WORKDIR /testbed" lines that appear before "RUN git clone"
    lines = dockerfile.split('\n')
    result_lines = []
    skip_workdir = False
    
    for i, line in enumerate(lines):
        # Check if this is a WORKDIR /testbed line
        if re.match(r'^\s*WORKDIR /testbed\s*$', line):
            # Look ahead to see if git clone comes after
            has_git_clone_after = False
            for j in range(i + 1, len(lines)):
                if 'git clone' in lines[j] and '/testbed' in lines[j]:
                    has_git_clone_after = True
                    break
                # Stop looking if we hit another significant command
                if lines[j].strip().startswith('RUN') and 'git clone' not in lines[j]:
                    break
            
            if has_git_clone_after:
                # Skip this WORKDIR line, we'll add it after git clone
                continue
        
        result_lines.append(line)
    
    # Now add WORKDIR /testbed after the git clone line if it's not already there
    final_lines = []
    for i, line in enumerate(result_lines):
        final_lines.append(line)
        # If this is the git clone line, add WORKDIR after it
        if 'git clone' in line and '/testbed' in line:
            # Check if next non-empty line is already WORKDIR
            next_is_workdir = False
            for j in range(i + 1, len(result_lines)):
                if result_lines[j].strip():
                    if 'WORKDIR /testbed' in result_lines[j]:
                        next_is_workdir = True
                    break
            if not next_is_workdir:
                final_lines.append('WORKDIR /testbed')
    
    return '\n'.join(final_lines)


def generate_python_profile_class(owner: str, repo: str, metadata: Dict[str, Any],
                                 parsed_results: Optional[Dict[str, Any]],
                                 install_script: Optional[str]) -> str:
    """Generate SWE-smith compatible Python profile class code."""
    class_name = create_class_name(owner, repo, metadata.get('commit_hash', ''))
    commit = metadata.get('commit_hash', 'unknown')
    install_commands = metadata.get('install_commands', ['pip install -e .'])

    # Format install commands for Python list syntax
    install_cmds_str = ',\n            '.join([f'"{cmd}"' for cmd in install_commands])

    # Header comment with metadata
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


def generate_javascript_profile_class(owner: str, repo: str, metadata: Dict[str, Any],
                                    parsed_results: Optional[Dict[str, Any]],
                                    dockerfile_content: Optional[str]) -> str:
    """Generate SWE-smith compatible JavaScript profile class code."""
    if not dockerfile_content:
        raise ValueError(f"No Dockerfile found for {owner}/{repo}. Agent must generate Dockerfile first.")
    
    class_name = create_class_name(owner, repo, metadata.get('commit_hash', ''))
    commit = metadata.get('commit_hash', 'unknown')
    test_commands = metadata.get('test_commands', ['npm test'])
    test_cmd = test_commands[0] if test_commands else 'npm test'

    parser_name = parsed_results.get('parser', 'mocha') if parsed_results else 'mocha'
    dockerfile_template = _template_dockerfile(dockerfile_content)

    header_comment = f"""# Auto-generated profile for {owner}/{repo}
# Commit: {commit}
# Generated: {datetime.now().isoformat()}
# Integration: Copy to swesmith/profiles/javascript.py
"""

    # Generate log parser based on detected framework
    if parser_name == 'jest':
        log_parser_code = '''def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_jest(log)'''
    elif parser_name == 'mocha':
        log_parser_code = '''def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)'''
    elif parser_name == 'vitest':
        log_parser_code = '''def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_vitest(log)'''
    else:
        log_parser_code = '''def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)  # Default fallback'''

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


def generate_generic_profile_class(owner: str, repo: str, metadata: Dict[str, Any],
                                 parsed_results: Optional[Dict[str, Any]],
                                 dockerfile_content: Optional[str]) -> str:
    """Generate SWE-smith compatible generic profile class code for non-JS/non-Python repos."""
    if not dockerfile_content:
        raise ValueError(f"No Dockerfile found for {owner}/{repo}. Agent must generate Dockerfile first.")
    
    class_name = create_class_name(owner, repo, metadata.get('commit_hash', ''))
    commit = metadata.get('commit_hash', 'unknown')
    language = metadata.get('language', 'unknown').lower()
    test_commands = metadata.get('test_commands', ['make test'])
    test_cmd = test_commands[0] if test_commands else 'make test'

    # Detect Maven from test commands
    is_maven = any('mvn' in cmd for cmd in test_commands)
    
    # Use Maven parser if Maven detected, otherwise use parsed_results or default
    if is_maven:
        parser_name = 'maven'
    else:
        parser_name = parsed_results.get('parser', 'unknown') if parsed_results else 'unknown'
    
    dockerfile_template = _template_dockerfile(dockerfile_content)
    
    # Determine the appropriate base class based on language
    base_class_mapping = {
        'java': 'JavaProfile',
        'go': 'GolangProfile',
        'golang': 'GolangProfile',
        'rust': 'RustProfile',
        'c': 'CProfile',
        'cpp': 'CppProfile',
        'c++': 'CppProfile',
        'csharp': 'CSharpProfile',
        'c#': 'CSharpProfile',
        'php': 'PhpProfile',
    }
    base_class = base_class_mapping.get(language, 'RepoProfile')

    header_comment = f"""# Auto-generated profile for {owner}/{repo} ({language})
# Commit: {commit}
# Generated: {datetime.now().isoformat()}
# Integration: Copy to swesmith/profiles/{language}.py
"""

    # Generate appropriate log parser based on detected framework
    if parser_name == 'go_test':
        log_parser_code = '''def log_parser(self, log: str) -> dict[str, str]:
        """Parse Go test output."""
        # Note: parse_log_go_test should be imported at top of file
        if parse_log_go_test is not None:
            return parse_log_go_test(log)
        return {}'''
    elif parser_name == 'cargo':
        log_parser_code = '''def log_parser(self, log: str) -> dict[str, str]:
        """Parse Cargo test output."""
        # Note: parse_log_cargo should be imported at top of file
        if parse_log_cargo is not None:
            return parse_log_cargo(log)
        return {}'''
    elif parser_name == 'maven':
        log_parser_code = '''def log_parser(self, log: str) -> dict[str, str]:
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
        log_parser_code = '''def log_parser(self, log: str) -> dict[str, str]:
        # Generic parser - customize based on your test framework
        test_status_map = {}
        for line in log.split("\\n"):
            if "PASS" in line:
                test_status_map[line.strip()] = "PASSED"
            elif "FAIL" in line:
                test_status_map[line.strip()] = "FAILED"
        return test_status_map'''

    profile_code = f'''{header_comment}
@dataclass
class {class_name}({base_class}):
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


def run_pipeline(repo_name: str, is_python_repo: bool, model_name: str = "claude-sonnet-4-20250514",
                 livestream: bool = False, verify: bool = False, verify_testing: bool = False, 
                 max_cost: float = 2.0, max_time: int = 1200) -> Dict[str, Any]:
    """Run the complete 3-stage pipeline with full output capture."""
    owner, repo = validate_repo_name(repo_name)
    result_dir = Path("agent-result") / f"{owner}-{repo}"

    # Get the directory where this script is located
    script_dir = Path(__file__).parent.resolve()

    pipeline_results = {
        'owner': owner,
        'repo': repo,
        'result_dir': result_dir,
        'stages': {
            'stage1': {'success': False, 'output': ''},
            'stage2': {'success': False, 'output': ''},
            'stage3': {'success': False, 'output': ''},
        }
    }

    # Set up output capture
    output_capture = OutputCapture()
    sys.stdout = output_capture
    sys.stderr = output_capture

    try:
        print(f"🎯 Starting end-to-end pipeline for {repo_name}")
        print(f"📂 Results will be saved to: {result_dir}")
        print(f"🏷️  Repository type: {'Python' if is_python_repo else 'Non-Python'}")
        print("=" * 60)

        # Stage 1: Generate Dockerfile/conda script + metadata
        stage1_cmd = [
            "python", str(script_dir / "simple_repo_to_dockerfile.py"), repo_name,
            "--model_name", model_name,
            "--max-cost", str(max_cost),
            "--max-time", str(max_time)
        ]
        if is_python_repo:
            stage1_cmd.append("--python-repo")
        if verify or verify_testing:
            stage1_cmd.append("--verify")
        if verify_testing:
            stage1_cmd.append("--verify-testing")

        exit_code, output = run_pipeline_command(
            stage1_cmd,
            "Stage 1: Generating Dockerfile/conda script + metadata",
            livestream=livestream
        )
        pipeline_results['stages']['stage1'] = {'success': exit_code == 0, 'output': output}

        if exit_code != 0:
            print(f"❌ Stage 1 failed with exit code {exit_code}")
            print(f"Output: {output}")
            return pipeline_results

        print(f"✅ Stage 1 completed successfully")

        # Stage 2: Verify and run tests
        stage2_cmd = ["python", str(script_dir / "verify_dockerfile.py"), str(result_dir)]
        if is_python_repo:
            stage2_cmd.append("--python-repo")
        stage2_cmd.append("--cleanup")

        exit_code, output = run_pipeline_command(
            stage2_cmd,
            "Stage 2: Running verification and tests",
            livestream=livestream
        )
        pipeline_results['stages']['stage2'] = {'success': exit_code == 0, 'output': output}

        if exit_code != 0:
            print(f"❌ Stage 2 failed with exit code {exit_code}")
            print(f"Output: {output}")
            print(f"🛑 Pipeline stopped - Stage 2 failure prevents Stage 3 execution")
            return pipeline_results
        else:
            print(f"✅ Stage 2 completed successfully")

        # Stage 3: Parse test output
        stage3_cmd = ["python", str(script_dir / "verify_testing.py"), str(result_dir)]
        if is_python_repo:
            stage3_cmd.append("--python-repo")

        exit_code, output = run_pipeline_command(
            stage3_cmd,
            "Stage 3: Parsing test output",
            livestream=livestream
        )
        pipeline_results['stages']['stage3'] = {'success': exit_code == 0, 'output': output}

        if exit_code != 0:
            print(f"❌ Stage 3 failed with exit code {exit_code}")
            print(f"Output: {output}")
            print(f"⚠️  Stage 3 parsing failed - profile generation may be limited")
        else:
            print(f"✅ Stage 3 completed successfully")

        return pipeline_results

    finally:
        # Restore original stdout/stderr
        sys.stdout = output_capture.original_stdout
        sys.stderr = output_capture.original_stderr

        # Save the full pipeline log to result directory
        if result_dir.exists():
            pipeline_log_path = result_dir / "pipeline_full_log.txt"
            try:
                with open(pipeline_log_path, 'w', encoding='utf-8') as f:
                    # Add header with timestamp and pipeline info
                    f.write(f"# Pipeline Full Log\n")
                    f.write(f"# Repository: {repo_name}\n")
                    f.write(f"# Python Repo: {is_python_repo}\n")
                    f.write(f"# Model: {model_name}\n")
                    f.write(f"# Timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"# " + "=" * 60 + "\n\n")
                    f.write(output_capture.get_captured_output())
                print(f"📋 Full pipeline log saved to: {pipeline_log_path}")
            except Exception as e:
                print(f"⚠️  Warning: Could not save pipeline log: {e}")
        else:
            print("⚠️  Warning: Result directory does not exist, cannot save pipeline log")


def generate_profile_from_pipeline(pipeline_results: Dict[str, Any], is_python_repo: bool) -> Optional[str]:
    """Generate and save SWE-smith compatible profile class from pipeline results."""
    owner = pipeline_results['owner']
    repo = pipeline_results['repo']
    result_dir = pipeline_results['result_dir']

    print(f"\n📝 Checking pipeline status for {owner}/{repo}...")

    # Check if essential stages completed successfully
    stage1_success = pipeline_results['stages']['stage1']['success']
    stage2_success = pipeline_results['stages']['stage2']['success']
    stage3_success = pipeline_results['stages']['stage3']['success']

    if not stage1_success:
        print("❌ Stage 1 failed - cannot generate profile without repository analysis")
        print("   Stage 1 is required for repo_metadata.json and deployment artifacts")
        return None

    if not stage2_success:
        print("❌ Stage 2 failed - cannot generate profile without installation/testing verification")
        print("   Stage 2 is required to ensure the profile works correctly")
        return None

    if not stage3_success:
        print("❌ Stage 3 failed - cannot generate profile without test output parsing")
        print("   Stage 3 is required to ensure the profile works correctly")
        return None

    print("✅ Essential pipeline stages completed successfully")
    print(f"📝 Generating SWE-smith compatible profile for {owner}/{repo}...")

    # Load data from pipeline outputs
    metadata = load_metadata(result_dir)
    parsed_results = load_parsed_results(result_dir)

    if not metadata:
        print("❌ Cannot generate profile without repo_metadata.json")
        return None

    print(f"✅ Loaded metadata: {metadata.get('language', 'unknown')} repository")

    if parsed_results:
        print(f"✅ Loaded parsing results: {parsed_results.get('parser', 'unknown')} parser identified")
    else:
        print("⚠️  No parsing results available - using defaults")

    # Generate profile based on repository type
    if is_python_repo:
        install_script = load_install_script(result_dir)
        if install_script:
            print("✅ Loaded conda installation script")
        profile_code = generate_python_profile_class(owner, repo, metadata, parsed_results, install_script)

    elif metadata.get('language', '').lower() == 'javascript':
        dockerfile_content = load_dockerfile(result_dir)
        if dockerfile_content:
            print("✅ Loaded Dockerfile content")
        profile_code = generate_javascript_profile_class(owner, repo, metadata, parsed_results, dockerfile_content)

    else:
        # Generic profile for other languages
        dockerfile_content = load_dockerfile(result_dir)
        if dockerfile_content:
            print("✅ Loaded Dockerfile content")
        profile_code = generate_generic_profile_class(owner, repo, metadata, parsed_results, dockerfile_content)

    # Save profile in SWE-smith compatible format
    class_name = create_class_name(owner, repo, metadata.get('commit_hash', ''))

    try:
        # Save the profile class
        profile_file = save_profile_class(result_dir, profile_code, class_name)
        print(f"✅ Profile class saved to: {profile_file}")

        # Save integration metadata
        metadata_file = save_integration_metadata(
            result_dir, owner, repo, metadata, parsed_results,
            is_python_repo, class_name, pipeline_results
        )
        print(f"✅ Integration metadata saved to: {metadata_file}")

        # Load the metadata to get target file for instructions
        with open(metadata_file, 'r') as f:
            integration_meta = json.load(f)

        # Generate integration instructions
        # instructions_file = generate_integration_instructions(
        #     result_dir, owner, repo, class_name, integration_meta['target_file']
        # )
        # print(f"✅ Integration instructions saved to: {instructions_file}")

        print(f"\n🎯 Profile ready for SWE-smith integration!")
        print(f"   Class name: {class_name}")
        print(f"   Target file: {integration_meta['target_file']}")
        print(f"   Integration ready: {integration_meta['integration_ready']}")

    except Exception as e:
        print(f"⚠️  Warning: Could not save profile files: {e}")

    return profile_code


def main():
    """Main CLI interface for end-to-end profile generation."""
    parser = argparse.ArgumentParser(
        description="Generate repository profiles using the complete mini-swe-agent pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          python generate_profile.py fastapi/typer --python-repo
          python generate_profile.py expressjs/express
          python generate_profile.py rust-lang/cargo --model gpt-4o-mini
        """)
    )

    parser.add_argument(
        "repo_name",
        help="GitHub repository in format 'owner/repo' (e.g., fastapi/typer)"
    )
    parser.add_argument(
        "--python-repo",
        action="store_true",
        help="Treat as Python repository (generates conda-based profile)"
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Model name to use for pipeline (default: claude-sonnet-4-20250514)"
    )
    parser.add_argument(
        "--output",
        help="Output file for generated profile (default: print to stdout)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output profile data as JSON instead of Python class"
    )
    parser.add_argument(
        "--livestream",
        action="store_true",
        help="Enable livestream output for pipeline stages (default: False)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Instruct the agent to verify the generated Dockerfile by building it (passed to simple_repo_to_dockerfile.py)"
    )
    parser.add_argument(
        "--verify-testing",
        action="store_true",
        help="Instruct the agent to also run verify_testing.py to parse test output (implies --verify, passed to simple_repo_to_dockerfile.py)"
    )
    parser.add_argument(
        "--max-cost",
        type=float,
        default=2.0,
        help="Maximum cost in dollars for agent execution in Stage 1 (default: 2.0)"
    )
    parser.add_argument(
        "--max-time",
        type=int,
        default=1200,
        help="Maximum time in seconds for agent execution in Stage 1 (default: 1200 = 20 minutes)"
    )

    args = parser.parse_args()

    try:
        # Validate repository name
        owner, repo = validate_repo_name(args.repo_name)

        # Run the complete pipeline
        pipeline_results = run_pipeline(args.repo_name, args.python_repo, args.model, args.livestream, args.verify,
                                       args.verify_testing, args.max_cost, args.max_time)

        # Generate profile
        profile_code = generate_profile_from_pipeline(pipeline_results, args.python_repo)

        if not profile_code:
            print("\n❌ Failed to generate profile")
            sys.exit(1)

        # Output results
        print("\n" + "=" * 60)
        print("🎉 Profile generation completed!")
        print("=" * 60)

        if args.json:
            # Convert to JSON format (simplified)
            metadata = load_metadata(pipeline_results['result_dir'])
            parsed_results = load_parsed_results(pipeline_results['result_dir'])

            profile_json = {
                'owner': owner,
                'repo': repo,
                'commit': metadata.get('commit_hash', 'unknown') if metadata else 'unknown',
                'language': metadata.get('language', 'unknown') if metadata else 'unknown',
                'is_python_repo': args.python_repo,
                'install_commands': metadata.get('install_commands', []) if metadata else [],
                'test_commands': metadata.get('test_commands', []) if metadata else [],
                'parser': parsed_results.get('parser', 'unknown') if parsed_results else 'unknown',
                'pipeline_success': all(stage['success'] for stage in pipeline_results['stages'].values())
            }

            output_content = json.dumps(profile_json, indent=2)
        else:
            output_content = profile_code

        # Write to file or stdout
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                f.write(output_content)
            print(f"📝 Profile written to: {output_path}")
        else:
            print("\n📋 Generated Profile:")
            print("-" * 40)
            print(output_content)

        # Summary
        successful_stages = sum(1 for stage in pipeline_results['stages'].values() if stage['success'])
        executed_stages = sum(1 for stage in pipeline_results['stages'].values() if stage['output'])

        print(f"\n📊 Pipeline Summary:")
        print(f"   Successful stages: {successful_stages}/{executed_stages}")
        print(f"   Result directory: {pipeline_results['result_dir']}")

        if executed_stages < 3:
            print(f"🛑 Pipeline terminated early after stage {executed_stages}")

        if successful_stages == 3:
            print("✅ All pipeline stages completed successfully!")
            sys.exit(0)
        else:
            if executed_stages < 3:
                print(f"❌ Pipeline failed at stage {executed_stages} - subsequent stages not executed")
            else:
                print(f"⚠️  {3-successful_stages} stage(s) had issues - profile may be incomplete")
            sys.exit(1)

    except ValueError as e:
        print(f"❌ Invalid repository name: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Profile generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()