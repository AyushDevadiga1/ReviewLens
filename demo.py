"""
demo.py — one-command ReviewLens demo loop. No Docker required.

    python demo.py [--seed N] [--no-seed] [--port API] [--ui-port UI]

Does, in order:
  1. Fills missing env with demo defaults (real .env / exported vars win
     for anything already set — run with a clean env for the true demo).
  2. Ensures the spacy model exists (downloads it on first run).
  3. Creates SQLite tables; loads N Amazon reviews if the DB is empty.
  4. Starts uvicorn, waits for /health (first boot downloads the ~2.5 GB
     ABSA checkpoint — one time, needs network), then starts Streamlit.
  5. Ctrl+C stops both servers.

Nothing here touches Docker, and nothing is committed: demo.db and
model files are gitignored.
"""

import argparse
import os
import subprocess
import sys
import time
import urllib.request

REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)


def parse_args():
    parser = argparse.ArgumentParser(description="Run the ReviewLens demo.")
    parser.add_argument("--seed", type=int, default=300,
                        help="reviews to load when the DB is empty")
    parser.add_argument("--no-seed", action="store_true",
                        help="never auto-load sample data")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--ui-port", type=int, default=8501)
    return parser.parse_args()


def ensure_env(api_port: int):
    defaults = {
        "DATABASE_URL": "sqlite:///" + os.path.join(REPO, "demo.db"),
        "API_KEY_SECRET": "demo-key",
        "API_BASE_URL": f"http://localhost:{api_port}",
        "API_KEY": "demo-key",
    }
    for key, value in defaults.items():
        if not os.environ.get(key):
            os.environ[key] = value
    print("env: DATABASE_URL=" + os.environ["DATABASE_URL"])
    print("env: API at " + os.environ["API_BASE_URL"])


def ensure_spacy():
    try:
        import spacy  # noqa: F401
        spacy.load("en_core_web_sm")
        print("spacy model: present")
    except Exception:
        print("spacy model: missing — downloading (one time)...")
        subprocess.run([sys.executable, "-m", "spacy", "download",
                        "en_core_web_sm"], check=True)


def ensure_data(seed: int, no_seed: bool):
    from db.session import create_tables, SessionLocal
    from db.models import Product

    create_tables()
    db = SessionLocal()
    try:
        n = db.query(Product).count()
    finally:
        db.close()
    if n > 0:
        print(f"data: {n} products already present, skipping seed")
        return
    if no_seed:
        print("data: empty and --no-seed given; dashboard will show "
              "degraded until you load data")
        return
    from data_ingestion.loaders.amazon_loader import load_amazon
    path = os.path.join(REPO, "data", "Cell_Phones_and_Accessories_5.json")
    if not os.path.exists(path):
        print(f"data: {path} missing — skipping seed "
              "(dashboard will show degraded)")
        return
    print(f"data: empty — loading {seed} sample reviews...")
    load_amazon(path, limit=seed)


def wait_for_health(base_url: str, timeout_s: int = 600):
    print("boot: waiting for API (first boot downloads models, be patient)...")
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(base_url + "/health/",
                                        timeout=10) as resp:
                if resp.status == 200:
                    print("boot: API healthy")
                    return True
        except Exception:
            pass
        time.sleep(5)
    return False


def main() -> int:
    args = parse_args()
    ensure_env(args.port)
    ensure_spacy()
    ensure_data(args.seed, args.no_seed)

    env = dict(os.environ)
    env["PYTHONPATH"] = REPO + os.pathsep + env.get("PYTHONPATH", "")
    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app",
         "--host", "127.0.0.1", "--port", str(args.port)],
        cwd=REPO, env=env)
    try:
        if not wait_for_health(f"http://localhost:{args.port}"):
            print("boot: API never became healthy — see terminal output above")
            return 1
        ui = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run",
             "frontend/Overview.py", "--server.port", str(args.ui_port),
             "--server.address", "127.0.0.1"],
            cwd=REPO, env=env)
        try:
            print(f"demo live: API http://localhost:{args.port}/health/  "
                  f"UI http://localhost:{args.ui_port}  (Ctrl+C to stop)")
            ui.wait()
        finally:
            ui.terminate()
    finally:
        api.terminate()
        api.wait(timeout=30)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
