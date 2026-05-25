import json
from pathlib import Path
from collections import defaultdict

RESULTS_PATH = Path(__file__).parent / "results.json"
NETWORK_ERROR_KEYWORDS = ["timed out", "connection error", "rate limit", "429"]


def is_network_error(error_msg: str) -> bool:
    if not error_msg:
        return False
    return any(kw in error_msg.lower() for kw in NETWORK_ERROR_KEYWORDS)


def analyze():
    with open(RESULTS_PATH, encoding="utf-8") as f:
        results = json.load(f)

    total = len(results)
    passed = sum(1 for r in results if r["pass"])
    
    real_failures = [r for r in results if not r["pass"] and not is_network_error(r.get("error", ""))]
    network_failures = [r for r in results if not r["pass"] and is_network_error(r.get("error", ""))]

    print("\n" + "=" * 60)
    print("ERROR ANALYSIS REPORT")
    print("=" * 60)
    print(f"\nOverall pass rate    : {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"Real failures        : {len(real_failures)}")
    print(f"Network failures     : {len(network_failures)} (infra issue, not agent)")

    # Adjusted rate excluding network noise
    valid_tests = total - len(network_failures)
    if valid_tests > 0:
        adjusted_rate = passed / valid_tests * 100
        print(f"Adjusted pass rate   : {passed}/{valid_tests} ({adjusted_rate:.1f}%) — excluding network errors")

    # Category breakdown
    category_stats = defaultdict(lambda: {"pass": 0, "real_fail": 0, "network_fail": 0})
    for r in results:
        if r["pass"]:
            category_stats[r["category"]]["pass"] += 1
        elif is_network_error(r.get("error", "")):
            category_stats[r["category"]]["network_fail"] += 1
        else:
            category_stats[r["category"]]["real_fail"] += 1

    print("\nBreakdown by Category:")
    print("-" * 40)
    for cat, stats in sorted(category_stats.items()):
        total_cat = sum(stats.values())
        print(f"  {cat:<20} {stats['pass']}/{total_cat} pass | {stats['real_fail']} real fail | {stats['network_fail']} net fail")

    # Real failures details (the ones we actually need to fix)
    if real_failures:
        print(f"\n🔴 Real Failures ({len(real_failures)}) — These need investigation:")
        print("-" * 40)
        for r in real_failures:
            print(f"\n  [{r['id']}] {r['input'][:55]}")
            print(f"  Expected tools : {r['expected_tools']}")
            print(f"  Tools used     : {r['tools_used']}")
            print(f"  Response       : {r['response'][:120]}")

    # Network failures (just FYI)
    if network_failures:
        print(f"\n⚠️  Network Failures ({len(network_failures)}) — Not agent issues:")
        print("-" * 40)
        for r in network_failures:
            print(f"  [{r['id']}] {r['input'][:55]}")

    # Missing tools (only from real failures)
    if real_failures:
        print("\n🔧 Missing Tools (real failures only):")
        print("-" * 40)
        missing = defaultdict(int)
        for r in real_failures:
            for t in r["expected_tools"]:
                if t not in r["tools_used"]:
                    missing[t] += 1
        for tool, count in sorted(missing.items(), key=lambda x: -x[1]):
            print(f"  {tool:<25} missed {count} time(s)")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    analyze()