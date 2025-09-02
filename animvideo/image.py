import abc
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import cv2
import numpy as np
import math



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
    def ring(self, color: tuple[int, int, int], inner_radius: int, outer_radius: int, center_x: int, center_y: int, rotation: float = 0.0):
        ...

    @abc.abstractmethod
    def ellipse(self, bbox: tuple[int, int, int, int], fill: tuple[int, int, int] = (0, 0, 0)):
        ...

    @abc.abstractmethod
    def glow(self):
        ...

def draw_ring(draw: Img, color, inner_radius: int, outer_radius: int, center_x: int, center_y: int, rotation: float = 0.0):
    """
    Draws a ring with a transparent center using the Pillow library.

    Args:
        draw (PIL.ImageDraw.ImageDraw): The draw object on which to draw the ring.
        color (str or tuple): The color of the ring (e.g., "blue", "#0000FF", or (0, 0, 255)).
        inner_radius (int): The radius of the inner, transparent hole.
        outer_radius (int): The radius of the outer circle.
        center_x (int): The x-coordinate of the center of the ring.
        center_y (int): The y-coordinate of the center of the ring.
        rotation (float): The rotation angle of the ring in radians around the center of the image.
    """
    if not isinstance(inner_radius, int) or not isinstance(outer_radius, int):
        raise TypeError("Radii must be integers.")
    if inner_radius <= 0 or outer_radius <= 0:
        raise ValueError("Radii must be positive.")
    if inner_radius >= outer_radius:
        raise ValueError("Inner radius must be less than the outer radius.")

    # Calculate bounding box coordinates
    center = (center_x, center_y)
    if rotation != 0.0:
        offset = (draw.size[0] // 2, draw.size[1] // 2)
        center = (center[0] - offset[0], center[1] - offset[1])
        sine = math.sin(rotation)
        cosine = math.cos(rotation)
        center = (center[0] * cosine - center[1] * sine, center[0] * sine + center[1] * cosine)
        center = (center[0] + offset[0], center[1] + offset[1])

    outer_bbox = (
        center[0] - outer_radius,
        center[1] - outer_radius,
        center[0] + outer_radius,
        center[1] + outer_radius,
    )
    inner_bbox = (
        center[0] - inner_radius,
        center[1] - inner_radius,
        center[0] + inner_radius,
        center[1] + inner_radius,
    )

    # Draw the outer circle with the specified color
    draw.ellipse(outer_bbox, fill=color)

    # Draw the inner circle with a transparent fill to create the hole
    draw.ellipse(inner_bbox, fill=(0, 0, 0))


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

    def glow(self):
        blur_image = self._image.filter(ImageFilter.GaussianBlur(radius=15))
        self._image = ImageChops.add(self._image, blur_image)
        self._draw = ImageDraw.Draw(self._image)

class _OpenCVImage(Img):
    def __init__(self, image: cv2.typing.MatLike):
        self._image = image

    def save(self, filename: str):
        cv2.imwrite(filename, self._image)

    def tobytes(self) -> bytes:
        if self._image.shape[2] == 3: # Check if it's a color image
            frame_rgb = cv2.cvtColor(self._image, cv2.COLOR_BGR2RGB)
            return frame_rgb.tobytes()
        else: # Grayscale or other formats
            # Handle other cases if necessary, e.g., convert grayscale to RGB
            # For now, we'll assume BGR input for simplicity
            raise ValueError("Unsupported NumPy array format. Expected 3-channel BGR.")


    @property
    def size(self) -> tuple[int, int]:
        flipped = self._image.shape[:2]
        return flipped[::-1]

    def ring(self, color: tuple[int, int, int], inner_radius: int, outer_radius: int, center_x: int, center_y: int, rotation: float = 0.0):
        color_bgr = (color[2], color[1], color[0])

        center = (center_x, center_y)
        if rotation != 0.0:
            offset = (self.size[0] // 2, self.size[1] // 2)
            center = (center[0] - offset[0], center[1] - offset[1])
            sine = math.sin(rotation)
            cosine = math.cos(rotation)
            center = (center[0] * cosine - center[1] * sine, center[0] * sine + center[1] * cosine)
            center = (int(center[0] + offset[0]), int(center[1] + offset[1]))
        thickness = outer_radius - inner_radius
        adjusted_radius = outer_radius - thickness // 2 if thickness > 1 else outer_radius
        cv2.circle(self._image, center, adjusted_radius, color_bgr, thickness)

    def ellipse(self, bbox: tuple[int, int, int, int], fill: tuple[int, int, int]|tuple[int, int, int, int] = (0, 0, 0)):
        # 1. Convert Pillow's bounding box to OpenCV's center and axes
        x0, y0, x1, y1 = bbox
        center = (int((x0 + x1) / 2), int((y0 + y1) / 2))
        axes = (int((x1 - x0) / 2), int((y1 - y0) / 2))

        # 2. Convert RGB color to OpenCV's BGR format
        color_bgr = (fill[2], fill[1], fill[0])

        # Is this a circle?
        if axes[0] == axes[1]:
            cv2.circle(self._image, center, axes[0], color_bgr, thickness=-1)
        else:
            cv2.ellipse(self._image, center, axes, 0, 0, 360, color_bgr, thickness=-1)

    def glow(self):
        blur_image = cv2.GaussianBlur(self._image, (79, 79), 0)
        self._image = cv2.add(self._image, blur_image)

def empty(size: tuple[int, int], color: tuple[int, int, int] = (0, 0, 0)) -> Img:
    # return _PillowImage(Image.new('RGB', size, color))
    return _OpenCVImage(np.zeros((size[1], size[0], 3), dtype=np.uint8))
