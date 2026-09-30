from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json
import sys
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "models" / "minilm_qaihub_float" / "minilm_v2-onnx-float" / "minilm_v2.onnx"
PORT = 8765

sys.path.insert(0, str(ROOT / "src"))

from orchestration.protocol import validate_request, build_response

tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
session = ort.InferenceSession(str(MODEL), providers=["CPUExecutionProvider"])

def embed(text):
    tokens = tokenizer(
        text,
        padding="max_length",
        truncation=True,
        max_length=128,
        return_tensors="np",
    )
    inputs = {
        "input_ids": tokens["input_ids"].astype(np.int32),
        "attention_mask": tokens["attention_mask"].astype(np.int32),
    }
    return session.run(None, inputs)[0][0]

def alignment(goal, activity):
    goal_embedding = embed(goal)
    activity_embedding = embed(activity)
    return float(np.dot(goal_embedding, activity_embedding))

class WorkerHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/infer":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            goal, activity = validate_request(payload)
            score = alignment(goal, activity)
            response = build_response(score)

            body = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

            print(f">>> Worker inference: {score:.6f}")

        except Exception as exc:
            body = json.dumps({"error": str(exc)}).encode("utf-8")
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, format, *args):
        return

def main():
    print("=" * 64)
    print("LOCKEDIN — REMOTE AI WORKER")
    print("=" * 64)
    print(f"Model: {MODEL}")
    print(f"Providers: {session.get_providers()}")
    print(f"Listening: http://127.0.0.1:{PORT}/infer")
    print()
    print("Waiting for orchestration requests...")

    server = HTTPServer(("0.0.0.0", PORT), WorkerHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n>>> Worker stopped.")
    finally:
        server.server_close()

if __name__ == "__main__":
    main()