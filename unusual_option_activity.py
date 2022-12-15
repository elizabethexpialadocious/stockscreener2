'''
screens the option database for any unusual option activity

'''

import sqlite3
import pandas as pd
import numpy as np
from pyparsing import cpp_style_comment
import gather_option_data as options
from credentials import *
from session_setup import session

import time as t
import sys
import send_mail as mail
import datetime as dt

MINIMUM_HISTORICAL_LENGTH = 3
'''
minimum length of option data to consider valid
''' 
rows_list = []

def make_connection():
    try:
        con = sqlite3.connect(options.OPTION_DATA_DATABASE)
    except Exception as e:
        print(str(e))
        raise
    else:
        return con

def check_for_uoa(ticker, current_price, variance_threshold=1):
    '''
    looks fer UOA for ticker in raw option data; to retrieve already found UOA use get_uoa
    https://marketxls.com/unusual-options-activity/
    https://www.investopedia.com/articles/optioninvestor/11/predict-earnings-with-options.asp
    ticker: stock symbol (string)
    returns: dataframe of the UOA in the format 'ticker', 'expiry' (date),
                                                'current_price', 'strike', 'call_put' (string 'CALL' or 'PUT'),
                                                'volume','open_interest', 'mean_volume',
                                                'as_of' (date  when option data retrieved)
    '''
    sql_option_query = '''SELECT underlying, 
                            date(datetime(expiration/1000, "unixepoch")) as expiry,
                            strike,
                            call_put,
                            volume,
                            open_interest,
                            CAST(volume as REAL)/open_interest as vol_over_oi,
                            date(datetime(timestamp, "unixepoch")) as ts
                        FROM 
                            option_volume 
                        WHERE 
                            underlying=?
                          AND
                            expiry >= date('now')
                        ORDER BY expiry, strike, call_put, ts
      ''' 


    con = make_connection()
    df = pd.read_sql(sql_option_query, con, params=[ticker], parse_dates=True)

    # now we need to group by the unique components and check for volume spike
    # on the last row
    
    rv = []
    for i in df.groupby(by=['expiry', 'strike', 'call_put']):
        # i[0] contains a set consisting of expiry, strake and call_put
        # i[1] contains a series consiting of the relevant rows from the squery
        # e.g. 
        #   underlying      expiry  strike call_put  volume  open_interest          ts
        # 0       AAPL  2022-01-21    25.0     CALL       0             90  2022-01-04
        
        e, s, cp = i[0]
        d = i[1] # convenience
        try: 
            if(len(d)) > MINIMUM_HISTORICAL_LENGTH:
                m = d['volume'].iloc[:-2].mean()
                var = d['volume'].iloc[:-2].var()
                vol = d['volume'].iloc[-1]
                vooi = d['vol_over_oi'].iloc[-1]
                oi = d['open_interest'].iloc[-1]
                ts = d['ts'].iloc[-1]


                # so we can do two tests as per the two URLs above. If either one is true, then it is flagged
                flag_it = False

                if vol > 0 and oi > 0 and m > 1:
                    # if True:
                    if (cp == "CALL" and s > current_price) or (cp  == "PUT" and s < current_price):
                        # 1) look for volume greater than 5 times the average volume
                        # if vol > 5 * m:
                        #     flag_it = True
                        # 2) volume greater than the average and the volume greater than the previous day's open interest
                        # if vol > m + variance_threshold * var and vol > d['open_interest'].iloc[-1]:
                        if vol > m * variance_threshold and  vol > d['open_interest'].iloc[-1]:
                            flag_it = True


 
                # if vol > 0 and oi > 0 and not np.isnan(vooi) and vooi > 0.5 and vol > m + variance_threshold * var:
                #     ok = False
                #     if cp == "CALL" and s > current_price:
                #         ok = True
                #     if cp  == "PUT" and s < current_price:
                #         ok = True
                #     if ok:
                #         print(ticker + " " + str(e) + " " + str(s) + " " + cp + " " + str(vol) + " " + str(oi) + " " + str(vooi))
           
                if flag_it:
                    # print(ticker + " " + str(e) + " " + str(s) + " " + cp + " " + str(vol) + " " + str(oi) + " " + str(m))
                    # register_uoa(ticker, e, s, cp, vol, oi, m, current_price, ts)
                    d = {
                        'ticker': ticker,
                        'expiry': dt.date.fromisoformat(e),
                        'current_price': current_price,
                        'strike': s,
                        'call_put': cp,
                        'volume': vol,
                        'open_interest': oi,
                        'mean_volume': m,
                        'as_of': dt.date.fromisoformat(ts)
                    }
                    rv.append(d)

        except Exception as e:
            print(str(e), file=sys.stderr)
                # print(str(m) + ", " + str(var) + ", " + str(m + variance_threshold * var))
                # print(i[1])

    return pd.DataFrame(rv)

def get_uoa(ticker, days_ahead = '60 days'):
    '''
    checks the database for UOA for the given ticker whose expiration is within
    days_ahead
    ticker: stock symbol
    days_ahead: include only UOA whose expiration is within n number of days, as a string (e.g. '60 days') 
    
    '''

    get_uoa_sql = '''   SELECT * FROM uoa
                        WHERE
                            ticker = ?
                        AND
                            expiry >= date('now')
                        AND
                            expiry <= date('now', ?)
    '''

    con = make_connection()
    return pd.read_sql(get_uoa_sql, con, params=(ticker, days_ahead))


def get_uoas(limit = 10, days_ahead='90 days'):
    '''
    returns a list of ticker symbols which could be considered as being worthy of
    further review that is not part of an ETF
    '''
    # SELECT ticker, max(volume/mean_volume) as vom FROM uoa GROUP BY ticker ORDER BY vom DESC limit 25;
    # select * from uoa where ticker  not in (select symbol from etfs);

    get_uoas_sql = '''  SELECT
                            ticker,
                            max(volume/mean_volume) as vom
                        FROM
                            uoa
                        WHERE
                            expiry > 0
                          AND
                            expiry <= date('now', ?)
                          AND
                            ticker not in (select symbol from etfs)
                        GROUP BY
                            ticker 
                        ORDER BY
                            vom DESC
                        LIMIT ?
    '''
    con = make_connection()
    con.row_factory = lambda cursor, row: row[0]
    c = con.cursor()
    return c.execute(get_uoas_sql, (days_ahead, limit,)).fetchall()

def get_current_price(ticker):
    global fmp_key
    d = session.get(f'https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={fmp_key}').json()
    return d[0]['price']

def get_range_uoa(ticker, future_days):
    '''
    finds the range of UOA for a particular ticker if its currently in the UOA database
    ticker: symbol of the stock
    future_days: consider only future expirations within this number of days (as a string, e.g. '60 days'))
    returns (uoa, min, max): uoa True/False whether UOA has been flagged for this symbol, min strike price, maX strike price   
    '''

    min_max_uoa_sql = '''select
                            min(strike) as mn,
                            max(strike) as mx 
                        FROM uoa
                        WHERE 
                            ticker= ?
                          AND
                            expiry < date('now', ?)
                          AND
                            expiry >= date('now')
    ''' 
    con = make_connection()
    df = pd.read_sql(min_max_uoa_sql, con, params=(ticker, future_days))
    if df['mn'].iloc[0] is None:
    # if df.empty or len(df) == 0:
        return (False, 0, 0)
    else:
        return (True, df['mn'].iloc[0], df['mx'].iloc[0])

############################################################################
# MAIN
############################################################################

if __name__ == '__main__':
    GOOD_STOCK_FILE="stocks_to_check.csv"
    df = pd.read_csv(GOOD_STOCK_FILE, parse_dates=True)

    k = 0
    results = pd.DataFrame()
    for i in df.index:
        if k > 0:
             t.sleep(1/2)
        ticker = str(df["Ticker"][i])
        try:
            d = check_for_uoa(ticker, get_current_price(ticker), 100)
            k = k + 1
            results = results.append(d)
        except Exception as e:
            print("Error: " + ticker + " " + str(e), file=sys.stderr)
        # if k > 25:
        #     break

    # store the results in the database
    con = make_connection()
    results.to_sql('uoa', con, if_exists='replace')


    q = '''
        SELECT *, volume/mean_volume as vom
        FROM uoa 
        WHERE ticker
        NOT IN
            (select symbol from etfs)
        ORDER BY
            vom DESC
        LIMIT 100
    '''
    con = make_connection()
    df = pd.read_sql(q, con)

    # old: contained too many ETFs
    # but only want email UOA whose expiray is in teh next 60 days
    # df = results[results['expiry'] < dt.date.today() + dt.timedelta(60)]
    # # https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas
    # pd.options.mode.chained_assignment = None  # default='warn'
    # df['vom'] = df['volume']/df['mean_volume']
    # # filename = dt.datetime.now().strftime("uoa-%y-%m-%d-%H-%M.xlsx")
    # # df.to_excel(filename)
    # # df = df.sort_values(by=['volume'], ascending=False)
    # # df = df.sort_values(by=['vom'], ascending=False)
    # a1 = (df.sort_values(by=['volume'], ascending=False)).iloc[:100].to_html()
    # a2 = (df.sort_values(by=['vom'], ascending=False)).iloc[:100].to_html()
    # a3 = (df.sort_values(by=['open_interest'], ascending=False)).iloc[:100].to_html()
    # body  = """<html><head></head><body>{0}<br>{1}<br>{2}</body></html>""".format(a1,a2,a3)

    body  = """<html><head></head><body>{0}</body></html>""".format(df.to_html())
    mail.send_with_attachment("sunshinekisses@gmail.com", "sunshinekisses@gmail.com", "UOA", body, files=[], body_mime_type='html')




    


    
    




