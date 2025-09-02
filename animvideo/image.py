import abc
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import cv2
import numpy as np
import pygame
import math



class Img(abc.ABC):
    """
    An abstract base class for a backend-agnostic image.

    This class provides a common interface for creating and manipulating
    images, regardless of the underlying implementation (e.g., Pillow or
    OpenCV). It is designed to be subclassed for specific backends.
    """

    @classmethod
    @abc.abstractmethod
    def empty(cls, size: tuple[int, int], color: tuple[int, int, int] = (0, 0, 0)) -> 'Img':
        """
        Creates a new image.

        Args:
            size (tuple[int, int]): The size of the image.
            color (tuple[int, int, int]): The color of the image.

        Returns:
            Img: The new image.
        """
        ...

    @abc.abstractmethod
    def save(self, filename: str):
        """
        Saves the image to a file.

        Args:
            filename (str): The name of the file to save the image to.
        """
        ...

    @abc.abstractmethod
    def tobytes(self) -> bytes:
        """
        Returns the raw pixel data of the image as a byte string.

        Returns:
            bytes: The pixel data.
        """
        ...

    @property
    @abc.abstractmethod
    def size(self) -> tuple[int, int]:
        """
        Returns the size of the image as a tuple of (width, height).

        Returns:
            tuple[int, int]: The width and height of the image.
        """
        ...

    @abc.abstractmethod
    def ring(self, color: tuple[int, int, int], inner_radius: int, outer_radius: int, center_x: int, center_y: int, rotation: float = 0.0):
        """
        Draws a ring on the image.

        Args:
            color (tuple[int, int, int]): The color of the ring.
            inner_radius (int): The inner radius of the ring.
            outer_radius (int): The outer radius of the ring.
            center_x (int): The x-coordinate of the center of the ring.
            center_y (int): The y-coordinate of the center of the ring.
            rotation (float, optional): The rotation of the ring in radians.
                Defaults to 0.0.
        """
        ...

    @abc.abstractmethod
    def ellipse(self, bbox: tuple[int, int, int, int], fill: tuple[int, int, int] = (0, 0, 0)):
        """
        Draws an ellipse on the image.

        Args:
            bbox (tuple[int, int, int, int]): The bounding box of the
                ellipse.
            fill (tuple[int, int, int], optional): The color to fill the
                ellipse with. Defaults to (0, 0, 0).
        """
        ...

    @abc.abstractmethod
    def glow(self, radius: int = 79):
        """
        Applies a glow effect to the image.

        Args:
            radius (int): The radius of the glow effect, if applicable.
        """
        ...



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

class _OpenCVImage(Img):
    def __init__(self, image: cv2.typing.MatLike):
        self._image = image

    @classmethod
    def empty(cls, size: tuple[int, int], color: tuple[int, int, int] = (0, 0, 0)) -> 'Img':
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

_use_opencv_for_glow = False

def set_use_opencv_for_glow(value: bool):
    global _use_opencv_for_glow
    _use_opencv_for_glow = value

class _PygameImage(Img):
    def __init__(self, surface: pygame.Surface):
        self._surface = surface

    @classmethod
    def empty(cls, size: tuple[int, int], color: tuple[int, int, int] = (0, 0, 0)) -> 'Img':
        surface = pygame.Surface(size)
        surface.fill(color)
        return _PygameImage(surface)

    def save(self, filename: str):
        pygame.image.save(self._surface, filename)

    def tobytes(self) -> bytes:
        return pygame.image.tostring(self._surface, 'RGB')

    @property
    def size(self) -> tuple[int, int]:
        return self._surface.get_size()

    def ring(self, color: tuple[int, int, int], inner_radius: int, outer_radius: int, center_x: int, center_y: int, rotation: float = 0.0):
        center = (center_x, center_y)
        if rotation != 0.0:
            offset = (self.size[0] // 2, self.size[1] // 2)
            center = (center[0] - offset[0], center[1] - offset[1])
            sine = math.sin(rotation)
            cosine = math.cos(rotation)
            center = (center[0] * cosine - center[1] * sine, center[0] * sine + center[1] * cosine)
            center = (int(center[0] + offset[0]), int(center[1] + offset[1]))
        pygame.draw.circle(self._surface, color, center, outer_radius)
        pygame.draw.circle(self._surface, (0, 0, 0), center, inner_radius)


    def ellipse(self, bbox: tuple[int, int, int, int], fill: tuple[int, int, int] = (0, 0, 0)):
        pygame.draw.ellipse(self._surface, fill, bbox)

    def glow(self, radius: int = 79):
        if _use_opencv_for_glow:
            self._opencv_glow(radius=radius)
        else:
            self._pygame_glow()

    def _pygame_glow(self):
        size = self.size
        scale_factor = 4
        small_size = (max(1, size[0] // scale_factor), max(1, size[1] // scale_factor))
        small_surface = pygame.transform.smoothscale(self._surface, small_size)
        blur_surface = pygame.transform.smoothscale(small_surface, size)
        self._surface.blit(blur_surface, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    def _opencv_glow(self, radius: int = 79):
        # 1. Get a NumPy array view of the PyGame surface's pixels
        # This is a view, not a copy, so it's fast!
        numpy_view = pygame.surfarray.pixels3d(self._surface)

        # 2. Transpose the axes from (width, height, RGB) to (height, width, RGB)
        # This is the format OpenCV expects.
        opencv_image_rgb = numpy_view.transpose([1, 0, 2])

        # 3. Convert the color order from RGB (PyGame) to BGR (OpenCV)
        opencv_image_bgr = cv2.cvtColor(opencv_image_rgb, cv2.COLOR_RGB2BGR)

        # 4. Apply the Gaussian Blur using OpenCV
        # The (51, 51) kernel size determines the blur intensity. It must be an odd number.
        blurred_bgr = cv2.GaussianBlur(opencv_image_bgr, (radius, radius), 0)
        blurred_bgr = cv2.add(blurred_bgr, opencv_image_bgr)

        # 5. Convert the color order back from BGR to RGB
        blurred_rgb = cv2.cvtColor(blurred_bgr, cv2.COLOR_BGR2RGB)

        pygame.surfarray.blit_array(self._surface, blurred_rgb.transpose([1, 0, 2]))

_current_implementation = _PygameImage

def set_implementation(name: str):
    global _current_implementation
    if name == 'opencv':
        _current_implementation = _OpenCVImage
    elif name == 'pygame':
        _current_implementation = _PygameImage
    elif name == 'pillow':
        _current_implementation = _PillowImage
    else:
        raise ValueError(f"Unknown implementation: {name}")

def empty(size: tuple[int, int], color: tuple[int, int, int] = (0, 0, 0)) -> Img:
    return _current_implementation.empty(size, color)
