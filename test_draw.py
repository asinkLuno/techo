def generate():
    num_x = 2
    num_y = 2
    start_x = 10
    start_y = 10
    STEP = 5
    GAP = 1.2
    EXT = 1.5
    for x_idx in range(num_x + 1):
        x = start_x + x_idx * STEP
        print(f"\\draw ({x:.2f}, -{start_y:.2f}) -- ({x:.2f}, -{start_y - EXT:.2f});")
        for y_idx in range(num_y):
            y_top = start_y + y_idx * STEP
            y_bottom = start_y + (y_idx + 1) * STEP
            print(f"\\draw ({x:.2f}, -{y_top + GAP:.2f}) -- ({x:.2f}, -{y_bottom:.2f});")
        y_last = start_y + num_y * STEP
        print(f"\\draw ({x:.2f}, -{y_last + GAP:.2f}) -- ({x:.2f}, -{y_last + EXT:.2f});")
generate()
