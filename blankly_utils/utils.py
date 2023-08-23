#!/usr/bin/env python3
import uuid
from dotenv import dotenv_values
from pathlib import Path
import json
import pandas as pd


def get_run_id():
    config = dotenv_values(".env")
    run_id = config["RUN_ID"]
    return run_id


def get_backtest_id():
    backtest_id = uuid.uuid4().hex
    backtest_id = backtest_id[:8]  # shorten
    return backtest_id


def get_final_values(results):
    final_values = results.get_account_history().iloc[-1].to_dict()
    del final_values["time"]
    for key in list(final_values.keys()):
        # if key.startswith("Account Value ("):
        #    del final_values[key]
        if final_values[key] == 0.0:
            del final_values[key]
    return final_values


def export_results(results, path="."):
    path = Path(path)
    d_results = results.to_dict()

    with open(path / "results_metrics.json", "w") as fd:
        json.dump(d_results["metrics"], fd)
    del d_results["metrics"]
    df_history = pd.DataFrame.from_records(d_results["history"])
    df_history["time"] = pd.to_datetime(df_history["time"], unit="s")
    df_history.set_index("time", inplace=True)
    df_history.to_excel(path / "results_history.xlsx", index=True)
    del d_results["history"]

    for col in [
        "created",
        "limits_executed",
        "limits_canceled",
        "executed_market_orders",
    ]:
        df_trades = pd.DataFrame.from_records(d_results["trades"][col])
        fname = path / ("results_trades_%s.xlsx" % col)
        if "time" in df_trades.columns:
            df_trades["time"] = pd.to_datetime(df_trades["time"], unit="s")
            df_trades.set_index("time", inplace=True)
            df_trades.to_excel(fname, index=True)
        else:
            df_trades.to_excel(fname, index=False)
    del d_results["trades"]

    # json_results = json.dumps(d_results)
    with open(path / "results.json", "w") as fd:
        json.dump(d_results, fd)
