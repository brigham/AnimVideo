import abc

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
