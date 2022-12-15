import pandas as pd
from session_setup import session
from credentials import fmp_key
import sys

def get_eps(ticker, limit=20):
    try:
        a = session.get(f'https://financialmodelingprep.com/api/v3/ratios/{ticker}?period=quarter&limit={limit}&apikey={fmp_key}').json()
        df = pd.DataFrame(a)
        x = df[['date', 'priceEarningsRatio']]
        x2 = x.rename({'priceEarningsRatio': 'eps'}, axis=1)
        x2.loc[:,'date'] = pd.to_datetime(df['date'])
        x2.set_index('date', inplace=True)
        return x2.iloc[::-1]
    except Exception as e:
        print("EPS error " + ticker + " " + str(e), file=sys.stderr)
        return pd.DataFrame()      

