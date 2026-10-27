"""Build and check the whole Lean project in a clean Modal container.

    modal run scripts/modal_build.py                      # everything
    modal run scripts/modal_build.py --target InfinityMachineOutput.Chip.Mac

Prints the build log and the axioms used by the headline theorems."""
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[1]
image = (
    modal.Image.debian_slim()
    .apt_install("curl", "git", "ca-certificates")
    .run_commands(
        "curl -sSfL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh"
        " | sh -s -- -y --default-toolchain none")
    .add_local_dir(ROOT, "/src", ignore=[".lake", ".git", "**/__pycache__"], copy=True)
    .run_commands("cd /src && PATH=$HOME/.elan/bin:$PATH lake exe cache get")
)
app = modal.App("infinity-machine-output-lean", image=image)


@app.function(cpu=16, memory=131072, timeout=6 * 3600)
def build(target: str = "") -> str:
    import subprocess
    env = {"PATH": "/root/.elan/bin:/usr/local/bin:/usr/bin:/bin", "HOME": "/root"}
    cmd = "lake build " + target if target else "lake build && lake env lean scripts/Axioms.lean"
    r = subprocess.run(["bash", "-lc", f"cd /src && time ({cmd}) 2>&1"], env=env,
                       capture_output=True, text=True)
    keep = [ln for ln in r.stdout.splitlines()
            if ln.strip() and not ln.startswith(("warning", "Note:", "trace"))
            and "linter" not in ln and "character limit" not in ln]
    return f"exit {r.returncode}\n" + "\n".join(keep[-400:]) + "\n" + r.stderr[-3000:]


@app.local_entrypoint()
def main(target: str = ""):
    print(build.remote(target))
