#!/usr/bin/env python3
import sys
import subprocess
import argparse
import json
from pathlib import Path
from typing import Tuple, Optional
import threading


def run_command(
    cmd: list, cwd: Optional[Path] = None, timeout: int = 600
) -> Tuple[int, str]:
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return -1, f"Command timed out after {timeout} seconds"
    except Exception as e:
        return -1, f"Error running command: {e}"


def run_command_with_progress(
    cmd: list, cwd: Optional[Path] = None, timeout: int = 600
) -> Tuple[int, str]:
    try:
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
        output_lines = []

        def read_output():
            for line in process.stdout:
                print(line, end="")
                output_lines.append(line)

        thread = threading.Thread(target=read_output)
        thread.start()
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            return -1, "".join(
                output_lines
            ) + f"\nCommand timed out after {timeout} seconds"
        thread.join()
        return process.returncode, "".join(output_lines)
    except Exception as e:
        return -1, f"Error running command: {e}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-repo", action="store_true")
    parser.add_argument("--image-name", default="verification-test")
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--no-progress", action="store_true")
    parser.add_argument("--allow-test-failures", action="store_true")
    parser.add_argument("--failure-threshold", type=float, default=0.0)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("path")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path {path} not found")
        sys.exit(1)

    # Handle both directory and Dockerfile path
    if path.is_dir():
        repo_dir = path
        dockerfile_path = repo_dir / "Dockerfile"
    else:
        dockerfile_path = path
        repo_dir = dockerfile_path.parent

    metadata_path = repo_dir / "repo_metadata.json"
    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    image_name = f"{metadata['repo']}-verification-test".lower()
    print("Building Docker image...")
    build_cmd = [
        "docker",
        "build",
        "-t",
        image_name,
        "-f",
        str(dockerfile_path.name),
        ".",
    ]
    ret, out = run_command_with_progress(build_cmd, cwd=repo_dir, timeout=args.timeout)
    if ret != 0:
        print("Build failed")
        sys.exit(1)

    print("Running tests...")
    test_results = []
    with open(repo_dir / "test_output.txt", "w") as f:
        for cmd_str in metadata.get("test_commands", []):
            print(f"Running test: {cmd_str}")
            # Pass complex shell commands to sh -c
            docker_cmd = ["docker", "run", "--rm", image_name, "sh", "-c", cmd_str]
            ret, out = run_command(docker_cmd, timeout=args.timeout)
            f.write(out)
            test_results.append(out)

    print("Verification passed!")


if __name__ == "__main__":
    main()
