from pathlib import Path
import time
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

model_dir = Path(r"C:\Users\Shreya\lockedin\models\all-MiniLM-L6-v2-onnx")
tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
session = ort.InferenceSession(str(model_dir / "model.onnx"), providers=["CPUExecutionProvider"])

text = "Finish my machine learning assignment"
tokens = tokenizer(text, return_tensors="np", padding=True, truncation=True)
feed = {
    "input_ids": tokens["input_ids"].astype(np.int64),
    "attention_mask": tokens["attention_mask"].astype(np.int64),
    "token_type_ids": tokens["token_type_ids"].astype(np.int64)
}

# Cold/session startup already happened above.
# First inference measures warm-up separately.
t0 = time.perf_counter()
session.run(None, feed)
cold_inference_ms = (time.perf_counter() - t0) * 1000

# Warm-up
for _ in range(10):
    session.run(None, feed)

times = []
for _ in range(100):
    t0 = time.perf_counter()
    session.run(None, feed)
    times.append((time.perf_counter() - t0) * 1000)

times = np.array(times)

print("=== LOCKEDIN ONNX CPU BENCHMARK ===")
print("Model: all-MiniLM-L6-v2")
print("Runtime: ONNX Runtime")
print("Execution Provider: CPUExecutionProvider")
print(f"Cold inference: {cold_inference_ms:.3f} ms")
print(f"Median:          {np.median(times):.3f} ms")
print(f"Mean:            {np.mean(times):.3f} ms")
print(f"P95:             {np.percentile(times, 95):.3f} ms")
print(f"Min:             {np.min(times):.3f} ms")
print(f"Max:             {np.max(times):.3f} ms")
print(f"Throughput:      {1000 / np.mean(times):.2f} inferences/sec")
