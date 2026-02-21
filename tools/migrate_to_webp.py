import concurrent.futures
import os

from PIL import Image

# Configuration
SOURCE_DIR = "frontend/img/cards"
DEST_DIR = "frontend/img/cards_webp"
QUALITY = 85


def convert_image(png_path):
    # Get filename without extension
    filename = os.path.basename(png_path)
    base_name = os.path.splitext(filename)[0]
    webp_filename = base_name + ".webp"
    webp_path = os.path.join(DEST_DIR, webp_filename)

    # Collision check (optional, but good for flat structures)
    # In LovecaSim, filenames usually include set IDs, so collisions are rare.

    try:
        with Image.open(png_path) as img:
            # Ensure it's RGB/RGBA
            if img.mode in ("P", "1"):
                img = img.convert("RGBA")
            img.save(webp_path, "WEBP", quality=QUALITY)
        return f"Converted: {filename} -> {webp_filename}"
    except Exception as e:
        return f"Error: {png_path} -> {e}"


def main():
    if not os.path.exists(SOURCE_DIR):
        print(f"Error: Source directory {SOURCE_DIR} not found.")
        return

    # Create destination if it doesn't exist
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)
        print(f"Created directory: {DEST_DIR}")

    # Gather all PNGs from subdirectories
    png_files = []
    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.lower().endswith(".png"):
                png_files.append(os.path.join(root, file))

    print(f"Found {len(png_files)} PNG files to convert and flatten.")

    # Use ThreadPoolExecutor for faster conversion
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(convert_image, png_files))

    # Summary
    success = sum(1 for r in results if r.startswith("Converted"))
    errors = [r for r in results if r.startswith("Error")]

    print("\nMigration Summary:")
    print(f"- Total processed: {len(results)}")
    print(f"- Successfully converted: {success}")
    print(f"- Errors: {len(errors)}")

    if errors:
        print("\nErrors encountered:")
        for err in errors[:10]:  # Show first 10
            print(err)


if __name__ == "__main__":
    main()
