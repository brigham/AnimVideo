from animvideo.image._img import Img
import pygame
import cv2
import math
import animvideo.image._config as config

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
        if config._use_opencv_for_glow:
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
