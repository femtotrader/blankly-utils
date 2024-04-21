# WIP: Not usable

using Dates
using Glob
using JSON
using DataFrames
using XLSX
using Dash

# Create Dash application
app = dash()
path = "output"


function load_backtest_results(backtest::AbstractString)
    fname = joinpath(path, backtest, "results.json")
    results = JSON.parsefile(fname)
    return results
end

function load_backtest_metrics(backtest::AbstractString)
    # Construct the file path
    fname = joinpath(path, backtest, "results_metrics.json")
  
    # Read the JSON file using JSON.jl
    metrics = JSON.parsefile(fname)
    return metrics

    # Convert dict of dict to DataFrame
    # names = String[]
    # values = Float64[]
    # for (key, value) in metrics
    #     push!(names, value["display_name"])
    #     push!(values, value["value"])
    # end
    # df_metrics = DataFrame(Dict("Metrics" => names, "Value" => values))
    # 
    # return df_metrics
end

struct BacktestResults
    results
    metrics
    history
    #trades_created
    #trades_executed_market_orders
    #trades_limits_canceled
    #trades_limits_executed
end

function load_backtest(backtest::AbstractString)
    println("load_backtest")

    results = load_backtest_results(backtest)
    metrics = load_backtest_metrics(backtest)

    fname = joinpath(path, backtest, "results_history.xlsx")
    table = XLSX.readtable(fname, "Sheet1")
    df_history = DataFrame(table)

    global backtest_results
    backtest_results = BacktestResults(results, metrics, df_history)

    println("loading completed")

    return backtest_results
end


function get_backtest_paths(path::AbstractString)
    return sort(filter(isdir, glob("*", path)))
end

function get_backtest_names(backtest_paths::Vector)
    backtest_names = String[]
    for p in backtest_paths
        backtest_name = splitpath(p)[end]
        metrics = load_backtest_metrics(backtest_name)
        if metrics["cum_returns"]["value"] != 0.0
            push!(backtest_names, backtest_name)
        end
    end
    return backtest_names
end

function serve_layout()
    dt_now = now(UTC)
    backtest_paths = get_backtest_paths(path)
    backtest_names = get_backtest_names(backtest_paths)
    return html_div([
        # html_meta(httpEquiv="refresh", content=String(refresh_sec)),
        html_h1(children="Display backtests", style=Dict("textAlign"=>"center")),
        html_div(children="Choose backtest"),
        html_br(),
        dcc_dropdown(
            options=backtest_names,
            value=backtest_names[end],
            id="dropdown-backtest-selection",
            # placeholder="Choose backtest",
        ),
        html_br(),
        html_div(
            children="", id="div-results"
        ),  # , style=Dict("display"=>"none")),
        html_br(),
        dash_datatable(id="datatable-metrics"),
        html_br(),
        dcc_dropdown(
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
        dcc_dropdown(
            options=[],
            value="",
            id="dropdown-base-selection",
        ),
        html_br(),
        dcc_graph(id="ts-graph"),
        dash_datatable(id="datatable-values", page_size=20),
        html_p("Last update: $(dt_now)", style=Dict("textAlign"=>"right"))
    ])
end

# Layout definition with connected data points
app.layout = serve_layout

# Callbacks
callback!(
    app,
    Output("datatable-metrics", "data"),
    Output("div-results", "children"),
    Output("dropdown-data-selection", "value"),
    Input("dropdown-backtest-selection", "value"),
) do backtest
    println("update_datatable_metrics")
    load_backtest(backtest)
    data = [(Metrics=value["display_name"], Value=value["value"]) for (key, value) in backtest_results.metrics]
    exchange = backtest_results.results["exchange"]
    quote_currency = backtest_results.results["quote_currency"]
    start_time = unix2datetime(backtest_results.results["start_time"])
    stop_time = unix2datetime(backtest_results.results["stop_time"])
    stats = "Backtest from $(start_time) to $(stop_time) Exchange: $(exchange) Quote currency: $(quote_currency)"
    return data, stats, "History"
end

# Run the Dash server
Dash.run_server(app, "0.0.0.0", 8000; debug=true)
