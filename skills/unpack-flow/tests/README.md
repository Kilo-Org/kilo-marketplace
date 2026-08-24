# UnpackFlow minimal archive test fixtures

`generate-minimal-public-suite.sh` creates a small, redistributable suite entirely from synthetic files generated during the test. It contains no customer files, personal paths, application payloads or historical archive names. The suite covers ZIP, TAR.GZ, nested ZIP, Unicode paths, inert `.EXE` payloads, a multipart RAR SFX first volume, an expected missing-volume failure, and contextual same-name output.

Generate and verify:

```bash
bash tests/generate-minimal-public-suite.sh
pwsh -NoProfile -File tests/test-minimal-public-suite.ps1
bash tests/test-minimal-public-suite.sh
```

The generated SFX `part01.exe` is archive data. Tests must never execute it. `MANIFEST.txt` inside the suite documents every case, and the adjacent `.sha256` file records artifact integrity.

Native Linux acceptance uses `/data/unpack-flow-testcases` by default. Set `UNPACK_FLOW_TEST_ROOT` to use another isolated path. Copy the compact ZIP and checksum there, then run `bash tests/run-native-linux-minimal.sh`; it creates a temporary result below the selected root and removes it after acceptance unless `UNPACK_FLOW_KEEP_TEST_OUTPUT=1` is set. Large optional suites must remain outside the default path and run only for explicit performance or additional compatibility checks.
