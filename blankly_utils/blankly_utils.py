import blankly
import math
from blankly.enums import Side
from blankly.exchanges.orders.market_order import MarketOrder
from blankly import utils


def clamp(x: float, lo=0, hi=1):
    """
    clamp a value to be within two bounds
    returns lo if x < lo, hi if x > hi else x
    """
    return min(hi, max(x, lo))


def portfolio_value(interface, quote_asset, available=True, hold=True):
    portfolio_value = 0.0
    for base_asset, account_values in interface.account.items():
        if account_values["available"] != 0 and available:
            if base_asset == quote_asset:
                values = account_values["available"]
                portfolio_value += values
            else:
                symbol = f"{base_asset}-{quote_asset}"
                price = interface.get_price(symbol)
                values = price * account_values["available"]
                portfolio_value += values
        if account_values["hold"] != 0 and hold:
            if base_asset == quote_asset:
                values = account_values["hold"]
                portfolio_value += values
            else:
                symbol = f"{base_asset}-{quote_asset}"
                price = interface.get_price(symbol)
                values = price * account_values["hold"]
                portfolio_value += values

    return portfolio_value


def get_position_weight(interface, symbol):
    quote_asset = utils.get_quote_asset(symbol)  # XBT-USDT -> USDT
    base_asset = utils.get_base_asset(symbol)  # XBT-USDT -> XBT
    pv = portfolio_value(interface, quote_asset)
    return (
        interface.get_account(base_asset)["available"] * interface.get_price(symbol)
    ) / pv


def market_order_target(interface, symbol: str, target: float) -> MarketOrder:
    quote_asset = utils.get_quote_asset(symbol)
    base_asset = utils.get_base_asset(symbol)
    pv = portfolio_value(interface, quote_asset)
    pos_weight = (
        interface.get_account(base_asset)["available"] * interface.get_price(symbol)
    ) / pv
    buy_pos = (target - pos_weight) * pv
    price = interface.get_price(symbol)
    filter = interface.get_order_filter(symbol)
    increment = filter["market_order"]["base_increment"]
    precision = utils.increment_to_precision(increment)
    buy_size = blankly.trunc(abs(buy_pos) / price, precision)
    sell_size = math.floor((abs(buy_pos) / price) * (10**precision)) / (
        10**precision
    )
    if buy_pos > 0:
        if buy_size >= filter["market_order"]["base_min_size"]:
            return interface.market_order(symbol, Side.BUY, buy_size)
    elif buy_pos < 0:
        if sell_size >= filter["market_order"]["base_min_size"]:
            return interface.market_order(symbol, Side.SELL, sell_size)
    return None
