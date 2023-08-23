#!/usr/bin/env python3

import os
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
    "--db-uri",
    default="sqlite:///accounts.sqlite",
    help="DB uri to send account values",
)
@click.option(
    "--quote",
    default="USDT",
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
def main(host, port, db_uri, quote, refresh_sec, theme):
    # print("main")
    # Incorporate data

    def load_data_account_values():
        global df
        # print("load_data_account_values")
        df = pd.read_sql(f"SELECT * FROM account_values", db_uri)
        # df = pd.read_sql(
        #     f"SELECT * FROM account_values WHERE token=:token",
        #     db_uri,
        #     params={"token": token},
        # )
        df["time"] = pd.to_datetime(df["time"])
        df.set_index("time", inplace=True)

    def serve_layout():
        load_data_account_values()

        year_min = df.index.year.min()
        year_max = df.index.year.max()
        years = df.index.year.unique()
        year_current = year_max

        now = datetime.datetime.utcnow()

        return html.Div(
            [
                html.Meta(httpEquiv="refresh", content=str(refresh_sec)),
                html.H1(children="Monitor strategy", style={"textAlign": "center"}),
                html.Div(children="Choose year / token / graph / base..."),
                html.Br(),
                dcc.Slider(
                    min=year_min,
                    max=year_max,
                    step=None,
                    value=year_current,
                    marks={str(year): str(year) for year in years},
                    id="year-slider",
                ),
                html.Br(),
                dcc.Dropdown(id="dropdown-token-selection"),
                html.Br(),
                dcc.Dropdown(
                    [
                        "Available amount sum",
                        "Hold amount sum",
                        "Available amount",
                        "Hold amount",
                        "Available",
                        "Hold",
                    ],
                    "Available amount sum",
                    id="dropdown-graph-selection",
                ),
                html.Br(),
                dcc.Dropdown(
                    # options=bases, value=bases[0], id="dropdown-base-selection", style={"display": "none"}
                    id="dropdown-base-selection",
                    style={"display": "none"},
                ),
                html.Br(),
                dcc.Graph(id="ts-graph"),
                dash_table.DataTable(id="datatable-account-values", page_size=20),
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
    auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)

    # App layout
    app.layout = serve_layout

    def filter_by_year(df, year):
        dff = df[df.index.year == year].copy()
        year_min = dff.index.year.min()
        year_max = dff.index.year.max()
        years = dff.index.year.unique()
        return dff

    def filter_by_year_and_token(df, year, token):
        dff = df[df.token == token].copy()
        dff = dff[dff.index.year == year]
        year_min = dff.index.year.min()
        year_max = dff.index.year.max()
        years = dff.index.year.unique()

        return dff

    @app.callback(
        [
            Output("dropdown-token-selection", "options"),
            Output("dropdown-token-selection", "value"),
        ],
        [
            Input("year-slider", "value"),
        ],
    )
    def update_dropdown_token_selection(year):
        # print("update_dropdown_token_selection")
        dff = filter_by_year(df, year)
        tokens = dff.token.unique()
        if len(tokens) > 0:
            token = dff.sort_index(ascending=True).token[-1]  # last seen strategy token
        else:
            token = None
        return tokens, token

    @app.callback(
        Output("ts-graph", "figure"),
        [
            Input("dropdown-token-selection", "value"),
            Input("dropdown-graph-selection", "value"),
            Input("dropdown-base-selection", "value"),
            Input("year-slider", "value"),
        ],
    )
    def update_ts_graph_figure(token, graph, base, year):
        # print("update_ts_graph_figure")
        dff = filter_by_year_and_token(df, year, token)
        _graph = graph.lower().replace(" ", "_")

        if graph in ["Available amount sum", "Hold amount sum"]:
            # print(dff[_graph])
            return {
                "data": [
                    {
                        "x": dff.index,
                        "y": dff[_graph],
                        "type": "lines",
                    },
                ],
                "layout": {"title": f"{graph} ({quote})"},
            }
        elif graph in ["Available amount", "Hold amount", "Available", "Hold"]:
            ts = pd.Series(0.0, index=dff.index)
            # print(graph, _graph, base)
            for dt, row in dff.iterrows():
                account = json.loads(row[_graph])
                if base in account.keys():
                    value = account[base]
                else:
                    value = 0
                ts.loc[dt] = value
            return {
                "data": [
                    {
                        "x": ts.index,
                        "y": ts.values,
                        "type": "lines",
                    },
                ],
                "layout": {"title": f"{graph} ({base})"},
            }
        else:
            warnings.warn(f"Unsupported graph '{graph}'")

    @app.callback(
        [
            Output("dropdown-base-selection", "options"),
            Output("dropdown-base-selection", "value"),
            Output("dropdown-base-selection", "style"),
        ],
        [
            Input("year-slider", "value"),
            Input("dropdown-token-selection", "value"),
            Input("dropdown-graph-selection", "value"),
        ],
    )
    def update_dropdown_base_selection_style(year, token, graph):
        # print("update_dropdown_base_selection_style")
        if graph in ["Available amount sum", "Hold amount sum"]:
            return [], "", {"display": "none"}
        else:
            dff = filter_by_year_and_token(df, year, token)
            _graph = graph.lower().replace(" ", "_")  # WIP
            selected = dff[_graph].map(json.loads)
            bases = list(set.union(*selected.map(lambda d: set(d.keys())).values))
            if len(bases) > 0:
                base = bases[0]
            else:
                base = ""
            return bases, base, {}

    @app.callback(
        Output("datatable-account-values", "data"),
        [Input("year-slider", "value"), Input("dropdown-token-selection", "value")],
    )
    def update_datatable_account_values_data(year, token):
        # print("update_datatable_account_values_data")
        dff = filter_by_year_and_token(df, year, token).reset_index()
        return dff[::-1].to_dict("records")

    # Run the app
    app.run(host=host, port=port, debug=True)


if __name__ == "__main__":
    main()
