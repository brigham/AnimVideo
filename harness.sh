#!/bin/bash
#
# Run a bunch of settings.

set -e

SCALE_DOWN=4

# opencv
uv run main.py --image-impl=opencv --glow-radius=180 --output=harness/opencv-3 --scale-down=$SCALE_DOWN --skip=3
uv run main.py --image-impl=opencv --glow-radius=180 --output=harness/opencv-6 --scale-down=$SCALE_DOWN --skip=6
uv run main.py --image-impl=opencv --glow-radius=180 --output=harness/opencv-9 --scale-down=$SCALE_DOWN --skip=9
uv run main.py --image-impl=opencv --glow-radius=180 --output=harness/opencv-12 --scale-down=$SCALE_DOWN --skip=12
uv run main.py --image-impl=opencv --glow-radius=180 --output=harness/opencv-15 --scale-down=$SCALE_DOWN --skip=15
uv run main.py --image-impl=opencv --glow-radius=180 --output=harness/opencv-18 --scale-down=$SCALE_DOWN --skip=18
uv run main.py --image-impl=opencv --glow-radius=180 --output=harness/opencv-21 --scale-down=$SCALE_DOWN --skip=21

# pygame
uv run main.py --image-impl=pygame --glow-combo=False --output=harness/pygame-3 --scale-down=$SCALE_DOWN --skip=3
uv run main.py --image-impl=pygame --glow-combo=False --output=harness/pygame-6 --scale-down=$SCALE_DOWN --skip=6
uv run main.py --image-impl=pygame --glow-combo=False --output=harness/pygame-9 --scale-down=$SCALE_DOWN --skip=9
uv run main.py --image-impl=pygame --glow-combo=False --output=harness/pygame-12 --scale-down=$SCALE_DOWN --skip=12
uv run main.py --image-impl=pygame --glow-combo=False --output=harness/pygame-15 --scale-down=$SCALE_DOWN --skip=15
uv run main.py --image-impl=pygame --glow-combo=False --output=harness/pygame-18 --scale-down=$SCALE_DOWN --skip=18
uv run main.py --image-impl=pygame --glow-combo=False --output=harness/pygame-21 --scale-down=$SCALE_DOWN --skip=21

uv run main.py --image-impl=pygame --glow-combo=True --glow-radius=180 --output=harness/pygamec-3 --scale-down=$SCALE_DOWN --skip=3
uv run main.py --image-impl=pygame --glow-combo=True --glow-radius=180 --output=harness/pygamec-6 --scale-down=$SCALE_DOWN --skip=6
uv run main.py --image-impl=pygame --glow-combo=True --glow-radius=180 --output=harness/pygamec-9 --scale-down=$SCALE_DOWN --skip=9
uv run main.py --image-impl=pygame --glow-combo=True --glow-radius=180 --output=harness/pygamec-12 --scale-down=$SCALE_DOWN --skip=12
uv run main.py --image-impl=pygame --glow-combo=True --glow-radius=180 --output=harness/pygamec-15 --scale-down=$SCALE_DOWN --skip=15
uv run main.py --image-impl=pygame --glow-combo=True --glow-radius=180 --output=harness/pygamec-18 --scale-down=$SCALE_DOWN --skip=18
uv run main.py --image-impl=pygame --glow-combo=True --glow-radius=180 --output=harness/pygamec-21 --scale-down=$SCALE_DOWN --skip=21
