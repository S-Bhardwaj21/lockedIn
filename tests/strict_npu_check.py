import sys
from pathlib import Path
import onnxruntime as ort

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "models" / "minilm_qaihub_float" / "minilm_v2-onnx-float" / "minilm_v2.onnx"

def main():
    print("=" * 72)
    print("LOCKEDIN — STRICT NPU CHECK")
    print("=" * 72)
    print("Model:", MODEL)
    print("ONNX Runtime:", ort.__version__)
    print("Available providers:", ort.get_available_providers())
    print()

    if "QNNExecutionProvider" not in ort.get_available_providers():
        print("FAIL: QNNExecutionProvider is unavailable.")
        print("LOCKEDIN refuses to fall back to CPU.")
        sys.exit(2)

    options = ort.SessionOptions()
    options.add_session_config_entry(
        "session.disable_cpu_ep_fallback",
        "1",
    )

    try:
        session = ort.InferenceSession(
            str(MODEL),
            sess_options=options,
            providers=["QNNExecutionProvider"],
            provider_options=[
                {
                    "backend_type": "htp",
                }
            ],
        )
    except Exception as exc:
        print("FAIL: Could not initialize QNN HTP session.")
        print("CPU fallback is disabled.")
        print()
        print(exc)
        sys.exit(3)

    providers = session.get_providers()
    print("Session providers:", providers)

    if "QNNExecutionProvider" not in providers:
        print("FAIL: QNN provider was not attached.")
        print("LOCKEDIN refuses CPU execution.")
        sys.exit(4)

    print()
    print("PASS: QNN Execution Provider initialized.")
    print("PASS: HTP backend requested.")
    print("PASS: CPU fallback disabled.")
    print()
    print("LOCKEDIN is configured for strict NPU execution.")

if __name__ == "__main__":
    main()