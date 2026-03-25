import os
import io
import torch
import timm
from PIL import Image
from torchvision import transforms

LABELS = ["bad", "average", "good"]

_WEIGHTS_PATH = os.environ.get("SOIL_MODEL_WEIGHTS", "")

_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


class SoilClassifier:
    def __init__(self):
        self._model = timm.create_model("efficientnet_b0", pretrained=True, num_classes=len(LABELS))
        if _WEIGHTS_PATH and os.path.isfile(_WEIGHTS_PATH):
            state = torch.load(_WEIGHTS_PATH, map_location="cpu")
            self._model.load_state_dict(state)
        self._model.eval()

    def forward_logits(self, image_bytes: bytes) -> torch.Tensor:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = _TRANSFORM(img).unsqueeze(0)
        with torch.no_grad():
            return self._model(tensor)

    def predict(self, image_bytes: bytes) -> dict:
        logits = self.forward_logits(image_bytes)
        probs = torch.softmax(logits, dim=1).squeeze(0)
        label_idx = int(probs.argmax())
        return {
            "label": LABELS[label_idx],
            "confidence": {label: round(float(probs[i]), 6) for i, label in enumerate(LABELS)},
        }
