# Git Workflow & Team Guide

This document outlines the Git workflow and best practices for our **FAQ Chatbot** team. Please follow these guidelines to keep our collaboration smooth and our codebase clean.

## 1. Getting Started

### Clone the Repository
If you haven't already, clone the repository to your local machine:
```bash
git clone <repository_url>
cd faq
```

### Check Your Status
Always check which branch you are on and if you have unsaved changes:
```bash
git status
```

---

## 2. Branching Strategy

We use a **Feature Branch** workflow. Never push directly to `main` (or `master`).

*   **`main`**: The production-ready code.
*   **`feature/your-feature-name`**: For new features (e.g., `feature/add-telegram-bot`).
*   **`fix/bug-name`**: For bug fixes (e.g., `fix/retrieval-error`).

### Creating a New Branch
Before starting work, update your local main and create a new branch:

```bash
# 1. Switch to main
git checkout main

# 2. Pull latest changes
git pull origin main

# 3. Create and switch to your new branch
git checkout -b feature/my-new-feature
```

---

## 3. Making Changes & Committing

### Staging Files
When you have made changes, add them to the "staging area":

```bash
# Add a specific file
git add filename.py

# OR add all changed files (use carefully)
git add .
```

### Committing
Write clear, descriptive commit messages.

```bash
git commit -m "Add retry logic to RAG engine"
```

*   **Good**: "Fix index out of bounds error in app.py"
*   **Bad**: "fix", "update", "wip"

---

## 4. Sharing Your Work

### Pushing to GitHub
When you are ready to save your work to the cloud (GitHub/GitLab):

```bash
# The first time you push a new branch
git push -u origin feature/my-new-feature

# Subsequent pushes
git push
```

### Pull Requests (PR)
1.  Go to the repository on GitHub.
2.  You will see a "Compare & pull request" button.
3.  Click it and write a description of your changes.
4.  Request a review from a team member.
5.  Once approved, merge the PR into `main`.

---

## 5. Staying Updated (Syncing)
To get contributions from other team members into your local branch:

```bash
# 1. Fetch latest state
git fetch origin

# 2. Merge main into your specific branch
git merge origin/main
```

---

## 6. Common Commands Cheat Sheet

| Command | Description |
| :--- | :--- |
| `git status` | Shows modified files and current branch. |
| `git log` | Shows commit history. |
| `git diff` | Shows specific code changes not yet staged. |
| `git checkout <branch>` | Switches to an existing branch. |
| `git branch` | Lists all local branches. |
| `git stash` | Temporarily saves changes (useful if you need to switch branches quickly). |
| `git stash pop` | Restores the stashed changes. |

## 7. Handling Conflicts
If you try to merge and see a "Conflict" message:
1.  Open the file with conflicts (VS Code helps with this).
2.  Choose which code to keep (Current Change vs. Incoming Change).
3.  Save the file.
4.  Run `git add <file>`.
5.  Run `git commit` to finish the merge.
