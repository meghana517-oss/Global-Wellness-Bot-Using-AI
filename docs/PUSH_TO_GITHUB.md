# Push WellBot to GitHub (PowerShell)

This guide helps you safely archive large or sensitive files and push your project to GitHub using PowerShell on Windows.

Steps

1. Review .gitignore

   Ensure `.gitignore` excludes virtual environments, data, credentials and large artifacts. We updated `.gitignore` to include common ignores like `venv/`, `data/`, `results/`, `models/`, `credentials.yml`, `endpoints.yml`, and `archives/`.

2. Create an archive of large files (optional but recommended)

   Run the helper script which creates a timestamped zip under `archives/`:

```powershell
# Dry run (shows what would be archived)
.
.\scripts\create_archive.ps1 -WhatIf

# Create the archive
.
.\scripts\create_archive.ps1
```

After creating the archive, inspect the zip under `archives/` before removing any files from your working tree.

3. Remove or move large files from repo

   If you want to keep the local files but not include in Git, move them outside the repository or rely on `.gitignore` so they won't be added.
   
   Specific notes:
   - Hugging Face / Transformers: model checkpoints and large pre-trained weights should NOT be committed. Use `transformers` to download models at runtime or store them in a separate artifacts bucket. If you have small fine-tuned weights you want to track, keep them under `models/` and use the negation rule in `.gitignore` to force-add only those files.
   - Datasets: store large datasets outside the repo (cloud storage / DVC) or add only the necessary small sample files. To track a dataset folder, use the `!data/my_dataset/` negation example in `.gitignore` and `git add -f` to force-add.
   - Rasa: generated models appear under `rasa/models/*.tar.gz`. Those files are ignored by default; to publish a trained model, either push it to a model store or use `rasa export` and store the manifest elsewhere.


4. Initialize git (if needed) and create a repo

```powershell
# Only if repo not already initialized
git init
git add .
git commit -m "Initial commit - cleaned up for GitHub"
```

5. Create a GitHub repository

- Create the repo on GitHub (web UI). Do NOT initialize with README or .gitignore if you're pushing an existing repo.

6. Add remote and push

```powershell
# Add your GitHub remote (replace URL)
git remote add origin https://github.com/<your-username>/<repo-name>.git

# Push main branch
git branch -M main
git push -u origin main
```

7. Protect secrets

- Never commit `credentials.yml`, `endpoints.yml`, `.env` or keys. If they accidentally got committed, remove them using `git filter-branch` or `git filter-repo` and rotate the secrets.

8. Optional: Add README and CI

- Add `README.md` describing the project and any required setup (Python version, venv setup, Streamlit run command).
- Consider adding GitHub Actions to run lint/tests on push.

Useful helper scripts (included):

- `scripts/create_archive.ps1` — create a timestamped zip containing venv, data, results, models, etc. Useful before removing them from the working tree.
- `scripts/list_large_files.ps1` — scan repo for files above a size threshold (default 10 MB) so you can find large artifacts to archive or ignore.

Troubleshooting

- If `git push` is rejected (non-fast-forward), fetch and merge remote changes first.
- If large files were already committed and you want them removed from history, use `git filter-repo` (recommended) or `git filter-branch` (older).

Contact

If you want, I can:
- Create a minimal `README.md` and `.github/workflows/python-app.yml` for CI checks.
- Run a quick scan to find large files in the repository and list them.
