import concurrent.futures
import os

from PIL import Image


def convert_image(png_path):
    webp_path = os.path.splitext(png_path)[0] + ".webp"
    if os.path.exists(webp_path):
        return f"Skipping {png_path} (exists)"

    try:
        with Image.open(png_path) as img:
            img.save(webp_path, "WEBP", quality=85)
        return f"Converted {png_path}"
    except Exception as e:
        return f"Error converting {png_path}: {e}"


def main():
    base_dir = "frontend/img/cards"
    png_files = []

    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith(".png"):
                png_files.append(os.path.join(root, file))

    print(f"Found {len(png_files)} PNG files.")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(convert_image, png_files))

    # Print status summary
    success = sum(1 for r in results if r.startswith("Converted"))
    skipped = sum(1 for r in results if r.startswith("Skipping"))
    errors = sum(1 for r in results if r.startswith("Error"))

    print(f"Summary: {success} converted, {skipped} skipped, {errors} errors.")


if __name__ == "__main__":
    main()
