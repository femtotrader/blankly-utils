from bar import Bar, Bars


def test_bar():
    bar = Bar(time=0, open=0.0, high=0.0, low=0.0, close=0.0, volume=0.0)


"""
def test_bars():
    bars = Bars(
        time=0,
        symbols={
            "SYMB1": Bar(time=0, open=0.0, high=0.0, low=0.0, close=0.0, volume=0.0)
        }
    )
"""
