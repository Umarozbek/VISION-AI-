import os
import urllib.request

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")

MODELS = {
    "age_net.caffemodel": (
        "https://raw.githubusercontent.com/GilLevi/AgeGenderDeepLearning/"
        "master/models/age_net.caffemodel"
    ),
    "gender_net.caffemodel": (
        "https://raw.githubusercontent.com/GilLevi/AgeGenderDeepLearning/"
        "master/models/gender_net.caffemodel"
    ),
    "face_detection_yunet_2023mar.onnx": (
        "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/"
        "models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
    ),
    "face_recognition_sface_2021dec.onnx": (
        "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/"
        "models/face_recognition_sface/face_recognition_sface_2021dec.onnx"
    ),
}


def download_file(url: str, dest: str) -> None:
    print(f"Yuklanmoqda: {os.path.basename(dest)} ...")
    urllib.request.urlretrieve(url, dest)
    print(f"Tayyor: {os.path.basename(dest)}")


def ensure_models() -> bool:
    os.makedirs(MODEL_DIR, exist_ok=True)
    all_ok = True

    for filename, url in MODELS.items():
        dest = os.path.join(MODEL_DIR, filename)
        if os.path.exists(dest) and os.path.getsize(dest) > 50_000:
            continue
        try:
            download_file(url, dest)
        except Exception as exc:
            print(f"Model yuklanmadi ({filename}): {exc}")
            all_ok = False

    return all_ok


if __name__ == "__main__":
    ok = ensure_models()
    print("Modellar tayyor" if ok else "Ba'zi modellar yuklanmadi — fallback ishlatiladi")
