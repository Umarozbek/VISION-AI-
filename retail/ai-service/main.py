from camera_manager import CameraManager
from download_models import ensure_models

if __name__ == "__main__":
    ensure_models()
    manager = CameraManager()
    manager.run_forever()
