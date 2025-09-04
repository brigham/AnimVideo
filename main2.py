import math
import os
import argparse
from animvideo.scene import Panda3DScene
from animvideo.config import Config
from animvideo.video import FFmpegVideoProducer

# https://youtu.be/a4Yge_o7XLg?si=YYmPQBmLYXq4cSoY at 1:10:30

radians = math.radians

def ncircles(disc_radius, radius):
    return math.floor(math.pi / math.asin(radius / disc_radius))

def parse_args() -> Config:
    default_values = Config()

    parser = argparse.ArgumentParser(description='Create a video with a rotating ring.')
    parser.add_argument('--output', type=str, default=default_values.OUTPUT_DIR + '-scene', help='Output directory.')
    parser.add_argument('--start-frame', type=int, default=default_values.START_FRAME_BASE, help='Start frame (inclusive)')
    parser.add_argument('--end-frame', type=int, default=default_values.END_FRAME_BASE, help='End frame (exclusive, -1 is default)')
    parser.add_argument('--scale-down', type=int, default=default_values.SCALE_DOWN * 2, help='Scale down factor')
    parser.add_argument('--glow-combo', type=bool, default=default_values.GLOW_COMBO, help='Enable glow combo (pygame only)')
    parser.add_argument('--glow-radius', type=int, default=default_values.GLOW_RADIUS_BASE, help='Glow radius')
    parser.add_argument('--skip', type=int, default=default_values.SKIP, help='Skip frames')

    parsed = parser.parse_args()
    return Config(
        OUTPUT_DIR=parsed.output,
        START_FRAME_BASE=parsed.start_frame,
        END_FRAME_BASE=parsed.end_frame,
        SCALE_DOWN_BASE=parsed.scale_down,
        GLOW_COMBO=parsed.glow_combo,
        GLOW_RADIUS_BASE=parsed.glow_radius,
        SKIP=parsed.skip
    )

def create_video(config: Config):
    print(f"Creating video with {config}")
    try:
        producer = FFmpegVideoProducer(config.output_path("output.mp4"), config.CANVAS_SIZE, config.CANVAS_SIZE, config.FPS)
        scene = Panda3DScene(config)
        t = 0.0
        step = 1.0 / config.FPS
        while t < 1.0:
            print(t)
            producer.add_frame(scene, int(t * config.FPS))
            t += step
            scene.time = t

        producer.finalize()
        # scene.save(config.output_path("red_ring.png"))
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
