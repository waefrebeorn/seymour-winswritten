# Waefrebeorn Repo Template - Dual License Setup

## What It Does

Every new waefrebeorn repository that contains "absorbed" code (code reused
from public domain, other licenses) uses this dual-license approach:

| File | License | Scope |
|------|---------|-------|
| `LICENSE` | Original license (Unlicense, MIT, Apache, etc.) | Absorbed/reused code |
| `LICENSE.waefrebeorn` | Waefrebeorn Umbrella License v3.0 | New waefrebeorn code, modifications, extensions |
| `README.md` | Dual-license disclosure | Links both LICENSE files |

## Usage

1. Copy the template files into a new repo
2. Replace `{project-name}` and `{project-description}` in README.md
3. Run `setup-license.sh` for automated setup
4. Keep the original LICENSE unchanged
5. New code goes under LICENSE.waefrebeorn

## Key Principle

- Original absorbed code stays under its original license
- Any expansion beyond the original code falls under Waefrebeorn Umbrella License v3.0
- Unmodified original code can never be subject to the Umbrella License's corporate restrictions
- This is true for all repos: Waefrebeorn, wubu, WuBu, any project created

## Files Produced

- `/home/wubu/seymour-project/templates/waefrebeorn-repo/` - full template directory
- `/home/wubu/seymour-project/ponderables/drafts/waefrebeorn-repo-template.md` - documentation

## License

The template itself is placed in the public domain. The Waefrebeorn Umbrella
License v3.0 applies to any code that modifies extends the template.
