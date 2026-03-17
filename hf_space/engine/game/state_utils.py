import logging
from typing import Any, Dict, Iterator

try:
    pass
except:
    pass

logger = logging.getLogger(__name__)


class StateMixin:
    """Base class for checking equality of state objects."""

    def __eq__(self, other):
        return isinstance(self, type(other)) and self.__dict__ == other.__dict__

    def copy_slots_to(self, target: "StateMixin") -> None:
        """Copy all fields defined in __slots__ to the target object."""
        if not hasattr(self, "__slots__"):
            return

        for name in self.__slots__:
            if hasattr(self, name):
                val = getattr(self, name)
                # Handle mutable types that need explicit copying
                if isinstance(val, list):
                    setattr(target, name, val[:])
                elif isinstance(val, set):
                    setattr(target, name, set(val))
                elif isinstance(val, dict):
                    setattr(target, name, dict(val))
                elif hasattr(val, "copy"):
                    setattr(target, name, val.copy())
                else:
                    setattr(target, name, val)


# ----------------------------------------------------------------------------
# Unique ID (UID) System
# ----------------------------------------------------------------------------
# Masks: 20 bits for Base ID, 12 bits for Instance
BASE_ID_MASK = 0xFFFFF
INSTANCE_SHIFT = 20


def get_base_id(uid: int) -> int:
    """Extract the base card definition ID from a potentially combined UID."""
    return uid & BASE_ID_MASK


def get_instance_index(uid: int) -> int:
    """Extract the instance index from a UID."""
    return uid >> INSTANCE_SHIFT


def create_uid(base_id: int, instance_index: int) -> int:
    """Create a unique instance ID from a base ID and an index."""
    # Safety check: base_id must fit in 20 bits
    if base_id > BASE_ID_MASK:
        logger.warning(f"Base ID {base_id} exceeds mask {BASE_ID_MASK}!")
    return (base_id & BASE_ID_MASK) | (instance_index << INSTANCE_SHIFT)


class MaskedDB(dict):
    """
    A dictionary wrapper that automatically masks unique instance IDs (UIDs)
    to retrieve data associated with the base ID.

    This allows the game state to essentially 'ignore' the instance part of an ID
    when looking up static card data.
    """

    def __init__(self, data: Dict[int, Any]):
        super().__init__(data)
        self._data = data

    def __getitem__(self, key: int) -> Any:
        # Resolve UID to base ID
        try:
            base_id = int(key) & BASE_ID_MASK
            if base_id in self._data:
                return self._data[base_id]
            # Fallback to string key for JSON-loaded data
            return self._data[str(base_id)]
        except (ValueError, TypeError):
            raise KeyError(key)

    def __contains__(self, key: object) -> bool:
        try:
            base_id = int(key) & BASE_ID_MASK
            return base_id in self._data or str(base_id) in self._data
        except (ValueError, TypeError):
            return False

    def get(self, key: int, default: Any = None) -> Any:
        try:
            if key is None:
                return default
            base_id = int(key) & BASE_ID_MASK
            if base_id in self._data:
                return self._data[base_id]
            # Fallback to string key
            return self._data.get(str(base_id), default)
        except (ValueError, TypeError):
            return default

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[int]:
        # Iterate over ORIGINAL base IDs (keys of _data)
        return iter(self._data)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()
