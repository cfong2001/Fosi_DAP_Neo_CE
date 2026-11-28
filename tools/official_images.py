"""Verified official Fosi DAP Neo (DP3) update images.

One table for every tool that must recognise an official image. Each entry
was downloaded from https://support.fosiaudio.com/products/dapneo and checked
against its Rockchip CRC. The images are not stored in the repository.
"""

# SHA-256 -> (version, header build date)
OFFICIAL = {
    'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef': ('V137', '2026-10-22'),
    '4713a2eb4b523d49ad003ac2df159c1c596339aef1a9a060e6ea6bbbf18e1332': ('V155', '2026-11-02'),
    '96e9216a9877a4ff5d845f47319abeef0b57f11309877fa8af1628bd612724ed': ('V161', '2026-11-12'),
    'ff201296d01f485dc7379c2505b95c78451955d49a06e9e5418ce072fe877aa0': ('V162', '2026-11-17'),
}

BY_VERSION = {version: sha for sha, (version, _date) in OFFICIAL.items()}
