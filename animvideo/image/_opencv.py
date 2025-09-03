import cv2
import numpy as np
from animvideo.image._img import Img
import math

class _OpenCVImage(Img):
    def __init__(self, image: cv2.typing.MatLike):
        self._image = image

    @classmethod
    def empty(cls, size: tuple[int, int], color: tuple[int, int, int] = (0, 0, 0)) -> Img:
        img = np.zeros((size[1], size[0], 3), dtype=np.uint8)
        img[:] = color
        return cls(img)

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

    def glow(self, radius: int = 79):
        blur_image = cv2.GaussianBlur(self._image, (radius, radius), 0)
        self._image = cv2.add(self._image, blur_image)
