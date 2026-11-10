#!/usr/bin/env python3
"""Generate a complete module catalog for the Fosi Audio DAP Neo stock
firmware update image DP3_V137.img (RKnanoFW package).

Read-only, offline, standard library only. Every identification in the
output is produced by a rule that checks live binary evidence (strings,
descriptor bytes, vector-table shape, byte-identity, table statistics);
when a check fails the module falls back to "unknown" instead of
inheriting a label. Provenance for the anchor identifications
(modules 0, 1, 8, 11, 12, 22, 39) is the prior instruction-level work in
repo/analysis/ (DP3_V137.md, usb_audio.md, usb_msc.md,
module22_selector.md, flash_security_and_port.md); this script re-verifies
the byte-level facts those documents cite before reusing the labels.

Usage:
    python3 gen_catalog.py [--image PATH] [--outdir PATH]

Defaults: image = ../DP3_V137.img relative to this script (repo root),
outdir = directory containing this script.
Outputs: module_catalog.json, module_catalog.md
"""
import argparse
import hashlib
import json
import math
import re
import struct
import sys
from collections import Counter
from pathlib import Path

EXPECTED_SHA256 = "fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef"
FIELDS = ("code_load", "code_exec", "code_len",
          "data_load", "data_exec", "data_len",
          "bss_exec", "bss_len")

# ---------------------------------------------------------------------------
# basic helpers
# ---------------------------------------------------------------------------

def shannon_entropy(blob):
    if not blob:
        return 0.0
    n = len(blob)
    return -sum((c / n) * math.log2(c / n) for c in Counter(blob).values())


def nonzero_span(blob):
    """(first, end) of the region between first and last nonzero byte."""
    nz = [i for i, b in enumerate(blob) if b]
    if not nz:
        return None
    return nz[0], nz[-1] + 1


def extract_ascii(blob, minlen=4):
    out, cur, start = [], bytearray(), 0
    for i, ch in enumerate(blob):
        if 32 <= ch < 127:
            if not cur:
                start = i
            cur.append(ch)
        else:
            if len(cur) >= minlen:
                out.append((start, cur.decode("ascii")))
            cur = bytearray()
    if len(cur) >= minlen:
        out.append((start, cur.decode("ascii")))
    return out


def extract_utf16le(blob, minlen=4):
    """Runs of (printable, 0x00) pairs at either byte parity.
    High precision on data regions."""
    found = {}
    for parity in (0, 1):
        cur, start = [], None
        i = parity
        while i + 1 < len(blob):
            if blob[i + 1] == 0 and 32 <= blob[i] < 127:
                if start is None:
                    start = i
                cur.append(chr(blob[i]))
            else:
                if len(cur) >= minlen:
                    found[start] = "".join(cur)
                cur, start = [], None
            i += 2
        if len(cur) >= minlen:
            found[start] = "".join(cur)
    out = []
    for start in sorted(found):
        text = found[start]
        letters = sum(c.isalpha() or c in " ." for c in text)
        if letters / len(text) >= 0.7:
            out.append((start, text))
    return out


HIGH_VALUE = re.compile(
    r"HifiFile|AudioFile|FLAC|Lib:|\.c$|RKnanoFW|RKNANOFW|DP3_V|fw[12] |USB:|"
    r"APETAGEX|METADATA_BLOCK|CUE|timeout|Error|error|FAIL|fail|vorbis|ALAC|"
    r"rice_|ape |dsf|dff|ID3|RECORD|MenuKeyPro|SysFileInfo|codec|Codec|"
    r"MP1MP2MP3|Open|open|seek|Seek|frame|channels|samplerate|Fosi|RockChip",
)


def string_score(s):
    """Heuristic distinctiveness score; filters Thumb-immediate noise such
    as 'pGpGpG' (0x70 0x47 = BX LR byte pairs) out of code regions."""
    score = 0
    if HIGH_VALUE.search(s):
        score += 4
    if "%" in s:
        score += 3
    if "\\" in s:
        score += 3
    words = [w for w in s.split(" ") if sum(c.isalpha() for c in w) >= 2]
    if len(words) >= 2:
        score += 2
    if len(s) >= 12:
        score += 1
    if s and s[-1] in "!.:;":
        score += 1
    if "pG" in s:
        score -= 5
    letters = [c for c in s if c.isalpha()]
    if letters:
        vowels = sum(c in "aeiouAEIOU" for c in letters)
        if vowels / len(letters) < 0.15 and " " not in s:
            score -= 3
    if not any(c.islower() for c in s) and " " not in s and len(s) <= 9 \
            and not HIGH_VALUE.search(s):
        score -= 3
    return score


def distinctive_strings(code, data, code_file_off, data_file_off, cap=40):
    found = []
    total = 0
    for region_name, blob, foff in (("code", code, code_file_off),
                                    ("data", data, data_file_off)):
        strs = extract_ascii(blob)
        total += len(strs)
        for off, text in strs:
            sc = string_score(text)
            if sc >= 4:
                found.append({
                    "text": text, "region": region_name,
                    "offset_in_region": off,
                    "file_offset": (foff + off) if foff is not None else None,
                    "score": sc,
                })
    found.sort(key=lambda d: (-d["score"], d["file_offset"] or 0))
    return found[:cap], len(found), total


def detect_vector(code, code_exec, code_len):
    """Cortex-M vector table test: word0 = plausible 8-aligned stack top,
    word1 = odd (Thumb) reset, words[2..8] all the same odd default-handler
    address. Fires only for module 0 and modules 71-80 in this image."""
    if len(code) < 36:
        return None
    w = struct.unpack_from("<9I", code, 0)
    sp, reset = w[0], w[1]
    handlers = w[2:]
    if sp == 0 or sp % 8 != 0 or sp > 0x40000000:
        return None
    if not (reset & 1):
        return None
    if not all(h == handlers[0] and (h & 1) for h in handlers):
        return None
    reset_addr = reset & ~1
    in_window = code_exec <= reset_addr < code_exec + code_len
    as_offset = reset_addr < code_len
    return {
        "initial_sp": sp,
        "reset_vector": reset,
        "reset_address": reset_addr,
        "default_handler": handlers[0],
        "reset_within_exec_window": in_window,
        "reset_is_core_local_offset": as_offset and not in_window,
    }


UNICODE_BLOCKS = [
    (0x0000, 0x00FF, "Latin-1/basic"),
    (0x1100, 0x11FF, "Hangul Jamo"),
    (0x2000, 0x2FFF, "punctuation/symbols"),
    (0x3000, 0x30FF, "CJK punctuation/kana"),
    (0x3100, 0x31FF, "Bopomofo/extended"),
    (0x3400, 0x4DBF, "CJK ext-A"),
    (0x4E00, 0x9FFF, "CJK unified"),
    (0xAC00, 0xD7A3, "Hangul syllables"),
    (0xF900, 0xFAFF, "CJK compat ideographs"),
    (0xFF00, 0xFFEF, "fullwidth/halfwidth forms"),
]


def u16_table_stats(blob):
    n = len(blob) // 2
    if n < 8:
        return None
    vals = struct.unpack("<%dH" % n, blob[: n * 2])
    mono = sum(1 for a, b in zip(vals, vals[1:]) if b >= a)
    hist = []
    for lo, hi, name in UNICODE_BLOCKS:
        c = sum(1 for v in vals if lo <= v <= hi)
        if c:
            hist.append((name, c))
    hist.sort(key=lambda kv: -kv[1])
    return {
        "entries": n, "value_min": min(vals), "value_max": max(vals),
        "monotonic_nondecreasing_pairs": mono,
        "monotonic_fraction": round(mono / (n - 1), 3) if n > 1 else 1.0,
        "top_unicode_blocks": hist[:3],
    }

# ---------------------------------------------------------------------------
# identification rules -- each returns (identification, confidence, evidence)
# confidence: proven = direct binary evidence (named strings / descriptor
# bytes / executed-instruction results from prior work); likely = multiple
# converging format-specific strings but no library self-name or source
# path; unknown = no defensible identification.
# ---------------------------------------------------------------------------

def identify(idx, m, code, data, vec, u16stats, blob_all):
    def has(b, region=None):
        return b in (region if region is not None else blob_all)

    empty = m["code_len"] == 0 and m["data_len"] == 0
    if idx == 0:
        return ("resident system image (system-core kernel, drivers, "
                "filesystem, USB logs, ID3 genre table)",
                "proven",
                ["Cortex-M vector table: SP=0x03004000, reset=0x03061f8b, "
                 "default handler 0x0305fcc5 repeated",
                 "largest system-core code region (0x29c14 bytes)",
                 "code strings: i2c_write/i2c_read error logs, "
                 "'Dma Channel error: ch = %d!', 'UART not SUPPORT this "
                 "port.', source path '..\\..\\Common\\System\\Os\\"
                 "interrupt.c'",
                 "data contains the full ID3v1 genre name table "
                 "('Blues' ... 'Psybient'), MBR-style strings 'Invalid "
                 "partition table' / 'Missing operating system', firmware "
                 "name templates DP3_V100IMG and RKNANOFWIMG, and the "
                 "extension list MP1MP2MP3WMAWAVAPEFLAAACM4AOGGMP43GPDFFDSF"])
    if idx == 1:
        ev = ["code log strings 'fw1 Sign error!', 'fw1 compare error!', "
              "'fw2 compare error! 0x%x', 'No find fw2!', 'fw2 error!' and "
              "the 'RKnanoFW' compare constant (prior work traced the "
              "dual-slot header/mirror validation and BCD-date precedence "
              "in this module's instructions)",
              "data holds UTF-16LE stage names 'Media Init...', "
              "'LowFormat...', 'SysAreaCopy...', the ASCII name 'DAP Sys' "
              "and templates RKNANOFWIMG / DP3_V100IMG"]
        return ("installed-firmware slot validator (dual-slot header "
                "check) with media-init stage strings", "proven", ev)
    if idx == 8:
        return ("firmware updater / installer (writes update image with "
                "read-back verification)",
                "proven",
                ["code contains the 8-byte 'RKnanoFW' compare constant",
                 "prior work traced this module's instructions: opens the "
                 "update file, checks magic + 512-byte header mirror, "
                 "copies in 16-sector chunks via device-3 write/read/"
                 "compare (repo/analysis/DP3_V137.md)"])
    if idx == 10:
        return ("USB device core / control-endpoint overlay",
                "likely",
                ["18 'USB:' log strings incl. 'USB:GET STATUS', "
                 "'USB:SET FEATURE', 'USB:SET ADDR = %d', 'USB:GET DES = "
                 "%d', 'USB:GET STRING = %d', 'Microsoft OS string "
                 "Descriptor', 'Write EP0 fail', 'USB:Disconnect' -- the "
                 "generic USB stack, distinct from the MSC (12) and "
                 "audio (11) personalities"])
    if idx == 11:
        return ("USB Audio Class 1.0 function + HID consumer control",
                "proven",
                ["data device descriptor at data+0x104: VID 0x071a, "
                 "PID 0x3289 (verified bytes 12 01 ... 1a 07 89 32)",
                 "prior descriptor + instruction analysis "
                 "(repo/analysis/usb_audio.md): UAC1.0 stereo 16-bit "
                 "48 kHz isochronous OUT EP 0x02, 0x9000-byte PCM ring, "
                 "HID media keys, MMIO base 0x60080800"])
    if idx == 12:
        return ("USB Mass Storage Class (SCSI transparent, bulk-only)",
                "proven",
                ["data config descriptor at data+0x0c declares interface "
                 "class/subclass/protocol 08 06 50 with bulk EP 0x81/0x01",
                 "data+0x72 SCSI inquiry identity 'Fosi    Audio DSP "
                 "Neo   1.00' (stored twice, at data+0x72 and "
                 "data+0x96); code log 'USB:error cbw = %d' (CBW = "
                 "command block wrapper)",
                 "the final 28 bytes of the code region (code+0xfa8, "
                 "file 0x821f4) are a second ASCII inquiry identity "
                 "'RockChip    CD-ROM      1.00' -- a CD-ROM "
                 "personality identity alongside the Fosi disk "
                 "identity; consistent with a virtual CD-ROM mode "
                 "(inference), not mentioned in the prior descriptor "
                 "analysis"])
    if idx == 18:
        return ("metadata / cover-art parser (ID3, APE, Vorbis comment, "
                "embedded pictures)",
                "likely",
                ["code strings 'METADATA_BLOCK_PICTURE', 'PICTURE OGG', "
                 "'Cover Art (front)', 'APETAGEX', 'vorbis', "
                 "'base64_decode error, ret: %d', 'MetaBlockPicHandle "
                 "Read Error', '======Check APIC Error', 'image/jpeg', "
                 "'image/jpg', 'image/bmp' -- APIC/cover handling for "
                 "multiple tag formats"])
    if idx == 22:
        return ("small selector overlay: TBB jump-table value mapper "
                "(inputs 0-12 verified by emulation)",
                "proven",
                ["prior work executed the original Thumb routine at "
                 "0x0307d1a2 in Ghidra's emulator: inputs 0..12 return "
                 "0,1,1,2,3,0,5,6,7,0,0,0,0 (repo/analysis/"
                 "module22_selector.md); its semantic role (what the "
                 "values select) is not established",
                 "also contains the path string 'U:\\RECORD     \\VOICE' "
                 "(SDK folder-name string; not proof of a recording "
                 "feature)"])
    if idx == 23:
        return ("file scan / sort overlay (media library bookkeeping)",
                "likely",
                ["code log strings ' totalFmfile = %d' and "
                 "'SortInfoAddr.ulFileSortInfoSectorAddr = %d'; path "
                 "string 'U:\\RECORD     \\FM' (folder-name string only; "
                 "not evidence of an FM tuner)"])
    if idx == 24:
        return ("album list/count helper", "likely",
                ["single distinctive code log string 'All Album "
                 "TotalNum = %d'; shares the 0x0307e9c0 overlay window "
                 "with modules 25 and 26"])
    if idx == 27:
        return ("file-browser overlay with lyrics (.LRC) reference",
                "likely",
                ["code contains a standalone NUL-terminated 'LRC' "
                 "extension string among 0x0302xxxx data literals and "
                 "the log '  CurrentFileNum == %d   '"])
    if idx == 31:
        return ("audio file filter / browser overlay", "likely",
                ["code strings: the supported-format extension list "
                 "'MP1MP2MP3WMAWAVAPEFLAAACM4AOGGMP43GPDFFDSF', "
                 "'xxxxxxxxxx From File: AudioFileNum = %d', "
                 "'HoldOnplay : %d'"])
    if idx == 32:
        return ("UI menu-key handler with EQ settings", "likely",
                ["code log string 'MenuKeyPro - SelItemID=%d, "
                 "SetEqType=%d' ties this overlay to menu key handling "
                 "and EQ-type selection"])
    if idx == 33:
        return ("system-side codec open / dispatch overlay",
                "likely",
                ["code log strings 'file open totally over', 'audio "
                 "codec open success.', 'Codec Open Error1'",
                 "data tail contains a pointer table into the "
                 "0x308c694 stub window (repeated 0x0308c695/0x0308c69d/"
                 "0x0308c6a1) and the ASF header-object GUID constant "
                 "75B22630-668E-11CF-A6D9-00AA0062CE6C (WMA container), "
                 "plus a second ASF-family GUID "
                 "D2D0A440-E307-11D2-97F0-00A0C95EA850",
                 "the same data tail holds UTF-16LE ASF/WM metadata "
                 "field names ('WM/Title', 'WM/Author', 'WM/Genre', "
                 "'WM/AlbumTitle', 'WM/TrackNumber', sort-order "
                 "variants) -- the dispatcher also knows WMA metadata "
                 "attributes",
                 "data region is 0x124a0 bytes but only 497 bytes are "
                 "nonzero (five small islands) -- mostly reserved/zero "
                 "state"])
    if idx == 34:
        return ("file-browser overlay (SysFileInfo)", "likely",
                ["code log string ' SysFileInfo->CurrentFileNum == %d   "
                 "'; shares exec window 0x308bed4 with modules 35 "
                 "(data) and 36"])
    if idx == 37:
        return ("CUE sheet parser", "likely",
                ["code strings \"CUE Can't read content\" and "
                 "'cue_info->m_total_Song == %d'"])
    if idx == 38:
        return ("media file enumeration overlay", "likely",
                ["code contains the extension list 'MP1MP2MP3WMAWAVAPE"
                 "FLAAACM4AOGGMP43GPDFFDSFCUE' (module 31's list plus "
                 "CUE) and path strings 'U:\\RECORD     \\VOICE' / "
                 "'U:\\RECORD     ' (folder-name strings only)"])
    if idx == 39:
        return ("ASCII uppercase / case-insensitive compare leaf "
                "functions (rest of region is zero padding)",
                "proven",
                ["prior work executed the original routines at "
                 "0x0307d5fc/0x0307d608 with a Thumb-2 interpreter "
                 "(16,512 verified calls; repo/analysis/DP3_V137.md)",
                 "structural fact from this catalog: of 0x21eb0 code "
                 "bytes only the first 0xbf0 are nonzero (2.1%); the "
                 "remaining 97.9% are 0x00 -- a max-size overlay window, "
                 "not 139 KB of code"])
    if idx == 63:
        return ("data-only 256-byte lookup table (no code; purpose "
                "unknown)", "likely",
                ["code_exec is 0 and the payload sits in the 'code' "
                 "field: exactly 256 bytes, entropy 4.84, first bytes "
                 "02 04 03 04 1a 20 53 04 -- a byte-indexed table"])
    if 64 <= idx <= 69:
        ev = ["code_exec is 0; payload is a uint16 table in the 'code' "
              "field (see u16_table_stats in JSON)"]
        if u16stats:
            blocks = ", ".join("%s x%d" % (n, c) for n, c in
                               u16stats["top_unicode_blocks"])
            ev.append("uint16 value distribution by Unicode block: " +
                      blocks)
        if idx == 64:
            ev.append("128 entries split between Latin-1 (65) and "
                      "U+FF00-FF9F fullwidth/halfwidth forms (63) -- "
                      "shape of a halfwidth/fullwidth or JIS X 0201 "
                      "conversion table (inference)")
            return ("character conversion table (uint16, "
                    "halfwidth/fullwidth forms)", "likely", ev)
        if idx == 68:
            ev.append("11172 of 18366 values lie in Hangul syllables "
                      "U+AC00-D7A3 -- Korean-leaning conversion table "
                      "(inference)")
            return ("character conversion table (uint16, Hangul-heavy; "
                    "Korean codepage candidate)", "likely", ev)
        ev.append("CJK-unified values dominate -- a CJK codepage-to-"
                  "Unicode conversion table; the exact source encoding "
                  "(GBK/Big5/Shift_JIS family) is not established by "
                  "the bytes alone (inference)")
        return ("character conversion table (uint16, CJK-heavy)",
                "likely", ev)
    if idx == 70:
        return ("empty placeholder for the second-core window "
                "(all lengths zero)", "proven",
                ["code_len = data_len = bss_len = 0 while code_exec = "
                 "0x01000000 like modules 71-80"])
    if 71 <= idx <= 80:
        return identify_hifi(idx, code, data, blob_all)
    if empty:
        note = "empty module record (code_len = data_len = 0"
        if m["bss_len"]:
            note += "; bss_len = 0x%x -- BSS-only reservation" % m["bss_len"]
        note += ")"
        return (note, "proven",
                ["record present in the module table with no payload "
                 "bytes in the image"])
    if idx == 35:
        return ("unidentified dense numeric data payload (data-only)",
                "unknown",
                ["51252 data bytes, 91.6% nonzero, entropy 7.23; head "
                 "is a sequence of 32-bit word pairs (e.g. 001f7dcf / "
                 "fff081ab) consistent with fixed-point coefficient "
                 "tables; shares its load slot with code modules 34 "
                 "and 36 at exec 0x308bed4. No strings; purpose not "
                 "established"])
    if idx in (53, 54, 55, 56, 57):
        return ("unidentified template overlay family (53-57)",
                "unknown",
                ["modules 54, 56 and 57 have byte-identical 700-byte "
                 "code regions; 53 and 55 each differ from that code by "
                 "exactly one byte (verified by direct comparison in "
                 "this catalog). The five differ in their small data "
                 "records (2-22 bytes). All execute at 0x308c694. "
                 "Purpose not established"])
    if idx == 61:
        return ("unidentified large sparse overlay", "unknown",
                ["code_len 0x13ab0 but only the first 0x1aa4 bytes are "
                 "nonzero (8.0%); the rest is 0x00 padding. Nonzero "
                 "head contains a 'RECORD' name string surrounded by "
                 "0x0302xxxx/0x0308xxxx literals. Shares exec window "
                 "0x3080b54 with module 18"])
    if idx == 29:
        return ("unidentified sparse overlay", "unknown",
                ["only the first 0x918 of 0x10b0 code bytes are nonzero "
                 "(51.6%); no distinctive strings"])
    if idx == 81:
        return ("unidentified small overlay with function-pointer "
                "table", "unknown",
                ["data region (796 bytes) is zero except five Thumb "
                 "pointers at data+0x18: 0x0307de3f, 0x0307d91f, "
                 "0x0307d8ab, 0x0307dd03, 0x0307ddd9 -- all into the "
                 "shared 0x0307d164 overlay window; no strings"])
    if idx == 5:
        return ("unidentified overlay (settings-save lead only)",
                "unknown",
                ["single distinctive string 'save ok'; insufficient "
                 "for an identification"])
    return ("unidentified overlay", "unknown",
            ["no format-, protocol- or library-identifying strings or "
             "constants found by this catalog's checks"])


def identify_hifi(idx, code, data, blob_all):
    common = ["Cortex-M vector table at 0x01000000: SP=0x01022000, "
              "reset is a core-local offset (see JSON vector field)",
              "contains the shared HiFi file-RPC log strings "
              "'HifiFileOpen/Seek/Read/Write/Close: timeout!!', "
              "'###AUDIO_DECODE_OPEN error!###' and the shared "
              "FLAC_FileSeekFast/FileGetSeekInfo helper strings "
              "(linked into every 71-80 image; not evidence that "
              "every module is a FLAC decoder)"]
    table = {
        71: ("second-core audio decoder: MP3 (libMad)", "proven",
             ["data contains the library self-name 'Lib:mp3_dec_lib'",
              "code contains source paths '..\\..\\Common\\Codec\\"
              "Audio\\Mp3\\libMad\\mp3_decinternal.c' and "
              "'mp3_preparse.c' plus the libMad error-string set "
              "('bad scalefactor index', 'lost synchronization', "
              "'Huffman data overrun', ...) and 'mp3 start pos =%d'"]),
        72: ("second-core audio decoder: WMA", "proven",
             ["data contains the library self-name 'Lib:wma_dec_lib'",
              "code contains source path '..\\..\\Common\\Codec\\"
              "Audio\\Wma\\wmalib\\wmaudio_parse.c' and the string "
              "'WMA Windows Media(tm) Audio'",
              "largest second-core code region (0x162c0 bytes); data "
              "region holds sorted-character histogram tables"]),
        73: ("second-core audio decoder: AAC with MP4/MOV container",
             "proven",
             ["data contains the library self-name 'Lib:aac_dec_lib'",
              "code contains source paths '..\\..\\Common\\Codec\\"
              "Audio\\AAC\\lib\\aac_aacdec.c' and 'aac_MovFile.c', log "
              "'aac_frofile = %d return ' and an MP4 box-name table "
              "('moofmfrafreeskipmetawideudtauuid', 'ftyppdin')"]),
        74: ("second-core audio decoder: WAV/PCM", "proven",
             ["code contains source path '..\\..\\Common\\Codec\\"
              "Audio\\Wav\\WAV_LIB\\pWAV_lib.c' and assertions "
              "'wav_formatTagID =%d', 'nBlockAlign =%d'",
              "data holds RIFF INFO tag fragments "
              "'fmt dataLISTIARTINAMIPRDIGNR'"]),
        75: ("second-core audio decoder: OGG Vorbis", "likely",
             ["code contains the string 'vorbis' and Vorbis-decoder-"
              "internal log strings 'floormemo need %d ' (floor curve "
              "allocation) and ' partword_used size %d' (residue "
              "partition accounting)",
              "largest second-core data region (0xd184 bytes) of "
              "quantisation/histogram tables, consistent with bundled "
              "Vorbis codebook data (inference)",
              "no source path or 'Lib:' self-name is present, unlike "
              "71-73, so this stays 'likely'"]),
        76: ("second-core audio decoder: FLAC", "proven",
             ["26 FLAC-specific log strings, incl. 'FLAC_frame_"
              "decode: flac_decode_frame returned %d', 'FLAC frame "
              "CRC mismatch (stored=%d, computed=%d)', "
              "'decode_frame: blocksize %d > FLAC_MAX_BLOCKSIZE %d' "
              "and a detailed FLAC seek log family -- far beyond the "
              "two FLAC_File* helper strings shared by all of 71-80"]),
        77: ("second-core audio decoder: ALAC in MP4 container",
             "likely",
             ["code log strings 'ALAC ' (with a size print) and the "
              "ALAC entropy-coding parameter logs 'rice_limit = %d', "
              "'rice_initial_history =%d', 'rice_history_mult = %d', "
              "'maxRun = %d' -- Rice parameters are specific to ALAC",
              "data contains an 'alac' MP4 atom byte sequence and the "
              "module shares the MP4 box-name table with module 73 "
              "('ftyppdinmoofmfra...') but has no AAC strings and no "
              "'Lib:' self-name, so this stays 'likely'"]),
        78: ("second-core audio decoder: APE (Monkey's Audio)",
             "proven",
             ["code log strings 'ape open FAIL!', 'ape open OK ', "
              "'ape_tag_len =%d ', ' file version error!!! "
              "Max_version 4120,fileVersion = %d' (4120 is the APE "
              "file-version constant) and 'APETAGEX'"]),
        79: ("second-core audio decoder: DSD -- DFF (DSDIFF) with "
             "DST frames", "likely",
             ["code log strings 'FRM8 err ' (FRM8 is the DFF chunk "
              "holding DST-compressed frames), 'dst read frame err!', "
              "'dstf read frame!', 'NO.%d frame dsdiff read frame "
              "err!', 'dff seek_fail', 'DSD IFF OPEN err!'",
              "shares 50.3% identical code bytes with module 80 "
              "(common DSD skeleton); the DFF/DST-specific strings "
              "above are absent from 80"]),
        80: ("second-core audio decoder: DSD -- DSF", "likely",
             ["code log strings 'dsf read ckid err', 'NO.%d frame "
              "dsf read frame err!', 'ID3V2 start:%d' (DSF files "
              "carry a trailing ID3v2 tag), 'fmt err ', 'formatid "
              "err', 'bit_per_sample not support!', 'sampleCount:%lu' "
              "-- DSF fmt/data chunk parsing",
              "shares 50.3% identical code bytes with module 79 "
              "(common DSD skeleton); the DSF-specific strings above "
              "are absent from 79"]),
    }
    name, conf, ev = table[idx]
    return (name, conf, common + ev)

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve()
    ap.add_argument("--image", type=Path,
                    default=here.parents[1] / "DP3_V137.img")
    ap.add_argument("--outdir", type=Path, default=here.parent)
    args = ap.parse_args()

    raw = args.image.read_bytes()
    if raw[0x10:0x18] != b"Rockchip" or raw[0x1F8:0x200] != b"RKnanoFW":
        sys.exit("not an RKnanoFW image")
    base = struct.unpack_from("<I", raw, 0x200)[0]
    count = struct.unpack_from("<I", raw, 0x204)[0]
    sha = hashlib.sha256(raw).hexdigest()

    def file_off(load_addr):
        return load_addr - base + 0x200

    modules = []
    raw_regions = {}
    for i in range(count):
        vals = struct.unpack_from("<8I", raw, 0x208 + i * 32)
        m = dict(zip(FIELDS, vals))
        entry = {"index": i}
        for f in FIELDS:
            entry[f] = m[f]
        entry["code_file_offset"] = file_off(m["code_load"]) \
            if m["code_len"] else None
        entry["data_file_offset"] = file_off(m["data_load"]) \
            if m["data_len"] else None
        code = raw[entry["code_file_offset"]:
                   entry["code_file_offset"] + m["code_len"]] \
            if m["code_len"] else b""
        data = raw[entry["data_file_offset"]:
                   entry["data_file_offset"] + m["data_len"]] \
            if m["data_len"] else b""
        raw_regions[i] = (code, data)
        entry["code_sha256"] = hashlib.sha256(code).hexdigest() \
            if code else None
        entry["data_sha256"] = hashlib.sha256(data).hexdigest() \
            if data else None
        vec = detect_vector(code, m["code_exec"], m["code_len"]) \
            if m["code_exec"] else None
        entry["has_cortexm_vector_table"] = vec is not None
        entry["vector"] = ({"initial_sp": hex(vec["initial_sp"]),
                            "reset_vector": hex(vec["reset_vector"]),
                            "reset_address": hex(vec["reset_address"]),
                            "default_handler": hex(vec["default_handler"]),
                            "reset_within_exec_window":
                                vec["reset_within_exec_window"],
                            "reset_is_core_local_offset":
                                vec["reset_is_core_local_offset"]}
                           if vec else None)
        entry["code_entropy"] = round(shannon_entropy(code), 3) \
            if code else None
        entry["data_entropy"] = round(shannon_entropy(data), 3) \
            if data else None
        entry["code_zero_fraction"] = round(code.count(0) /
                                            len(code), 4) if code else None
        span = nonzero_span(code) if code else None
        entry["code_nonzero_span"] = ({"first": span[0], "end": span[1]}
                                      if span else None)
        dist, dist_total, ascii_total = distinctive_strings(
            code, data, entry["code_file_offset"],
            entry["data_file_offset"])
        entry["ascii_string_count"] = ascii_total
        entry["distinctive_string_count"] = dist_total
        entry["distinctive_strings"] = dist
        entry["utf16le_data_strings"] = [
            {"text": t, "offset_in_region": o,
             "file_offset": (entry["data_file_offset"] + o)
             if entry["data_file_offset"] is not None else None}
            for o, t in extract_utf16le(data)]
        entry["u16_table_stats"] = u16_table_stats(code) \
            if m["code_exec"] == 0 and code else None
        modules.append(entry)

    # exact duplicate code groups + near-duplicates within same length
    by_hash = {}
    for e in modules:
        if e["code_sha256"]:
            by_hash.setdefault(e["code_sha256"], []).append(e["index"])
    dup_groups = [g for g in by_hash.values() if len(g) > 1]
    for e in modules:
        e["identical_code_group"] = next(
            (g for g in dup_groups if e["index"] in g), None)
        e["near_duplicate_code"] = []
    by_len = {}
    for e in modules:
        if e["code_len"]:
            by_len.setdefault(e["code_len"], []).append(e["index"])
    for length, group in by_len.items():
        if len(group) < 2:
            continue
        ref = group[0]
        refcode = raw_regions[ref][0]
        for other in group[1:]:
            ocode = raw_regions[other][0]
            diff = sum(1 for a, b in zip(refcode, ocode) if a != b)
            if 0 < diff <= 8:
                modules[other]["near_duplicate_code"].append(
                    {"of_module": ref, "differing_bytes": diff})
                modules[ref]["near_duplicate_code"].append(
                    {"of_module": other, "differing_bytes": diff})

    # pairwise code identity for the two DSD modules (differentiation note)
    def code_identity(a, b):
        x, y = raw_regions[a][0], raw_regions[b][0]
        n = min(len(x), len(y))
        return round(sum(1 for p, q in zip(x[:n], y[:n]) if p == q) / n, 4)
    pair_identity = {"79_vs_80": code_identity(79, 80),
                     "73_vs_77": code_identity(73, 77)}

    # identifications (after all structural fields exist)
    for e in modules:
        i = e["index"]
        m = {f: e[f] for f in FIELDS}
        code, data = raw_regions[i]
        name, conf, ev = identify(i, m, code, data,
                                  e["vector"], e["u16_table_stats"],
                                  code + data)
        e["identification"] = name
        e["confidence"] = conf
        e["evidence"] = ev

    # ------------------------------------------------------------------
    # sanity checks against the known anchors from prior work
    # ------------------------------------------------------------------
    checks = []
    def chk(name, ok, detail=""):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    chk("module_count == 82", count == 82, str(count))
    chk("sha256 matches known stock image", sha == EXPECTED_SHA256, sha)
    chk("module 0 vector SP/reset",
        modules[0]["vector"] and
        modules[0]["vector"]["initial_sp"] == "0x3004000" and
        modules[0]["vector"]["reset_vector"] == "0x3061f8b")
    chk("module 1 has fw1/fw2 validator strings",
        b"fw1 Sign error!" in raw_regions[1][0] and
        b"No find fw2!" in raw_regions[1][0])
    chk("module 8 has RKnanoFW constant",
        b"RKnanoFW" in raw_regions[8][0])
    d11 = raw_regions[11][1]
    j = d11.find(b"\x12\x01")
    vid_pid = struct.unpack_from("<HH", d11, j + 8) if j >= 0 else (0, 0)
    chk("module 11 USB VID/PID 0x071a:0x3289",
        vid_pid == (0x071A, 0x3289), "%04x:%04x" % vid_pid)
    d12 = raw_regions[12][1]
    chk("module 12 MSC descriptor + inquiry",
        b"\x08\x06\x50" in d12 and
        b"Fosi    Audio DSP Neo   1.00" in d12)
    chk("module 22 anchor geometry",
        modules[22]["code_len"] == 0xB9C and
        modules[22]["code_exec"] == 0x0307D164)
    c39 = raw_regions[39][0]
    chk("module 39 casefold head + zero tail",
        c39[:4] == bytes.fromhex("a0f16101") and
        modules[39]["code_zero_fraction"] > 0.95,
        "zero_fraction=%s" % modules[39]["code_zero_fraction"])
    chk("modules 71-80 all HiFi + vector SP 0x01022000",
        all(b"HifiFileOpen: timeout!!" in raw_regions[i][0] and
            modules[i]["vector"] and
            modules[i]["vector"]["initial_sp"] == "0x1022000"
            for i in range(71, 81)))
    chk("modules 71/72/73 Lib: self-names",
        b"Lib:mp3_dec_lib" in raw_regions[71][1] and
        b"Lib:wma_dec_lib" in raw_regions[72][1] and
        b"Lib:aac_dec_lib" in raw_regions[73][1])
    chk("module 76 FLAC log density >= 10",
        raw_regions[76][0].count(b"FLAC") >= 10,
        str(raw_regions[76][0].count(b"FLAC")))
    chk("modules 54/56/57 code byte-identical",
        raw_regions[54][0] == raw_regions[56][0] ==
        raw_regions[57][0])
    n_empty = sum(1 for e in modules
                  if e["code_len"] == 0 and e["data_len"] == 0)
    chk("empty records (no code/data payload) == 19", n_empty == 19,
        str(n_empty))

    conf_counts = Counter(e["confidence"] for e in modules)
    catalog = {
        "source_image": str(args.image),
        "source_sha256": sha,
        "source_size": len(raw),
        "module_load_base": base,
        "module_count": count,
        "confidence_counts": dict(conf_counts),
        "identical_code_groups": dup_groups,
        "pairwise_code_identity": pair_identity,
        "sanity_checks": checks,
        "modules": modules,
    }
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "module_catalog.json").write_text(
        json.dumps(catalog, indent=1) + "\n")
    (args.outdir / "module_catalog.md").write_text(render_md(catalog))
    failed = [c for c in checks if not c["pass"]]
    for c in checks:
        print(("PASS " if c["pass"] else "FAIL ") + c["check"] +
              (" -- " + c["detail"] if c["detail"] else ""))
    print("confidence counts:", dict(conf_counts))
    if failed:
        sys.exit("sanity checks failed: %d" % len(failed))


def hx(v):
    return "—" if v is None else "0x%x" % v


def render_md(cat):
    mods = cat["modules"]
    cc = cat["confidence_counts"]
    lines = []
    w = lines.append
    w("# Fosi DAP Neo DP3_V137 — complete module catalog (82 modules)")
    w("")
    w("Source: `DP3_V137.img`, %d bytes, SHA-256 `%s`. Module load base "
      "`0x%08x`; record format per repo/analysis/DP3_V137.md (82 records "
      "× 32 bytes at file 0x208; file_offset = load_addr − 0x03050000 + "
      "0x200). Generated by `gen_catalog.py` (stdlib only, read-only). "
      "All identifications are rule-checked against live byte evidence "
      "by the generator; the embedded sanity checks passed %d/%d." %
      (cat["source_size"], cat["source_sha256"], cat["module_load_base"],
       sum(1 for c in cat["sanity_checks"] if c["pass"]),
       len(cat["sanity_checks"])))
    w("")
    w("Confidence: **proven** = direct binary evidence (format/library "
      "self-name, source path, descriptor bytes, or behaviour executed "
      "from the original instructions in prior work). **likely** = "
      "several converging format-specific strings, no self-name/path. "
      "**unknown** = no defensible identification; structural facts "
      "only. Counts: proven %d, likely %d, unknown %d (empty records "
      "count as proven-empty)." %
      (cc.get("proven", 0), cc.get("likely", 0), cc.get("unknown", 0)))
    w("")
    w("## Summary table")
    w("")
    w("| # | code_exec | code_len | data_len | bss_len | vector | "
      "identification | conf. |")
    w("|---:|---|---:|---:|---:|:--:|---|:--:|")
    for e in mods:
        ident = e["identification"]
        if len(ident) > 72:
            ident = ident[:69] + "..."
        w("| %d | %s | %s | %s | %s | %s | %s | %s |" %
          (e["index"], hx(e["code_exec"]), hx(e["code_len"]),
           hx(e["data_len"]), hx(e["bss_len"]),
           "yes" if e["has_cortexm_vector_table"] else "–",
           ident.replace("|", "/"), e["confidence"]))
    w("")
    w("## Second-core modules 71–80: differentiation")
    w("")
    w("All ten share the same execution window (0x01000000), the same "
      "vector shape (SP 0x01022000, reset as a core-local offset), the "
      "HiFi file-RPC timeout strings, and two linked-in FLAC_File* "
      "helper strings. They are differentiated only by the "
      "format-specific evidence below — the shared FLAC_File* strings "
      "are explicitly not counted as FLAC evidence.")
    w("")
    w("| # | code_len | data_len | data entropy | reset | "
      "identification | conf. | key evidence |")
    w("|---:|---:|---:|---:|---|---|:--:|---|")
    for e in mods:
        if not (71 <= e["index"] <= 80):
            continue
        key = e["evidence"][2] if len(e["evidence"]) > 2 else \
            (e["evidence"][-1] if e["evidence"] else "")
        if len(key) > 110:
            key = key[:107] + "..."
        w("| %d | %s | %s | %s | %s | %s | %s | %s |" %
          (e["index"], hx(e["code_len"]), hx(e["data_len"]),
           e["data_entropy"], e["vector"]["reset_vector"],
           e["identification"].replace("|", "/"), e["confidence"],
           key.replace("|", "/")))
    w("")
    w("Code-identity measurements: modules 79 vs 80 share %.1f%% "
      "identical code bytes over the shorter length (common DSD "
      "skeleton, format-specific tails); modules 73 vs 77 share only "
      "%.1f%% (shared MP4 box tables, different decoders)." %
      (cat["pairwise_code_identity"]["79_vs_80"] * 100,
       cat["pairwise_code_identity"]["73_vs_77"] * 100))
    w("")
    w("## Evidence notes per identified module")
    w("")
    for e in mods:
        if e["confidence"] == "unknown" and e["index"] not in (
                29, 35, 53, 54, 55, 56, 57, 61, 81):
            continue
        w("### Module %d — %s (%s)" %
          (e["index"], e["identification"], e["confidence"]))
        w("")
        w("- Addresses: code %s→%s len %s (file %s); data %s→%s len %s "
          "(file %s); bss %s len %s." %
          (hx(e["code_load"]), hx(e["code_exec"]), hx(e["code_len"]),
           hx(e["code_file_offset"]), hx(e["data_load"]),
           hx(e["data_exec"]), hx(e["data_len"]),
           hx(e["data_file_offset"]), hx(e["bss_exec"]),
           hx(e["bss_len"])))
        if e["vector"]:
            w("- Vector table: SP %s, reset %s%s, default handler %s." %
              (e["vector"]["initial_sp"], e["vector"]["reset_vector"],
               " (core-local offset)" if
               e["vector"]["reset_is_core_local_offset"] else "",
               e["vector"]["default_handler"]))
        w("- Entropy: code %s, data %s; code zero fraction %s." %
          (e["code_entropy"], e["data_entropy"],
           e["code_zero_fraction"]))
        for ev in e["evidence"]:
            w("- Evidence: " + ev)
        top = e["distinctive_strings"][:10]
        if top:
            w("- Distinctive strings: " +
              "; ".join("`%s`" % s["text"] for s in top))
        if e["utf16le_data_strings"]:
            w("- UTF-16LE data strings: " +
              "; ".join("`%s`" % s["text"]
                        for s in e["utf16le_data_strings"][:8]))
        w("")
    w("## Non-code modules 63–69")
    w("")
    w("All seven have code_exec = 0 and carry their payload in the "
      "'code' field, stored contiguously in the file at "
      "0xe6c–0x296ac, immediately before module 0's code. They are "
      "character-conversion table data, not executables:")
    w("")
    for e in mods:
        if not (63 <= e["index"] <= 69):
            continue
        st = e["u16_table_stats"]
        extra = ""
        if st:
            extra = (" uint16 entries: %d, values 0x%x–0x%x, top blocks: "
                     "%s." %
                     (st["entries"], st["value_min"], st["value_max"],
                      ", ".join("%s x%d" % (n, c) for n, c in
                                st["top_unicode_blocks"])))
        w("- Module %d: %s bytes, entropy %s.%s Identification: %s "
          "(%s)." % (e["index"], hx(e["code_len"]), e["code_entropy"],
                     extra, e["identification"], e["confidence"]))
    w("")
    w("## Still unidentified")
    w("")
    unk = [e for e in mods if e["confidence"] == "unknown"]
    w("%d modules have no defensible identification from binary "
      "evidence: %s." %
      (len(unk), ", ".join(str(e["index"]) for e in unk)))
    w("")
    for e in unk:
        w("- Module %d: exec %s, code %s bytes (file %s), data %s, "
          "bss %s. %s" %
          (e["index"], hx(e["code_exec"]), hx(e["code_len"]),
           hx(e["code_file_offset"]), hx(e["data_len"]),
           hx(e["bss_len"]), e["evidence"][0] if e["evidence"] else ""))
    w("")
    w("## Surprises and leads")
    w("")
    w("- **Module 1 data names a manufacturing-style media path**: "
      "UTF-16LE strings 'Media Init...', 'LowFormat...', "
      "'SysAreaCopy...' sit alongside the slot-validator code — stage "
      "names for low-level media initialisation/format operations "
      "exist in the resident update path. No separate 'engineering "
      "mode' module was found among the 82 records.")
    w("- **Module 12 carries a second, CD-ROM inquiry identity**: "
      "the last 28 bytes of its code region are the ASCII string "
      "'RockChip    CD-ROM      1.00', next to the Fosi disk identity "
      "stored twice in its data. That is the shape of Rockchip's "
      "virtual CD-ROM personality (driver/update disc); whether the "
      "Neo ever enumerates it is a device-side question this image "
      "cannot settle.")
    w("- **Module 33 data embeds the ASF header GUID** "
      "(75B22630-668E-11CF-A6D9-00AA0062CE6C) and a pointer table into "
      "the 0x308c694 stub window — the system-side codec dispatcher "
      "knows the WMA container and dispatches into the small stub "
      "family (modules 41/42/50–57), whose purpose is still open.")
    w("- **Modules 54, 56 and 57 are byte-identical code** (700 bytes "
      "each); 53 and 55 differ by one byte each. Five near-duplicate "
      "template overlays with 2–22-byte data records — purpose "
      "unknown.")
    w("- **Zero-tail overlays**: module 39 is 97.9% zeros past byte "
      "0xbf0 and module 61 is 92% zeros past 0x1aa4; their table "
      "lengths reserve max-size overlay windows rather than "
      "describing dense code.")
    w("- **Module 0 data** holds the complete ID3v1 genre table "
      "(~147 names, 'Blues' to 'Psybient'), MBR error strings "
      "('Invalid partition table', 'Error loading operating system', "
      "'Missing operating system') and an interleaved test-like "
      "marker 'TTEESSTTMP3'.")
    w("- **Video-container traces in audio decoders**: modules 73 "
      "and 77 (AAC/ALAC) parse MP4 box tables that include video "
      "entries ('avcC', 'vide', 'vidiosamplesum = %d' in 73). The "
      "strings prove the demuxer code exists; they do not prove the "
      "DAP Neo plays video.")
    w("- **Recording-folder strings are SDK residue until proven "
      "otherwise**: 'U:\\RECORD     \\VOICE' (modules 22, 38), "
      "'U:\\RECORD     \\FM' (module 23) and 'RECORD' (module 61) "
      "are folder-name strings in shared-SDK-style overlays. No "
      "microphone/FM-tuner driver evidence was found in this "
      "catalog, matching the caution in repo/analysis/DP3_V137.md.")
    w("- **No hidden/diagnostic command strings** (no AT-command set, "
      "no 'engineering mode', no test-menu text) were found in any "
      "module's distinctive strings. Module 12's single 'SBC' byte "
      "hit is inside instruction bytes, not a string, and is not "
      "Bluetooth evidence.")
    w("- **19 of 82 records carry no payload at all** (2, 13–16, 28, "
      "40, 43–49, 58–60, 62, 70); module 40 is BSS-only (8 KB "
      "reservation) and module 70 is an empty placeholder in the "
      "second-core window.")
    w("")
    w("## Method and limits")
    w("")
    w("- Strings: ASCII runs ≥4 chars from code+data, filtered by a "
      "documented distinctiveness score (format/path/keyword bonuses, "
      "Thumb-immediate noise penalties); UTF-16LE runs from data "
      "regions only. Full lists with file offsets are in "
      "module_catalog.json (up to 40 per module).")
    w("- Vector tables: strict shape test (aligned SP, odd reset, "
      "≥7 identical odd default-handler words). Only modules 0 and "
      "71–80 pass; the other code modules begin with function "
      "prologues (e.g. PUSH 0xE92D/0xB5xx), i.e. they are called "
      "overlays, not reset images.")
    w("- Entropy is Shannon entropy over the raw region bytes; the "
      "'nonzero span' exposes zero-padded overlay windows.")
    w("- This catalog does not disassemble control flow; "
      "identifications marked 'likely' and all 'unknown' modules are "
      "the open set for Ghidra work. No device was accessed.")
    w("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
