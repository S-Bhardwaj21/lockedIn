from sentence_transformers import SentenceTransformer
from pathlib import Path

output = Path(r"C:\Users\Shreya\lockedin\models\all-MiniLM-L6-v2")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
model.save(str(output))
print("Model saved to:", output)
