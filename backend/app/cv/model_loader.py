"""Chooses which model file the tracker loads (with one-time export).

On CPU, YOLO inference via raw PyTorch is slow. OpenVINO runs the same
model noticeably faster on any modern x86 CPU, so when the device is CPU
and the backend allows it, the .pt weights are exported once to an
OpenVINO directory next to the weights and reused on later runs.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_OPENVINO_SUFFIX = "_openvino_model"
_KNOWN_BACKENDS = ("auto", "torch", "openvino")


def resolve_device(device: str | None) -> str:
    """Resolve an explicit device, falling back to cuda/cpu auto-detect."""
    if device:
        return device
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def resolve_model(model_path: str, device: str, backend: str) -> str:
    """Return the model path to load, exporting to OpenVINO if useful.

    Falls back to the original weights whenever export is unavailable.
    """
    if backend not in _KNOWN_BACKENDS:
        logger.warning("Unknown inference backend '%s'; using PyTorch", backend)
        return model_path
    if backend == "torch" or device != "cpu":
        return model_path
    if not model_path.endswith(".pt"):
        return model_path  # already an exported/optimized model

    exported = _openvino_dir(model_path)
    if exported.exists():
        return str(exported)
    try:
        return str(_export_openvino(model_path, exported))
    except Exception as exc:  # noqa: BLE001 - intentional fallback
        logger.warning("OpenVINO export failed (%s); using PyTorch", exc)
        return model_path


def _openvino_dir(model_path: str) -> Path:
    src = Path(model_path)
    return src.with_name(src.stem + _OPENVINO_SUFFIX)


def _export_openvino(model_path: str, target: Path) -> Path:
    from ultralytics import YOLO

    logger.info(
        "Exporting %s to OpenVINO (one-time step, takes ~a minute)...",
        model_path,
    )
    YOLO(model_path).export(format="openvino")
    if not target.exists():
        raise RuntimeError(f"export did not produce {target}")
    logger.info("OpenVINO model ready at %s", target)
    return target
