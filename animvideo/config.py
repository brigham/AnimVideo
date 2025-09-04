from enum import Enum
import os
from typing import Tuple, List
from dataclasses import dataclass, field
from PIL import ImageColor

class Mode(str, Enum):
    FULL = 'full'
    VIDEO = 'video'
    THUMBS = 'thumbs'

    @property
    def enable_video(self) -> bool:
        return self != Mode.THUMBS

    @property
    def enable_thumbs(self) -> bool:
        return self != Mode.VIDEO

def minutes(m):
    return m * 60

@dataclass
class Config:
    OUTPUT_DIR: str = 'output'
    FPS: int = 60
    SCALE_DOWN_BASE: int = 1
    OUTER_RADIUS_BASE: int = 40
    INNER_RADIUS_BASE: int = 30
    CANVAS_SIZE_BASE: Tuple[int, int] = (3840 * 2, 2160 * 2)
    ADJUSTMENT: int = 25
    SECONDS: int = 1
    SKIP: int = 21
    LEVELS: int = 53
    START_FRAME_BASE: int = 0
    END_FRAME_BASE: int = -1
    MODE: Mode = Mode.FULL
    COLORS0_BASE: List[str|tuple[int, int, int]] = field(default_factory=lambda: ['blue', 'green', 'yellow', 'red'])
    COLORS1_BASE: List[str|tuple[int, int, int]] = field(default_factory=lambda: ['cyan', 'yellow', 'orange', 'magenta'])
    IMAGE_IMPL: str = 'pygame'
    GLOW_COMBO: bool = True
    GLOW_RADIUS_BASE: int = 180

    @property
    def SCALE_DOWN(self) -> int:
        return self.SCALE_DOWN_BASE if self.IMAGE_IMPL != 'panda3d' else self.SCALE_DOWN_BASE * 2

    @property
    def OUTER_RADIUS(self) -> int:
        return self.OUTER_RADIUS_BASE // self.SCALE_DOWN

    @property
    def INNER_RADIUS(self) -> int:
        return self.INNER_RADIUS_BASE // self.SCALE_DOWN

    @property
    def CANVAS_SIZE(self) -> Tuple[int, int]:
        return (self.CANVAS_SIZE_BASE[0] // self.SCALE_DOWN, self.CANVAS_SIZE_BASE[1] // self.SCALE_DOWN)

    @property
    def FRAMES(self) -> int:
        return int(self.SECONDS * self.FPS * self.SKIP)

    @property
    def START_FRAME(self) -> int:
        if self.START_FRAME_BASE < 0:
            raise ValueError("START_FRAME_BASE must be non-negative")
        if self.START_FRAME_BASE >= self.FRAMES:
            raise ValueError("START_FRAME_BASE must be less than FRAMES")
        result = self.START_FRAME_BASE
        return result // self.SKIP * self.SKIP

    @property
    def END_FRAME(self) -> int:
        if self.END_FRAME_BASE < -1:
            raise ValueError("END_FRAME_BASE must be non-negative")
        if self.END_FRAME_BASE > -1 and self.END_FRAME_BASE < self.START_FRAME:
            raise ValueError(f"END_FRAME_BASE must be greater than or equal to START_FRAME ({self.START_FRAME})")
        if self.END_FRAME_BASE > self.FRAMES:
            raise ValueError("END_FRAME_BASE must be less than FRAMES")
        result = self.END_FRAME_BASE if self.END_FRAME_BASE != -1 else self.FRAMES

        is_off = result % self.SKIP != 0

        return (result // self.SKIP * self.SKIP) + self.SKIP if is_off else result

    @property
    def DURATION(self) -> float:
        return self.END_FRAME - self.START_FRAME

    @property
    def COLORS0(self) -> list[tuple[int, int, int]]:
        return [ImageColor.getrgb(color)[:3] if isinstance(color, str) else color for color in self.COLORS0_BASE]

    @property
    def COLORS1(self) -> list[tuple[int, int, int]]:
        return [ImageColor.getrgb(color)[:3] if isinstance(color, str) else color for color in self.COLORS1_BASE]

    @property
    def GLOW_RADIUS(self) -> int:
        scaled = self.GLOW_RADIUS_BASE // self.SCALE_DOWN
        return scaled + 1 if scaled % 2 == 0 else scaled

    def output_path(self, filename: str) -> str:
        return os.path.join(self.OUTPUT_DIR, filename)
