"""TN Cover — Generate cover spread with white margins and print layouts.

Usage: techo tn-cover <image-path> --size tn|tnp --margin 10
"""

import shutil
from pathlib import Path

from .. import sizes


def generate(image_path: Path, size: str) -> None:
    # 1. Look up size parameters
    if size not in sizes.SIZES:
        raise ValueError(f"Size '{size}' not found in sizes.py")

    s = sizes.SIZES[size]
    PW = s["pw"]
    PH = s["ph"]

    # 2. Ensure sizes.tex is generated
    sizes.write_sizes_tex()

    # 3. Create output directory
    out = Path("outputs") / f"tn-cover-{size}"
    out.mkdir(parents=True, exist_ok=True)

    # 4. Calculate printable area dimensions (full spread, no margin)
    img_width = 2 * PW
    img_height = PH

    # 5. Copy or crop the cover image to the output folder
    image_path = Path(image_path)
    suffix = image_path.suffix.lower()
    if suffix not in [".png", ".jpg", ".jpeg", ".pdf"]:
        print(f"Warning: Image file suffix '{suffix}' may not be supported by xelatex.")

    copied_img_name = f"cover_img{suffix}"
    dest_image_path = out / copied_img_name

    if suffix in [".png", ".jpg", ".jpeg"]:
        try:
            from PIL import Image

            target_aspect = img_width / img_height
            with Image.open(image_path) as img:
                img_w, img_h = img.size
                img_aspect = img_w / img_h

                if img_aspect > target_aspect:
                    # Input is wider: crop left and right
                    new_w = int(img_h * target_aspect)
                    left = (img_w - new_w) // 2
                    right = left + new_w
                    top = 0
                    bottom = img_h
                else:
                    # Input is taller: crop top and bottom
                    new_h = int(img_w / target_aspect)
                    top = (img_h - new_h) // 2
                    bottom = top + new_h
                    left = 0
                    right = img_w

                cropped = img.crop((left, top, right, bottom))
                cropped.save(dest_image_path)
            print(
                f"Cropped image from {img_w}x{img_h} to target aspect ratio {target_aspect:.4f} and saved."
            )
        except (OSError, ValueError) as error:
            print(
                f"Warning: Failed to crop image with Pillow: {error}. Copying original instead."
            )
            shutil.copy2(image_path, dest_image_path)
    else:
        # Vector PDF or other files are copied directly
        shutil.copy2(image_path, dest_image_path)

    # 6. Generate the cover wrapper tex file
    paper_width = 2 * PW
    paper_height = PH
    wrapper_tex_content = (
        f"\\def\\EDITION{{{size}}}%\n"
        f"\\def\\IMGNAME{{{copied_img_name}}}%\n"
        f"\\def\\IMGWIDTH{{{img_width:.2f}}}%\n"
        f"\\def\\IMGHEIGHT{{{img_height:.2f}}}%\n"
        f"\\def\\PAPERWD{{{paper_width:.2f}}}%\n"
        f"\\def\\PAPERHT{{{paper_height:.2f}}}%\n"
        f"\\def\\DRAWFOLD{{1}}%\n"
        f"\\input{{../../src/tn_cover/tn_cover.tex}}%\n"
    )
    (out / f"tn-cover-{size}.tex").write_text(wrapper_tex_content)

    print(f"Generated {out}/tn-cover-{size}.tex (full bleed)")

    # 7. Compile the cover PDF
    sizes.compile(f"tn-cover-{size}.tex", out)
    print(f"Compiled {out}/tn-cover-{size}.pdf")
