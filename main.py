import math
import os
import argparse
from animvideo.video import NoopProducer, GlobVideoProducer, FFmpegVideoProducer
from animvideo.image import empty, set_use_opencv_for_glow, set_implementation
from animvideo.config import Config, Mode

# https://youtu.be/a4Yge_o7XLg?si=YYmPQBmLYXq4cSoY at 1:10:30

radians = math.radians

def ncircles(disc_radius, radius):
    return math.floor(math.pi / math.asin(radius / disc_radius))

def parse_args() -> Config:
    default_values = Config()

    parser = argparse.ArgumentParser(description='Create a video with a rotating ring.')
    parser.add_argument('--output', type=str, default=default_values.OUTPUT_DIR, help='Output directory.')
    parser.add_argument('--mode', type=Mode, default=default_values.MODE, choices=[mode.value for mode in Mode], help='Mode of operation')
    parser.add_argument('--start-frame', type=int, default=default_values.START_FRAME_BASE, help='Start frame (inclusive)')
    parser.add_argument('--end-frame', type=int, default=default_values.END_FRAME_BASE, help='End frame (exclusive, -1 is default)')
    parser.add_argument('--scale-down', type=int, default=default_values.SCALE_DOWN, help='Scale down factor')
    parser.add_argument('--glow-combo', type=bool, default=default_values.GLOW_COMBO, help='Enable glow combo (pygame only)')
    parser.add_argument('--glow-radius', type=int, default=default_values.GLOW_RADIUS_BASE, help='Glow radius')
    parser.add_argument('--image-impl', type=str, default=default_values.IMAGE_IMPL, choices=['pillow', 'pygame', 'opencv', 'panda3d'], help='Image implementation')
    parser.add_argument('--skip', type=int, default=default_values.SKIP, help='Skip frames')

    parsed = parser.parse_args()
    return Config(
        OUTPUT_DIR=parsed.output,
        MODE=parsed.mode,
        START_FRAME_BASE=parsed.start_frame,
        END_FRAME_BASE=parsed.end_frame,
        SCALE_DOWN_BASE=parsed.scale_down,
        GLOW_COMBO=parsed.glow_combo,
        GLOW_RADIUS_BASE=parsed.glow_radius,
        IMAGE_IMPL=parsed.image_impl,
        SKIP=parsed.skip
    )

def create_video(config: Config):
    print(f"Creating video with {config}")
    if config.GLOW_COMBO:
        set_use_opencv_for_glow(True)
    set_implementation(config.IMAGE_IMPL)
    try:
        thumb_producer = producer = NoopProducer()
        if config.MODE.enable_thumbs:
            thumb_producer = GlobVideoProducer(config.output_path("thumbnails.mp4"), config.CANVAS_SIZE, config.FPS, config.output_path("red_ring"))
        if config.MODE.enable_video:
            output_size = config.CANVAS_SIZE if config.IMAGE_IMPL == 'panda3d' else (config.CANVAS_SIZE[0] // 2, config.CANVAS_SIZE[1] // 2)
            producer = FFmpegVideoProducer(config.output_path("output.mp4"), config.CANVAS_SIZE, output_size, config.FPS)
        start_frame = config.START_FRAME
        end_frame = config.END_FRAME
        print(f"Frames: {start_frame} to {end_frame}")
        for add_rot in range(start_frame, end_frame, config.SKIP):
            add_rot_f = add_rot / 2
            image = empty(config.CANVAS_SIZE, (0, 0, 0))
            def red_ring(level, rotation, adj):
                rotprime = rotation * 6 % (2 * math.pi)
                quadnum = int(rotation * 3 / (math.pi / 2))
                cosine = abs(math.cos(rotprime))
                if quadnum % 3 == 0:
                    quadrant = config.COLORS0[level % len(config.COLORS0)]
                else:
                    quadrant = config.COLORS1[level % len(config.COLORS1)]
                mult = 1 - math.pow(cosine, 2)
                quadrant = (quadrant[0] * mult, quadrant[1] * mult, quadrant[2] * mult)

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

            image.glow(radius=config.GLOW_RADIUS)
            if add_rot % 100 == 0:
                thumb_producer.add_frame(image, add_rot)
            producer.add_frame(image, add_rot)
            image.destroy()
        producer.finalize()
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

def main():
    config = parse_args()
    # Remove old output files.
    if os.path.exists(config.OUTPUT_DIR) and not os.path.isdir(config.OUTPUT_DIR):
        raise ValueError(f"Output directory '{config.OUTPUT_DIR}' is not a directory.")
    if not os.path.exists(config.OUTPUT_DIR):
        os.makedirs(config.OUTPUT_DIR)
    for f in os.listdir(config.OUTPUT_DIR):
        os.remove(os.path.join(config.OUTPUT_DIR, f))
    create_video(config)

if __name__ == "__main__":
    main()
