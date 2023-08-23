from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime

Base = declarative_base()


class BacktestRun(Base):
    __tablename__ = "backtest_runs"
    id = Column(Integer, primary_key=True)

    run_id = Column(String)
    scheduled_time = Column(DateTime)
    run_comment = Column(String)

    backtest_id = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    backtest_comment = Column(String)
    backtest_start = Column(DateTime)
    backtest_end = Column(DateTime)

    input = Column(String)
    output = Column(String)

    initial_values = Column(String)
    final_values = Column(String)

    def __repr__(self):
        return (
            f"<BacktestRun("
            f"run_id='{self.run_id}', "
            f"scheduled_time='{self.scheduled_time}', "
            f"run_comment='{self.run_comment}', "
            f"backtest_id='{self.backtest_id}', "
            f"start_time='{self.start_time}', "
            f"end_time='{self.end_time}', "
            f"backtest_comment='{self.backtest_comment}', "
            f"backtest_start='{self.backtest_start}', "
            f"backtest_end='{self.backtest_end}', "
            f"input='{self.input}', "
            f"output='{self.output}')>"
            f"initial_values='{self.initial_values}', "
            f"final_values='{self.final_values}')>"
        )
