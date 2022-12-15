'''
contains the various tests for an individual stock to see whether
or not it should be further reviewed
'''

import sys
import pandas as pd
import math
import unusual_option_activity as uoa
# import pandas_market_calendars as mcal

MIN_PRICE = 10
MIN_VOLUME = 500000
GEN_DAY_CHECK = 3
NUM_UOAS_TO_CONSIDER = 25

ffty = None
uoa_tickers = None

def add_testing_data(df):
    '''
    adds all necessary to a given dataframe that one or more
    tests can use to test the stock; this simply prevents more than
    one test performng the same rudimentry thing twice

    should be called before the tests are run on the given df

    if a test needs to add sometrhing to the dataframe of the stock
    (as as a moving average), that addition should be done here
    '''

    # Mark Minirvi screener test needs SMA50, SMA150, ans SMA200

    df["sma50"] = df['Adj Close'].rolling(50).mean()
    df["sma150"] = df['Adj Close'].rolling(150).mean()
    df["sma200"] = df['Adj Close'].rolling(200).mean()  

    # my own tests:

    # volume SMA
    df['volume_sma50'] = df['Volume'].rolling(50).mean()
    df['volume_std'] = df['Volume'].rolling(50).std()

    df['close_std50'] = df['Adj Close'].rolling(50).std()
    df['close_std150'] = df['Adj Close'].rolling(150).std()

    return df
      
def high_volume_up(df, std_threshold=1.33):
    '''
    checks to see if last day was high volume and the price
    is up

    '''
    # print("     high volume entry 1", file=sys.stderr)
    # convenience
    last_day = df.iloc[-1]
    try:
        n2l_day = df.iloc[-2]
    except  Exception as e:
        n2l_day =  df.empty
        print(str(e), file=sys.stderr)
    
    volume = last_day['Volume']
    vma = last_day['volume_sma50']
    vstd = last_day['volume_std']


    if volume > (vma + std_threshold * vstd):
        # print("     high volume pass 1", file=sys.stderr)
        # check if the stock is green
        if last_day['Open'] < last_day['Adj Close']:
            # green daybso good
            print("     PASS high_volume-up-1", file=sys.stderr)
            return True

        if not n2l_day.empty and n2l_day['Adj Close'] < last_day['Adj Close']:
            # so higher today
            print("     PASS high_volume-up-2", file=sys.stderr)
            return True
    
    return False

def mark_minervini_test(df):
    '''
    Mark Minervini test, from Richard Moglen
    doent check with the IBD requirements

    I haven't udpdated the ffty file in a long time so will no longer apply
    this test to the stocks (12/14/22)
    '''

    global ffty

    if ffty is None:
        ffty=pd.read_csv('ffty.csv', header=0, names=['code', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6'], index_col=0)

    # check if this stock is in the FFTY - maybe not a great idea
    # as this really limits the number of matchung stocks

    # note this won't work because Ticker s not in the dataframe
    if not df['Ticker'][-1] in ffty.index:
        return False

    currentClose = df["Adj Close"][-1]
    moving_average_50 = df["sma50"][-1]
    moving_average_150 = df["sma150"][-1]
    moving_average_200 = df["sma200"][-1]
    low_of_52week = min(df["Adj Close"][-260:])
    high_of_52week = max(df["Adj Close"][-260:])

    try:
        moving_average_200_20 = df["sma200"][-20]

    except Exception as e:
        moving_average_200_20 = 0
        print(str(e), file=sys.stderr)

    # print("     Mark Minirvini pass 0", file=sys.stderr)
    # Condition 1: Current Price > 150 SMA and > 200 SMA
    if (currentClose > moving_average_150 > moving_average_200):
        # print("     Mark Minirvini pass 1", file=sys.stderr)
        cond_1 = True
    else:
        cond_1 = False
    # Condition 2: 150 SMA and > 200 SMA
    if (moving_average_150 > moving_average_200):
        # print("     Mark Minirvini pass 2", file=sys.stderr)
        cond_2 = True
    else:
        cond_2 = False
    # Condition 3: 200 SMA trending up for at least 1 month (ideally 4-5 months)
    if (moving_average_200 > moving_average_200_20):
        # print("     Mark Minirvini pass 2", file=sys.stderr)
        cond_3 = True
    else:
        cond_3 = False
    # Condition 4: 50 SMA> 150 SMA and 50 SMA> 200 SMA
    if (moving_average_50 > moving_average_150 > moving_average_200):
        # print("Condition 4 met")
        # print("     Mark Minirvini pass 3", file=sys.stderr)
        cond_4 = True
    else:
        # print("Condition 4 not met")
        cond_4 = False
    # Condition 5: Current Price > 50 SMA
    if (currentClose > moving_average_50):
        # print("     Mark Minirvini pass 5", file=sys.stderr)
        cond_5 = True
    else:
        cond_5 = False
    # Condition 6: Current Price is at least 30% above 52 week low (Many of the best are up 100-300% before
    # coming out of consolidation)
    if (currentClose >= (1.3 * low_of_52week)):
        # print("     Mark Minirvini pass 6", file=sys.stderr)
        cond_6 = True
    else:
        cond_6 = False
    # Condition 7: Current Price is within 25% of 52 week high
    if (currentClose >= (.75 * high_of_52week)):
        # print("     Mark Minirvini pass 7", file=sys.stderr)
        cond_7 = True
    else:
        cond_7 = False


    # note that I don't have access to the IBD stock lists so just
    # use the IBD50 for the time being


    # Condition 8: IBD RS rating >70 and the higher the better
    # if (RS_Rating > 70):
    #     cond_8 = True
    # else:
    #     cond_8 = False



    # if (cond_1 and cond_2 and cond_3 and cond_4 and cond_5 and cond_6 and cond_7 and cond_8):
    #     exportList = exportList.append({'Stock': stock, "RS_Rating": RS_Rating, "50 Day MA": moving_average_50,
    #                                     "150 Day Ma": moving_average_150, "200 Day MA": moving_average_200,
    #                                     "52 Week Low": low_of_52week, "52 week High": high_of_52week},
    #                                     ignore_index=True)

    if (cond_1 and cond_2 and cond_3 and cond_4 and cond_5 and cond_6 and cond_7):
        print("     Mark Minirvini pass", file=sys.stderr)
        return True

    return False

def close_above_sma(df):
    '''
    check for the close being above the lowest sma (50 or 150) - its standard deviation
    '''

    last_day = df.iloc[-1]
    close = last_day['Adj Close']
    price_50 = last_day['sma50']
    price_150 = last_day['sma150']
    std_50 = last_day['close_std50']
    std_150 = last_day['close_std150']

    # need to make sure that these are vactually defined and not NaN

    # the 150 is more likely to be undefined
    lowest = close

    # three conditions
    # a - both 50 and 150n day are undefined
    # b - 50 is defined but 150 us not
    # c - both are

    if math.isnan(price_150):
        if math.isnan(price_50):
            # can't check it so say its good
            return True
        else:
            # lowest = price_50 - std_50
            lowest = price_50
    else:
        # theyre both defined som assign to lowest whichever is lower
        # a = price_150 - std_150
        # b = price_50 - std_50
        a = price_150 
        b = price_50
        if a < b:
            lowest = a
        else:
            lowest = b
    if close > lowest:
        return True
    return False


def consecutive_up_days(s, num_days=GEN_DAY_CHECK):
    '''
    consecutive_up_days(stock, num_days)
    return true if the stock has last num_days consecutive days going up
    where up means a higher open/close over previous open/close for num_days
    in a row

    on a chart this would show the bars going stepping up in value regarrdless
    f whether or not they are up days or down days
    '''    
    # print(s["Open"][-1])

    h = [0, 0]
    l = [0, 0]

    '''
    This functioo has been tested against normal data
    but sometimes weird stock data (e.g. it has no volume,
    or it's last close day was not the last market day close)
    can screw it up; therefore these iterations through the last
    few days (GEN_DAY_CHECK) will be wrapped with exception
    handling until I come up with a better solution  
    '''

    try:
        for i in range(-num_days, -1):
            for j in range(0, 2):
                if s["Open"][i+j] < s["Adj Close"][i+j]:
                    h[j] = s["Open"][i+j]
                    l[j] = s["Adj Close"][i+j]
                else:
                    h[j] = s["Adj Close"][i+j]
                    l[j] = s["Open"][i+j]

            if h[0] > h[1]:
                return False
            if l[0] > l[1]:
                return False
        print("  Passed conecutive_up_days", file=sys.stderr)
        return True
    except:
        print("  ERROR conecutive_up_days", file=sys.stderr)
        return False


'''
consecutive_green_days(stock, num_days)
return True/False

similar to the above function but checks if the given stock's
last num_days have all been green (not necessarily increasing)

'''

def consecutive_green_days(s, num_days=GEN_DAY_CHECK):
    try:
        for i in range(-num_days, 0):
            if s["Open"][i] >= s["Close"][i]:
                return False

        print("  Passed consecutive_green_days", file=sys.stderr)
        return True
    except:
        print("  ERROR consecutive_green_days", file=sys.stderr)
        return False


def is_a_uoa(df):
    '''
    checks to see if UOA is associated with the ticker of the given df
    df: stock data containing Ticker
    
    '''
    global uoa_tickers
    try:
        if uoa_tickers is None:
            uoa_tickers = uoa.get_uoas(NUM_UOAS_TO_CONSIDER)
    
        if df['Ticker'][0] in uoa_tickers:
            print("  Passed UOA", file=sys.stderr)
            return True
    except Exception as e:
        print("  ERROR " + str(e), file=sys.stderr)

    return False



def high_enough_price(df, min_price = MIN_PRICE):
    """
    checks to make sure that the average price of this stock is high
    enough to consider worth dealing with
    """
    if df["Close"].mean() < min_price:
        print("  FAILED high_enough_price", file=sys.stderr)        
        return False
    else:
        print("  Passed high_enough_price", file=sys.stderr)
        return True

def high_enough_volume(df, min_volume = MIN_VOLUME):
    '''
    checks to make sure the volume is above MIN_VOLUME
    '''

    if df["Volume"].mean() < min_volume:
        print("  FAILED high_enough_volume", file=sys.stderr)        
        return False
    else:
        print("  Passed high_enough_volume", file=sys.stderr)
        return True
 


def run_tests_conjuction(df, functions):
    '''
    returns true if all the functions in the list of functions is true when
    passed the df
    '''
    for f in functions:
        if not f(df):
            return False
    return True

def run_tests_disjuction(df, functions):
    '''
    returns True if any one of the functions returns True when
    passed the given df
    '''
    

    for f in functions:
        if f(df):
            return True
    return False


def run_all_tests(df):
    '''
    runs all the tests on the given stock dataframe
    returns True if the given stock (dataframe) passes
    at least one test
    '''

    # df = add_testing_data(df)

    and_tests = [high_enough_price]
    or_tests = [
        is_a_uoa,
        consecutive_up_days, 
        consecutive_green_days,
        high_volume_up,
        # mark_minervini_test
        ]

    if run_tests_conjuction(df, and_tests):
        if run_tests_disjuction(df, or_tests):
            return True
    return False

def run_screen_tests(df):
 
    # if there are any tests which don't need to pass preliminary tests
    # put them here before add_testing_data

    df = add_testing_data(df)

    # high_volume_up is okay if its below the SMA assumming
    # the volume is nuts (3)

    if is_a_uoa(df) or high_volume_up(df, 3):
        return True

    # else make sure price is abive sma

    if close_above_sma(df):
        or_tests = [
            high_volume_up,
            # mark_minervini_test,
            consecutive_up_days, 
            consecutive_green_days,
            ]
        if run_tests_disjuction(df, or_tests):
            return True

    return False


def run_preliminary_tests(df):
    '''
    runs tests for intial brief screen

    currntly just checks volume and price
    '''

    and_tests = [high_enough_price, high_enough_volume]
    if run_tests_conjuction(df, and_tests):
        return True
    else:
        return False


