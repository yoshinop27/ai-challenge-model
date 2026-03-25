import io
import pytest
import torch
from PIL import Image
from backend.model import SoilClassifier, LABELS


def make_dummy_image() -> bytes:
    img = Image.new("RGB", (224, 224), color=(100, 80, 60))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture(scope="module")
def model():
    return SoilClassifier()


def test_labels_are_correct():
    assert LABELS == ["bad", "average", "good"]


def test_model_loads(model):
    assert model is not None


def test_output_shape(model):
    img_bytes = make_dummy_image()
    logits = model.forward_logits(img_bytes)
    assert logits.shape == (1, 3)


def test_predict_returns_label_and_confidence(model):
    img_bytes = make_dummy_image()
    result = model.predict(img_bytes)
    assert "label" in result
    assert result["label"] in LABELS
    assert "confidence" in result
    assert set(result["confidence"].keys()) == {"bad", "average", "good"}


def test_confidence_sums_to_one(model):
    img_bytes = make_dummy_image()
    result = model.predict(img_bytes)
    total = sum(result["confidence"].values())
    assert abs(total - 1.0) < 1e-5


def test_confidence_values_are_floats(model):
    img_bytes = make_dummy_image()
    result = model.predict(img_bytes)
    for v in result["confidence"].values():
        assert isinstance(v, float)
