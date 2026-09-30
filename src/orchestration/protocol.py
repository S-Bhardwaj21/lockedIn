import json

def build_request(goal, activity):
    return {"goal": str(goal), "activity": str(activity)}

def validate_request(payload):
    if not isinstance(payload, dict):
        raise ValueError("Request must be a JSON object.")
    if not isinstance(payload.get("goal"), str):
        raise ValueError("Missing or invalid 'goal'.")
    if not isinstance(payload.get("activity"), str):
        raise ValueError("Missing or invalid 'activity'.")
    return payload["goal"], payload["activity"]

def build_response(alignment, worker="local-worker"):
    return {"alignment": float(alignment), "worker": worker}

def encode(payload):
    return json.dumps(payload).encode("utf-8")

def decode(data):
    return json.loads(data.decode("utf-8"))