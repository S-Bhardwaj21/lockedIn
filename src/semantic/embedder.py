from pathlib import Path
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

MODEL_DIR = Path(r"C:\Users\Shreya\lockedin\models\minilm_qaihub_float\minilm_v2-onnx-float")
MODEL_PATH = MODEL_DIR / "minilm_v2.onnx"
TOKENIZER_PATH = Path(r"C:\Users\Shreya\lockedin\models\all-MiniLM-L6-v2")

class MiniLMEmbedder:
    def __init__(self, model_path=MODEL_PATH, tokenizer_path=TOKENIZER_PATH):
        self.tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_path))
        available = ort.get_available_providers()
        preferred = ["QNNExecutionProvider", "CPUExecutionProvider"]
        self.providers = [p for p in preferred if p in available]
        if not self.providers:
            raise RuntimeError(f"No usable ONNX Runtime provider found. Available: {available}")
        self.session = ort.InferenceSession(str(model_path), providers=self.providers)
        self.output_name = self.session.get_outputs()[0].name

    def embed(self, text):
        tokens = self.tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=128,
            return_tensors="np"
        )
        inputs = {
            "input_ids": tokens["input_ids"].astype(np.int32),
            "attention_mask": tokens["attention_mask"].astype(np.int32),
        }
        output = self.session.run([self.output_name], inputs)[0][0]
        embedding = np.asarray(output, dtype=np.float32)
        norm = np.linalg.norm(embedding)
        if norm == 0:
            raise RuntimeError("Model returned a zero embedding.")
        return embedding / norm