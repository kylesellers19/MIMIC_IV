# Draft email to PhysioNet support — terminal downloads of MIMIC-IV refused

**Status:** draft for the researcher to review and send from their own account (run_2026-09-19, Phase 10.5).
Built from the repo's record (`scripts/download_mimic.sh.broken`: curl, credentials via a curl config on stdin,
endpoints under `https://physionet.org/files/mimiciv/3.1/hosp/` and `https://physionet.org/files/mimic-iv-note/2.2/note/`;
`README.md`; `docs/admin/data_inventory.md` for the checksum result). Items marked `[confirm]` come from the run-file
description of the failure and are not recorded anywhere in the repository — please confirm before sending.
No credentials, usernames or addresses appear below. Body is under 200 words.

---

**To:** contact@physionet.org
**Subject:** HTTP 403 on command-line downloads of credentialed files (MIMIC-IV 3.1, MIMIC-IV-Note 2.2)

Hello PhysioNet team,

I have approved credentialed access to MIMIC-IV v3.1 and MIMIC-IV-Note v2.2. Downloading the files through the browser works, and the files verify against the published SHA256SUMS. Command-line downloads of the same files are refused.

Our script calls `curl` on `https://physionet.org/files/mimiciv/3.1/hosp/...` and `https://physionet.org/files/mimic-iv-note/2.2/note/...`, supplying the account credentials through a curl config on stdin (curl's `user =` option, which sends a pre-emptive Basic-auth header). Every request returned HTTP 403 `[confirm]`, regardless of endpoint, user agent, or how the credentials were formatted `[confirm]`. It appears the server rejects a pre-emptive Basic header without first issuing a 401 challenge `[confirm]`. `wget` is not available on this machine `[confirm]`, so we could not compare with the wget method.

Could you tell me which command-line method is currently supported for credentialed files, or whether something on the account side blocks non-browser access? This only affects automating and re-verifying downloads; the data are otherwise fine.

Thank you for your help.

Kind regards,
[name]
