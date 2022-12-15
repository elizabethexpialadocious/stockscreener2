# get_option_data.py
# option data is only avaliable dering trading hours
# so consider running this an hour before closing time

import sqlite3
from session_setup import session

from credentials import tda_key
import pandas as pd
from os.path import exists
from session_setup import session
import datetime as dt
import time
import sys

OPTION_DATA_DATABASE="option-data.db"
con = None

# table schema
# -------------
# underlying
# expiration
# strike
# call/put
# volume
# openinterest
# timestamp



def create_option_table():
    '''
    just simply create the option table
    '''    
    global conn

    sql_create_option_table = """CREATE TABLE IF NOT EXISTS option_volume (
        underlying TEXT NOT NULL,
        expiration INTEGER NOT NULL,
        strike REAL NOT NULL,
        call_put TEXT NOT NULL,
        volume INTEGER NOT NULL,
        open_interest INTEGER NOT NULL,
        timestamp INTEGER NOT NULL,
        PRIMARY KEY (underlying,expiration,strike,call_put,timestamp));"""


    conn = make_connection()

    try:
        c = conn.cursor()
        c.execute(sql_create_option_table)
    except Exception as e:
        print(e)
        return

def make_connection():
    global con
    try:
        if con is None:
            con = sqlite3.connect(OPTION_DATA_DATABASE)
    except Exception as e:
        print(str(e), file=sys.stderr)
        raise
    return con

def insert_the_data(conn, ticker, o):
    sql_insertion_str = """INSERT INTO option_volume (
                        underlying, 
                        expiration, 
                        strike,
                        call_put,
                        volume,
                        open_interest,
                        timestamp) values (?,?,?,?,?,?,?)"""
    for expirary in o :
        for strike in o[expirary]:
                s = o[expirary][strike][0]["strikePrice"]
                v = o[expirary][strike][0]["totalVolume"]
                e = o[expirary][strike][0]["expirationDate"]
                oe = o[expirary][strike][0]["openInterest"]
                cp = o[expirary][strike][0]["putCall"]
                conn.execute(sql_insertion_str, (ticker, e, s, cp, v, oe, int(dt.datetime.utcnow().timestamp())))
  


def store_option_data_for_stock(ticker):

    con = make_connection()

    try:
        d1 = session.get(f"https://api.tdameritrade.com/v1/marketdata/chains?apikey={tda_key}&symbol={ticker}").json()
    except Exception as e:
        print("EROR: " + str(e))
    else:
        try:
            # "insert into minute_data(date, ticker, open, low, high, close, volume) values (?,?,?,?,?,?,?)", (j["date"], ticker, j["open"], j["low"], j['high'], j['close'], j['volume']))
 
            insert_the_data(con, ticker, d1['callExpDateMap'])
            insert_the_data(con, ticker, d1['putExpDateMap'])

            con.commit() 
        except Exception as e:
            print("error: " +  str(e) + " " + ticker)

def get_volume_sum_df(ticker, call_put, min_strike, max_strike, days_til_expiration=30):
    volume_sum_sql = '''select
                          underlying, 
                          date(datetime(expiration/1000, "unixepoch")) as expiry,
                          (julianday(date(datetime(expiration/1000, "unixepoch"))) - julianday(date('now'))) as du,
                          strike,
                          call_put,
                          volume,
                          open_interest,
                          sum(volume) as csum
                        from option_volume
                         where underlying = ? and call_put = ? and du > 0 and du < ?  and strike >= ? and strike <= ?
                         group by underlying, strike, call_put
                            '''
    con = make_connection()
    df = pd.read_sql(volume_sum_sql, con, params=[ticker, call_put, days_til_expiration, min_strike, max_strike])
    return df

def get_latest_option_info_df(ticker, call_put, min_strike, max_strike, days_til_expiration=30):
    latest_option_info_select_sql = '''
        select
            a.underlying,
            (julianday(date(datetime(a.expiration/1000, "unixepoch"))) - julianday(date('now'))) as du,
            a.strike,
            a.call_put, 
            date(datetime(a.expiration/1000, "unixepoch")) as expiry,
            a.volume,
            a.open_interest 
        from option_volume a 
        inner join ( 
            select underlying, expiration, strike, call_put, max(timestamp) as ts 
            from option_volume 
            group by underlying, expiration, strike, call_put ) b 
            on a.underlying = b.underlying and a.expiration=b.expiration and a.strike=b.strike and  a.call_put = b.call_put and b.ts = a.timestamp
            where a.underlying=? and a.call_put = ? and a.open_interest > 0 and du > 0 and du < ? and a.strike >= ? and a.strike <= ? 
        '''
    con = make_connection()

    df = pd.read_sql(latest_option_info_select_sql, con, params=[ticker, call_put, days_til_expiration, min_strike, max_strike])
    return df

#################################################################
### MAIN
#################################################################

if __name__ == '__main__':
    if not exists(OPTION_DATA_DATABASE):
        create_option_table()   

    # now just go through the listing of stocks and get the minute volume info
    # from simple_screen import GOOD_STOCK_FILE   
    GOOD_STOCK_FILE="stocks_to_check.csv"
    df = pd.read_csv(GOOD_STOCK_FILE, parse_dates=True)

    # store_option_data_for_stock("ANET")

    k = 0
    for i in df.index:
        if k > 0:
            time.sleep(1/2)
        ticker = str(df["Ticker"][i])
        print(ticker)
        store_option_data_for_stock(ticker)
        k = k + 1

 

  




