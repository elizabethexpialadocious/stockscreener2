'''
get_daily_stock_data.py

data fetching routines

only handles daily stock price data and returns NUM_DAYS_TO_FETCH days
unless a different value is specified
'''

import datetime as dt
import pandas as pd
import os
import sys

import requests_cache
import requests

from credentials import fmp_key     # stock data is fetched from finanicalmodelingprep.com - you need a key
                                    # so make sure to define it as fmp_key in the file credentials.py
from session_setup import session

NUM_DAYS_TO_FETCH=365
'''
the number of days of stock that shall always be fetched
'''

def fetch(symbol, past_days_to_check=NUM_DAYS_TO_FETCH, last_close_date=None):
    print("Fetching: " + symbol, file=sys.stderr)
    df = None

    # we only care about the last close date if it is explicitly sent to the function
    # else we can ignore it and just send the latest data
    # otoh, if it is sent, we must make sure that the last day received is the same as the
    # one wanted

    # we use lcd instead of last_close_date and check later if need to make an exception

    if last_close_date is None:
        lcd = dt.date.today()
    else:
        lcd = last_close_date

    try:
        if past_days_to_check < NUM_DAYS_TO_FETCH:
            shorten_to = past_days_to_check
            past_days_to_check = NUM_DAYS_TO_FETCH
        else:
            shorten_to = past_days_to_check
        start = lcd - dt.timedelta(past_days_to_check)
        # df = web.DataReader(symbol, 'yahoo', start, last_close_date, session=session)

        d1 = session.get(f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={start}&to={lcd}&apikey={fmp_key}").json()
        df = pd.DataFrame.from_dict(reversed(d1["historical"]))
        df['Date'] = pd.to_datetime(df['date'])
        df.set_index('Date', inplace=True)
        # rename a few of the colmuns to make it similar to before
        df = df.rename(columns={'adjClose':'Adj Close', 'high':"High", 'low':'Low', 'open':'Open', 'close':'Close', 'volume':'Volume'})

        # check if the last day in the received data is the same as the date requested and if it is
        # not throw an exception
        # print(df.index[-1].date())
        if df.index[-1].date() != lcd and not (last_close_date is None):
            raise ValueError("received date is not what was requesnted; got: " + str(df.index[-1].date()) + "; wanted: " + str(last_close_date))

        print(" OK: " + symbol, file=sys.stderr)
        df['Ticker'] = symbol.upper()
        return df.tail(shorten_to)
    except:
        print(" Error fetching: " + symbol, file=sys.stderr)
        raise

def fetch_close_of_a_bunch_of_stocks(stocks, past_days_to_check=NUM_DAYS_TO_FETCH, last_close_date=None):
    '''
    returns close for a group of stocks whose tickers are passed
    in as a list

    found at: https://dev.to/shanelee/how-to-visualise-multiple-stocks-with-matplotlib-4050
    '''
    # Create an empty dataframe
    good_stocks = []
    data = pd.DataFrame()
    for stock in stocks: 
        # Create a column for the adjusted close of each stock
        # Here we use the DataReader library to get the data.
        try:
            data[stock] = fetch(stock, past_days_to_check, last_close_date=last_close_date)['Adj Close']
            good_stocks.append(stock)
        except Exception as e:
            print("skipping: " + str(e), file=sys.stderr)

    return (data, good_stocks)


def fetch_index_data(symbol):
    '''
    gets the latest index data whose beggining and endings cannot be adjusted,
    it's just the latest for the the last five years or so

    symbol: tickery symbol of the index (e.g. "^IXIC")
    returns a dataframe of the index in ascending order by date
    '''
    # for commodities, it is the same url
    # https://financialmodelingprep.com/api/v3/historical-price-full/ZGUSD?apikey=YOUR_API_KEY
    
    a = session.get(f'https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={fmp_key}').json()
    df = pd.DataFrame(a['historical'])
    df.index = pd.DatetimeIndex(df['date'])
    df = df.iloc[::-1]
    return df