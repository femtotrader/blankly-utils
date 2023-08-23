import sys
from pathlib import Path
import shutil
from dotenv import dotenv_values


def main():
    config = dotenv_values(".env")
    run_id = config["RUN_ID"]
    if len(sys.argv) == 2:
        mode = sys.argv[1]
        if mode == "backtest":
            fname = Path("bot_run_backtest.html")
            # dest = Path(f"output")  # copy but don't rename file
            dest = Path(
                f"output/bot_run_backtest_{run_id}.html"
            )  # copy and rename with run_id
            shutil.copy(fname, dest)
            fname = Path(".env")
            dest = Path("output")
            shutil.copy(fname, dest)
        elif mode == "papertrade":
            print(f"No post-processing for {mode}")
        elif mode == "livetrade":
            print(f"No post-processing for {mode}")
        else:
            raise NotImplementedError(f"Unsupported mode '{mode}'")
    else:
        raise NotImplementedError("Incorrect number of arguments (1 required)")


if __name__ == "__main__":
    main()
