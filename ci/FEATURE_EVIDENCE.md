# Feature evidence ledger

`feature-evidence.json` records the current limits of the CE work under
review. It is a maintenance and review aid, not an automatic certification
of firmware. Update a feature's evidence when its implementation, tests, or
device observations change; do not infer device behavior from an image build.

Each entry records four independent levels:

- `source_review`: analysis of the relevant code and integration paths.
- `emulation`: execution of applicable code paths in a model or emulator.
- `combined_build`: integration and behavior of the composed feature set.
- `hardware`: observation on the intended physical device.

`verified` means the entry's stated behavior has evidence at that level;
`incomplete` means partial evidence; `issues_found` records a known defect;
`not_run` means the level has not been tested. Evidence must describe the
specific scope and any outstanding limitations. A status at one level does
not imply a status at another, and the ledger cannot establish flash safety.
The stock and CE displays on the configuration site are illustrations, not
emulations of processor instructions or proof of hardware behavior.

Validate the file with:

```sh
python3 ci/check_feature_evidence.py
python3 -m unittest discover -s tests -p 'test_feature_evidence.py'
```

The validator checks shape and explicit status declarations. Reviewers must
still verify the cited evidence and update the entries as work proceeds.
