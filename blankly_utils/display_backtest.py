#!/usr/bin/env python3

import os
from pathlib import Path
from collections import namedtuple
import datetime
import json
import warnings
from dotenv import load_dotenv
import click
import pandas as pd
from dash import Dash, html, dcc, dash_table, callback, Output, Input
import dash_bootstrap_components as dbc
import dash_auth


load_dotenv()

"""
Create a .env file like:
WEB_UI_ADMIN_USERNAME=YourAdminUsername
WEB_UI_ADMIN_PASSWORD=YourAdminPassword
"""
VALID_USERNAME_PASSWORD_PAIRS = {
    os.getenv("WEB_UI_ADMIN_USERNAME", default="admin"): os.getenv(
        "WEB_UI_ADMIN_PASSWORD", default="password"
    )
}
print(VALID_USERNAME_PASSWORD_PAIRS)


@click.command()
@click.option(
    "--host",
    default="0.0.0.0",
    help="host (0.0.0.0=all, 127.0.0.1=localhost)",
)
@click.option(
    "--port",
    default=8050,
    help="port (8050 or other)",
)
@click.option(
    "--refresh-sec",
    default=300,
)
@click.option(
    "--theme",
    default="YETI",
    help="A Bootswatch theme among CERULEAN, COSMO, CYBORG, "
    "DARKLY, FLATLY, JOURNAL, LITERA, LUMEN, LUX, MATERIA, "
    "MINTY, MORPH, PULSE, QUARTZ, SANDSTONE, SIMPLEX, SKETCHY, "
    "SLATE, SOLAR, SPACELAB, SUPERHERO, UNITED, VAPOR, YETI, ZEPHYR. "
    "See https://dash-bootstrap-components.opensource.faculty.ai/docs/themes/explorer/ "
    "for more information",
)
def main(host, port, refresh_sec, theme):
    # print("main")
    # Incorporate data

    path = Path("output")

    def load_backtest(backtest):
        print(f'load_backtest("{backtest}")')
        global backtest_results

        fname = path / backtest / "results.json"
        with open(fname, "r") as fd:
            results = json.load(fd)

        fname = path / backtest / "results_metrics.json"
        df_metrics = pd.read_json(fname)
        df_metrics = df_metrics.loc[["display_name", "value"], :].transpose()
        df_metrics.columns = ["Metrics", "Value"]

        fname = path / backtest / "results_history.xlsx"
        df_history = pd.read_excel(fname)
        df_history.set_index("time", inplace=True)

        fname = path / backtest / "results_trades_created.xlsx"
        df_trades_created = pd.read_excel(fname)

        fname = path / backtest / "results_trades_executed_market_orders.xlsx"
        df_trades_executed_market_orders = pd.read_excel(fname)

        fname = path / backtest / "results_trades_limits_canceled.xlsx"
        df_trades_limits_canceled = pd.read_excel(fname)

        fname = path / backtest / "results_trades_limits_executed.xlsx"
        df_trades_limits_executed = pd.read_excel(fname)

        BacktestResults = namedtuple(
            "BacktestResults",
            [
                "results",
                "metrics",
                "history",
                "trades_created",
                "trades_executed_market_orders",
                "trades_limits_canceled",
                "trades_limits_executed",
            ],
        )

        backtest_results = BacktestResults(
            results=results,
            metrics=df_metrics,
            history=df_history,
            trades_created=df_trades_created,
            trades_executed_market_orders=df_trades_executed_market_orders,
            trades_limits_canceled=df_trades_limits_canceled,
            trades_limits_executed=df_trades_limits_executed,
        )

        print("end of load")

    def serve_layout():
        now = datetime.datetime.utcnow()

        backtest_paths = sorted(filter(lambda p: p.is_dir(), path.glob("*")))
        backtest_names = [path.parts[-1] for path in backtest_paths]

        return html.Div(
            [
                html.Meta(httpEquiv="refresh", content=str(refresh_sec)),
                html.H1(children="Display backtests", style={"textAlign": "center"}),
                html.Div(children="Choose backtest"),
                html.Br(),
                dcc.Dropdown(
                    options=backtest_names,
                    value=backtest_names[-1],
                    id="dropdown-backtest-selection",
                    # placeholder="Choose backtest",
                ),
                html.Br(),
                html.Div(
                    children="", id="div-results"
                ),  # , style={"display": "none"}),
                html.Br(),
                dash_table.DataTable(id="datatable-metrics"),
                html.Br(),
                dcc.Dropdown(
                    options=[
                        "History",
                        "Trades created",
                        "Trades executed market orders",
                        "Trades limits canceled",
                        "Trades limits executed",
                    ],
                    value="History",
                    id="dropdown-data-selection",
                ),
                dcc.Dropdown(
                    options=[],
                    value="",
                    id="dropdown-base-selection",
                ),
                html.Br(),
                dcc.Graph(id="ts-graph"),
                dash_table.DataTable(id="datatable-values", page_size=20),
                html.P(f"Last update: {now}", style={"textAlign": "right"}),
            ]
        )

    # Initialize the app
    # external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    # external_stylesheets = [
    #     "https://gist.githubusercontent.com/zluvsand/4debf98c2d12bea077275c56f90bc767/raw/ccbfe65ac9dab4b232ee016e6344c3b2ffba72b8/style.css"
    # ]
    # app = Dash(__name__, external_stylesheets=external_stylesheets)
    bc_theme = getattr(
        dbc.themes, theme
    )  # Boostrap Components Theme see https://dash-bootstrap-components.opensource.faculty.ai/docs/themes/
    app = Dash(
        __name__, external_stylesheets=[bc_theme]
    )  # Dash Bootstrap Components : BOOTSTRAP / CYBORG
    # app = Dash(__name__)

    # Setup basic authentification
    secret_key = os.getenv("WEB_UI_SECRET_KEY", default="Super Secret Key")
    auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS, secret_key=secret_key)

    # App layout
    app.layout = serve_layout

    @app.callback(
        [
            Output("datatable-metrics", "data"),
            Output("div-results", "children"),
            Output("dropdown-data-selection", "value"),
        ],
        [
            Input("dropdown-backtest-selection", "value"),
        ],
    )
    def update_datatable_metrics(backtest):
        print("update_datatable_metrics")
        load_backtest(backtest)

        data = backtest_results.metrics.to_dict("records")

        exchange = backtest_results.results["exchange"]
        quote_currency = backtest_results.results["quote_currency"]
        start_time = pd.to_datetime(backtest_results.results["start_time"], unit="s")
        stop_time = pd.to_datetime(backtest_results.results["stop_time"], unit="s")
        stats = f"Backtest from {start_time} to {stop_time} Exchange: {exchange} Quote currency: {quote_currency}"

        return data, stats, "History"

    @app.callback(
        [
            Output("dropdown-base-selection", "style"),
            Output("dropdown-base-selection", "options"),
            Output("dropdown-base-selection", "value"),
        ],
        [
            Input("dropdown-backtest-selection", "value"),
            Input("dropdown-data-selection", "value"),
        ],
    )
    def update_ts_graph_figure(backtest, data):
        print("update_ts_graph_figure")
        # load_backtest(backtest)
        if data == "History":
            return (
                {},
                backtest_results.history.columns,
                backtest_results.history.columns[-1],
            )
        # elif data == "Trades created":
        #    df = load_data_trades_created(backtest)
        #    return  {}, [], None
        else:
            return {"display": "none"}, [], None

    @app.callback(
        [
            Output("ts-graph", "figure"),
            Output("ts-graph", "style"),
            Output("datatable-values", "data"),
        ],
        [
            Input("dropdown-backtest-selection", "value"),
            Input("dropdown-data-selection", "value"),
            Input("dropdown-base-selection", "value"),
        ],
    )
    def update_datatable_values_data(backtest, data, base):
        print("update_datatable_values_data")
        # load_backtest(backtest)
        if data == "History":
            backtest_results.history["value"] = backtest_results.history["value"].round(
                2
            )
            figure = {
                "data": [
                    {
                        "x": backtest_results.history.index,
                        "y": backtest_results.history[base],
                        "type": "lines",
                    },
                ],
                "layout": {"title": f"{data} ({base})"},
            }
            graph_style = {}
            datatable_data = backtest_results.history.reset_index()[::-1].to_dict(
                orient="records"
            )
            return figure, graph_style, datatable_data
        elif data == "Trades created":
            figure = {}
            graph_style = {"display": "none"}
            datatable_data = backtest_results.trades_created.to_dict(orient="records")
            return figure, graph_style, datatable_data
        elif data == "Trades executed market orders":
            figure = {}
            graph_style = {"display": "none"}
            df = pd.merge(
                backtest_results.trades_created,
                backtest_results.trades_executed_market_orders,
                on="id",
            )
            datatable_data = df.to_dict(orient="records")
            return figure, graph_style, datatable_data
        elif data == "Trades limits canceled":
            figure = {}
            graph_style = {"display": "none"}
            if "id" in backtest_results.trades_limits_canceled.columns:
                df = pd.merge(
                    backtest_results.trades_created,
                    backtest_results.trades_limits_canceled,
                    on="id",
                )
            else:
                df = backtest_results.trades_limits_canceled
            datatable_data = df.to_dict(orient="records")
            return figure, graph_style, datatable_data
        elif data == "Trades limits executed":
            figure = {}
            graph_style = {"display": "none"}
            if "id" in backtest_results.trades_limits_executed.columns:
                df = pd.merge(
                    backtest_results.trades_created,
                    backtest_results.trades_limits_executed,
                    on="id",
                )
            else:
                df = backtest_results.trades_limits_executed
            datatable_data = df.to_dict(orient="records")
            return figure, graph_style, datatable_data

        figure = {}
        graph_style = {"display": "none"}
        datatable_data = []
        return figure, graph_style, datatable_data

    # Run the app
    app.run(host=host, port=port, debug=True)


if __name__ == "__main__":
    main()
