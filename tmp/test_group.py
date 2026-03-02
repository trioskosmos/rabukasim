import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from engine.models.enums import Group

test_series = "ラブライブ！虹ヶ咲学園スクールアイドル同好会"
group = Group.from_japanese_name(test_series)
print(f"Series: {test_series}")
print(f"Parsed Group: {group.name} ({int(group)})")

test_series_2 = "ラブライブ！"
group_2 = Group.from_japanese_name(test_series_2)
print(f"Series: {test_series_2}")
print(f"Parsed Group: {group_2.name} ({int(group_2)})")
