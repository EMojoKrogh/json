import requests
import os  # <-- added to read GH_TOKEN

# -------------------------------
# CONFIGURATION
# -------------------------------
OWNER = "nlohmann"
REPO = "json"
BRANCH = "develop"

# Read token from environment variable
TOKEN = os.getenv("GH_TOKEN")  # export GH_TOKEN=ghp_xxx

# -------------------------------
# HELPER: Make GitHub API request
# -------------------------------
def gh(url):
    headers = {"Accept": "application/vnd.github+json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()

# -------------------------------
# HELPER: Paginated GET for /files
# -------------------------------
def gh_paginated(url):
    results = []
    page = 1
    while True:
        paged_url = f"{url}?page={page}&per_page=100"
        data = gh(paged_url)

        if not isinstance(data, list):
            break

        results.extend(data)

        if len(data) < 100:
            break

        page += 1

    return results

# -------------------------------
# Test file detection helper
# -------------------------------
def is_test_file(filename):
    lower = filename.lower()

    # directory-based detection
    if lower.startswith("test/") or lower.startswith("tests/") or "/test/" in lower or "/tests/" in lower:
        return True

    # filename-based detection (suffixes)
    test_suffixes = [
        "_test.cpp", "_test.cc", "_test.cxx",
        ".test.cpp", ".test.cc", ".test.cxx",
        "_unittest.cpp", "_unittest.cc", "_unittest.cxx",
    ]

    if any(lower.endswith(suf) for suf in test_suffixes):
        return True

    return False


# -------------------------------
# Fetch merged PRs targeting main
# -------------------------------
print("Fetching merged PRs…")
prs = gh(
    f"https://api.github.com/repos/{OWNER}/{REPO}/pulls"
    f"?state=closed&base={BRANCH}&per_page=100"
)

merged_prs = [pr for pr in prs if pr.get("merged_at")]
print(f"Found {len(merged_prs)} merged PRs.")

CPP_EXTS = (".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx", ".h")

results = []

print("Inspecting file changes and commit counts…")

for pr in merged_prs:
    pr_number = pr["number"]
    pr_title = pr["title"]

    # --- Fetch commit count + head SHA ---
    pr_details_url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls/{pr_number}"
    pr_details = gh(pr_details_url)
    commit_count = pr_details.get("commits", 0)
    head_sha = pr_details["head"]["sha"]

    # --- Fetch changed files (paginated!) ---
    files_url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls/{pr_number}/files"
    files = gh_paginated(files_url)

    # Only non-test C++ files
    cpp_files = [
        f for f in files
        if f["filename"].lower().endswith(CPP_EXTS)
        and not is_test_file(f["filename"])          # <-- NEW RULE
    ]

    results.append({
        "number": pr_number,
        "title": pr_title,
        "cpp_files": len(cpp_files),        # non-test C++ files only
        "total_files": len(files),
        "commits": commit_count,
        "head_sha": head_sha,
        "url": pr["html_url"],
    })

# Sort by most non-test C/C++ files changed
results.sort(key=lambda x: x["cpp_files"], reverse=True)

# -------------------------------
# Display results
# -------------------------------
print("\n=== Pull Requests sorted by NON-TEST C/C++ files changed ===\n")
for r in results[:30]:
    print(
        f"PR #{r['number']:5d} | "
        f"Non-test C/C++ files: {r['cpp_files']:3d} / {r['total_files']:3d} | "
        f"Commits: {r['commits']:2d} | "
        f"Head SHA: {r['head_sha']} | "
        f"{r['title']}\n    {r['url']}\n"
    )
