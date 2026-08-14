---
name: repo-health
description: Pre-PR health checks for amir (format, types, tests, docs).
---

# Repo health

Before opening a PR:

```bash
poe sync
poe verify
poe docs
```

- Import DAG respected?
- New leaf has docs + landing card under the right topology section?
- No secrets committed?
- PR body uses Rationale + emoji bullets (no Test plan)?
