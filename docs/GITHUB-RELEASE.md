# GitHub release guide

1. Unzip the repository candidate into a new local folder. Review `RELEASE-REVIEW.md` and `LICENSE-REVIEW.md`. Create a **private** empty GitHub repository first (no auto-generated README).
2. From the repository root run `python -m unittest discover -s skills/skill-lifecycle-management/tests -v` and `python tools/package.py`.
3. Initialize Git and inspect the staged files before the first push:

```bash
git init
git add .
git diff --cached --stat
git diff --cached --check
git status --short
git commit -m "chore: prepare SLM v0.2.1 distribution"
git branch -M main
git remote add origin https://github.com/OWNER/skill-lifecycle-management.git
git push -u origin main
```

Replace OWNER with your real GitHub owner. Verify Actions results. After owner/IP/license review and target-host validation, switch visibility to public only if approved. Create the version tag when appropriate:

```bash
git tag v0.2.1
git push origin v0.2.1
```

If the tag already exists, do not force-move it; choose a new release identifier under your versioning policy. The tag workflow builds ZIPs, SHA-256 manifest and CI artifacts. It has read-only permissions and will not publish a GitHub Release. After reviewing artifacts, publish them manually with release notes that disclose limitations. Verify actual CLI installation and host behavior before advertising compatibility.
