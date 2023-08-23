#!/usr/bin/env python3

import click
import os
#from dotenv import dotenv_values
import warnings
import datetime
import requests
import pandas as pd
import json

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, DateTime, String, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

Base = declarative_base()


class AccountValues(Base):
    __tablename__ = "account_values"
    id = Column(Integer, primary_key=True)

    token = Column(String)

    time = Column(DateTime)

    available = Column(String)
    hold = Column(String)
    available_amount = Column(String)
    hold_amount = Column(String)

    available_amount_sum = Column(Float)
    hold_amount_sum = Column(Float)


def query_account(url, token):
    endpoint = "/api/account"
    response = requests.get(url + endpoint, params={"token": token})
    status_code = response.status_code
    if status_code == 200:
        account = response.json()
        account = pd.DataFrame(account)
        account = account.transpose()
        account_sum = account[["available_amount", "hold_amount"]].sum()
        return account.to_dict(), account_sum.to_dict()
    else:
        warnings.warn(f"error with status_code={status_code}")
    return None


def store_account_values(
    db_uri,
    token,
    now,
    available,
    hold,
    available_amount,
    hold_amount,
    available_amount_sum,
    hold_amount_sum,
):
    account = AccountValues(
        token=token,
        time=now,
        available=json.dumps(available),
        hold=json.dumps(hold),
        available_amount=json.dumps(available_amount),
        hold_amount=json.dumps(hold_amount),
        available_amount_sum=available_amount_sum,
        hold_amount_sum=hold_amount_sum,
    )

    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(account)
        session.commit()


def process_account_values(verbose, url, token, db_uri):
    query_result = query_account(url, token)
    if query_result is None:
        return
    account, account_sum = query_result
    now = datetime.datetime.utcnow()

    available = account["available"]
    hold = account["hold"]
    available_amount = account["available_amount"]
    hold_amount = account["hold_amount"]

    available_amount_sum = account_sum["available_amount"]
    hold_amount_sum = account_sum["hold_amount"]

    if verbose:
        print(
            f"Storing {now} {token} {available} {hold} {available_amount} {hold_amount} {available_amount_sum} {hold_amount_sum}"
        )

    store_account_values(
        db_uri,
        token,
        now,
        available,
        hold,
        available_amount,
        hold_amount,
        available_amount_sum,
        hold_amount_sum,
    )


@click.command()
@click.option("--url", default="http://localhost:8000", help="url to send queries")
@click.option("--token", default="", help="token for auth")
@click.option(
    "--db-uri",
    default="sqlite:///accounts.sqlite",
    help="DB uri to send account values",
)
@click.option("--schedule/--no-schedule", default=True, help="schedule")
@click.option("--seconds", default=0, help="schedule using seconds interval")
@click.option(
    "--crontab",
    default="* * * * *",
    help="schedule using crontab syntax ('* * * * *' = every minute, '0 * * * *' = every hour at minute 0 ... see https://crontab.guru/",
)
@click.option("--verbose/--no-verbose", default=True, help="verbose")
def main(url, token, db_uri, schedule, seconds, crontab, verbose):
    #warnings.warn("H"* 100)
    print(f"Connect to {url}")
    print(f"Store to {db_uri}")
    if token == "":
        #config = dotenv_values(".env")
        #token = config["RUN_ID"]
        token = os.getenv("RUN_ID")
        print(f"token={token}")

    if schedule:
        if verbose:
            print("dry run")
        # process_account_values(verbose, url, token, db_uri)
        query_account(url, token)
        scheduler = BlockingScheduler()
        _process_account_values = lambda: process_account_values(
            verbose, url, token, db_uri
        )
        if seconds > 0:
            if verbose:
                print(f"scheduling with interval {seconds} seconds")
            scheduler.add_job(
                _process_account_values, "interval", seconds=seconds
            )  # every n seconds
        else:
            if verbose:
                print(f"scheduling with crontab '{crontab}'")
            scheduler.add_job(
                _process_account_values, CronTrigger.from_crontab(crontab)
            )
            # scheduler.add_job(_process_account_values, 'cron', second=0)  # every minutes
            # scheduler.add_job(_process_account_values, "cron", minute=0)  # every hours
        scheduler.start()
    else:
        process_account_values(verbose, url, token, db_uri)


if __name__ == "__main__":
    main()
