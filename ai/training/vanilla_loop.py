import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _maybe_reexec_workspace_venv() -> None:
    venv_python = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        return
    current_python = Path(sys.executable).resolve()
    if current_python == venv_python.resolve():
        return
    if os.environ.get("RABUKA_SKIP_VENV_REEXEC") == "1":
        return

    env = os.environ.copy()
    env["RABUKA_SKIP_VENV_REEXEC"] = "1"
    result = subprocess.run([str(venv_python), *sys.argv], env=env)
    raise SystemExit(result.returncode)

from alphazero.training.overnight_vanilla import main

if __name__ == "__main__":
    _maybe_reexec_workspace_venv()
    main()