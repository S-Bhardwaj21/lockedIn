from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
import onnxruntime as ort
from transformers import AutoTokenizer

base_dir = Path(r"C:\Users\Shreya\lockedin\models\all-MiniLM-L6-v2")
onnx_dir = Path(r"C:\Users\Shreya\lockedin\models\all-MiniLM-L6-v2-onnx")

texts = [
    "Finish my machine learning assignment",
    "Gradient Descent Explained",
    "MrBeast Shorts"
]

# Original SentenceTransformer
st_model = SentenceTransformer(str(base_dir))
st_embeddings = st_model.encode(texts, normalize_embeddings=True)

# ONNX
tokenizer = AutoTokenizer.from_pretrained(str(onnx_dir))
session = ort.InferenceSession(
    str(onnx_dir / "model.onnx"),
    providers=["CPUExecutionProvider"]
)

def onnx_embed(text):
    tokens = tokenizer(text, return_tensors="np", padding=True, truncation=True)
    feed = {
        "input_ids": tokens["input_ids"].astype(np.int64),
        "attention_mask": tokens["attention_mask"].astype(np.int64),
        "token_type_ids": tokens["token_type_ids"].astype(np.int64)
    }
    hidden = session.run(None, feed)[0]
    mask = tokens["attention_mask"][..., None].astype(np.float32)
    embedding = (hidden * mask).sum(axis=1) / mask.sum(axis=1)
    embedding = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)
    return embedding[0]

onnx_embeddings = np.array([onnx_embed(t) for t in texts])

print("=== EMBEDDING PARITY ===")
for i, text in enumerate(texts):
    cosine = float(np.dot(st_embeddings[i], onnx_embeddings[i]))
    max_diff = float(np.max(np.abs(st_embeddings[i] - onnx_embeddings[i])))
    mean_diff = float(np.mean(np.abs(st_embeddings[i] - onnx_embeddings[i])))
    print(f'\n{text}')
    print(f'Cosine similarity : {cosine:.8f}')
    print(f'Max absolute diff : {max_diff:.8f}')
    print(f'Mean absolute diff: {mean_diff:.8f}')

print("\n=== ORIGINAL SENTENCE TRANSFORMER ===")
for i in range(1, len(texts)):
    print(f'Goal -> "{texts[i]}": {np.dot(st_embeddings[0], st_embeddings[i]):.8f}')

print("\n=== ONNX ===")
for i in range(1, len(texts)):
    print(f'Goal -> "{texts[i]}": {np.dot(onnx_embeddings[0], onnx_embeddings[i]):.8f}')
