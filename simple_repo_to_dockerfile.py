#!/usr/bin/env python3
"""
Simplified script to generate Dockerfiles from GitHub repositories using mini-swe-agent.

This version lets the agent handle everything directly - no command tracking or post-processing.
The agent creates the Dockerfile using git clone approach with extended timeouts.
"""

import sys
import os
import shutil
import yaml
import platform
import subprocess
import argparse
import json
import re
import signal
import threading
from pathlib import Path
from dataclasses import asdict, dataclass, field
from typing import Any, Optional, Dict

from minisweagent.agents.default import DefaultAgent
from minisweagent.agents.interactive import InteractiveAgent, InteractiveAgentConfig
from minisweagent.models.litellm_model import LitellmModel
from minisweagent.run.utils.save import save_traj

@dataclass
class ExtendedLocalEnvironmentConfig:
    """Extended LocalEnvironmentConfig with increased timeout for long-running operations."""
    cwd: str = ""
    env: dict[str, str] = field(default_factory=dict)
    timeout: int = 1200  # 20 minutes instead of 5 minutes


class ExtendedLocalEnvironment:
    """Extended LocalEnvironment with longer timeout for complex repository operations."""
    
    def __init__(self, *, config_class: type = ExtendedLocalEnvironmentConfig, **kwargs):
        """This class executes bash commands directly on the local machine with extended timeouts."""
        self.config = config_class(**kwargs)

    def execute(self, command: str, cwd: str = ""):
        """Execute a command in the local environment and return the result as a dict."""
        cwd = cwd or self.config.cwd or os.getcwd()
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            cwd=cwd,
            env=os.environ | self.config.env,
            timeout=self.config.timeout,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return {"output": result.stdout, "returncode": result.returncode}

    def get_template_vars(self) -> dict[str, Any]:
        return asdict(self.config) | platform.uname()._asdict() | os.environ


def extract_test_command_from_dockerfile(dockerfile_path: Path) -> Optional[Dict]:
    """
    Extract test command information from a Dockerfile by parsing RUN commands.
    This is a fallback in case the agent didn't create test_commands.json.
    """
    if not dockerfile_path.exists():
        return None
    
    dockerfile_content = dockerfile_path.read_text()
    
    # Look for RUN commands that likely run tests
    test_patterns = [
        r'RUN\s+(npm\s+test)',
        r'RUN\s+(yarn\s+test)',
        r'RUN\s+(pytest)',
        r'RUN\s+(python\s+-m\s+pytest)',
        r'RUN\s+(cargo\s+test)', 
        r'RUN\s+(go\s+test)',
        r'RUN\s+(mvn\s+test)',
        r'RUN\s+(gradle\s+test)',
        r'RUN\s+(.+test.+)',  # Generic fallback
    ]
    
    for pattern in test_patterns:
        match = re.search(pattern, dockerfile_content, re.IGNORECASE)
        if match:
            test_command = match.group(1)
            
            # Try to determine framework from command - standardized names
            framework = "unknown"
            language = "unknown"
            
            if "npm" in test_command or "yarn" in test_command:
                # Try to detect specific JS framework
                framework = "mocha"  # Default, could be jest
                language = "javascript"
            elif "pytest" in test_command:
                framework = "pytest"
                language = "python"
            elif "cargo test" in test_command:
                framework = "cargo"
                language = "rust"
            elif "go test" in test_command:
                framework = "go_test"
                language = "go"
            elif "mvn" in test_command:
                framework = "maven"
                language = "java"
            elif "gradle" in test_command:
                framework = "maven"  # Use maven parser for gradle too
                language = "java"
            
            return {
                "test_command": test_command,
                "test_framework": framework,
                "language": language
            }
    
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate a Dockerfile or conda installation script for a GitHub repository using mini-swe-agent."
    )
    parser.add_argument(
        "repo_name",
        type=str,
        help="GitHub repository in the form owner/repo (e.g., expressjs/express)",
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default="claude-sonnet-4-20250514",
        help="Model name to use (default: claude-sonnet-4-20250514)",
    )
    parser.add_argument(
        "--python-repo",
        action="store_true",
        help="Treat repository as Python-based (use conda installation script instead of Dockerfile)",
    )
    parser.add_argument(
        "--no-livestream",
        action="store_true",
        help="Enable real-time display of agent-environment interactions",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Instruct the agent to verify the generated Dockerfile by building it. The agent will automatically fix issues and retry if verification fails.",
    )
    parser.add_argument(
        "--verify-testing",
        action="store_true",
        help="Instruct the agent to also run verify_testing.py to parse test output and ensure it works correctly. This implies --verify.",
    )
    parser.add_argument(
        "--max-cost",
        type=float,
        default=2.0,
        help="Maximum cost in dollars for agent execution (default: 2.0)"
    )
    parser.add_argument(
        "--max-time",
        type=int,
        default=1200,
        help="Maximum time in seconds for agent execution (default: 1200 = 20 minutes)"
    )
    args = parser.parse_args()

    repo_name = args.repo_name
    MODEL_NAME = args.model_name

    # Parse repository owner and name
    if '/' not in repo_name:
        print(f"❌ Repository name must be in format 'owner/repo', got: {repo_name}")
        sys.exit(1)

    owner, repo = repo_name.split('/', 1)
    print(f"📦 Repository owner: {owner}")
    print(f"📦 Repository name: {repo}")

    # Determine if this is a Python repository based on command-line flag
    is_python_repo = args.python_repo
    if is_python_repo:
        print(f"🐍 Repository {repo_name} will be treated as Python-based")

    # Set up generation mode
    # Note: --verify-testing implies --verify
    verify_mode = args.verify or args.verify_testing
    
    if is_python_repo:
        print(f"🐍 Generating conda installation script for {repo_name} using model '{MODEL_NAME}'...")
        config_filename = "conda_installation_generation.yaml"
        output_type = "conda installation script"
    else:
        if verify_mode:
            verification_msg = "and verifying" if not args.verify_testing else "verifying and parsing tests for"
            print(f"🚀 Generating {verification_msg} Dockerfile for {repo_name} using model '{MODEL_NAME}'...")
            config_filename = "dockerfile_generation_with_verification.yaml"
            output_type = "Dockerfile (with verification)"
        else:
            print(f"🚀 Generating Dockerfile for {repo_name} using model '{MODEL_NAME}'...")
            config_filename = "dockerfile_generation.yaml"
            output_type = "Dockerfile"

    # Create repo-specific directory in agent-result/ under current working directory
    base_result_dir = Path("agent-result")
    base_result_dir.mkdir(exist_ok=True)

    # Create folder with repo name (replace / with -)
    repo_folder_name = repo_name.replace("/", "-")
    repo_result_dir = base_result_dir / repo_folder_name

    if repo_result_dir.exists():
        shutil.rmtree(repo_result_dir)
    repo_result_dir.mkdir()

    print(f"📁 Results will be saved to: {repo_result_dir}")

    # Setup model
    model = LitellmModel(model_name=MODEL_NAME)

    # Setup environment with extended timeout
    environment = ExtendedLocalEnvironment()

    # Load appropriate config based on repository type
    config_path = Path(__file__).parent / config_filename
    if not config_path.exists():
        print(f"❌ Configuration file {config_filename} not found!")
        sys.exit(1)

    config_data = yaml.safe_load(config_path.read_text())["agent"]
    
    # Override cost_limit with CLI argument
    config_data['cost_limit'] = args.max_cost
    
    # Inject script directory into templates for agent to use
    script_dir = str(Path(__file__).parent.resolve())
    if 'instance_template' in config_data:
        # Add script directory information to the beginning of the prompt
        helper_scripts_section = f"""
## Helper Scripts Available

The following helper scripts are available in this directory:
- Verification script: `{script_dir}/verify_dockerfile.py`
- Testing verification: `{script_dir}/verify_testing.py`

Use the full paths shown above when calling these scripts.

"""
        
        # Add verify-testing specific instructions if flag is set
        if args.verify_testing:
            helper_scripts_section += f"""
## IMPORTANT: Test Output Parsing Required

**IF THE REPOSITORY HAS TESTS:**

After running `verify_dockerfile.py` successfully, you MUST also run `verify_testing.py` to parse the test output:

```bash
python {script_dir}/verify_testing.py agent-result/$repo_folder_name/Dockerfile
```

The `verify_testing.py` script will:
1. Read `test_output.txt` generated by `verify_dockerfile.py`
2. Read `repo_metadata.json` to determine the test framework
3. Parse the test output and generate `parsed_test_status.json`

**Your task is not complete until `verify_testing.py` runs successfully and generates `parsed_test_status.json`.**

**If `verify_testing.py` fails:**

Check `test_output.txt` to see if tests actually ran:
- **Tests ran successfully but parsing failed**: Create/update a parser (see options below)
- **No tests exist**: Mark as no-tests repo (see below)

**Creating/Updating Parsers (if tests ran but couldn't be parsed):**

Choose the appropriate approach:
1. **Add framework parser** (e.g., `cspell.py`): For known frameworks we don't support
2. **Enhance existing parser**: Add patterns to existing parser (only if safe)
3. **Custom parser** (e.g., `graphql_spec_custom.py`): For unique test formats

Requirements:
- Location: `{script_dir}/log_parser/parsers/`
- Signature: `parse_log_<name>(log: str) -> dict[str, str]`
- Register in `verify_testing.py`: Add to PARSERS dict and import
- **Never break existing parsers** - if unsure, make a custom one

Example:
```python
from enum import Enum

class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

def parse_log_<name>(log: str) -> dict[str, str]:
    # Parse logic based on test_output.txt format
    return {{"test_name": TestStatus.PASSED.value}}
```

**Repos with NO tests (rare):**

Only mark as no-tests if ALL true:
- No test scripts in package.json/setup.py/etc.
- No test files or directories
- Running test command shows "no tests found"

Then: Set `test_commands: []` and `test_framework: "none"`, skip `verify_testing.py`

"""
        
        config_data['instance_template'] = helper_scripts_section + config_data['instance_template']
        
        # Also replace any hardcoded references
        config_data['instance_template'] = config_data['instance_template'].replace(
            'python verify_dockerfile.py',
            f'python {script_dir}/verify_dockerfile.py'
        )

    # Create agent based on livestream preference
    if not args.no_livestream:
        print("🔴 Livestream mode enabled - you'll see real-time agent interactions")
        # Configure InteractiveAgent in yolo mode for fully automated execution with live output
        agent = InteractiveAgent(
            model,
            environment,
            config_class=InteractiveAgentConfig,
            mode="yolo",  # Execute without confirmation prompts
            confirm_exit=False,  # Don't ask for confirmation when finishing
            **config_data
        )
    else:
        agent = DefaultAgent(
            model,
            environment,
            **config_data
        )
    
    try:
        # Run the agent - it will handle everything including output creation
        print(f"🤖 Starting agent to analyze {repo_name}...")
        print(f"💰 Cost limit: ${args.max_cost:.2f}")
        print(f"⏱️  Time limit: {args.max_time} seconds ({args.max_time // 60} minutes)")

        # Set up timeout using threading
        timeout_occurred = False
        result_container = {}
        
        def run_agent_with_timeout():
            try:
                result_container['exit_status'], result_container['result'] = agent.run(task=repo_name)
            except Exception as e:
                result_container['error'] = e
        
        agent_thread = threading.Thread(target=run_agent_with_timeout)
        agent_thread.daemon = True
        agent_thread.start()
        agent_thread.join(timeout=args.max_time)
        
        if agent_thread.is_alive():
            # Timeout occurred
            timeout_occurred = True
            print(f"⏰ Agent execution exceeded time limit of {args.max_time} seconds!")
            exit_status = "TIMEOUT"
            result = f"Agent execution timed out after {args.max_time} seconds"
        elif 'error' in result_container:
            raise result_container['error']
        else:
            exit_status = result_container.get('exit_status', 'ERROR')
            result = result_container.get('result', 'Unknown error')

        # Save trajectory
        trajectory_path = repo_result_dir / "trajectory.json"
        print(f"💾 Saving agent trajectory to: {trajectory_path}")
        
        if timeout_occurred:
            # Save partial trajectory with timeout status
            print(f"⚠️  Saving partial trajectory due to timeout")
        
        save_traj(agent, trajectory_path, exit_status=exit_status, result=result)
        
        # Report final costs
        if hasattr(agent.model, 'cost'):
            print(f"💵 Total cost: ${agent.model.cost:.4f}")
        if hasattr(agent.model, 'n_calls'):
            print(f"📞 Total API calls: {agent.model.n_calls}")
        
        if timeout_occurred:
            print(f"❌ Agent timed out - Dockerfile generation incomplete")
            sys.exit(1)

        if is_python_repo:
            # Check for conda installation script
            sh_files = list(repo_result_dir.glob("*.sh"))
            metadata_path = repo_result_dir / "repo_metadata.json"

            if len(sh_files) == 0:
                print("❌ No conda installation script (.sh file) was created. Check the agent output above.")
                print(f"Exit status: {exit_status}, Result: {result}")
            elif len(sh_files) > 1:
                print(f"❌ Multiple .sh files found in {repo_result_dir}: {[f.name for f in sh_files]}")
                print("Expected exactly one installation script. Check the agent output above.")
                print(f"Exit status: {exit_status}, Result: {result}")
            else:
                install_script_path = sh_files[0]
                print(f"✅ Conda installation script successfully created at {install_script_path}")
                print("\n🐍 Generated Conda Installation Script:")
                print("-" * 50)
                print(install_script_path.read_text())
                print("-" * 50)

                # Check for metadata file
                if metadata_path.exists():
                    print(f"✅ Repository metadata file created at {metadata_path}")
                    print("\n📊 Repository Metadata:")
                    print("-" * 50)
                    print(metadata_path.read_text())
                    print("-" * 50)
                else:
                    print("⚠️  Warning: repo_metadata.json was not created by agent")

                print(f"🎉 Conda installation script generation completed successfully!")
                print(f"📋 Script ready for SWE-smith try_install_py workflow:")

                # Try to extract commit hash from metadata for usage instructions
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                            commit_hash = metadata.get('commit_hash', '<COMMIT_HASH>')
                        print(f"   python -m swesmith.build_repo.try_install_py {repo_name} {install_script_path.absolute()} --commit {commit_hash}")
                    except:
                        print(f"   python -m swesmith.build_repo.try_install_py {repo_name} {install_script_path.absolute()} --commit <COMMIT_HASH>")
                        print(f"   (Check repo_metadata.json for the actual commit hash)")
                else:
                    print(f"   python -m swesmith.build_repo.try_install_py {repo_name} {install_script_path.absolute()} --commit <COMMIT_HASH>")
                    print(f"   (Commit hash should be provided - check agent output)")
        else:
            # Check if Dockerfile was created
            dockerfile_path = repo_result_dir / "Dockerfile"
            metadata_path = repo_result_dir / "repo_metadata.json"

            if dockerfile_path.exists():
                print(f"✅ Dockerfile successfully created at {dockerfile_path}")
                print("\n📋 Generated Dockerfile:")
                print("-" * 50)
                print(dockerfile_path.read_text())
                print("-" * 50)

                # Check for metadata file
                if metadata_path.exists():
                    print(f"✅ Repository metadata file created at {metadata_path}")
                    print("\n📊 Repository Metadata:")
                    print("-" * 50)
                    print(metadata_path.read_text())
                    print("-" * 50)
                else:
                    print("⚠️  Warning: repo_metadata.json was not created by agent")
                    # Try to extract from Dockerfile as fallback
                    extracted_commands = extract_test_command_from_dockerfile(dockerfile_path)
                    if extracted_commands:
                        print("📋 Attempting to extract metadata from Dockerfile...")
                        # Convert to new format
                        metadata = {
                            "install_commands": ["unknown"],
                            "test_commands": [extracted_commands.get("test_command", "unknown")],
                            "language": extracted_commands.get("language", "unknown"),
                            "test_framework": extracted_commands.get("test_framework", "unknown"),
                            "commit_hash": "unknown"
                        }
                        with open(metadata_path, 'w') as f:
                            json.dump(metadata, f, indent=2)
                        print(f"✅ Created repo_metadata.json from Dockerfile analysis")
                        print("\n📊 Extracted Repository Metadata:")
                        print("-" * 50)
                        print(json.dumps(metadata, indent=2))
                        print("-" * 50)
                    else:
                        print("❌ Could not extract metadata from Dockerfile")

                print("🎉 Dockerfile generation completed successfully!")
                
                if verify_mode:
                    print("\n💡 Note: The agent was instructed to verify the Dockerfile.")
                    print("   Check the trajectory above to see if verification passed.")
                    
                    if args.verify_testing:
                        print("\n🧪 Note: The agent was also instructed to run verify_testing.py.")
                        parsed_status_path = repo_result_dir / "parsed_test_status.json"
                        if parsed_status_path.exists():
                            print(f"   ✅ Test parsing succeeded! Results saved to: {parsed_status_path}")
                            try:
                                with open(parsed_status_path, 'r') as f:
                                    parsed_data = json.load(f)
                                    parser_used = parsed_data.get('parser', 'unknown')
                                    test_count = len(parsed_data.get('parsed_test_status', {}))
                                    print(f"   📊 Parser used: {parser_used}")
                                    print(f"   📊 Tests parsed: {test_count}")
                            except:
                                pass
                        else:
                            print(f"   ⚠️  Test parsing may have failed - check trajectory for details")
            else:
                print("❌ No Dockerfile was created. Check the agent output above.")
                print(f"Exit status: {exit_status}, Result: {result}")
            
    except Exception as e:
        print(f"❌ Error running agent: {e}")
        
        # Still try to save trajectory if possible
        try:
            trajectory_path = repo_result_dir / "trajectory_error.json"
            save_traj(agent, trajectory_path, exit_status="ERROR", result=str(e))
        except:
            pass
        raise


if __name__ == "__main__":
    main()