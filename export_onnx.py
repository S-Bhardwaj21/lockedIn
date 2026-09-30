from optimum.onnxruntime import ORTModelForFeatureExtraction
from transformers import AutoTokenizer
from pathlib import Path

model_dir = Path(r"C:\Users\Shreya\lockedin\models\all-MiniLM-L6-v2")
onnx_dir = Path(r"C:\Users\Shreya\lockedin\models\all-MiniLM-L6-v2-onnx")
onnx_dir.mkdir(parents=True, exist_ok=True)

tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
model = ORTModelForFeatureExtraction.from_pretrained(
    str(model_dir),
    export=True
)
model.save_pretrained(str(onnx_dir))
tokenizer.save_pretrained(str(onnx_dir))

print("ONNX model exported to:", onnx_dir)
print("Files:")
for p in sorted(onnx_dir.iterdir()):
    print(" ", p.name)
