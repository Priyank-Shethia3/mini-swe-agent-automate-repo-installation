import csv
import os


def filter_repos():
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    repos_path = os.path.join(base_dir, "repos.csv")
    existing_repos_path = os.path.join(base_dir, "existing_repos.csv")
    output_path = os.path.join(base_dir, "new_repos.csv")

    # Read existing repos
    existing_names = set()
    if os.path.exists(existing_repos_path):
        with open(existing_repos_path, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "full_name" in row:
                    existing_names.add(row["full_name"])

    # Read all repos and filter
    if not os.path.exists(repos_path):
        print(f"Error: {repos_path} not found.")
        return

    new_rows = []
    fieldnames = []
    with open(repos_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row["full_name"] not in existing_names:
                new_rows.append(row)

    # Output to new_repos.csv
    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(new_rows)

    print(f"Filtered {len(existing_names)} existing repos (matched against input).")
    print(f"Saved {len(new_rows)} new repos to {output_path}")


if __name__ == "__main__":
    filter_repos()
