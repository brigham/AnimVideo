from enum import Enum
import math
import os
import glob
import itertools
from typing import Tuple, List
from dataclasses import dataclass, field
import argparse
from animvideo.video import NoopProducer, GlobVideoProducer, FFmpegVideoProducer
from animvideo.image import empty
from PIL import ImageColor

# https://youtu.be/a4Yge_o7XLg?si=YYmPQBmLYXq4cSoY at 1:10:30

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
    FPS: int = 60
    SCALE_DOWN: int = 1
    OUTER_RADIUS_BASE: int = 40
    INNER_RADIUS_BASE: int = 30
    CANVAS_SIZE_BASE: Tuple[int, int] = (3840 * 2, 2160 * 2)
    ADJUSTMENT: int = 25
    SECONDS: int = 10
    SKIP: int = 18
    LEVELS: int = 53
    START_FRAME_BASE: int = 0
    END_FRAME_BASE: int = -1
    MODE: Mode = Mode.FULL
    COLORS0_BASE: List[str|tuple[int, int, int]] = field(default_factory=lambda: ['blue', 'green', 'yellow', 'red'])
    COLORS1_BASE: List[str|tuple[int, int, int]] = field(default_factory=lambda: ['cyan', 'yellow', 'orange', 'magenta'])

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


def radians(degrees):
    return degrees * math.pi / 180

def ncircles(disc_radius, radius):
    return math.floor(math.pi / math.asin(radius / disc_radius))

def parse_args() -> Config:
    parser = argparse.ArgumentParser(description='Create a video with a rotating ring.')
    parser.add_argument('--mode', type=Mode, default=Mode.FULL, choices=[mode.value for mode in Mode], help='Mode of operation')
    parser.add_argument('--start-frame', type=int, default=0, help='Start frame (inclusive)')
    parser.add_argument('--end-frame', type=int, default=-1, help='End frame (exclusive, -1 is default)')
    parser.add_argument('--scale-down', type=int, default=1, help='Scale down factor')

    parsed = parser.parse_args()
    return Config(
        MODE=parsed.mode,
        START_FRAME_BASE=parsed.start_frame,
        END_FRAME_BASE=parsed.end_frame,
        SCALE_DOWN=parsed.scale_down
    )

def create_video(config: Config):
    print(f"Creating video with {config}")
    try:
        thumb_producer = producer = NoopProducer()
        if config.MODE.enable_thumbs:
            thumb_producer = GlobVideoProducer("thumbnails.mp4", config.CANVAS_SIZE, config.FPS, "red_ring")
        if config.MODE.enable_video:
            producer = FFmpegVideoProducer("output.mp4", config.CANVAS_SIZE, config.FPS)
        start_frame = config.START_FRAME
        end_frame = config.END_FRAME
        print(f"Frames: {start_frame} to {end_frame}")
        for add_rot in range(start_frame, end_frame, config.SKIP):
            add_rot_f = add_rot / 2
            image = empty(config.CANVAS_SIZE, (0, 0, 0))
            def red_ring(level, rotation, adj):
                rotprime = rotation * 3 % (2 * math.pi)
                quadnum = int(rotation * 3 / (math.pi / 2))
                sine = abs(math.sin(rotprime))
                cosine = abs(math.cos(rotprime))
                if sine > 0.98 or cosine > 0.98:
                    return
                # quadrant = 'red' if rotprime < math.pi / 2 else 'blue' if rotprime < math.pi else 'green' if rotprime < 3 * math.pi / 2 else 'yellow'
                if quadnum % 3 == 0:
                    quadrant = config.COLORS0[level % len(config.COLORS0)]
                else:
                    quadrant = config.COLORS1[level % len(config.COLORS1)]
                if sine > 0.93 or cosine > 0.93:
                    # Darken the color
                    quadrant = (quadrant[0] * 0.15, quadrant[1] * 0.25, quadrant[2] * 0.25)
                elif sine > 0.87 or cosine > 0.87:
                    quadrant = (quadrant[0] * 0.25, quadrant[1] * 0.35, quadrant[2] * 0.35)

                image.ring(color=quadrant,
                    inner_radius=config.INNER_RADIUS, outer_radius=config.OUTER_RADIUS,
                    center_x=config.CANVAS_SIZE[0] // 2 - level * config.OUTER_RADIUS * 2 - config.ADJUSTMENT, center_y=config.CANVAS_SIZE[1] // 2,
                    rotation=rotation + adj
                )
            for level in range(1, config.LEVELS):
                n = ncircles(level * config.OUTER_RADIUS * 2 + config.ADJUSTMENT, config.OUTER_RADIUS)
                #print(f"Level {level}: {n} circles would fit.")
                cnt = 0
                rotation = 0.0
                while rotation < 360.0:
                    red_ring(level=level, rotation=radians(rotation), adj=radians(add_rot_f * (1.0 - level / config.LEVELS)))
                    rotation += 360.0 / n
                    cnt += 1
                #print(f"Created {cnt} circles.")

            image.glow()
            if add_rot % 100 == 0:
                thumb_producer.add_frame(image, add_rot)
            producer.add_frame(image, add_rot)
        producer.finalize()
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

def main():
    config = parse_args()
    # Delete old png files
    for f in itertools.chain(glob.glob('red_ring*.png'), glob.glob('red_ring*.bmp')):
        os.remove(f)
    create_video(config)

if __name__ == "__main__":
    main()
