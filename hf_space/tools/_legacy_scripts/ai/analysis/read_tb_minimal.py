import os
import struct

from google.protobuf import event_pb2


def parse_tfevent(file_path):
    with open(file_path, "rb") as f:
        while True:
            # Read length (8 bytes)
            length_bytes = f.read(8)
            if not length_bytes:
                break
            length = struct.unpack("q", length_bytes)[0]

            # Read crc (4 bytes)
            f.read(4)

            # Read event data
            data = f.read(length)
            if not data:
                break

            # Read crc (4 bytes)
            f.read(4)

            event = event_pb2.Event()
            event.ParseFromString(data)

            if event.HasField("summary"):
                for v in event.summary.value:
                    if v.HasField("simple_value"):
                        yield event.step, v.tag, v.simple_value


log_dir = r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\logs\vector_tensorboard\ProgressPPO_0120_000139_1"
event_files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if "tfevents" in f]

stats = {}
if event_files:
    # Use only the first file for speed
    for step, tag, value in parse_tfevent(event_files[0]):
        if tag not in stats:
            stats[tag] = []
        stats[tag].append(value)

results = {}
for tag, values in stats.items():
    if values:
        results[tag] = {
            "last": values[-1],
            "avg_recent": sum(values[-5:]) / len(values[-5:]),
            "max": max(values),
            "min": min(values),
        }

import json

print(json.dumps(results, indent=2))
