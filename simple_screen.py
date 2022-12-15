'''
go through the list of stocks in the market cap listing and
get a stock listing for each one, then determine if it has the
necessary requirements to check daily (such as a high enough price).
This keeps us from checking stocks that won't even be
considered daily, say once a week or once a month
'''

import datetime as dt
import pandas as pd
import argparse

import stock_tests as st
import get_daily_stock_data as dailys

MAIN_STOCK_FILE="america_2022-02-06.csv"
# got this initial listing of stocks off of TradingView.com - specifically their screener
# probabably should be updated

# MAIN_STOCK_FILE="america_2021-12-09.csv"
# MAIN_STOCK_FILE="america_2021-11-25.csv"
# MAIN_STOCK_FILE="america_2021-11-25-short-2.csv"

GOOD_STOCK_FILE="stocks_to_check.csv"
# GOOD_STOCK_FILE="america_2021-11-25-short-1.csv"

NUM_DAYS_NEEDED=30

def make_good_stock_df(in_df): 
    '''
    called weekly. Screens the ticker info in MAIN_STOCK_FILE and determines via
    a call to the stock info provider if it's a "good" stock and if it is, writes
    the data into GOOD_STOCK_FILE

    the tests are in stock_tests.py and the function that runs them is called
    run_preliminary_tests
    
    '''

    # in_df = pd.read_csv(MAIN_STOCK_FILE)
    # out_l = []
    # out_df = in_df.iloc[0:0]
    out_df = pd.DataFrame(columns=in_df.columns)
    # out_df = pd.DataFrame(data=None, columns=in_df.columns, index=in_df.index)

    for i in in_df.index:
        try:
            df = dailys.fetch(in_df["Ticker"][i], NUM_DAYS_NEEDED)
        except Exception as e:
            print("Error fetching: " + in_df["Ticker"][i] + " " + str(e))
        else:
            if st.run_preliminary_tests(df):
                # update info about the stock as necessarr
                
                in_df.loc[i, 'Volume'] = df["Volume"].iloc[-1]
                in_df.loc[i, 'Last' ] =  df["Adj Close"].iloc[-1]
 
                out_df = out_df.append(in_df.iloc[i])
        
    # out_df = pd.DataFrame(out_l, columns = ['Ticker'])
    # out_df.to_csv(GOOD_STOCK_FILE)
    out_df.reset_index(drop=True, inplace=True)
    return out_df

def test():
    # this could be more robust and check each stock separetrly
    # but this is good enough for the time being just to make sured it'll
    # work if the stock checking fn receives a bad ticker symbol

    stocks = ['AAPL', 'BRK.A', 'CVS']
    df = pd.DataFrame(stocks, columns=['Ticker']) 
    make_good_stock_df(df)


if __name__ == "__main__":
    # got this from https://docs.python.org/3/howto/argparse.html
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", help="runs the test function", action="store_true")
    parser.add_argument("--infile", help="stiplates name of input file")
    parser.add_argument("--outfile", help="stipulates name of output file")
    args = parser.parse_args()

    if args.test:
        test()
    else:
        infile = MAIN_STOCK_FILE
        outfile = GOOD_STOCK_FILE

        if args.infile:
            infile = args.infile
        if args.outfile:
            outfile = args.outfile

        # print(infile, outfile)

        in_df = pd.read_csv(infile)
        out_df = make_good_stock_df(in_df)
        out_df.to_csv(outfile,index=False)


