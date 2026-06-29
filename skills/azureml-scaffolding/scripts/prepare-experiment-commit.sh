#!/usr/bin/env bash

set -euo pipefail

usage() {
    cat <<EOF
Create an experiment commit on the experiments branch.

Ensures the working directory is clean, fetches the remote, verifies the
current branch is up to date with upstream main, then builds a two-commit
chain on the local experiments branch:

  1. A sync commit that restores main's tree on experiments (skipped if
     already in sync).
  2. The experiment commit with the current tree on top, so the diff shows
     only what changed from main.

Because the experiment commit shares the same tree as HEAD, the caller can
\`git checkout \$EXP_REF\` without losing working-directory state. Intended
pattern:

  commit_id=\$(scripts/prepare-experiment-commit.sh "message")
  curr_branch=\$(git rev-parse --abbrev-ref HEAD)
  git checkout \$EXP_REF
  # ... submit job ...
  git push origin "\$commit_id:\$EXP_REF"   # only on success
  git checkout "\$curr_branch"

Usage:
  $0 "EXPERIMENT_MESSAGE"

Environment:
  BASE_REF   Base reference for main branch (default: main)
  EXP_REF    Branch name for experiment commits (default: experiments)
  REMOTE     Git remote name (default: origin)

Examples:
  $0 "test new featurizer"
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

message=${1:-}
if [[ -z "$message" ]]; then
    echo "Missing experiment message." >&2
    usage
    exit 1
fi

base_ref=${BASE_REF:-main}
exp_ref=${EXP_REF:-experiments}
remote=${REMOTE:-origin}

if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "Not inside a git repository." >&2
    exit 1
fi

# 1. Working directory must be clean
if ! git diff --quiet; then
    echo "Working directory is dirty. Commit or stash changes first." >&2
    exit 1
fi

# 2. Fetch remote so all refs are current
git fetch "$remote"

# 3. Current branch must be up to date with upstream main
src_ref=$(git rev-parse --abbrev-ref --symbolic-full-name HEAD)
up_main_ref=$(git rev-parse --abbrev-ref --symbolic-full-name "${base_ref}@{upstream}")
up_main_id=$(git rev-parse "$up_main_ref")
merge_base_id=$(git merge-base "$up_main_ref" "$src_ref")

if [[ "$merge_base_id" != "$up_main_id" ]]; then
    echo "Branch is not up to date with $up_main_ref." >&2
    echo "Run: git merge $up_main_ref" >&2
    exit 1
fi

# 4. Check if this tree was already pushed to experiments (nothing to do)
remote_exp_ref="$remote/$exp_ref"
src_tree_id=$(git log -1 --pretty=%T "$src_ref")
if git rev-parse --verify --quiet "$remote_exp_ref" >/dev/null 2>&1; then
    if grep -q -F "$src_tree_id" < <(git log --pretty=%T "$remote_exp_ref"); then
        echo "Experiment already pushed (same tree exists); nothing to do." >&2
        exit 0
    fi
fi

# 5. Sync experiments branch with main's tree if needed
up_main_tree_id=$(git log -1 --pretty=%T "$up_main_ref")

if git rev-parse --verify --quiet "$remote_exp_ref" >/dev/null 2>&1; then
    IFS=: read -r exp_head_id exp_tree_id < <(
        git log -1 --pretty="%H:%T" "$remote_exp_ref"
    )
    if [[ "$up_main_tree_id" != "$exp_tree_id" ]]; then
        exp_head_id=$(
            git commit-tree \
                -p "$remote_exp_ref" \
                -m "restore main ($(git log -1 --pretty=%h "$up_main_id"))" \
                "$up_main_tree_id"
        )
    fi
else
    # experiments branch doesn't exist remotely yet — start from main
    exp_head_id=$(git rev-parse "$up_main_ref")
fi

# 6. Create experiment commit on top of synced experiments head
new_commit=$(git commit-tree -p "$exp_head_id" -m "$message" "$src_tree_id")
git update-ref "refs/heads/$exp_ref" "$new_commit"

echo "$new_commit"
