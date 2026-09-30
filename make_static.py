import onnx
from pathlib import Path

src = Path(r"C:\Users\Shreya\lockedin\models\all-MiniLM-L6-v2-onnx\model.onnx")
dst = Path(r"C:\Users\Shreya\lockedin\models\all-MiniLM-L6-v2-onnx\model_static128.onnx")

model = onnx.load(str(src))

for inp in model.graph.input:
    shape = inp.type.tensor_type.shape
    for dim in shape.dim:
        if dim.dim_param or dim.dim_value == 0:
            dim.ClearField("dim_param")
            dim.dim_value = 1
    shape.dim[0].dim_value = 1
    shape.dim[1].dim_value = 128

onnx.save(model, str(dst))
print("Created:", dst)
for inp in model.graph.input:
    dims = [d.dim_value for d in inp.type.tensor_type.shape.dim]
    print(inp.name, dims)
