import os
import re
import json
from datetime import datetime


def analyze_results():
    results_dir = "agent-result"
    if not os.path.exists(results_dir):
        if os.path.exists("agent-results"):
            results_dir = "agent-results"
        else:
            print(f"Error: Directory '{results_dir}' or 'agent-results' not found.")
            return

    data = []
    total_cost = 0.0
    valid_counts = 0
    success_count = 0
    no_tests_count = 0
    timestamps = []
    ts_pattern = re.compile(r"# Timestamp: ([\d\-T:\.]+)")

    # Regex to match "💵 Total cost: $0.1234"
    # Handling potential leading whitespace and the exact format found in logs
    cost_pattern = re.compile(r"💵 Total cost: \$([\d\.]+)")

    # Get subdirectories and sort them
    try:
        names = sorted(
            [
                d
                for d in os.listdir(results_dir)
                if os.path.isdir(os.path.join(results_dir, d))
            ]
        )
    except Exception as e:
        print(f"Error accessing directories: {e}")
        return

    for name in names:
        log_path = os.path.join(results_dir, name, "pipeline_full_log.txt")
        cost = None
        ts = None
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    content = f.read()

                    # Extract cost
                    match = cost_pattern.search(content)
                    if match:
                        cost = float(match.group(1))
                        total_cost += cost
                        valid_counts += 1

                    # Extract timestamp (usually at the top)
                    ts_match = ts_pattern.search(content)
                    if ts_match:
                        try:
                            ts = datetime.fromisoformat(ts_match.group(1))
                            timestamps.append(ts)
                        except ValueError:
                            pass
            except Exception:
                pass

        success = os.path.isdir(os.path.join(results_dir, name, "generated_profiles"))

        # Check if repo has no tests
        has_no_tests = False
        metadata_path = os.path.join(results_dir, name, "repo_metadata.json")
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    test_commands = metadata.get("test_commands", [])
                    test_framework = metadata.get("test_framework", "")
                    if (not test_commands or test_commands == []) and (
                        test_framework == "none" or not test_framework
                    ):
                        has_no_tests = True
                        no_tests_count += 1
            except Exception:
                pass

        if success and not has_no_tests:
            success_count += 1

        data.append((name, cost, success, ts, has_no_tests))

    # Calculate average
    average_cost = total_cost / valid_counts if valid_counts > 0 else 0

    # Formatting durations
    def format_delta(delta):
        total_secs = int(delta.total_seconds())
        h = total_secs // 3600
        m = (total_secs % 3600) // 60
        s = total_secs % 60
        if h > 0:
            return f"{h}h {m}m {s}s"
        return f"{m}m {s}s"

    # Calculate individual durations
    # Sort items that have timestamps by time
    with_ts = sorted([item for item in data if item[3] is not None], key=lambda x: x[3])
    durations = {}  # name -> duration_str
    for i in range(len(with_ts)):
        name = with_ts[i][0]
        ts = with_ts[i][3]
        if i < len(with_ts) - 1:
            next_ts = with_ts[i + 1][3]
            durations[name] = format_delta(next_ts - ts)
        else:
            durations[name] = "-"

    # Print table
    header_name = "name"
    header_cost = "cost"
    header_success = "success"
    header_duration = "duration"

    # Count repos with tests only
    repos_with_tests_count = len(data) - no_tests_count
    success_summary = f"{success_count} / {repos_with_tests_count}"

    name_col_width = (
        max(
            len(header_name), max([len(n) for n, _, _, _, _ in data] + [len("Average")])
        )
        + 2
    )
    success_col_width = max(len(header_success), len(success_summary)) + 2
    cost_col_width = 15
    duration_col_width = 12

    print(
        f"{header_name:<{name_col_width}} | {header_success:<{success_col_width}} | {header_cost:<{cost_col_width}} | {header_duration:<{duration_col_width}}"
    )
    print(
        "-"
        * (name_col_width + cost_col_width + success_col_width + duration_col_width + 9)
    )

    for name, cost, success, ts, has_no_tests in data:
        cost_str = f"${cost:.4f}" if cost is not None else "N/A"
        if has_no_tests:
            success_str = "NO TESTS"
        else:
            success_str = "YES" if success else "NO"
        duration_str = durations.get(name, "N/A")
        print(
            f"{name:<{name_col_width}} | {success_str:<{success_col_width}} | {cost_str:<{cost_col_width}} | {duration_str:<{duration_col_width}}"
        )

    print(
        "-"
        * (name_col_width + cost_col_width + success_col_width + duration_col_width + 9)
    )

    total_cost_str = f"${total_cost:.4f}"
    avg_cost_str = f"${average_cost:.4f}"

    if timestamps:
        total_duration = max(timestamps) - min(timestamps)
        avg_delta = (
            total_duration / (len(data) - 1) if len(data) > 1 else total_duration
        )
        total_dur_str = format_delta(total_duration)
        avg_dur_str = format_delta(avg_delta)
    else:
        total_dur_str = "N/A"
        avg_dur_str = "N/A"

    print(
        f"{'Total':<{name_col_width}} | {success_summary:<{success_col_width}} | {total_cost_str:<{cost_col_width}} | {total_dur_str:<{duration_col_width}}"
    )
    print(
        f"{'Average':<{name_col_width}} | {'':<{success_col_width}} | {avg_cost_str:<{cost_col_width}} | {avg_dur_str:<{duration_col_width}}"
    )

    # Print summary of repos with no tests
    if no_tests_count > 0:
        print(
            f"\n📝 Note: {no_tests_count} repo(s) marked as 'NO TESTS' (excluded from success count)"
        )


if __name__ == "__main__":
    analyze_results()
