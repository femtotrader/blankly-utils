# WIP: Not usable

using ArgParse
using Dates
using Glob
using JSON
using DataFrames
using XLSX
using Dash
using DashBootstrapComponents

const hidden_style = Dict("display" => "none")
const empty_style = Dict{String, String}()
const empty_figure = Dict{String, String}()

struct BacktestResults
    results
    metrics
    history
    trades_created
    trades_executed_market_orders
    trades_limits_canceled
    trades_limits_executed
end

path = "output"
refresh_sec = 300  # seconds
const s_themes = join(map(s -> "\"" * string(s) * "\"", keys(dbc_themes)), ", ")

function create_app(theme)
    bc_theme = getfield(dbc_themes, Symbol(theme))
    app = dash(external_stylesheets=[bc_theme])
    return app
end


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

function load_backtest_all_results(backtest::AbstractString)
    println("load_backtest_all_results")

    results = load_backtest_results(backtest)
    metrics = load_backtest_metrics(backtest)

    fname = joinpath(path, backtest, "results_history.xlsx")
    table = XLSX.readtable(fname, "Sheet1", infer_eltypes=true)
    df_history = DataFrame(table)

    fname = joinpath(path, backtest, "results_trades_created.xlsx")
    df_trades_created = DataFrame(XLSX.readtable(fname, "Sheet1", infer_eltypes=true))

    fname = joinpath(path, backtest, "results_trades_executed_market_orders.xlsx")
    df_trades_executed_market_orders = DataFrame(XLSX.readtable(fname, "Sheet1", infer_eltypes=true))

    fname = joinpath(path, backtest, "results_trades_limits_canceled.xlsx")
    df_trades_limits_canceled = DataFrame()
    try
        df_trades_limits_canceled = DataFrame(XLSX.readtable(fname, "Sheet1", infer_eltypes=true))
    catch e
        println(e)
    end

    fname = joinpath(path, backtest, "results_trades_limits_executed.xlsx")
    df_trades_limits_executed = DataFrame()
    try
        df_trades_limits_executed = DataFrame(XLSX.readtable(fname, "Sheet1", infer_eltypes=true))
    catch e
        println(e)
    end

    global backtest_results
    backtest_results = BacktestResults(results, metrics, df_history, df_trades_created,
        df_trades_executed_market_orders, df_trades_limits_canceled, df_trades_limits_executed)

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
        html_meta(httpEquiv="refresh", content=string(refresh_sec)),
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
        html_button(children="Load backtest results", id="but-load", n_clicks=0, disabled=true),
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
            #disabled=true
        ),
        dcc_dropdown(
            options=[],
            value="",
            id="dropdown-base-selection",
            #disabled=true
        ),
        html_br(),
        dcc_graph(id="ts-graph", style=hidden_style),
        dash_datatable(id="datatable-values", page_size=20),
        html_p("Last update: $(dt_now)", style=Dict("textAlign"=>"right"))
    ])
end



function parse_commandline()
    s = ArgParseSettings()

    @add_arg_table s begin
        "--host", "-H"
            help = "host (0.0.0.0=all, 127.0.0.1=localhost)"
            default = "0.0.0.0"
        "--port", "-p"
            help = "port (8000 or other)"
            arg_type = Int
            default = 8000
        "--refresh-sec"
            arg_type = Int
            default = refresh_sec
        "--theme"
            help = "A Bootswatch theme among $(s_themes). \
See https://dash-bootstrap-components.opensource.faculty.ai/docs/themes/explorer/ \
for more information"
            default = "YETI"
    end

    return parse_args(s)
end

function main()
    parsed_args = parse_commandline()
    println("Parsed args:")
    for (arg,val) in parsed_args
        println("  $arg  =>  $val")
    end
    global app, refresh_sec

    app = create_app(parsed_args["theme"])
    refresh_sec = parsed_args["refresh-sec"]
    # Layout definition with connected data points
    app.layout = serve_layout

    # Callbacks
    callback!(
        app,
        Output("datatable-metrics", "data"),
        Output("but-load", "disabled"),
        Input("dropdown-backtest-selection", "value"),
    ) do _backtest
        global backtest
        backtest = _backtest
        println("update_datatable_metrics_simple")
        metrics = load_backtest_metrics(backtest)
        data = [(Metrics=value["display_name"], Value=value["value"]) for (key, value) in metrics]
        return data, false
    end

    callback!(
        app,
        Output("div-results", "children"),
        Output("dropdown-data-selection", "value"),
        Input("but-load", "n_clicks"),
        prevent_initial_call=true
    ) do n_clicks
        load_backtest_all_results(backtest)
        exchange = backtest_results.results["exchange"]
        quote_currency = backtest_results.results["quote_currency"]
        start_time = unix2datetime(backtest_results.results["start_time"])
        stop_time = unix2datetime(backtest_results.results["stop_time"])
        stats = "Backtest from $(start_time) to $(stop_time) Exchange: $(exchange) Quote currency: $(quote_currency)"
        return stats, "History"
    end

    callback!(
        app,
        Output("dropdown-base-selection", "style"),
        Output("dropdown-base-selection", "options"),
        Output("dropdown-base-selection", "value"),
        Input("dropdown-data-selection", "value"),
        State("dropdown-backtest-selection", "value"),
        prevent_initial_call=true
    ) do data, backtest
        println("update_ts_graph_figure")
        println(backtest)
        println(data)
        if data == "History"
            cols = names(backtest_results.history)[2:end]
            return (
                Dict{String,String}(),
                cols,
                cols[end],
            )
        # elseif data == "Trades created":
        #    df = load_data_trades_created(backtest)
        #    return  Dict{String,String}(), [], nothing
        else
            return Dict("display"=>"none"), [], nothing
        end
    end


    callback!(
        app,
        Output("ts-graph", "figure"),
        Output("ts-graph", "style"),
        Output("datatable-values", "data"),
        #Input("dropdown-data-selection", "disabled"),
        #Input("dropdown-base-selection", "disabled"),
        #Input("dropdown-backtest-selection", "value"),
        Input("dropdown-data-selection", "value"),
        Input("dropdown-base-selection", "value"),
        prevent_initial_call=true
    #) do backtest, data, base
    ) do data, base
        println("update_datatable_values_data")
        if data == "History"
            #backtest_results.history[:value] = backtest_results.history[:value].round(2)
            figure = Dict(
                "data" => [
                    Dict(
                        "x" => backtest_results.history[!, :time],
                        "y" => backtest_results.history[!, base],
                        "type" => "lines",
                    ),
                ],
                "layout" => Dict("title" => "$(data) ($(base))"),
            )
            datatable_data = [NamedTuple(row) for row in reverse(eachrow(backtest_results.history))]
            println(dash_datatable)
            return figure, empty_style, datatable_data
        elseif data == "Trades created"
            figure = Dict{String, String}()
            datatable_data = [NamedTuple(row) for row in eachrow(backtest_results.trades_created)]
            return figure, hidden_style, datatable_data
        elseif data == "Trades executed market orders"
            figure = empty_figure
            graph_style = hidden_style
            df = innerjoin(
                backtest_results.trades_created,
                backtest_results.trades_executed_market_orders,
                on=:id,
            )
            datatable_data = [NamedTuple(row) for row in eachrow(df)]
            return figure, graph_style, datatable_data
        elseif data == "Trades limits canceled"
            figure = empty_figure
            graph_style = hidden_style
            if :id in names(backtest_results.trades_limits_canceled)
                df = innerjoin(
                    backtest_results.trades_created,
                    backtest_results.trades_limits_canceled,
                    on=:id,
                )
            else
                df = backtest_results.trades_limits_canceled
            end
            datatable_data = [NamedTuple(row) for row in eachrow(df)]
            return figure, graph_style, datatable_data
        elseif data == "Trades limits executed"
            figure = empty_figure
            graph_style = hidden_style
            if :id in names(backtest_results.trades_limits_executed)
                df = innerjoin(
                    backtest_results.trades_created,
                    backtest_results.trades_limits_executed,
                    on=:id,
                )
            else
                df = backtest_results.trades_limits_executed
            end
            datatable_data = [NamedTuple(row) for row in eachrow(df)]
            return figure, graph_style, datatable_data
        else
            figure = empty_figure
            graph_style = hidden_style
            datatable_data = []
            return figure, graph_style, datatable_data    
        end

end

    # Run the Dash server
    Dash.run_server(app, parsed_args["host"], parsed_args["port"]; debug=true)
end

main()
