import io
import pytest
from PIL import Image
from backend.model import DualClassifier


def make_dummy_image() -> bytes:
    img = Image.new("RGB", (224, 224), color=(100, 80, 60))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture(scope="module")
def model():
    return DualClassifier()


def test_model_loads(model):
    assert model is not None


def test_output_shape(model):
    img_bytes = make_dummy_image()
    result = model.predict(img_bytes)
    assert "soil" in result
    assert "moisture" in result


def test_predict_returns_label_and_confidence(model):
    img_bytes = make_dummy_image()
    result = model.predict(img_bytes)
    assert "label" in result["soil"]
    assert "confidence" in result["soil"]
    assert result["soil"]["label"] in result["soil"]["confidence"]
    assert "label" in result["moisture"]
    assert "confidence" in result["moisture"]
    assert result["moisture"]["label"] in result["moisture"]["confidence"]


def test_confidence_sums_to_one(model):
    img_bytes = make_dummy_image()
    result = model.predict(img_bytes)
    soil_total = sum(result["soil"]["confidence"].values())
    moisture_total = sum(result["moisture"]["confidence"].values())
    assert abs(soil_total - 1.0) < 1e-5
    assert abs(moisture_total - 1.0) < 1e-5


def test_confidence_values_are_floats(model):
    img_bytes = make_dummy_image()
    result = model.predict(img_bytes)
    for v in result["soil"]["confidence"].values():
        assert isinstance(v, float)
    for v in result["moisture"]["confidence"].values():
        assert isinstance(v, float)
