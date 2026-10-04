#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CI gate for the merged build.

A successful spcomp run only proves the merged source compiles.  It does NOT
prove the two invariants this repository actually cares about, both of which
have been broken silently in the past and are invisible to the compiler:

  1. BMAG contains exactly the intended module set.  The design is that BMAG
     holds NO SourceMod stock plugin - official plugins are the operator's own
     install (see README section 3).  A stock module merged back in would
     double-register its console commands against the official .smx, and that
     only shows up at server load time, never here.

  2. BMAG does not reference the in-merge symbols of those modules.  merge.py
     rewrites calls to a merged module's functions into direct calls to its
     prefixed symbols (mod_<module>_*); a leftover reference means a module was
     dropped from MODULES without its consumer being handled.

      python ci_check.py --sp src/scripting/BMAG/BMAG.sp --log build.log \\
                         --warn-baseline 35

Exit code 0 = all checks passed, 1 = at least one failed.
"""
import argparse
import re
import sys

# The 16 modules BMAG is supposed to be built from, in merge order.  Kept as a
# literal on purpose: deriving it from merge.py would make this check
# tautological and it would stop catching "someone edited MODULES by mistake".
EXPECTED_MODULES = [
    "admincheats", "advertisements", "adv-weapon_cleaner",
    "connectmessage", "fast_spawn",
    "missing_viewmodel_fix", "motd-fixer",
    "pause", "showhealth", "sm_noearbleed",
    "SpecDetails", "speclist", "teamjoinblocker",
    "bms_match", "textmsg_fix", "spawn_distribute",
]

# Prefixes that must never appear: these modules are external now, so nothing
# in BMAG may call into a merged copy of them.
FORBIDDEN_SYMBOL_PREFIXES = [
    "mod_adminmenu_",
    "mod_basecomm_",
    "mod_clientprefs_",
    "mod_mapchooser_",
    "mod_adminhelp_",
]

MODULE_RE = re.compile(r"^// ---- Module: (.+) ----\s*$", re.M)
SUMMARY_RE = re.compile(r"(\d+)\s+(Error|Warning)s?\s*\.")
DETAIL_RE = re.compile(r":\s+(error|warning)\s+\d+\s*:")


def read_text(path):
    """Decode a build artifact without assuming the shell's default encoding.

    The compile log is written by PowerShell, and Tee-Object / Out-File default
    to UTF-16LE on Windows PowerShell 5.1 but UTF-8 on pwsh 7.  Sniffing the BOM
    keeps the check working whichever shell produced the file.
    """
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\xff\xfe"):
        return raw.decode("utf-16")
    if raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16-be")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    return raw.decode("utf-8", "replace")


def fail(msg):
    print("FAIL: %s" % msg)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sp", required=True, help="path to the generated BMAG.sp")
    ap.add_argument("--log", help="spcomp output, to check the warning/error counts")
    ap.add_argument("--warn-baseline", type=int,
                    help="expected warning count; a different count fails the build")
    ap.add_argument("--modules", help="comma separated module list to expect "
                                      "instead of the built-in one")
    args = ap.parse_args()

    expected = EXPECTED_MODULES
    if args.modules:
        expected = [m.strip() for m in args.modules.split(",") if m.strip()]

    failures = 0

    # ---- 1. compiled at all -------------------------------------------------
    try:
        text = read_text(args.sp)
    except OSError as exc:
        fail("cannot read %s: %s" % (args.sp, exc))
        return 1

    # ---- 2. module set ------------------------------------------------------
    found = MODULE_RE.findall(text)
    if found == expected:
        print("OK   module set: %d modules, exactly as expected" % len(found))
    else:
        failures += 1
        missing = [m for m in expected if m not in found]
        extra = [m for m in found if m not in expected]
        fail("module set mismatch (found %d, expected %d)" % (len(found), len(expected)))
        if missing:
            print("     missing: %s" % ", ".join(missing))
        if extra:
            print("     unexpected: %s" % ", ".join(extra))
        if not missing and not extra:
            print("     same members but different order")
            print("     found:    %s" % ", ".join(found))
            print("     expected: %s" % ", ".join(expected))

    # ---- 3. no dangling in-merge references ---------------------------------
    leaked = []
    for prefix in FORBIDDEN_SYMBOL_PREFIXES:
        n = text.count(prefix)
        if n:
            leaked.append("%s (%d)" % (prefix, n))
    if leaked:
        failures += 1
        fail("references to modules that are no longer merged: %s" % ", ".join(leaked))
        print("     these modules must stay external; see README section 3")
    else:
        print("OK   no in-merge references to externalised modules")

    # ---- 4. compiler diagnostics -------------------------------------------
    if args.log:
        try:
            log = read_text(args.log)
        except OSError as exc:
            failures += 1
            fail("cannot read %s: %s" % (args.log, exc))
            log = None

        if log is not None:
            errors = 0
            warnings = 0
            summary_seen = False
            for n, kind in SUMMARY_RE.findall(log):
                summary_seen = True
                if kind == "Error":
                    errors = max(errors, int(n))
                else:
                    warnings = max(warnings, int(n))

            if not summary_seen and log.strip():
                # Never let an unparsed log read as "0 errors, 0 warnings": that
                # silently turns this gate into a no-op (it is how a UTF-16
                # teed log looked like a clean build the first time round).
                failures += 1
                fail("no '<n> Warnings.' / '<n> Errors.' summary in %s - "
                     "log truncated or in an unexpected format?" % args.log)
            else:
                # Cross-check the summary against the per-line diagnostics.
                counted = {"error": 0, "warning": 0}
                for kind in DETAIL_RE.findall(log):
                    counted[kind] += 1

                if errors:
                    failures += 1
                    fail("spcomp reported %d error(s)" % errors)
                else:
                    print("OK   0 compile errors")

                if summary_seen and (counted["warning"] != warnings
                                     or counted["error"] != errors):
                    failures += 1
                    fail("log summary disagrees with its own detail lines: "
                         "summary says %d error(s) / %d warning(s), "
                         "detail lines show %d / %d"
                         % (errors, warnings, counted["error"], counted["warning"]))
                elif summary_seen:
                    print("OK   log detail lines agree with the summary")

                if args.warn_baseline is None:
                    print("--   warning count: %d (no baseline given)" % warnings)
                elif warnings == args.warn_baseline:
                    print("OK   warning count matches baseline: %d" % warnings)
                else:
                    failures += 1
                    fail("warning count %d != baseline %d" % (warnings, args.warn_baseline))
                    print("     if the change is intentional, update WARN_BASELINE in")
                    print("     .github/workflows/build.yml and the baseline in README")

    print("")
    if failures:
        print("ci_check: %d check(s) FAILED" % failures)
        return 1
    print("ci_check: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
