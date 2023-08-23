import pandas as pd


class RiskManager:
    def __init__(
        self,
        interface,
        max_trades_per_year=64,
        max_trades_per_month=15,
        max_trades_per_week=5,
        max_trades_per_day=1,
        trail_pv_pct=0.10,
        target_pv_pct=0.10,
    ):
        self.interface = interface

        self.enabled = True

        self.trades = 0

        self.trades_per_year = 0
        self.trades_per_month = 0
        self.trades_per_week = 0
        self.trades_per_day = 0

        self.trades_per_year_max_reached = 0
        self.trades_per_month_max_reached = 0
        self.trades_per_week_max_reached = 0
        self.trades_per_day_max_reached = 0

        self.max_trades_per_year = max_trades_per_year
        self.max_trades_per_month = max_trades_per_month
        self.max_trades_per_week = max_trades_per_week
        self.max_trades_per_day = max_trades_per_day

        self.cum_trade_size = 0
        self.cum_trade_size_abs = 0

        self.pv = 0.0
        self.pv_max = 0.0
        self.pv_prev = 0.0
        self.trail_pv_pct = trail_pv_pct
        self.target_pv_pct = target_pv_pct
        self.pv_target = None

        self.risk_coeff = 1.0
        self.risk_coeff_penalty = +0.01

    def disable(self):
        self.enabled = False

    def update_daily(self, state, pv):
        date_last_time = pd.to_datetime(state.time, unit="s").date()
        if date_last_time.month == 1 and date_last_time.day == 1:  # yearly
            self.trades_per_year = 0
            self.risk_coeff = 1.0

        if date_last_time.day == 1:  # monthly
            self.trades_per_month = 0
            # self.reset_pv_max()
            # self.risk_coeff = 1.0

        # weekly
        if (
            date_last_time.weekday() == 5
        ):  # monday=0 tuesday=1 wednesday=2 thursday=3 friday=4 saturday=5 sunday=6
            self.reset_pv_max()
            self.trades_per_week = 0

        self.trades_per_day = 0  # daily

        self.update_hourly(state, pv)

    def update_hourly(self, state, pv):
        self.pv = pv
        if self.pv > self.pv_max:
            self.pv_max = self.pv

        if self.pv > self.pv_prev:
            self.risk_coeff = self.risk_coeff * (1 + self.risk_coeff_penalty)
        else:
            self.risk_coeff = self.risk_coeff * (1 - self.risk_coeff_penalty)
        self.pv_prev = self.pv

    def reset_pv_max(self):
        self.pv_max = 0.0

    def on_trade_enter(self, pv):
        self.trades_per_year += 1
        self.trades_per_month += 1
        self.trades_per_week += 1
        self.trades_per_day += 1
        self.trades += 1

        self.pv_target = pv * (1 + self.target_pv_pct)

        if self.trades_per_year > self.trades_per_year_max_reached:
            self.trades_per_year_max_reached = self.trades_per_year

        if self.trades_per_month > self.trades_per_month_max_reached:
            self.trades_per_month_max_reached = self.trades_per_month

        if self.trades_per_week > self.trades_per_week_max_reached:
            self.trades_per_week_max_reached = self.trades_per_week

        if self.trades_per_day > self.trades_per_day_max_reached:
            self.trades_per_day_max_reached = self.trades_per_day

        # if self.trades_per_day == self.max_trades_per_day:
        #     print("Risk: max_trades_per_day reached")

        if self.trades_per_week >= self.max_trades_per_week:
            print(
                "Risk: max_trades_per_week reached (%d/%d)"
                % (self.trades_per_week, self.max_trades_per_week)
            )

        if self.trades_per_month >= self.max_trades_per_month:
            print(
                "Risk: max_trades_per_month reached (%d/%d)"
                % (self.trades_per_month, self.max_trades_per_month)
            )

        if self.trades_per_year >= self.max_trades_per_year:
            print(
                "Risk: max_trades_per_year reached (%d/%d)"
                % (self.trades_per_year, self.max_trades_per_year)
            )

    def on_trade_exit(self):
        print("on_trade_exit")

    @property
    def is_trading_allowed(self):
        """
        if self.trades_per_year >= self.max_trades_per_year:
            print("not allowed (TR/year)")
        if self.trades_per_week >= self.max_trades_per_week:
            print("not allowed (TR/week)")
        if self.pv <= (1-self.trail_pv_pct)*self.pv_max:
            print("not allowed (trailing PV)")
        """
        if self.enabled:
            return (
                self.trades_per_year <= self.max_trades_per_year
                and self.trades_per_month <= self.max_trades_per_month
                and self.trades_per_week <= self.max_trades_per_week
                and self.pv >= (1 - self.trail_pv_pct) * self.pv_max
            )
        else:
            return False

    def print_status(self):
        print("TR: %d" % self.trades)
        # print("cum_trade_size    : %.2f" % self.cum_trade_size)
        # print("cum_trade_size_abs: %.2f" % self.cum_trade_size_abs)
        print(
            "TR/year  : %d / %d (max reached %d)"
            % (
                self.trades_per_year,
                self.max_trades_per_year,
                self.trades_per_year_max_reached,
            )
        )
        print(
            "TR/month : %d / %d (max reached %d)"
            % (
                self.trades_per_month,
                self.max_trades_per_month,
                self.trades_per_month_max_reached,
            )
        )
        print(
            "TR/week  : %d / %d (max reached %d)"
            % (
                self.trades_per_week,
                self.max_trades_per_week,
                self.trades_per_week_max_reached,
            )
        )
        print(
            "TR/day   : %d / %d (max reached %d)"
            % (
                self.trades_per_day,
                self.max_trades_per_day,
                self.trades_per_day_max_reached,
            )
        )
