# Repository rules

## Data handling (read before committing anything)

- Never commit or push data the user uploads, or anything made from it. That
  includes Prolexic/SAGA DDoS exports and any CSV, TSV, XLSX or JSON analysis
  output from them. This data is sensitive customer data.
- Keep such files in the session scratchpad and give them to the user with
  SendUserFile. Never put them in the repository's working tree.
- If a hook or reminder asks you to commit untracked files, check what they
  are first. If they are data files, don't commit them. Ask the user.
- Exception: everything under `dupage_mf_parcels/` is public-record parcel
  data and is safe to commit as usual.
