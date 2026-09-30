from pathlib import Path
import json
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from orchestration.protocol import build_request
from semantic.decision import classify_alignment

WINDOWS_WORKER_URL = "http://192.168.43.77:8765/infer"
ONEPLUS_WORKER_URL = "http://192.168.43.224:8765/infer"

def request_worker(url, goal, activity):
    payload = build_request(goal, activity)
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))

def orchestrate(goal, activity):
    workers = {
        "windows-worker": WINDOWS_WORKER_URL,
        "oneplus-11": ONEPLUS_WORKER_URL,
    }

    results = {}
    for name, url in workers.items():
        try:
            results[name] = {
                "status": "available",
                "response": request_worker(url, goal, activity),
            }
        except Exception as exc:
            results[name] = {
                "status": "unavailable",
                "error": str(exc),
            }

    alignment = None
    worker = None
    decision = None

    windows_result = results.get("windows-worker", {})
    response = windows_result.get("response", {})

    if windows_result.get("status") == "available":
        alignment = response.get("alignment")
        worker = "windows-worker"
        decision = classify_alignment(alignment, goal, activity)

    return {
        "goal": goal,
        "activity": activity,
        "alignment": alignment,
        "classification": decision["classification"] if decision else None,
        "reason": decision["reason"] if decision else None,
        "worker": worker,
        "workers": results,
    }

def main():
    goal = "Finish my ML assignment"
    activity = "Watch a Gradient Descent lecture"

    print("=" * 64)
    print("LOCKEDIN — ORCHESTRATION COORDINATOR")
    print("=" * 64)
    print(f"Goal:     {goal}")
    print(f"Activity: {activity}")
    print()

    result = orchestrate(goal, activity)

    print(">>> NORMALIZED ORCHESTRATION RESULT:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()