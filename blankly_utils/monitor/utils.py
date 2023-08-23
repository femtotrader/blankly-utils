import warnings
import pandas as pd


def get_account_values(interface, quote):
    df = pd.DataFrame(interface.account).transpose()

    df = df[(df["available"] > 0) | (df["hold"] > 0)]

    for base in df.index:
        symbol = f"{base}-{quote}"
        if base != quote:
            try:
                price = interface.get_price(symbol)
            except:
                warnings.warn(f"can't fetch price for {symbol}")
                price = 0
        else:
            price = 1
        df.loc[base, "price"] = price
    df["available_amount"] = (df["available"] * df["price"]).fillna(0)
    df["hold_amount"] = (df["hold"] * df["price"]).fillna(0)
    df.sort_values("available_amount", ascending=False, inplace=True)
    return df
