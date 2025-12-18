# Automating Repository Profile Generation using Mini-SWE-Agent

A sophisticated 3-stage automated pipeline that converts GitHub repositories into SWE-smith compatible profile classes using mini-swe-agent for repository analysis and intelligent test framework detection.

## 🚀 Quick Start

**Full automated pipeline (recommended):**
```bash
# Python repository with conda environment
python generate_profile.py Instagram/MonkeyType --python-repo --model claude-sonnet-4-20250514

# JavaScript repository with Docker environment
python generate_profile.py expressjs/express --model claude-sonnet-4-20250514

# Rust repository with livestreaming agent action
python generate_profile.py BurntSushi/ripgrep --livestream --model claude-sonnet-4-20250514
```

**Output:** Ready-to-integrate SWE-smith profile classes in `agent-result/owner-repo/generated_profiles/`

## 📋 Overview

This pipeline automatically:
1. **Analyzes repositories** using mini-swe-agent to understand structure and dependencies
2. **Generates deployment artifacts** (Dockerfiles for most languages, conda scripts for Python)
3. **Verifies installations** and captures test execution output with smart parsing
4. **Parses test frameworks** to identify the correct parser (pytest, mocha, jest, cargo, etc.)
5. **Generates SWE-smith profiles** with correct naming conventions and integration metadata

**Supported Languages:** Python, JavaScript, TypeScript, Rust, Go, Java, C/C++, PHP, Ruby

## 🛠 Installation & Setup

### Prerequisites
```bash
# Install mini-swe-agent submodule
cd mini-swe-agent
pip install -e .

# API Keys (choose one)
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"
export GEMINI_API_KEY="your-gemini-key"
```

### Dependencies
- Docker (for non-Python repositories)
- Conda/Miniconda (for Python repositories)
- Git
- Python 3.8+

## 🎯 Core Architecture: 3-Stage Pipeline

### Stage 1: Repository Analysis & Artifact Generation
**Script:** `simple_repo_to_dockerfile.py`

```bash
# Python repositories (generates conda installation script)
python simple_repo_to_dockerfile.py owner/repo --python-repo --model_name claude-sonnet-4-20250514

# Non-Python repositories (generates Dockerfile)
python simple_repo_to_dockerfile.py owner/repo --model_name claude-sonnet-4-20250514
```

**What it does:**
- Clones and analyzes repository structure
- Detects programming language and framework
- Identifies installation and test commands
- Creates deployment artifacts (Dockerfile or conda script)
- Generates `repo_metadata.json` with standardized format

**Output files:**
- `agent-result/owner-repo/Dockerfile` (or `*_install.sh` for Python)
- `agent-result/owner-repo/repo_metadata.json`
- `agent-result/owner-repo/trajectory.json` (agent interaction log)

### Stage 2: Build Verification & Test Execution
**Script:** `verify_dockerfile.py`

```bash
# Verify Python repository (SWE-smith compatible workflow)
python verify_dockerfile.py agent-result/owner-repo --python-repo --cleanup

# Verify non-Python repository (Docker-based)
python verify_dockerfile.py agent-result/owner-repo/Dockerfile --cleanup
```

**What it does:**
- **Python repos:** Clones repo, creates conda "testbed" environment, runs installation script, executes tests from cloned repository
- **Non-Python repos:** Docker build verification + intelligent test result parsing that ignores npm notices
- **Smart verification:** Separates installation success from testing success
- **Detailed reporting:** Clear status for both installation and testing phases

**Output files:**
- `agent-result/owner-repo/test_output.txt`
- `agent-result/owner-repo/sweenv_RepoName.yml` (Python only)

### Stage 3: Test Output Parsing
**Script:** `verify_testing.py`

```bash
# Parse test output with framework detection
python verify_testing.py agent-result/owner-repo --python-repo  # for Python repos
python verify_testing.py agent-result/owner-repo               # for others
```

**What it does:**
- Detects test framework from output patterns
- Parses individual test results (PASSED/FAILED/SKIPPED)
- Maps test names to status using framework-specific parsers
- Handles multiple fallback strategies for unknown frameworks

**Supported frameworks:**
- **Python:** pytest, unittest
- **JavaScript:** jest, mocha, vitest
- **Rust:** cargo test
- **Go:** go test
- **Java:** maven, gradle

**Output files:**
- `agent-result/owner-repo/parsed_test_status.json`

## 🚀 Master Orchestrator: End-to-End Execution

**Script:** `generate_profile.py` - **Recommended for most use cases**

### Full Pipeline with SWE-smith Integration

```bash
# Python repository (conda-based profile)
python generate_profile.py Instagram/MonkeyType --python-repo --model claude-sonnet-4-20250514

# JavaScript repository (Docker-based profile)
python generate_profile.py expressjs/express --model claude-sonnet-4-20250514

# With custom output file
python generate_profile.py fastapi/typer --python-repo --output typer_profile.py

# JSON output for programmatic use
python generate_profile.py owner/repo --json
```

### Pipeline Options

| Option | Description | Default |
|--------|-------------|---------|
| `--python-repo` | Treat as Python repository (conda workflow) | False |
| `--model` | Model to use for analysis | `claude-sonnet-4-20250514` |
| `--output` | Save profile to file | Print to stdout |
| `--json` | Output JSON instead of Python class | False |
| `--livestream` | Enable real-time output | True |

### Pipeline Features

- **🔴 Livestream Mode:** See mini-swe-agent working in real-time
- **🛑 Failure Handling:** Pipeline stops if previous stage fails (Stage 1→2→3)
- **📋 Complete Logging:** Full pipeline output saved to `pipeline_full_log.txt`
- **⚡ Smart Verification:** Separate installation and testing checks
- **🎯 SWE-smith Ready:** Generates integration-ready profile classes
- **✅ Quality Assurance:** Profiles only generated if Stages 1&2 succeed

## 📁 Output Structure

After running the full pipeline:

```
agent-result/owner-repo/
├── Dockerfile                     # (or *_install.sh for Python)
├── repo_metadata.json             # Repository metadata
├── test_output.txt                # Test execution output
├── parsed_test_status.json        # Test parsing results
├── pipeline_full_log.txt          # Complete pipeline log
└── generated_profiles/            # 🎯 SWE-smith Integration Files
    ├── profile_class.py           # Ready-to-copy profile class
    ├── profile_metadata.json      # Integration metadata
    └── integration_instructions.md # Step-by-step integration guide
```

## 🔗 SWE-smith Integration

The pipeline generates **zero-friction integration** files for SWE-smith:

### Generated Profile Classes

**Python Example:**
```python
# Auto-generated profile for Instagram/MonkeyType
# Integration: Copy to swesmith/profiles/python.py

@dataclass
class MonkeyType15e7bca6(PythonProfile):
    owner: str = "Instagram"
    repo: str = "MonkeyType"
    commit: str = "15e7bca60146a7afbde46ee8782a0c650f781c74"
    install_cmds: list = field(default_factory=lambda: [
        "pip install -e .",
        "pip install pytest"
    ])
```

**JavaScript Example:**
```python
@dataclass
class Express9a7afb28(JavaScriptProfile):
    owner: str = "expressjs"
    repo: str = "express"
    commit: str = "9a7afb2886247603ebd69a1c8ee5d2f29542a6c0"
    test_cmd: str = "npm test -- --verbose"

    @property
    def dockerfile(self):
        return f"""FROM node:18-slim
RUN apt-get update && apt-get install -y git
RUN git clone https://github.com/{self.mirror_name} /testbed
WORKDIR /testbed
RUN npm install
"""

    def log_parser(self, log: str) -> dict[str, str]:
        return parse_log_mocha(log)
```

### Integration Workflow

1. **Check Integration Status:**
   ```bash
   cat agent-result/owner-repo/generated_profiles/profile_metadata.json
   # Look for "integration_ready": true
   ```

2. **Copy Profile Class:**
   ```bash
   cat agent-result/owner-repo/generated_profiles/profile_class.py >> /path/to/SWE-smith/swesmith/profiles/python.py
   ```

3. **Test Integration:**
   ```python
   from swesmith.profiles import registry
   profile = registry.get("owner/repo")
   print(f"Profile loaded: {profile.__class__.__name__}")
   ```

## 🧪 Individual Stage Usage (Testing/Debugging)

### When to use individual stages:
- **Stage 1 only:** Test repository analysis and artifact generation
- **Stage 2 only:** Debug installation or test execution issues
- **Stage 3 only:** Test output parsing with different frameworks
- **Stages 1+2:** Skip parsing if you only need installation verification

### Stage 1: Repository Analysis

```bash
# Python repository
python simple_repo_to_dockerfile.py Instagram/MonkeyType --python-repo --model_name claude-sonnet-4-20250514

# JavaScript repository
python simple_repo_to_dockerfile.py expressjs/express --model_name claude-sonnet-4-20250514

# With livestream enabled
python simple_repo_to_dockerfile.py owner/repo --livestream
```

### Stage 2: Verification Only

```bash
# Verify existing Python repository artifacts
python verify_dockerfile.py agent-result/Instagram-MonkeyType --python-repo --cleanup

# Verify existing Dockerfile
python verify_dockerfile.py agent-result/expressjs-express/Dockerfile --cleanup

# Without cleanup (keep containers)
python verify_dockerfile.py agent-result/owner-repo/Dockerfile
```

### Stage 3: Parsing Only

```bash
# Parse existing test output
python verify_testing.py agent-result/owner-repo --python-repo
python verify_testing.py agent-result/owner-repo

# Test specific framework parsing
python -c "from log_parser.parsers.mocha import parse_log_mocha; print(parse_log_mocha(open('test_output.txt').read()))"
```

## 🐛 Troubleshooting & Debugging

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Stage 1 fails | API key missing/invalid | Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` |
| Stage 2 false failure | npm notices causing non-zero exit | Use smart parsing (already implemented) |
| Python tests fail | Running from wrong directory | Uses SWE-smith workflow (clones repo) |
| Missing test framework | Parsing strategy failed | Check `parsed_test_status.json` |
| Docker build fails | Missing dependencies | Check generated Dockerfile |
| No profile generated | Stage 1 or 2 failed | Both stages must succeed for profile generation |

### Debugging Commands

```bash
# Check pipeline stages status
ls -la agent-result/owner-repo/

# Examine test output in detail
cat agent-result/owner-repo/test_output.txt

# Review full pipeline execution log
cat agent-result/owner-repo/pipeline_full_log.txt

# Check agent decision making
head -100 agent-result/owner-repo/trajectory.json

# Re-run Stage 2 with detailed output
python verify_dockerfile.py agent-result/owner-repo --python-repo

# Test specific parsing
python verify_testing.py agent-result/owner-repo --python-repo
```

### Getting Help

- **Generated files:** Check `integration_instructions.md` for specific guidance
- **Pipeline issues:** Review `pipeline_full_log.txt` for complete execution trace
- **Agent behavior:** Examine `trajectory.json` for analysis decisions
- **Parsing problems:** Test individual parsers in `log_parser/` directory

## 🎯 Advanced Configuration

### Model Selection

| Model | Best For | Speed | Accuracy |
|--------|----------|--------|----------|
| `claude-sonnet-4-20250514` | Complex repos, high accuracy | Slower | ⭐⭐⭐⭐⭐ |
| `gemini-3.0-flash` | Fast iteration, high throughput | Faster | ⭐⭐⭐⭐ |
| `gpt-4o-mini` | Simple repos, fast iteration | Faster | ⭐⭐⭐⭐ |

### Extended Timeouts

For large repositories that need longer analysis time:
```bash
timeout 300 python generate_profile.py complex/repo --model claude-sonnet-4-20250514
```

### Batch Processing

```bash
# Process multiple repositories
for repo in "owner1/repo1" "owner2/repo2" "owner3/repo3"; do
    python generate_profile.py "$repo" --model claude-sonnet-4-20250514
done
```

## 📊 Supported Languages & Frameworks

| Language | Frameworks | Base Images | Test Parsers |
|----------|------------|-------------|--------------|
| **Python** | pip, poetry, conda | miniconda3 | pytest, unittest |
| **JavaScript** | npm, yarn | node:18-slim | jest, mocha, vitest |
| **TypeScript** | npm, yarn, tsc | node:18-slim | jest, mocha |
| **Rust** | cargo | rust:latest | cargo test |
| **Go** | go modules | golang:1.21 | go test |
| **Java** | maven, gradle | openjdk:17 | maven, junit |
| **C/C++** | make, cmake | gcc:latest | ctest, custom |
| **Ruby** | bundler | ruby:latest | rspec, minitest |
| **PHP** | composer | php:latest | phpunit |

## 🎉 Success Stories

**Verified Repositories:**
- ✅ **Instagram/MonkeyType** (Python) - pytest framework, 379 tests
- ✅ **expressjs/express** (JavaScript) - mocha framework, 1235 tests
- ✅ **fastapi/typer** (Python) - pytest framework, CLI tool
- ✅ **facebook/react** (JavaScript) - jest framework, large codebase
- ✅ **BurntSushi/ripgrep** (Rust) - cargo test, performance tool

Ready to automate your repository profile generation! 🚀