#!/bin/bash
#
# Run a bunch of settings.

set -e

SCALE_DOWN=4

# opencv
uv run main.py --image-impl=opencv --glow-radius=180 --output=opencv-3 --scale-down=$SCALE_DOWN --skip=3
uv run main.py --image-impl=opencv --glow-radius=180 --output=opencv-6 --scale-down=$SCALE_DOWN --skip=6
uv run main.py --image-impl=opencv --glow-radius=180 --output=opencv-9 --scale-down=$SCALE_DOWN --skip=9
uv run main.py --image-impl=opencv --glow-radius=180 --output=opencv-12 --scale-down=$SCALE_DOWN --skip=12
uv run main.py --image-impl=opencv --glow-radius=180 --output=opencv-15 --scale-down=$SCALE_DOWN --skip=15
uv run main.py --image-impl=opencv --glow-radius=180 --output=opencv-18 --scale-down=$SCALE_DOWN --skip=18
uv run main.py --image-impl=opencv --glow-radius=180 --output=opencv-21 --scale-down=$SCALE_DOWN --skip=21

# pygame
uv run main.py --image-impl=pygame --glow-combo=False --output=pygame-3 --scale-down=$SCALE_DOWN --skip=3
uv run main.py --image-impl=pygame --glow-combo=False --output=pygame-6 --scale-down=$SCALE_DOWN --skip=6
uv run main.py --image-impl=pygame --glow-combo=False --output=pygame-9 --scale-down=$SCALE_DOWN --skip=9
uv run main.py --image-impl=pygame --glow-combo=False --output=pygame-12 --scale-down=$SCALE_DOWN --skip=12
uv run main.py --image-impl=pygame --glow-combo=False --output=pygame-15 --scale-down=$SCALE_DOWN --skip=15
uv run main.py --image-impl=pygame --glow-combo=False --output=pygame-18 --scale-down=$SCALE_DOWN --skip=18
uv run main.py --image-impl=pygame --glow-combo=False --output=pygame-21 --scale-down=$SCALE_DOWN --skip=21

uv run main.py --image-impl=pygame --glow-combo=True --glow-radius=180 --output=pygamec-3 --scale-down=$SCALE_DOWN --skip=3
uv run main.py --image-impl=pygame --glow-combo=True --glow-radius=180 --output=pygamec-6 --scale-down=$SCALE_DOWN --skip=6
uv run main.py --image-impl=pygame --glow-combo=True --glow-radius=180 --output=pygamec-9 --scale-down=$SCALE_DOWN --skip=9
uv run main.py --image-impl=pygame --glow-combo=True --glow-radius=180 --output=pygamec-12 --scale-down=$SCALE_DOWN --skip=12
uv run main.py --image-impl=pygame --glow-combo=True --glow-radius=180 --output=pygamec-15 --scale-down=$SCALE_DOWN --skip=15
uv run main.py --image-impl=pygame --glow-combo=True --glow-radius=180 --output=pygamec-18 --scale-down=$SCALE_DOWN --skip=18
uv run main.py --image-impl=pygame --glow-combo=True --glow-radius=180 --output=pygamec-21 --scale-down=$SCALE_DOWN --skip=21
