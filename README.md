I wanted to teach myself a new skill, specifically animation.

Intro
=====
I started with what I know: Pillow, and quickly discovered that it was pretty slow
for a lot of things, especially once I wanted to create a glow effect.

I had some experience with OpenCV, which was much faster on the glow effect, but
not by much and the drawing performance was disappointing.

That made me look into PyGame and then Panda3d. PyGame didn't have a great way to
do the glow effect, so I still had to pull in OpenCV.

I also realized PyGame would make it difficult to do any three dimensional effects, so Panda3D was the next thing to try.

I still wasn't happy with the performance, but I realized that I was recreating
the scene for each frame, but Panda3d was perfectly capable of creating the
scene once and then mutating the parts that changed frame to frame.

Running the code
================
Just use `uv` to install the packages.

`uv run main2.py` to generate the animation.

`uv run autoplay.py output-scene/output.mp4` will start a web server to auto-reload the animation in your browser on `localhost:8000`.

To auto generate the animation on code changes: `uvx --from watchdog==6.0.0 watchmedo shell-command --patterns='*.py' --recursive --command='uv run main2.py' --wait .`

Legacy
======
main.py and the code in image/ is the original approach that didn't keep any state
between frames. I plan to remove it at some point.
