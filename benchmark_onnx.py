from pathlib import Path
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

model_dir = Path(r"C:\Users\Shreya\lockedin\models\all-MiniLM-L6-v2-onnx")
tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
session = ort.InferenceSession(str(model_dir / "model.onnx"), providers=["CPUExecutionProvider"])

print("Providers:", session.get_providers())
print("Inputs:", [(x.name, x.shape, x.type) for x in session.get_inputs()])
print("Outputs:", [(x.name, x.shape, x.type) for x in session.get_outputs()])

texts = [
    "Finish my machine learning assignment",
    "Gradient Descent Explained",
    "MrBeast Shorts"
]

def embed(text):
    tokens = tokenizer(text, return_tensors="np", padding=True, truncation=True)
    feed = {
        "input_ids": tokens["input_ids"].astype(np.int64),
        "attention_mask": tokens["attention_mask"].astype(np.int64),
        "token_type_ids": tokens["token_type_ids"].astype(np.int64)
    }
    hidden = session.run(None, feed)[0]
    mask = tokens["attention_mask"][..., None]
    embedding = (hidden * mask).sum(axis=1) / mask.sum(axis=1)
    embedding = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)
    return embedding[0]

embeddings = [embed(t) for t in texts]

print("\nEmbedding dimensions:", [len(x) for x in embeddings])

goal = embeddings[0]
for text, emb in zip(texts[1:], embeddings[1:]):
    similarity = float(np.dot(goal, emb))
    print(f'Goal ? "{text}": {similarity:.4f}')
