from PIL import Image, ImageDraw
import math
import ffmpeg
import os
import glob
import itertools

# https://youtu.be/a4Yge_o7XLg?si=YYmPQBmLYXq4cSoY at 1:10:30

def draw_ring(draw: ImageDraw.ImageDraw, color, inner_radius: int, outer_radius: int, center_x: int, center_y: int, rotation: float = 0.0):
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

    Returns:
        PIL.Image.Image: A Pillow image object containing the drawn ring.
    """
    if not isinstance(inner_radius, int) or not isinstance(outer_radius, int):
        raise TypeError("Radii must be integers.")
    if inner_radius <= 0 or outer_radius <= 0:
        raise ValueError("Radii must be positive.")
    if inner_radius >= outer_radius:
        raise ValueError("Inner radius must be less than the outer radius.")

    # Create a new image with a transparent background (RGBA mode)
    image = draw._image

    # Calculate bounding box coordinates
    center = (center_x, center_y)
    if rotation != 0.0:
        offset = (image.size[0] // 2, image.size[1] // 2)
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
    draw.ellipse(inner_bbox, fill=(0, 0, 0, 0))

def radians(degrees):
    return degrees * math.pi / 180

def ncircles(disc_radius, radius):
    return math.floor(math.pi / math.asin(radius / disc_radius))

FPS = 120
SCALE_DOWN = 5
OUTER_RADIUS = 40 // SCALE_DOWN
INNER_RADIUS = 30 // SCALE_DOWN
CANVAS_SIZE = (3840 * 2 // SCALE_DOWN, 2160 * 2 // SCALE_DOWN)
ADJUSTMENT = 25
SECONDS = 20
SKIP = 9
FRAMES = SECONDS * FPS * SKIP
LEVELS = 53

def generate_video(fps, canvas_size):
    stream = ffmpeg.input('red_ring_*.png', pattern_type='glob', framerate=fps).filter('scale', canvas_size[0] // 2, -1)
    stream.output("output.mp4", pix_fmt='yuv420p', sws_flags='lanczos').overwrite_output().run()
    print("Video created successfully!")

def main():
    # Delete old png files
    for f in itertools.chain(glob.glob('red_ring*.png'), glob.glob('red_ring*.bmp')):
        os.remove(f)
    try:
        # rpm = 100
        for add_rot in range(0, FRAMES, SKIP):
            add_rot_f = add_rot / 2
            image = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            def red_ring(level, rotation, adj):
                sine = abs(math.sin(rotation))
                cosine = abs(math.cos(rotation))
                if sine > 0.98 or cosine > 0.98:
                    return
                quadrant = 'red' if rotation < math.pi / 2 else 'blue' if rotation < math.pi else 'green' if rotation < 3 * math.pi / 2 else 'yellow'
                draw_ring(
                    draw, color=quadrant,
                    inner_radius=INNER_RADIUS, outer_radius=OUTER_RADIUS,
                    center_x=CANVAS_SIZE[0] // 2 - level * OUTER_RADIUS * 2 - ADJUSTMENT, center_y=CANVAS_SIZE[1] // 2,
                    rotation=rotation + adj
                )
            for level in range(1, LEVELS):
                n = ncircles(level * OUTER_RADIUS * 2 + ADJUSTMENT, OUTER_RADIUS)
                #print(f"Level {level}: {n} circles would fit.")
                cnt = 0
                rotation = 0.0
                while rotation < 360.0:
                    red_ring(level=level, rotation=radians(rotation), adj=radians(add_rot_f * (1.0 - level / LEVELS)))
                    rotation += 360.0 / n
                    cnt += 1
                #print(f"Created {cnt} circles.")

            filename = f"red_ring_{add_rot:06d}.png"
            image.save(filename, compress_level=1)
            print(f"Ring image '{filename}' created successfully!")
        generate_video(FPS, CANVAS_SIZE)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
