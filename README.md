# Skill Lifecycle Management (SLM)

**Discover repeatable work. Turn proven experience into reusable skills.**

[简体中文](README_CN.md) · [Host acceptance tests](docs/HOST-TEST.md) · [Release review](docs/RELEASE-REVIEW.md)

Version **0.2.1** — GitHub distribution candidate; not yet a verified public release.

SLM is a meta skill plus a local Python/SQLite engine. A host agent extracts structured task semantics; the engine matches independent successful tasks, checks registered capabilities, and proposes creating, reusing or optimizing an instruction-based skill. Users choose whether to proceed. Approved changes follow Spec-Driven Development (SDD).

## Features

- Natural-language skill routing where supported by the host, plus explicit invocation.
- Cross-session task records in an authorized fixed local directory; project isolation by default.
- Default recommendation after three independent verified tasks; two with evidence of high reuse value.
- Recommendation cooldown (24 hours plus new evidence), defer and ignore controls.
- Approval-bound proposal hashes, SDD documents, dependency declarations, version records and rollback.
- Feedback-based evaluation; no invented performance gains.

## Requirements and installation

Python 3.9+ with `sqlite3`; authorized local filesystem and execution access; a host capable of loading Agent Skills and semantic reasoning. The engine has no third-party Python runtime package dependencies. Node.js/npm is optional for the external Skills CLI, not required by the core.

After the repository is published, replace `OWNER` with its actual owner:

```sh
npx skills add OWNER/skill-lifecycle-management --skill skill-lifecycle-management
```

For local testing from the repository root:

```sh
npx skills add ./skills/skill-lifecycle-management
```

Alternatively, run `python tools/package.py` and import the generated standard ZIP through the host's supported mechanism. For TeleAgent, use the separate lowercase `skill.md` ZIP. Back up the old skill and data before upgrading; stop writers before backup and do not copy an active SQLite database without its WAL state. Do not run old and new versions against the same database concurrently. These host installation routes are **not end-to-end verified for this distribution**.

## Usage example

1. Enable the skill and authorize a fixed directory for redacted task summaries. Ask the host to retain this permission and path only through its supported mechanism.
2. Work normally across three separate tasks, e.g. fix a calculation error, fix a string-handling error, and repair a validation bug, preserving unrelated behavior and verifying each result.
3. If the host loads SLM, it records independently verified summaries, queries historical patterns and may recommend a reusable minimal-change skill. No suggestion should be fabricated if evidence is insufficient.
4. Choose create, adjust, defer or ignore. Review the specific SDD proposal and hash before approving. Dependency checks and actual host behavior tests are required before installation/publication.

Manual fallback: “Analyze my recent repeatable work and recommend reusable skills.” If the host does not load the skill automatically, invoke it explicitly.

## Run the core and tests

From the repository root:

```sh
python skills/skill-lifecycle-management/scripts/slm.py --version
python skills/skill-lifecycle-management/scripts/slm.py --home ./local-test-data --help
python -m unittest discover -s skills/skill-lifecycle-management/tests -v
python tools/package.py
```

To exercise the CLI with a synthetic, **unverified** sample (never use production storage):

```sh
python skills/skill-lifecycle-management/scripts/slm.py --home ./local-test-data observe skills/skill-lifecycle-management/assets/task.example.json
python skills/skill-lifecycle-management/scripts/slm.py --home ./local-test-data tasks --project demo
```

The sample cannot count as a verified success. Remove only the isolated test directory when finished. More commands: [CLI reference (Chinese)](docs/CLI-CN.md). The complete execution protocol resides in the installable skill's `references/` directory.

## Verified scope and limits

Core tests use synthetic records; they do not measure host LLM semantic accuracy or automatic trigger rate. The engine is deterministic and does not include an embedding model. It cannot see conversations unless loaded by the host. Session changes require a stable task ID; installed external skill equivalence depends on the host. No background observer, automatic installation, network upload or publishing API is supplied. Generated skills are instruction drafts, not generated executable scripts. Dependency discovery does not prove runtime compatibility. Local approval checks are not independent human identity authentication.

See [test evidence](docs/TEST-RESULTS.txt), [distribution retest](docs/DISTRIBUTION-TEST.txt), and [security policy](SECURITY.md). Host compatibility and real workflow efficiency remain to be verified.

## Repository and release

The complete skill is in `skills/skill-lifecycle-management/` (including core, tests, examples, and SDD specifications). `tools/package.py` builds deterministic standard and TeleAgent ZIPs and SHA-256 manifests. GitHub Actions tests the core on Windows, Linux and macOS and builds artifacts on version tags or manual runs; it does not automatically publish a release. Only publish reviewed artifacts after rights and host checks.

## License status

**Not yet licensed for public distribution.** See [license review](docs/LICENSE-REVIEW.md) and the proposed MIT template. The owner must verify ownership/permission and explicitly adopt a license before making this repository public. Do not treat the template as a granted license.
