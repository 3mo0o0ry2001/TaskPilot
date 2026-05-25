import json
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from agent import Agent

DATASET_PATH = Path(__file__).parent / "dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.json"

DELAY_BETWEEN_TESTS = 4
RETRY_DELAY = 10
NETWORK_ERROR_KEYWORDS = ["timed out", "connection error", "rate limit", "429"]


def extract_tools_used(tracer) -> list[str]:
    return [
        e["data"]["tool_name"]
        for e in tracer.events
        if e["type"] == "tool_call"
    ]


def check_tools_match(used: list, expected: list) -> bool:
    return all(tool in used for tool in expected)


def is_network_error(error_msg: str) -> bool:
    return any(kw in error_msg.lower() for kw in NETWORK_ERROR_KEYWORDS)


def run_single_test(tc: dict) -> dict:
    agent = Agent()
    try:
        response = agent.run(tc["input"])
        tools_used = extract_tools_used(agent.tracer)
        tools_ok = check_tools_match(tools_used, tc["expected_tools"])
        return {
            "id": tc["id"],
            "category": tc["category"],
            "input": tc["input"],
            "expected_tools": tc["expected_tools"],
            "tools_used": tools_used,
            "tools_match": tools_ok,
            "response": response,
            "expected_behavior": tc["expected_behavior"],
            "pass": tools_ok,
            "error": None
        }
    except Exception as e:
        return {
            "id": tc["id"],
            "category": tc["category"],
            "input": tc["input"],
            "expected_tools": tc["expected_tools"],
            "tools_used": [],
            "tools_match": False,
            "response": f"ERROR: {str(e)}",
            "expected_behavior": tc["expected_behavior"],
            "pass": False,
            "error": str(e)
        }


def run_evals():
    with open(DATASET_PATH, encoding="utf-8") as f:
        dataset = json.load(f)

    results = []
    print(f"\nRunning {len(dataset)} test cases (1st pass)...")
    print("-" * 60)

    for tc in dataset:
        print(f"[{tc['id']}] {tc['input'][:55]}...")
        result = run_single_test(tc)
        status = "✅ PASS" if result["pass"] else "❌ FAIL"
        print(f"  {status} | Tools: {result['tools_used']}")
        results.append(result)
        time.sleep(DELAY_BETWEEN_TESTS)

    # Retry pass: re-run only network failures
    network_fails = [
        i for i, r in enumerate(results)
        if not r["pass"] and r["error"] and is_network_error(r["error"])
    ]

    if network_fails:
        print(f"\nRetrying {len(network_fails)} network failures (2nd pass)...")
        print("-" * 60)
        time.sleep(RETRY_DELAY)

        for idx in network_fails:
            tc = dataset[idx]
            print(f"[{tc['id']}] retry...")
            new_result = run_single_test(tc)
            new_result["retried"] = True
            status = "✅ PASS" if new_result["pass"] else "❌ FAIL"
            print(f"  {status} | Tools: {new_result['tools_used']}")
            results[idx] = new_result
            time.sleep(DELAY_BETWEEN_TESTS)

    # Summary
    passed = sum(1 for r in results if r["pass"])
    real_fails = [r for r in results if not r["pass"] and not (r.get("error") and is_network_error(r["error"]))]
    persistent_network_fails = [r for r in results if not r["pass"] and r.get("error") and is_network_error(r["error"])]

    print("\n" + "=" * 60)
    print(f"Final: {passed}/{len(dataset)} passed ({passed/len(dataset)*100:.1f}%)")
    print(f"  Real failures        : {len(real_fails)}")
    print(f"  Network failures     : {len(persistent_network_fails)} (after retry)")
    print("=" * 60)

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to {RESULTS_PATH}")
    return results


if __name__ == "__main__":
    run_evals()