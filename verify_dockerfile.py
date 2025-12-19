#!/usr/bin/env python3
"""
Dockerfile Verification Tool

Tests generated Dockerfiles to ensure they build and run correctly.
This is a companion tool to repo_to_dockerfile.py
"""

import sys
import subprocess
import argparse
import json
import re
import os
import shutil
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import threading
import time

def run_command(cmd: list, cwd: Optional[Path] = None, timeout: int = 300) -> Tuple[int, str]:
    """Run a command and return exit code and output."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return -1, f"Command timed out after {timeout} seconds"
    except Exception as e:
        return -1, f"Error running command: {e}"

def run_command_with_progress(cmd: list, cwd: Optional[Path] = None, timeout: int = 300) -> Tuple[int, str]:
    """Run a command with real-time output streaming."""
    try:
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        output_lines = []

        # Read output line by line and print in real-time
        while True:
            line = process.stdout.readline()
            if not line:
                break
            print(line.rstrip())  # Print without extra newline
            output_lines.append(line)
            sys.stdout.flush()  # Ensure immediate output

        # Wait for process to complete
        process.wait(timeout=timeout)

        return process.returncode, ''.join(output_lines)

    except subprocess.TimeoutExpired:
        process.kill()
        return -1, f"Command timed out after {timeout} seconds"
    except Exception as e:
        return -1, f"Error running command: {e}"

def parse_test_results(output: str, test_framework: str = None) -> Dict[str, Any]:
    """Parse test output to determine actual test results."""

    # Initialize result dictionary
    result = {
        'tests_run': False,
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'errors': 0,
        'total': 0,
        'success': False,
        'framework_detected': test_framework
    }

    # Try to detect test framework if not provided
    if not test_framework:
        if 'mocha' in output.lower() or '✔' in output or '✓' in output:
            test_framework = 'mocha'
        elif 'jest' in output.lower() or 'PASS' in output or 'FAIL' in output:
            test_framework = 'jest'
        elif 'pytest' in output.lower() or 'passed' in output.lower():
            test_framework = 'pytest'
        elif 'npm test' in output.lower():
            test_framework = 'npm'

    # Parse based on framework
    if test_framework in ['mocha', 'npm']:
        # Look for mocha-style output: "X passing"
        passing_match = re.search(r'(\d+)\s+passing', output)
        failing_match = re.search(r'(\d+)\s+failing', output)
        pending_match = re.search(r'(\d+)\s+pending', output)

        if passing_match:
            result['tests_run'] = True
            result['passed'] = int(passing_match.group(1))

        if failing_match:
            result['failed'] = int(failing_match.group(1))

        if pending_match:
            result['skipped'] = int(pending_match.group(1))

        # Count checkmarks as alternative
        if not result['tests_run']:
            checkmarks = len(re.findall(r'[✔✓]', output))
            crosses = len(re.findall(r'[✗✖×]', output))
            if checkmarks > 0 or crosses > 0:
                result['tests_run'] = True
                result['passed'] = checkmarks
                result['failed'] = crosses

    elif test_framework == 'jest':
        # Look for jest-style output - handle flexible format with commas
        # Format: "Tests:       257 failed, 2 skipped, 3354 passed, 3613 total"
        pass_match = re.search(r'(\d+)\s+passed', output)
        fail_match = re.search(r'(\d+)\s+failed', output)
        skip_match = re.search(r'(\d+)\s+skipped', output)
        total_match = re.search(r'(\d+)\s+total', output)

        if pass_match or fail_match or total_match:
            result['tests_run'] = True
            
        if pass_match:
            result['passed'] = int(pass_match.group(1))

        if fail_match:
            result['failed'] = int(fail_match.group(1))
        
        if skip_match:
            result['skipped'] = int(skip_match.group(1))

        if total_match:
            result['total'] = int(total_match.group(1))

    elif test_framework == 'pytest':
        # Look for pytest-style output
        summary_match = re.search(r'(\d+)\s+passed', output.lower())
        failed_match = re.search(r'(\d+)\s+failed', output.lower())
        error_match = re.search(r'(\d+)\s+error', output.lower())
        skipped_match = re.search(r'(\d+)\s+skipped', output.lower())

        if summary_match:
            result['tests_run'] = True
            result['passed'] = int(summary_match.group(1))

        if failed_match:
            result['failed'] = int(failed_match.group(1))

        if error_match:
            result['errors'] = int(error_match.group(1))

        if skipped_match:
            result['skipped'] = int(skipped_match.group(1))

    # Calculate total and success
    result['total'] = result['passed'] + result['failed'] + result['skipped'] + result['errors']
    result['success'] = result['tests_run'] and result['failed'] == 0 and result['errors'] == 0

    return result

def cleanup_conda_env(env_name: str = "testbed") -> None:
    """Clean up conda environment if it exists."""
    try:
        # Check if environment exists
        env_list = subprocess.run(
            "conda env list",
            check=True,
            shell=True,
            text=True,
            capture_output=True
        ).stdout

        if env_name in env_list:
            print(f"🧹 Removing conda environment '{env_name}'...")
            subprocess.run(
                f"conda env remove -n {env_name} -y",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"✅ Conda environment removed")
    except Exception as e:
        print(f"⚠️  Could not remove conda environment: {e}")

def verify_python_installation_swe_smith_style(repo_dir: Path, show_progress: bool = True, failure_threshold: float = 0.09) -> Tuple[bool, bool]:
    """
    Verify Python installation using SWE-smith inspired workflow.
    Returns (installation_success, testing_success) tuple.
    """

    print(f"🔍 Verifying Python installation in: {repo_dir}")

    # Load metadata
    metadata_path = repo_dir / "repo_metadata.json"
    if not metadata_path.exists():
        print(f"❌ No repo_metadata.json found at {metadata_path}")
        return False, False

    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        # Get owner/repo from metadata
        owner = metadata.get('owner')
        repo = metadata.get('repo')

        if not owner or not repo:
            print("❌ Owner/repo fields missing from metadata")
            return False, False
        commit_hash = metadata.get('commit_hash', 'HEAD')
        test_commands = metadata.get('test_commands', [])
        test_framework = metadata.get('test_framework', 'pytest')

        print(f"📦 Repository: {owner}/{repo}")
        print(f"📌 Commit: {commit_hash}")
        print(f"🧪 Test framework: {test_framework}")

    except Exception as e:
        print(f"❌ Error reading metadata: {e}")
        return False, False

    # Find installation script
    install_scripts = list(repo_dir.glob("*_install.sh"))
    if not install_scripts:
        print(f"❌ No installation script (*_install.sh) found")
        return False, False

    install_script = install_scripts[0]
    print(f"📜 Found installation script: {install_script.name}")

    # Step 1: Clone repository
    clone_dir = repo_dir / "cloned_repo"
    if clone_dir.exists():
        print(f"🧹 Removing existing cloned repository...")
        shutil.rmtree(clone_dir)

    print(f"\n1️⃣  Cloning repository {owner}/{repo}...")
    clone_cmd = [
        "git", "clone",
        f"https://github.com/{owner}/{repo}.git",
        str(clone_dir)
    ]

    exit_code, output = run_command(clone_cmd, timeout=300)
    if exit_code != 0:
        print(f"❌ Failed to clone repository: {output}")
        return False, False

    print(f"✅ Repository cloned successfully")

    # Step 2: Checkout specific commit
    if commit_hash and commit_hash != 'HEAD':
        print(f"📌 Checking out commit {commit_hash}...")
        checkout_cmd = ["git", "checkout", commit_hash]
        exit_code, output = run_command(checkout_cmd, cwd=clone_dir, timeout=60)

        if exit_code != 0:
            print(f"⚠️  Could not checkout commit {commit_hash}, using HEAD")

    # Step 3: Make installation script executable
    print("\n2️⃣  Setting up conda installation...")
    chmod_cmd = ["chmod", "+x", str(install_script)]
    run_command(chmod_cmd, timeout=10)

    # Step 4: Run installation in the cloned repository
    print("\n3️⃣  Running conda installation script in cloned repository...")

    # Create a wrapper script that runs installation in the cloned repo
    wrapper_script = repo_dir / "install_wrapper.sh"
    wrapper_content = f"""#!/bin/bash
set -e
cd {clone_dir}
source {install_script}
"""

    with open(wrapper_script, 'w') as f:
        f.write(wrapper_content)

    os.chmod(wrapper_script, 0o755)

    if show_progress:
        print("🐍 Installation progress (real-time):")
        print("=" * 50)
        exit_code, output = run_command_with_progress([str(wrapper_script)], cwd=clone_dir, timeout=900)
        print("=" * 50)
    else:
        exit_code, output = run_command([str(wrapper_script)], cwd=clone_dir, timeout=900)

    installation_success = (exit_code == 0)

    if installation_success:
        print("✅ Installation completed successfully!")
    else:
        print("❌ Installation failed!")
        if not show_progress:
            print("Installation output:")
            print(output[:5000])  # Show first 5000 chars
        # Clean up and return
        if clone_dir.exists():
            shutil.rmtree(clone_dir)
        return False, False

    # Step 5: Export conda environment (SWE-smith style)
    print("\n4️⃣  Exporting conda environment...")
    env_yml_path = repo_dir / f"sweenv_{repo}.yml"

    export_cmd = f"conda env export -n testbed > {env_yml_path}"
    exit_code, output = run_command(["bash", "-c", export_cmd], timeout=60)

    if exit_code == 0:
        print(f"✅ Exported conda environment to {env_yml_path.name}")

        # Edit YAML to exclude the package itself (SWE-smith style)
        try:
            with open(env_yml_path, 'r') as f:
                lines = f.readlines()

            with open(env_yml_path, 'w') as f:
                for line in lines:
                    # Exclude the package by repository name
                    if line.strip().startswith(f"- {repo}==") or \
                       line.strip().startswith(f"- {repo.lower()}=="):
                        continue
                    f.write(line)
        except Exception as e:
            print(f"⚠️  Could not edit environment YAML: {e}")
    else:
        print(f"⚠️  Could not export conda environment")

    # Step 6: Run tests in the cloned repository
    print("\n5️⃣  Running tests in cloned repository...")
    test_output_path = repo_dir / "test_output.txt"
    all_output = []
    testing_success = True

    if not test_commands:
        print("⚠️  No test commands found, skipping tests")
        testing_success = True
    else:
        for i, test_command in enumerate(test_commands, 1):
            if len(test_commands) > 1:
                print(f"   Running test {i}/{len(test_commands)}: {test_command}")
            else:
                print(f"   Running test: {test_command}")

            # Run test in conda environment within cloned repo
            test_wrapper = f"""#!/bin/bash
source /opt/miniconda3/bin/activate || source ~/miniconda3/bin/activate || source /root/miniconda3/bin/activate
conda activate testbed
cd {clone_dir}
{test_command}
"""

            test_wrapper_script = repo_dir / f"test_wrapper_{i}.sh"
            with open(test_wrapper_script, 'w') as f:
                f.write(test_wrapper)

            os.chmod(test_wrapper_script, 0o755)

            exit_code, output = run_command([str(test_wrapper_script)], timeout=900)

            # Collect output
            if len(test_commands) > 1:
                all_output.append(f"=== Command {i}: {test_command} ===")
                all_output.append(f"Exit code: {exit_code}")

            all_output.append(output)
            all_output.append("")  # Empty line

            # Just report that the command executed
            # Test parsing and failure threshold checking is handled by verify_testing.py (Stage 3)
            if exit_code == 0:
                print(f"   ✅ Command completed (exit code 0)")
            else:
                print(f"   ⚠️  Command exited with code {exit_code}")
                print(f"   ℹ️  Test results will be analyzed by verify_testing.py")
            
            # Stage 2 always succeeds if tests ran (even with failures)
            # Let Stage 3 (verify_testing.py) determine actual pass/fail based on threshold

    # Save test output
    combined_output = '\n'.join(all_output)
    with open(test_output_path, 'w', encoding='utf-8') as f:
        f.write(combined_output)

    print(f"💾 Test output saved to {test_output_path.name}")

    # Step 7: Clean up
    print("\n6️⃣  Cleaning up...")
    if clone_dir.exists():
        shutil.rmtree(clone_dir)
        print("✅ Removed cloned repository")

    # Clean up wrapper scripts
    for script in repo_dir.glob("*_wrapper*.sh"):
        script.unlink()

    return installation_success, testing_success

def verify_dockerfile(dockerfile_path: Path, image_name: str = None, show_progress: bool = True, failure_threshold: float = 0.09) -> Tuple[bool, bool]:
    """
    Verify that a Dockerfile builds successfully and tests pass.
    Returns (installation_success, testing_success) tuple.
    """

    if not dockerfile_path.exists():
        print(f"❌ Dockerfile not found: {dockerfile_path}")
        return False, False

    if not image_name:
        # Use the directory name where the Dockerfile is located
        image_name = f"{dockerfile_path.parent.name.lower()}-test"

    print(f"🔍 Verifying Dockerfile: {dockerfile_path}")
    print(f"🏷️  Image name: {image_name}")

    # Step 1: Build the Docker image (Installation Check)
    print("\n1️⃣  Building Docker image (Installation Check)...")

    build_cmd = [
        "docker", "build",
        "-f", str(dockerfile_path),
        "-t", image_name,
        str(dockerfile_path.parent)  # Use the directory containing the Dockerfile as build context
    ]

    if show_progress:
        print("📦 Build progress (real-time):")
        print("=" * 50)
        exit_code, output = run_command_with_progress(build_cmd, timeout=600)  # 10 minute timeout for build
        print("=" * 50)
    else:
        exit_code, output = run_command(build_cmd, timeout=600)  # 10 minute timeout for build

    installation_success = (exit_code == 0)

    if installation_success:
        print("✅ Docker build successful! (Installation Check: PASSED)")
    else:
        print("❌ Docker build failed! (Installation Check: FAILED)")
        if not show_progress:
            print("Build output:")
            print(output)
        return False, False

    # Step 2: Test running the container
    print("\n2️⃣  Testing container execution...")
    run_cmd = [
        "docker", "run", "--rm",
        image_name,
        "echo", "Container is working"
    ]

    exit_code, output = run_command(run_cmd, timeout=60)

    if exit_code == 0:
        print("✅ Container runs successfully!")
    else:
        print("❌ Container failed to run!")
        print(f"Output: {output}")
        return installation_success, False

    # Step 3: Run tests and evaluate results (Testing Check)
    print("\n3️⃣  Running tests and evaluating results (Testing Check)...")

    dockerfile_dir = dockerfile_path.parent
    metadata_path = dockerfile_dir / "repo_metadata.json"
    test_output_path = dockerfile_dir / "test_output.txt"

    if not metadata_path.exists():
        print("⚠️  No repo_metadata.json found, skipping test execution")
        return installation_success, True

    testing_success = True

    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        test_commands = metadata.get('test_commands', [])
        test_framework = metadata.get('test_framework', '')
        language = metadata.get('language', '')

        if not test_commands:
            print("⚠️  No test commands found, skipping tests")
            return installation_success, True

        print(f"🧪 Test configuration:")
        print(f"   Commands: {test_commands}")
        print(f"   Framework: {test_framework}")
        print(f"   Language: {language}")

        all_output = []

        for i, test_command in enumerate(test_commands, 1):
            if len(test_commands) > 1:
                print(f"\n   Running test {i}/{len(test_commands)}: {test_command}")
            else:
                print(f"\n   Running test: {test_command}")

            # For npm test or commands with shell operators, use shell form
            shell_operators = ['||', '&&', ';', '|', '>', '<', '$(', '`']
            needs_shell = test_command.startswith('npm') or any(op in test_command for op in shell_operators)
            
            if needs_shell:
                docker_cmd = ["docker", "run", "--rm", image_name, "sh", "-c", test_command]
            else:
                # Split the command for direct execution
                test_cmd_parts = test_command.split()
                docker_cmd = ["docker", "run", "--rm", image_name] + test_cmd_parts

            print(f"   Executing: {' '.join(docker_cmd)}")

            # Run with extended timeout for tests
            exit_code, output = run_command(docker_cmd, timeout=600)

            # Collect output
            if len(test_commands) > 1:
                all_output.append(f"=== Command {i}: {test_command} ===")
                all_output.append(f"Exit code: {exit_code}")

            all_output.append(output)
            all_output.append("")  # Empty line

            # Just report that the command executed
            # Test parsing and failure threshold checking is handled by verify_testing.py (Stage 3)
            if exit_code == 0:
                print(f"   ✅ Command completed successfully (exit code 0)")
            else:
                print(f"   ⚠️  Command exited with code {exit_code}")
                print(f"   ℹ️  Test results will be analyzed by verify_testing.py")
            
            # Stage 2 always succeeds if tests ran (even with failures)
            # Let Stage 3 (verify_testing.py) determine actual pass/fail based on threshold

        # Save test output
        combined_output = '\n'.join(all_output)
        with open(test_output_path, 'w', encoding='utf-8') as f:
            f.write(combined_output)

        print(f"\n💾 Test output saved to {test_output_path.name}")

        # Show summary
        lines = combined_output.split('\n')
        if len(lines) > 20:
            print("\n📋 Test output preview (last 10 lines):")
            for line in lines[-10:]:
                if line.strip():
                    print(f"   {line}")

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        testing_success = False

    return installation_success, testing_success

def cleanup_image(image_name: str) -> None:
    """Remove the test Docker image."""
    print(f"\n🧹 Cleaning up image: {image_name}")
    cleanup_cmd = ["docker", "rmi", image_name]
    exit_code, output = run_command(cleanup_cmd, timeout=60)

    if exit_code == 0:
        print("✅ Image removed successfully")
    else:
        print("⚠️  Could not remove image (it may not exist)")

def main():
    """Main CLI interface for Dockerfile and Python installation verification."""
    parser = argparse.ArgumentParser(
        description="Verify generated Dockerfiles or conda installation scripts, build/install and run tests correctly"
    )
    parser.add_argument("path", help="Path to Dockerfile (non-Python) or directory containing installation script (Python)")
    parser.add_argument("--python-repo", action="store_true", help="Treat as Python repository with conda installation script")
    parser.add_argument("--image-name", help="Docker image name for testing (non-Python repos only)")
    parser.add_argument("--cleanup", action="store_true", help="Remove test image/environment after verification")
    parser.add_argument("--no-progress", action="store_true", help="Disable real-time progress output")
    parser.add_argument("--allow-test-failures", action="store_true",
                        help="Accept repositories where installation succeeds but tests fail (exit 0 if installation passed)")
    parser.add_argument("--failure-threshold", type=float, default=0.09,
                        help="[Passed to verify_testing.py] Maximum fraction of tests allowed to fail (default: 0.09 = 9%%)")

    args = parser.parse_args()

    input_path = Path(args.path).resolve()
    if not input_path.exists():
        print(f"❌ Path not found: {input_path}")
        sys.exit(1)

    try:
        if args.python_repo:
            # Python repository verification
            if not input_path.is_dir():
                print(f"❌ Python repos require a directory path, got: {input_path}")
                sys.exit(1)

            print(f"🐍 Verifying Python installation script in: {input_path}")
            installation_success, testing_success = verify_python_installation_swe_smith_style(
                input_path, not args.no_progress, args.failure_threshold
            )

            # Clean up conda environment if requested
            if args.cleanup:
                cleanup_conda_env("testbed")

        else:
            # Non-Python (Dockerfile) verification
            if input_path.is_dir():
                dockerfile_path = input_path / "Dockerfile"
                if not dockerfile_path.exists():
                    print(f"❌ Dockerfile not found in directory: {dockerfile_path}")
                    sys.exit(1)
            else:
                dockerfile_path = input_path
                if not dockerfile_path.exists():
                    print(f"❌ Dockerfile not found: {dockerfile_path}")
                    sys.exit(1)

            # Check if Docker is available for non-Python repos
            exit_code, output = run_command(["docker", "--version"], timeout=10)
            if exit_code != 0:
                print("❌ Docker is not available or not running")
                print("Please ensure Docker is installed and the daemon is running")
                sys.exit(1)

            print(f"🐳 Using Docker: {output.strip()}")

            # Generate image name if not provided
            image_name = args.image_name or f"{dockerfile_path.parent.name.lower()}-verification-test"

            # Verify the Dockerfile
            show_progress = not args.no_progress
            installation_success, testing_success = verify_dockerfile(
                dockerfile_path, image_name, show_progress, args.failure_threshold
            )

            if installation_success:
                # Show usage instructions for Docker
                print(f"\n📋 Docker usage instructions:")
                print(f"   docker run --rm -it {image_name}")
                print(f"   docker run --rm {image_name} <your-command-here>")

            if args.cleanup:
                cleanup_image(image_name)

        # Final summary
        print("\n" + "=" * 60)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 60)

        if args.python_repo:
            print(f"🐍 Python Repository Verification:")
        else:
            print(f"🐳 Docker Repository Verification:")

        print(f"   ✅ Installation Check: {'PASSED' if installation_success else 'FAILED'}")
        print(f"   {'✅' if testing_success else '❌'} Test Execution: {'PASSED' if testing_success else 'FAILED'}")
        if testing_success:
            print(f"   ℹ️  Test results saved to test_output.txt")
            print(f"   ℹ️  Run verify_testing.py to parse results and check thresholds")

        overall_success = installation_success and testing_success

        if overall_success:
            print(f"\n🎉 OVERALL RESULT: VERIFICATION PASSED")
            print(f"   Installation and test execution completed successfully!")
            print(f"   ℹ️  Use verify_testing.py to analyze test results and check failure thresholds")
            sys.exit(0)
        elif args.allow_test_failures and installation_success:
            print(f"\n⚠️  OVERALL RESULT: PARTIAL SUCCESS (Installation Passed)")
            print(f"   Installation succeeded and tests were executed")
            print(f"   ℹ️  Use verify_testing.py to analyze test results and check failure thresholds")
            print(f"   Exiting with success code due to --allow-test-failures flag")
            sys.exit(0)
        else:
            print(f"\n❌ OVERALL RESULT: VERIFICATION FAILED")
            if not installation_success:
                print(f"   Installation/build failed")
            if not testing_success:
                print(f"   Could not execute tests or capture output")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n⏹️  Verification interrupted by user")
        if args.cleanup:
            if args.python_repo:
                cleanup_conda_env("testbed")
            else:
                cleanup_image(image_name)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.cleanup:
            if args.python_repo:
                cleanup_conda_env("testbed")
            else:
                cleanup_image(image_name)
        sys.exit(1)

if __name__ == "__main__":
    main()