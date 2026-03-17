import numpy as np
from flask import Flask
from flask.json.provider import DefaultJSONProvider


class NumpyJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


app = Flask(__name__)
app.json = NumpyJSONProvider(app)


def test_json_serialization():
    print("Testing JSON Serialization with Numpy Types...")

    data = {
        "normal_bool": True,
        "numpy_bool": np.bool_(True),
        "numpy_int": np.int64(10),
        "numpy_float": np.float64(1.5),
    }

    try:
        json_str = app.json.dumps(data)
        print("Success:", json_str)
    except TypeError as e:
        print("FAILED:", e)
        # Check if it matches the user error
        if (
            "Object of type bool is not JSON serializable" in str(e)
            or "Object of type bool_ is not JSON serializable" in str(e)
        ):  # Note: python error is usually 'Object of type bool_ is not JSON serializable' for numpy bools, user said 'bool'. Wait.
            # User said: "TypeError: Object of type bool is not JSON serializable"
            # Standard bool should be serializable.
            # Maybe they meant 'bool_'? Or maybe something else?
            # Let's see what the output is.
            pass


if __name__ == "__main__":
    test_json_serialization()
