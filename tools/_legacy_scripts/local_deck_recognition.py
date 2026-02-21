import argparse
import json
from pathlib import Path

import cv2
import numpy as np


class LocalDeckScanner:
    def __init__(
        self, card_db_path="engine/data/cards.json", img_dir="frontend/img/cards", cache_file="data/card_features.npz"
    ):
        self.card_db_path = Path(card_db_path)
        self.img_dir = Path(img_dir)
        self.cache_file = Path(cache_file)
        self.card_db = self._load_db()
        self.orb = cv2.ORB_create(nfeatures=500)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.card_features = {}
        self.load_cache()

    def _load_db(self):
        if not self.card_db_path.exists():
            # Fallback for running from tools/
            alt_path = Path("../engine/data/cards.json")
            if alt_path.exists():
                return json.load(open(alt_path, "r", encoding="utf-8"))
            return {}
        with open(self.card_db_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _get_card_path(self, cid):
        card_data = self.card_db.get(cid, {})
        local_rel = card_data.get("_img")
        if local_rel:
            p = Path(local_rel)
            if p.exists():
                return p

        for ext in [".png", ".webp"]:
            matches = list(self.img_dir.rglob(f"{cid}{ext}"))
            if matches:
                return matches[0]
        return None

    def load_cache(self):
        if self.cache_file.exists():
            print(f"Loading features from {self.cache_file}...")
            data = np.load(self.cache_file, allow_pickle=True)
            for cid in data.files:
                self.card_features[cid] = data[cid]
            print(f"Loaded {len(self.card_features)} cards.")

    def save_cache(self):
        if not self.cache_file.parent.exists():
            self.cache_file.parent.mkdir(parents=True)
        print(f"Saving features to {self.cache_file}...")
        np.savez(self.cache_file, **self.card_features)

    def index_cards(self, limit=None):
        if self.card_features:
            print("Using cached features.")
            return

        print("Indexing local card assets... (This may take a minute)")
        count = 0
        for cid in self.card_db:
            if limit and count >= limit:
                break
            path = self._get_card_path(cid)
            if not path:
                continue

            img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue

            _, des = self.orb.detectAndCompute(img, None)
            if des is not None:
                self.card_features[cid] = des
                count += 1

        self.save_cache()
        print(f"Indexed {count} cards.")

    def find_cards_in_image(self, screenshot_path):
        scene = cv2.imread(screenshot_path)
        if scene is None:
            return []

        gray_scene = cv2.cvtColor(scene, cv2.COLOR_BGR2GRAY)
        slots = self._detect_slots_via_quantity_boxes(scene)
        print(f"Detected {len(slots)} potential slots.")

        results = []
        for i, (bx, by, bw, bh) in enumerate(slots):
            # Estimate card region from quantity box
            card_w = int(bw * 4.5)
            card_h = int(card_w * 1.4)
            cx, cy = max(0, bx + bw - card_w), max(0, by + bh - card_h)

            card_crop = gray_scene[cy : by + bh, cx : bx + bw]
            cid = self._match_card(card_crop)
            qty = self._detect_quantity(scene[by : by + bh, bx : bx + bw])

            if cid:
                results.append({"card_id": cid, "quantity": qty})
                print(f"Match: {cid} x{qty}")
            else:
                print(f"Slot {i} at ({bx},{by}): No match found.")

        return results

    def _detect_slots_via_quantity_boxes(self, img):
        """Find card slots by looking for rectangular contours with specific proportions."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Use adaptive thresholding to be robust to brightness/contrast
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        boxes = []
        img_h, img_w = img.shape[:2]
        img_area = img_h * img_w

        for i, cnt in enumerate(contours):
            # We want "leaf" contours or those with small children (the numbers inside)
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h

            # Card aspect ratio is ~0.7, quantity box is ~1.5-2.0
            # Let's look for the quantity boxes first as they are very distinct white-on-black or inverse
            if 15 < w < 100 and 15 < h < 80:
                aspect = w / float(h)
                if 1.0 < aspect < 2.5:
                    # Check if it's "mostly black" in the original (or whatever color the UI uses)
                    # For Loveca, these are black boxes with white text.
                    boxes.append((x, y, w, h))

        # Filter: Deduplicate similar boxes
        unique_boxes = []
        for b in sorted(boxes, key=lambda x: x[1] * 10000 + x[0]):
            if not any(abs(b[0] - ub[0]) < 10 and abs(b[1] - ub[1]) < 10 for ub in unique_boxes):
                unique_boxes.append(b)

        # If we failed to find boxes, fallback to grid detection?
        # For now, let's see if this picks up more than 1.
        return unique_boxes

    def _match_card(self, card_gray):
        _, des_slot = self.orb.detectAndCompute(card_gray, None)
        if des_slot is None:
            return None

        best_cid = None
        max_matches = 0
        for cid, des_db in self.card_features.items():
            matches = self.matcher.match(des_slot, des_db)
            good = [m for m in matches if m.distance < 35]
            if len(good) > max_matches:
                max_matches = len(good)
                best_cid = cid

        return best_cid if max_matches > 5 else None

    def _detect_quantity(self, box_img):
        """Estimate quantity based on white pixel density (digital only)."""
        gray = cv2.cvtColor(box_img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
        white_count = cv2.countNonZero(thresh)

        # This mapping is specific to the UI font size in the screenshot
        if white_count < 100:
            return 1
        if white_count < 180:
            return 2
        if white_count < 250:
            return 3
        return 4  # Most common in digital decks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--save", default="local_recognized_deck.json")
    args = parser.parse_args()

    scanner = LocalDeckScanner()
    scanner.index_cards()
    results = scanner.find_cards_in_image(args.image)

    if results:
        with open(args.save, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Recognized {len(results)} cards. Output saved to {args.save}")


if __name__ == "__main__":
    main()
