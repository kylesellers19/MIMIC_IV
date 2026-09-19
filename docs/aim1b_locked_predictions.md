# Aim 1b — locked GOLD_HOLDOUT predictions (run_2026-09-19, Phase 9.2)

Produced by `scripts/run0919_fusion_lock.py`; hashes in `docs/run_2026-09-19/results/locked_predictions.json`.

Every GOLD_HOLDOUT admission (all admissions of every subject in the 400-chart sample or the 20-chart training set) was scored by every arm and variant **before any adjudication exists**. The file below is untracked (credentialed derivative); its SHA-256 and the model-file hashes are recorded here so that, when the gold labels arrive, it can be shown that no model was tuned against them.

- File: `data/processed/gold_holdout_predictions_v1.parquet` · rows 2,865 · written 2026-09-19T21:49:43Z
- SHA-256: `0b3d9a4d256568534772adef66435986b3fda96238cf146b9593f721601e7aca`
- Columns (37): `cat|FS-A|unweighted`, `cat|FS-A|weighted`, `cat|FS-A|weighted+corrected`, `cat|FS-B|unweighted`, `cat|FS-B|weighted`, `cat|FS-B|weighted+corrected`, `cat|FS-AVAIL|unweighted`, `cat|FS-AVAIL|weighted`, `cat|FS-AVAIL|weighted+corrected`, `xgb|FS-A|unweighted`, `xgb|FS-A|weighted`, `xgb|FS-A|weighted+corrected`, `xgb|FS-B|unweighted`, `xgb|FS-B|weighted`, `xgb|FS-B|weighted+corrected`, `lgb|FS-A|unweighted`, `lgb|FS-A|weighted`, `lgb|FS-A|weighted+corrected`, `lgb|FS-B|unweighted`, `lgb|FS-B|weighted`, `lgb|FS-B|weighted+corrected`, `tfidf|U|unweighted`, `tfidf|U|weighted`, `tfidf|U|weighted+corrected`, `tfidf|M|unweighted`, `tfidf|M|weighted`, `tfidf|M|weighted+corrected`, `tfidf|S|unweighted`, `tfidf|S|weighted`, `tfidf|S|weighted+corrected`, `embed|S|lr`, `embed|S|lgbm`, `aug|FS-B+notes|unweighted`, `aug|FS-B+notes|weighted`, `aug|FS-B+notes|weighted+corrected`, `fusion|primary`, `fusion|sensitivity_FS-A`

| model file | bytes | SHA-256 |
| --- | --: | --- |
| aug_FS-B_notes_unweighted.cbm | 340,904 | `5b0ef40e300c89210394564f590b6453022252f840e8edce095fba37f4251f54` |
| aug_FS-B_notes_weighted.cbm | 165,964 | `eb54b3b96e88c28528e11d69db7d62fa4f60a7dabf7ff6933c9287bc723dbf4e` |
| cat_FS-AVAIL_unweighted.cbm | 1,357,800 | `1f8dde32d6cf3b5dc06ac1c682b9afeb9e5e85fac71b3a296cc133aa9f3fda72` |
| cat_FS-AVAIL_weighted.cbm | 1,368,872 | `7ab00cbf7098a36588e743715cf23732941358ac2fa08c90d70730c0d700d945` |
| cat_FS-A_unweighted.cbm | 2,254,728 | `143c4e9e06002f47103fa991a3299d74959a2d9034bddbf240f1c4f8db753fca` |
| cat_FS-A_weighted.cbm | 1,566,048 | `8e2e237f9837ad2cee717df2fdd62fe8b0dd7e279002832090e546c1c107c34b` |
| cat_FS-B_unweighted.cbm | 2,163,576 | `1835e0ea5bb1ce1d1d31f91b702791b5d1ed4ef84421535b2c7d21a2eadf2d2b` |
| cat_FS-B_weighted.cbm | 1,242,360 | `10b0eeb6bdb121fc111557689b73172cd6257ba6751dfafbbfffa006f6ee016f` |
| lgb_FS-A_unweighted.txt | 1,126,866 | `2db2237cce4481b13c7d015c9c3082942fdf582e41f19f1508cbd77e4edd617e` |
| lgb_FS-A_weighted.txt | 19,889 | `a20e15b29206a60ca177da7559e39f916ca89cc79b984ed91288859f4db47793` |
| lgb_FS-B_unweighted.txt | 817,943 | `f1d7f0fde99a4b3438c2189b320f3188606583f7a3c3361080a003d51c99ee9d` |
| lgb_FS-B_weighted.txt | 11,783 | `f81878dba15c556ad94b3b6e71a1bee899687698ef43f4be28ad21b7b0ad789d` |
| xgb_FS-A_unweighted.json | 4,124,129 | `a2dea04158fd21c5aee61857d62a60cb940d636288fd039d669013120cb22f89` |
| xgb_FS-A_weighted.json | 16,094,475 | `402187c0ff73ab8e4bfc1a94c60707b1220efc24bf32177847f21f08958eb4d9` |
| xgb_FS-B_unweighted.json | 3,437,993 | `606468812407330ce1ffa23175251ba7bc9a658ae23669df66bc5b8c5ac9442a` |
| xgb_FS-B_weighted.json | 16,080,870 | `9cf008d5729fc77f72a2b9ddc83a880fcd2ba06ad8114c2df89e0ccabe973c64` |

Per-arm gold prediction files:

- `notes_arm_gold.parquet`: `aa6e4dd4c57861d1d4ae41d63d9bc99845c0c35fc7fef66418886d1058a7889f`
- `notes_tfidf_gold.parquet`: `fb32514dde344452b9dbd6bd144e6b909c4d33d193d1246f7a322ae1ab4ad642`
- `structured_gold.parquet`: `9f410afee6908afabedd4ded0dd46143a03d38fc60b49456e081c3a3f771557e`
