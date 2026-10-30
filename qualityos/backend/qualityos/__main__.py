import argparse
import os
from pathlib import Path

from .api import ROOT, create_app


def main():
    parser = argparse.ArgumentParser(description="Local QualityOS synthetic prototype")
    parser.add_argument(
        "command", choices=["serve", "init", "evaluate"], nargs="?", default="serve"
    )
    parser.add_argument("--port", type=int, default=8107)
    args = parser.parse_args()
    app = create_app()
    if args.command == "init":
        print(
            "Local store initialised. Private account credentials are in qualityos/var/local-credentials.json."
        )
    elif args.command == "evaluate":
        from .evaluation import run_evaluation

        result = run_evaluation(app.state.store)
        print(
            f"Independent synthetic corpus: {result['passed']}/{result['total']} matched; report saved locally."
        )
    else:
        import uvicorn

        uvicorn.run(app, host="127.0.0.1", port=args.port, workers=1, log_level="warning")


if __name__ == "__main__":
    main()
