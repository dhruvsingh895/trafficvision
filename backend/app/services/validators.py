"""Video file validation helpers."""
import cv2


def is_valid_extension(filename: str, allowed: set[str]) -> bool:
    """Check filename has an allowed extension."""
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return suffix in allowed


def is_readable_video(path: str) -> bool:
    """Verify the file can be opened and a frame read via OpenCV."""
    cap = cv2.VideoCapture(path)
    try:
        if not cap.isOpened():
            return False
        ok, frame = cap.read()
        return ok and frame is not None
    finally:
        cap.release()
