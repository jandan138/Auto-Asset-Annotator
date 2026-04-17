# Documentation Tail Cleanup

## Research / Investigation

- Audited the main maintained docs against the current code paths in `src/auto_asset_annotator/`.
- Compared user-facing docs, development docs, and internal `.claude` maintenance docs against the current API backend and DLC upgrades.
- Identified a short list of concrete residual mismatches rather than doing another broad documentation rewrite.

## Design Decisions

- Keep this pass narrowly focused on stale details that could mislead users or maintainers today.
- Prefer wording corrections over structural rewrites.
- Treat historical docs as historical unless a current-facing statement was genuinely misleading.

## Code Changes

- Corrected asset-list guidance so docs no longer imply `data.asset_list_file` is a declared config field.
- Updated examples to show that `--asset_list_file` still relies on `--input_dir` for relative asset paths.
- Clarified where checked-in YAML values differ from code-level dataclass fallbacks.
- Aligned development/guidebook docs with the current loader order and `list_assets()` traversal behavior.
- Updated internal `.claude` docs so maintainer-facing guidance references:
  - `parse_structured_text_enhanced()` as the main parser path
  - `tests/` as the canonical test surface
  - current API/DLC maintenance surfaces

## Testing

- Verified the edited statements against:
  - `src/auto_asset_annotator/config/settings.py`
  - `src/auto_asset_annotator/main.py`
  - `src/auto_asset_annotator/core/model.py`
  - `src/auto_asset_annotator/core/prompt.py`
  - `src/auto_asset_annotator/utils/file.py`
- No runtime code changed in this pass.

## Open Issues

- Historical docs under `docs/changes/` still describe older project states by design.
- There may still be lower-priority internal docs outside the touched set that are not worth updating unless they become active maintenance surfaces again.
