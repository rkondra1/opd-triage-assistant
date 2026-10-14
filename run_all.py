"""
Convenience runner: generate data -> train -> evaluate -> wait-time sim.

    python run_all.py
    python run_all.py --n 30000 --seed 7
"""

from __future__ import annotations

import argparse

from src import evaluate, generate_data, train, waittime


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30000)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    print("\n[1/4] Generating synthetic data ...")
    generate_data.generate(args.n, args.seed)

    print("\n[2/4] Training models ...")
    train.main()

    print("\n[3/4] Evaluating (asymmetric cost + emergency recall) ...")
    evaluate.evaluate()

    print("\n[4/4] Wait-time simulation (stretch goal) ...")
    waittime.main()

    print("\nDone. Launch the demo UI with:  streamlit run app/streamlit_app.py")


if __name__ == "__main__":
    main()
