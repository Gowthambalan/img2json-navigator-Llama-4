import base64
from pathlib import Path
import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

def encode_image(path: Path) -> str:
    with path.open("rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    suffix = path.suffix.lstrip(".").lower()
    if suffix not in {"jpg", "jpeg", "png", "tif", "tiff", "webp"}:
        raise ValueError(f"Unsupported image type: .{suffix}")
    return f"data:image/{suffix};base64,{b64}"

def extract_one(path: Path, llm) -> dict:
    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": (
    "Extract all key fields from the document and return them in JSON format. "
    "Make sure to include reference numbers, document codes, stamped numbers, and any metadata in the corners. "
    "If any field is unclear or missing, return null for that field."
)
            },
            {"type": "image_url", "image_url": {"url": encode_image(path)}},
        ]
    )
    model_with_structure = llm.with_structured_output(method="json_mode")
    return model_with_structure.invoke([message])
