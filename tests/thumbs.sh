#!/bin/bash
# Run the program and make sure it generates the expected thumbnails.


set -e

if [[ -e red_ring_*.png ]]
then
    rm red_ring_*.png
fi

uv run main.py --end-frame=1801 --scale-down=5 --mode=thumbs --skip=9

for file in tests/goldens/red_ring_*.png; do
    cmp "output/$(basename "$file")" "$file"
done
