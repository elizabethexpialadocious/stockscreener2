import datetime as dt
import pandas as pd
import os
import sys
import pandas_market_calendars as mcal
import numpy as np
import argparse

from matplotlib.backends.backend_pdf import PdfPages

import stock_tests
import get_daily_stock_data
import generate_graphs
import simple_screen
import send_mail
import gather_minute_data

from shutil import copyfile

from credentials import default_sender, default_recipient

SUBSCRIBER_FILE='subscribers.txt' # one subscriber per line, no comments

NUM_STOCKS_PER_SECTOR_CHART=20
NUM_DAYS_PER_SECTOR_CHART=10

def check_stock(symbol, last_close_date=None):
    '''
    gets the data for the symbol returning a tuple, the first of which indicates
    whether or not the data was correctly received 
    '''
    try:
        df = get_daily_stock_data.fetch(symbol, last_close_date=last_close_date)
    except:
        return (False, None)

    result = False
    if stock_tests.run_screen_tests(df):
        result = True
    return (result,df)

def make_market_summary(pdf=None):
    '''
    simply produces a bunch of graphs of various indices supposed to
    indicate a summary of the market at the time of this function
    being called
    '''
    indices_to_use = [
        ['^DJI', "Dow Jones Industrial Average", ['sma50', 'sma150', 'vol50']],
        ["^GSPC", "S&P 500", ['sma50', 'sma150', 'vol50']],
        ["^IXIC", "NASDAQ Composite", ['sma50', 'sma150', 'vol50']],
        ["^RUT", "Russel 2000", ['sma50', 'sma150', 'vol50']],
        ["^NYA","NYSE Composite",  ['sma50', 'sma150', 'vol50']],
        ["^VIX", 'Volatility Index', ['sma50']],
        ["GCUSD", "Gold", ['sma50', 'sma150', 'vol50']],
        ['CLUSD', 'Crude Oil',  ['sma50', 'sma150', 'vol50']],
        ['NGUSD', "Natural Gas", ['sma50', 'sma150', 'vol50']],
        ['BTCUSD', "Bitcoin", ['sma50', 'sma150', 'vol50']]
        # ['DOGEUSD', "Dogecoin", ['sma50', 'sma150', 'vol50']]
    ]

    for i in indices_to_use:
        try:
            df = get_daily_stock_data.fetch_index_data(i[0])
            generate_graphs.make_simple_plot_of_security(df, i[1], 365, pdf, embellishments=i[2])
        except Exception as e:
            print("ERROR making index graph " + i[0] + " " + str(e), file=sys.stderr)



def make_file_of_stocks(stocks, filename, last_close_date=None):
    '''
    createss the pdf file but hands off thestocs to
    make_standard_plots_of_stocks
    to avtually plot

    '''
    pdf = PdfPages(filename)

    df = pd.read_csv(simple_screen.GOOD_STOCK_FILE, parse_dates=True)
    num = 0

    if not args.no_summary:
        make_market_summary(pdf)

        if 'LastChange' in df.columns:
            columns_to_use = ['Volume', 'LastChange', 'VolumeChange', 'VolumeAndLastChange']
            descrip_to_use = ["by Volume", "by % Price Change", "by % Volume Change", "by % Volume Change x % Price Change"]
            for i in range(len(columns_to_use)):
                j = df.sort_values([columns_to_use[i]],ascending=False)
                leaders = j['Ticker'].tolist()[:NUM_STOCKS_PER_SECTOR_CHART]
                generate_graphs.create_single_plot_of_a_bunch_of_stocks(leaders, pdf, title="Entire Market " + descrip_to_use[i], days=NUM_DAYS_PER_SECTOR_CHART, last_close_date=last_close_date)
        else:
            print("ERROR in the freshly generated file " + simple_screen.GOOD_STOCK_FILE, file=sys.stderr)


    if not args.no_sectors: 
        # start with an overview of the sectors
        etfs = ['XLC', 'XLF', 'XLI', 'XLK', 'XLB', 'XLE', 'XLY', 'XLV', 'XLRE', 'XLP', 'XLU']
        names = ["Communications", "Financials", "Industrials", "Tech", "Materials", "Energy", "Consumer Discretionary", "Health Care", "Real Estate", "Consumer Staples", "Utilities"]
        generate_graphs.create_single_plot_of_a_bunch_of_stocks(etfs, pdf, names, days=NUM_DAYS_PER_SECTOR_CHART, title="Sectors", last_close_date=last_close_date)

        # generate graph for each sector
        # using different criteria

        # get highest volume

        # df.sort_values(['job','count'],ascending=False).groupby('job').head(3)

        # leading performers for the entire market

        for i in df.sort_values(['Sector','Volume'],ascending=False).groupby('Sector'):
            leaders = i[1]['Ticker'].tolist()[:NUM_STOCKS_PER_SECTOR_CHART]
            generate_graphs.create_single_plot_of_a_bunch_of_stocks(leaders, pdf, title=i[0] + " by Volume", days=NUM_DAYS_PER_SECTOR_CHART, last_close_date=last_close_date)

        # there is the possibility that the list of stocks didin't update
        # correctly so make sure that the columns ectually exist
        if 'LastChange' in df.columns:
            # use highest price change
            for i in df.sort_values(['Sector','LastChange'],ascending=False).groupby('Sector'):
                leaders = i[1]['Ticker'].tolist()[:NUM_STOCKS_PER_SECTOR_CHART]
                generate_graphs.create_single_plot_of_a_bunch_of_stocks(leaders, pdf, title=i[0] + " by % Price Change", days=NUM_DAYS_PER_SECTOR_CHART, last_close_date=last_close_date)

            # use highet volume change
            for i in df.sort_values(['Sector','VolumeChange'],ascending=False).groupby('Sector'):
                leaders = i[1]['Ticker'].tolist()[:NUM_STOCKS_PER_SECTOR_CHART]
                generate_graphs.create_single_plot_of_a_bunch_of_stocks(leaders, pdf, title=i[0] + " by % Volume Change", days=NUM_DAYS_PER_SECTOR_CHART, last_close_date=last_close_date)

            # use highest combination of above
            for i in df.sort_values(['Sector','VolumeAndLastChange'],ascending=False).groupby('Sector'):
                leaders = i[1]['Ticker'].tolist()[:NUM_STOCKS_PER_SECTOR_CHART]
                generate_graphs.create_single_plot_of_a_bunch_of_stocks(leaders, pdf, title=i[0] + " by % Volume Change x % Price Change", days=NUM_DAYS_PER_SECTOR_CHART, last_close_date=last_close_date)
        else:
            print("ERROR in the freshly generated file " + simple_screen.GOOD_STOCK_FILE, file=sys.stderr)

    generate_graphs.make_standard_plots_of_stocks(stocks, pdf, last_close_date=last_close_date, show_option_info=not args.dont_show_option_info, show_volume_profile=not args.dont_show_volume_profile)
    pdf.close()
    return filename

parser = argparse.ArgumentParser()
parser.add_argument("--test", help="runs the test function", action="store_true")
parser.add_argument('--stocks', help="runs scanner agaunst the passed list if stocks seoerated by a comma")
parser.add_argument('--dont-email', action="store_true", help="don't email anything")
parser.add_argument('--all-good', action="store_true", help="don't test but rather assumne all the stocks match the requirements")
parser.add_argument('--dont-graph', action="store_true", help="don't make any graphs")
parser.add_argument('--close', help="date string of the last close to check (e.g. 2021-9-3)")
parser.add_argument('--force-update', action="store_true", help="always update the list of stocks")
parser.add_argument('--no-sectors', action="store_true", help="don't generate sector graphs")
parser.add_argument('--no-summary', action="store_true", help="don't generate summary graphs")
parser.add_argument('--production', action="store_true", help="consider this a polished production product for distribution")
parser.add_argument('--dont-show-option-info', action="store_true", help="don't add option data to the graph")
parser.add_argument('--dont-show-volume-profile', action="store_true", help="don't add volume profile to the graph")

# no longer used
# parser.add_argument('--send-to-mailing-list', help="sends the result to the given name of a mailing list (e.g. 'daily-scan-1')")

args = parser.parse_args()

nyse = mcal.get_calendar('NYSE')
now_in_nyse = dt.datetime.now(nyse.tz)
two_weeks_ago =  now_in_nyse - dt.timedelta(days=14)
twentyfour_hours_ago = now_in_nyse - dt.timedelta(hours=24)
last_two_week_closes = nyse.schedule(start_date=two_weeks_ago, end_date=dt.datetime.now(tz=nyse.tz))["market_close"]
if last_two_week_closes[-1] > now_in_nyse:
    last_market_close = last_two_week_closes[-2]
else:
    last_market_close = last_two_week_closes[-1]

if args.close:
    last_close_to_use = dt.date.fromisoformat(args.close)
else:
    last_close_to_use = last_market_close.date()
    # last_close_to_use = dt.date.today()

write_on_changes = False

if args.test:
    # test case
    # list of stocks to test
    test_stocks = ['AAPL', 'QQQ', 'PSQ', 'SPY', 'BRK.A', 'BRKS', 'QCOM', 'FB']
    stocks = pd.DataFrame(test_stocks, columns=['Ticker'])
elif args.stocks:
    stocks = args.stocks.split(',')
    stocks = pd.DataFrame(stocks, columns=['Ticker'])
else:
    # normal behavior
    # stocks = pd.read_csv("america_2021-11-25.csv")
    # stocks = pd.read_csv("america_2021-11-25-short-1.csv")
    stocks = pd.read_csv(simple_screen.GOOD_STOCK_FILE)
    # stocks = pd.read_csv(simple_screen.GOOD_STOCK_FILE, index_col=0)

    # since we update the incoming GOOD_STOCK_FILE during the initial
    # pass through the stocks, we only want to write the changes to the
    # disk if we checked the very last close date

    print("last_close_to_use: " + str(last_close_to_use) + ", last_market_close: " + str(last_market_close), file=sys.stderr)
    # only want to update this good stock file if the date we're running the scan
    # on is within the last 24 hours
    # if args.force_update or (last_close_to_use >= (dt.date.today() - dt.timedelta(hours=24))):
    if args.force_update or last_close_to_use == last_market_close.date():
        write_on_changes = True
    # chck to see if market close was within the last 24 hours ans if not just exit
    # this was made so as to not scan if there was a holiday or similar
    if not args.close and not args.force_update:
        if last_market_close < twentyfour_hours_ago :
            sys.exit("last market close (" + str(last_market_close) + ") was over 24 hours ago (" + str(twentyfour_hours_ago) + "); will not scan")

good_stocks = []
# stocks = pd.DataFrame()
changes = 0

for i in stocks.index:
    print("" + str(i+1) + "/" + str(stocks.index.stop), file=sys.stderr)
    stock = str(stocks["Ticker"][i])

    result = False

    if args.all_good:
        result = True
    else:
        # here we actually receive back from the checking funbction
        # nit inly the result if checking hyt also the stock data itself
        # which can be used for whateverv resson

        (result, df) = check_stock(stock, last_close_date=last_close_to_use)

        # here we update the close (Last) and volume and later write the
        # data back out where it came from
        if not (df is None):  # make sure stock data actually arrived
            # prevents a warning
            stocks.loc[i, 'Volume'] = df["Volume"].iloc[-1]
            stocks.loc[i, 'Last' ] =  df["Adj Close"].iloc[-1]
            if len(stocks) > 1:
                pchange = lambda a,b: (a-b)/b
                vc =pchange(df["Volume"].iloc[-1], df["Volume"].iloc[-2])
                lc =  pchange(df["Adj Close"].iloc[-1], df["Adj Close"].iloc[-2])              
                stocks.loc[i, 'VolumeChange'] = vc
                stocks.loc[i, 'LastChange' ] = lc
                stocks.loc[i, 'VolumeAndLastChange' ] = vc * lc                

            # stocks['Volume'][i] =  df["Volume"].iloc[-1]
            # stocks['Last'][i] =  df["Adj Close"].iloc[-1]
            changes = changes + 1

            # this is a good place to get the daily minute volume
            # provided this is part of the daily scan
            if last_close_to_use == last_market_close.date():
                gather_minute_data.store_minute_data_for_stock(stock)
    
    if result == True:
        good_stocks.append(stock)
        print(stock)

# if changes made to thevstock infodata so go ahead and update the file
print("changes: " + str(changes) + "; write_on_changes: " + str(write_on_changes), file=sys.stderr)
if changes > 0 and write_on_changes:
    copyfile(simple_screen.GOOD_STOCK_FILE, simple_screen.GOOD_STOCK_FILE + "~")
    with open(simple_screen.GOOD_STOCK_FILE,"w") as f:
        stocks.to_csv(f, index=False)

date_as_pretty_string = dt.datetime.now().strftime("%B %-d, %Y")

sender = default_sender
recipient = default_recipient

subject = "Scan Results " + date_as_pretty_string
files_to_send = []
body = ''

if len(good_stocks) == 0:
    print("No stocks found")
    body = "No stocks found."
else:
    body = ",".join(good_stocks)
    print(body)

    if not args.dont_graph:
        filename = dt.datetime.now().strftime("scan_results-%y-%m-%d-%H-%M.pdf")
        make_file_of_stocks(good_stocks, filename, last_close_date=last_close_to_use)
        print("Results in  " + filename, file=sys.stderr)
        files_to_send.append(filename)



if not args.dont_email:
    bcc = None
    if args.production:
        # should probabbly make sure the file exsits?
        with open(SUBSCRIBER_FILE) as x: bcc = x.read().splitlines()
        # print(bcc)
        # send_mail.send_production(subject, body, files_to_send)
    send_mail.send_with_attachment(sender, recipient, subject, body, files_to_send, bcc=bcc)

    # stopped working sometime in the Fall 2022
    # if args.send_to_mailing_list:
    #    send_mail.send_to_listmonk_mailinglist(args.send_to_mailing_list, subject, body, files_to_send)





