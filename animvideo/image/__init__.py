from animvideo.image._img import Img
from typing import Type, Callable
from animvideo.image._config import set_use_opencv_for_glow

def _import_OpenCVImage() -> Type[Img]:
    from animvideo.image._opencv import _OpenCVImage
    return _OpenCVImage

def _import_PillowImage() -> Type[Img]:
    from animvideo.image._pillow import _PillowImage
    return _PillowImage

def _import_PygameImage() -> Type[Img]:
    from animvideo.image._pygame import _PygameImage
    return _PygameImage

_thunk: Callable[[], Type[Img]] = _import_PygameImage

def set_implementation(name: str):
    global _thunk
    if name == 'opencv':
        _thunk = _import_OpenCVImage
    elif name == 'pygame':
        _thunk = _import_PygameImage
    elif name == 'pillow':
        _thunk = _import_PillowImage
    else:
        raise ValueError(f"Unknown implementation: {name}")

def empty(size: tuple[int, int], color: tuple[int, int, int] = (0, 0, 0)) -> Img:
    return _thunk().empty(size, color)
