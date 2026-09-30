from pathlib import Path
import sys
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parent.parent
FLOAT_MODEL = ROOT / "models" / "minilm_qaihub_float" / "minilm_v2-onnx-float" / "minilm_v2.onnx"
W8A8_MODEL = ROOT / "models" / "minilm_v2_w8a8" / "minilm_v2-onnx-w8a8" / "minilm_v2.onnx"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SCALE = 0.0017485282151028514
ZERO_POINT = 134

TESTS = [
    ("Finish my ML assignment", "Watch a Gradient Descent lecture"),
    ("Finish my ML assignment", "Watch MrBeast Shorts"),
    ("Finish my ML assignment", "Read a machine learning research paper"),
    ("Scroll Instagram", "Scroll Instagram"),
    ("Scroll Instagram", "Open Instagram Reels"),
    ("Listen to music", "Listen to Spotify"),
    ("Finish Python homework", "Open WhatsApp"),
]

def load_session(path):
    return ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])

def prepare_inputs(tokenizer, text):
    encoded = tokenizer(
        text,
        padding="max_length",
        truncation=True,
        max_length=128,
        return_tensors="np",
    )
    return {
        "input_ids": encoded["input_ids"].astype(np.int32),
        "attention_mask": encoded["attention_mask"].astype(np.int32),
    }

def run_model(session, inputs):
    return session.run(["embeddings"], inputs)[0]

def dequantize(values):
    return (values.astype(np.float32) - ZERO_POINT) * SCALE

def cosine(a, b):
    a = np.asarray(a, dtype=np.float32).reshape(-1)
    b = np.asarray(b, dtype=np.float32).reshape(-1)
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    if denominator == 0:
        return 0.0
    return float(np.dot(a, b) / denominator)

def main():
    print("=" * 72)
    print("LOCKEDIN — MiniLM Float vs W8A8 Parity Benchmark")
    print("=" * 72)
    print(f"ONNX Runtime: {ort.__version__}")
    print(f"Float model:  {FLOAT_MODEL}")
    print(f"W8A8 model:   {W8A8_MODEL}")
    print(f"W8A8 scale:   {SCALE}")
    print(f"W8A8 zero:    {ZERO_POINT}")
    print()

    if not FLOAT_MODEL.exists():
        print("ERROR: Float model not found.")
        sys.exit(1)

    if not W8A8_MODEL.exists():
        print("ERROR: W8A8 model not found.")
        sys.exit(1)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    float_session = load_session(FLOAT_MODEL)
    w8a8_session = load_session(W8A8_MODEL)

    print("Float providers:", float_session.get_providers())
    print("W8A8 providers: ", w8a8_session.get_providers())
    print()

    results = []

    for goal, activity in TESTS:
        goal_inputs = prepare_inputs(tokenizer, goal)
        activity_inputs = prepare_inputs(tokenizer, activity)

        float_goal = run_model(float_session, goal_inputs)
        float_activity = run_model(float_session, activity_inputs)

        w8_goal_raw = run_model(w8a8_session, goal_inputs)
        w8_activity_raw = run_model(w8a8_session, activity_inputs)

        w8_goal = dequantize(w8_goal_raw)
        w8_activity = dequantize(w8_activity_raw)

        goal_embedding_cosine = cosine(float_goal, w8_goal)
        activity_embedding_cosine = cosine(float_activity, w8_activity)

        float_alignment = cosine(float_goal, float_activity)
        w8_alignment = cosine(w8_goal, w8_activity)

        goal_max_error = float(np.max(np.abs(float_goal - w8_goal)))
        activity_max_error = float(np.max(np.abs(float_activity - w8_activity)))

        results.append({
            "goal": goal,
            "activity": activity,
            "goal_embedding_cosine": goal_embedding_cosine,
            "activity_embedding_cosine": activity_embedding_cosine,
            "float_alignment": float_alignment,
            "w8_alignment": w8_alignment,
            "goal_max_error": goal_max_error,
            "activity_max_error": activity_max_error,
        })

    print("-" * 72)
    print("RESULTS")
    print("-" * 72)

    for r in results:
        print(f"\nGoal:     {r['goal']}")
        print(f"Activity: {r['activity']}")
        print(f"  Goal embedding cosine:      {r['goal_embedding_cosine']:.8f}")
        print(f"  Activity embedding cosine:  {r['activity_embedding_cosine']:.8f}")
        print(f"  Float alignment:             {r['float_alignment']:.8f}")
        print(f"  W8A8 alignment:              {r['w8_alignment']:.8f}")
        print(f"  Goal max absolute error:     {r['goal_max_error']:.8f}")
        print(f"  Activity max absolute error: {r['activity_max_error']:.8f}")

    embedding_cosines = []
    alignment_deltas = []

    for r in results:
        embedding_cosines.append(r["goal_embedding_cosine"])
        embedding_cosines.append(r["activity_embedding_cosine"])
        alignment_deltas.append(
            abs(r["float_alignment"] - r["w8_alignment"])
        )

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"Minimum embedding cosine: {min(embedding_cosines):.8f}")
    print(f"Mean embedding cosine:    {np.mean(embedding_cosines):.8f}")
    print(f"Maximum alignment delta:  {max(alignment_deltas):.8f}")
    print(f"Mean alignment delta:     {np.mean(alignment_deltas):.8f}")
    print("=" * 72)

if __name__ == "__main__":
    main()