# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 2.0.x   | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x: |

## Reporting a Vulnerability

Please report security vulnerabilities or unsafe privilege/file-handling issues (for example in `install.sh`, `bin/steam-net-boost` / `sudoers`, `localconfig.vdf` editing, or `.env` profile loading) via GitHub Security Advisories or by opening a private report / issue on the repository rather than posting exploit details publicly.

- **Response target:** Acknowledgment within a few days, followed by a triage status and fix plan.
- **Accepted reports:** Fixes are prepared on a branch, verified against the unit test suite (`python3 -m unittest discover -s tests -v`), `ShellCheck`, and CI/CodeQL checks, and published in a new patch release without altering immutable tags.
- **Declined reports:** If an issue is out of scope or not a security vulnerability, a brief explanation will be provided.
