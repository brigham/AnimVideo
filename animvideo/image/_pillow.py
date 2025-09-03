from animvideo.image._img import Img
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import math

class _PillowImage(Img):
    def __init__(self, image: Image.Image):
        self._image = image
        self._draw = ImageDraw.Draw(self._image)

    @classmethod
    def empty(cls, size: tuple[int, int], color: tuple[int, int, int] = (0, 0, 0)) -> 'Img':
        return cls(Image.new('RGB', size, color))

    def save(self, filename: str):
        self._image.save(filename, compress_level=1)

    def tobytes(self) -> bytes:
        image = self._image if self._image.mode == 'RGB' else self._image.convert('RGB')
        return image.tobytes()

    @property
    def size(self) -> tuple[int, int]:
        return self._image.size

    def ring(self, color: tuple[int, int, int], inner_radius: int, outer_radius: int, center_x: float|int, center_y: float|int, rotation: float = 0.0):
        center = (center_x, center_y)
        if rotation != 0.0:
            offset = (self.size[0] // 2, self.size[1] // 2)
            center = (center[0] - offset[0], center[1] - offset[1])
            sine = math.sin(rotation)
            cosine = math.cos(rotation)
            center = (center[0] * cosine - center[1] * sine, center[0] * sine + center[1] * cosine)
            center = (center[0] + offset[0], center[1] + offset[1])
        center_x, center_y = center

        # Calculate the bounding boxes for the inner and outer circles
        outer_bbox = (
            center_x - outer_radius,
            center_y - outer_radius,
            center_x + outer_radius,
            center_y + outer_radius,
        )
        inner_bbox = (
            center_x - inner_radius,
            center_y - inner_radius,
            center_x + inner_radius,
            center_y + inner_radius,
        )

        # Draw the outer circle with the specified color
        self._draw.ellipse(outer_bbox, fill=color)

        # Draw the inner circle with a transparent fill to create the hole
        self._draw.ellipse(inner_bbox, fill=(0, 0, 0))

    def ellipse(self, bbox: tuple[int, int, int, int], fill: tuple[int, int, int] = (0, 0, 0)):
        self._draw.ellipse(bbox, fill=fill)

    def glow(self, radius: int = 79):
        blur_image = self._image.filter(ImageFilter.GaussianBlur(radius=radius))
        self._image = ImageChops.add(self._image, blur_image)
        self._draw = ImageDraw.Draw(self._image)
