import abc
from PIL import Image, ImageDraw, ImageFilter, ImageChops

class Img(abc.ABC):
    @abc.abstractmethod
    def save(self, filename: str):
        ...

    @abc.abstractmethod
    def tobytes(self) -> bytes:
        ...

    @property
    @abc.abstractmethod
    def size(self) -> tuple[int, int]:
        ...

    @abc.abstractmethod
    def ellipse(self, bbox: tuple[int, int, int, int], fill: tuple[int, int, int] = (0, 0, 0)):
        ...

    @abc.abstractmethod
    def glow(self):
        ...

class _PillowImage(Img):
    def __init__(self, image: Image.Image):
        self._image = image
        self._draw = ImageDraw.Draw(self._image)

    def save(self, filename: str):
        self._image.save(filename, compress_level=1)

    def tobytes(self) -> bytes:
        image = self._image if self._image.mode == 'RGB' else self._image.convert('RGB')
        return image.tobytes()

    @property
    def size(self) -> tuple[int, int]:
        return self._image.size

    def ellipse(self, bbox: tuple[int, int, int, int], fill: tuple[int, int, int] = (0, 0, 0)):
        self._draw.ellipse(bbox, fill=fill)

    def glow(self):
        blur_image = self._image.filter(ImageFilter.GaussianBlur(radius=15))
        self._image = ImageChops.add(self._image, blur_image)
        self._draw = ImageDraw.Draw(self._image)

def empty(size: tuple[int, int], color: tuple[int, int, int] = (0, 0, 0)) -> Img:
    return _PillowImage(Image.new('RGB', size, color))
