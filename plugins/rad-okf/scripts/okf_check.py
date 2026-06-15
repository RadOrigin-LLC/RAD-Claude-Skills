# plugins/rad-okf/scripts/okf_check.py
"""CLI: validate an OKF bundle. Read-only (no --fix in Plan 1)."""
import argparse, json, sys
import okf_bundle as ob
import okf_validate as ov

def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate an OKF bundle.")
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--stale-days", type=int, default=180)
    args = ap.parse_args(argv)

    root = ob.find_bundle_root(args.path)
    result = ov.validate(root, max_age_days=args.stale_days)

    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        for f in result["findings"]:
            print("[%s] %s: %s — %s" % (f["severity"], f["code"], f["id"], f["message"]))
        print("\n%d findings across %d files." % (len(result["findings"]), result["counts"]["files"]))

    return 1 if any(f["severity"] == "error" for f in result["findings"]) else 0

if __name__ == "__main__":
    sys.exit(main())
