import src.sizes as sizes

for size, g in sizes.MIDORI_GRID.items():
    s = sizes.SIZES[size]
    usable_w = s["pw"] - g["binding"] - g["right_margin"]
    usable_h = s["ph"] - g["top_margin"] - g["bottom_margin"]
    num_x = int(usable_w // g["grid_step"])
    num_y = int(usable_h // g["grid_step"])
    print(f"{size}: {num_x}x{num_y}, mid_x={num_x / 2.0}, mid_y={num_y / 2.0}")
