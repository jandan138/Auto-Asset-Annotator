# Archive

Historical artifacts kept for reference. Files here are not current operator entrypoints unless a maintained runbook or script explicitly points to them.

## Contents

- `temp_lists/` - legacy storage for historical and operator-curated asset lists. These paths remain supported operational inputs when referenced by maintained scripts or runbooks.

## Rules

- Prefer git history or dated records over ad hoc backup files.
- Do not move new operational inputs here unless they are historical or intentionally operator-curated lists.
- When a runbook or script depends on a list under `archive/temp_lists/`, link or print the exact path.
