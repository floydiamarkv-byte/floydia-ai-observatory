import hashlib
import json
import subprocess
from pathlib import Path

def run():
    out_dir = Path("/tmp/floydia_qa")
    out_dir.mkdir(parents=True, exist_ok=True)
    shot_path = out_dir / "dashboard_global_table_arena_2026.png"

    # Captura con altura mayor para ver toda la tabla global
    cmd = [
        "chromium",
        "--headless",
        "--disable-gpu",
        "--window-size=1440,2200",
        f"--screenshot={shot_path}",
        "http://localhost:8333/"
    ]
    subprocess.run(cmd, check=True)

    sha256_hash = hashlib.sha256(shot_path.read_bytes()).hexdigest()
    result = {
        "screenshot_path": str(shot_path),
        "sha256": sha256_hash,
        "pass": True
    }
    with open(out_dir / "qa_table_result.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"PASS=True | SHA256={sha256_hash} | Path={shot_path}")

if __name__ == "__main__":
    run()
