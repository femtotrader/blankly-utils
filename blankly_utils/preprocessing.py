import sys
import uuid


def cat(fname):
    print("#" * 10 + f" {fname}" + "#" * 10)
    with open(fname, "r") as fd:
        print(fd.read())


def get_run_id():
    run_id = uuid.uuid4().hex
    run_id = run_id[:12]  # shorten
    return run_id


def create_dotenv_file(fname):
    run_id = get_run_id()
    with open(fname, "w") as f:
        f.write(f"RUN_ID={run_id}\n")


def main():
    if len(sys.argv) == 2:
        mode = sys.argv[1]
        fname = "strategy.env"
        create_dotenv_file(fname)
        cat(fname)
        cat("bot.py")
    else:
        raise NotImplementedError("Incorrect number of arguments (1 required)")


if __name__ == "__main__":
    main()
