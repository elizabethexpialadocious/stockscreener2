''' generate_graphs.py

graphing routines used by the screener
'''

# lyne style reference
# https://www.pythonpool.com/matplotlib-linestyle/

from doctest import DocFileCase
from socket import AF_AX25
import pandas
import sys
import mplfinance as mpf
from matplotlib.backends.backend_pdf import PdfPages
import get_daily_stock_data
import matplotlib.pyplot as plt
import datetime as dt
import gather_minute_data as minute_data
import gather_option_data as option_data
import unusual_option_activity as uoa
import gather_upcoming_earnings as earnings
import draw_calendar as cal
import matplotlib.patches as patches
import get_fundamentals

from mpl_toolkits.axes_grid1.inset_locator import inset_axes

import seaborn as sns
import numpy as np

mc = mpf.make_marketcolors(
    up='tab:green', down='tab:red',
    # edge='lime',
    # wick={'up':'blue','down':'red'},
    volume='blue',
)

style = mpf.make_mpf_style(base_mpl_style="seaborn", marketcolors=mc)

# just fetch it once since we"ll be using it over and over again
# spy = get_daily_stock_data.fetch('spy')
spy = None


def add_attrition(ax, x=0.05, y=0.05, color="black", alpha=1):
    '''
    places a little notice regarding the source of financial information
    ax: axes
    '''
    ax.text(x, y, 'Financial Data from FinancialModelingPrep.com', transform=ax.transAxes,
            fontsize="xx-small", color=color, alpha=alpha,
            ha='left', va='top', rotation='0')


def add_little_longer_price_graph(df, big_graph_num_days, ax):
    '''
    draws a little plot of the given df if contains sufficiently more days than big_graph_num_days
    df: dataframe containing the stock info
    big_graph_num_days: the number of days used in the large plot; note that this is used to determine whether or not to display the little graph at all (consider the situation of a recent IPO and all the data is contained in the big graph)
    ax: the axes to draw to
    '''

    # maku sure there is enough data in df to buther showing a small plot
    if df.shape[0] < big_graph_num_days * 2:
        return
    else:
        little_graph_length = big_graph_num_days * 4
        if little_graph_length > df.shape[0]:
            little_graph_length = df.shape[0]

    ia = inset_axes(ax,
                    height="30%",  # set height
                    width="30%",  # and width
                    loc="upper left")  # center, you can check the different codes in plt.legend?

    ia.text(0.5, 0.5, "daily (" + str(little_graph_length) + " days)", transform=ia.transAxes,
            fontsize=20, color='gray', alpha=0.25,
            ha='center', va='center', rotation='30')

    #    ia = ax.inset_axes((0,0,2,1))

    # https://stackoverflow.com/questions/2176424/hiding-axis-text-in-matplotlib-plots

    # ia.spines['bottom'].set_color('0.5')
    # ia.spines['top'].set_color('0.5')
    # ia.spines['right'].set_color('0.5')
    # ia.spines['left'].set_color('0.5')

    # inset_axes.plot(df.tail(365))
    # ia.xaxis.label.set_visible(False)
    # ia.yaxis.label.set_visible(False)
    ia.set_axis_off()
    df.tail(little_graph_length)["Adj Close"].plot(
        kind='line', ax=ia, legend=False, alpha=0.5)

    # ia.plot(df.tail(little_graph_length))
    # mpf.plot(df.tail(little_graph_length), type="line", ax=ia)
    # mpf.plot(df.tail(90), type="candle", ax=ax)


def add_earnings(df, ax):
    try:
        eps = get_fundamentals.get_eps(df['Ticker'][0], limit=40)

        ia = inset_axes(ax,
                        height="30%",  # set height
                        width="30%",  # and width
                        loc="upper center")  # center, you can check the different codes in plt.legend?
        ia.text(0.5, 0.5, 'EPS', transform=ia.transAxes,
                fontsize=40, color='gray', alpha=0.25,
                ha='center', va='center', rotation='30')
        ia.set_axis_off()

        # use the last 20 (at most) values in the graph
        eps['eps'].tail(20).plot(kind='line', ax=ia,
                                 legend=False, alpha=0.5, style='.-')

        # we also want to do a quarter/quarter but we have to have enough data
        if len(eps.index) > 4:
            # we do so make q/q
            eps['q/q'] = eps['eps']/eps['eps'].shift(4)

            epsqq_adj = eps['q/q'] * (eps["eps"].max()-eps["eps"].min()) / \
                (eps['q/q'].max() - eps['q/q'].min())

            # now we want to scale thi data to that already plotted

            # ax1 = ia.twinx()
            # ax2 = ia.twinx()
            # and just plot it against it using the same length as
            # before
            # eps['eps'].tail(20).plot(kind='line', ax=ax1, legend=False, alpha=0.5, style='.-')

            epsqq_adj.tail(20).plot(kind='line', ax=ia,
                                    legend=False, alpha=0.5, style='--')

            # we only want to show the last 20 quarters but may not have that much
            # data
            # days_to_use = 20 if len(eps.index) >= 20 else len(eps.index)
            # eps = eps.tail(days_to_use)

            # we have to normalize it to the first non NaN in q/q - and just don't
            # plot Nan

            # f = eps['q/q'].first_valid_index()

            # normalize each part separately in case
            # they aren't the same length
            # eps[f:,'q/q'] = eps[f:,'q/q'].apply(lambda x: (x / x[0] * 100))
            # normalized.loc[f:] = eps[f:].apply(lambda x: (x / x[0] * 100))
            # eps['eps'] = eps['eps'].apply(lambda x: (x / x[0] * 100))

            # DOSESNT WORK
            # ~~~~~~~ ~~~~
            # consider using twinx for this
            # https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.twinx.html

            # normalized = eps[f:].apply(lambda x: (x / x[0] * 100))
            # normalized['q/q'].plot(kind='line', ax=ia, legend=False, alpha=0.5, style='--')
            # (xmin,xmax) = ia.get_xlim()
            # ia.hlines(y=normalized['eps'][0], linewidth=1, xmin=xmin, xmax=xmax, color='r', alpha=0.5)
        else:
            #     # just plot the eps if we don't have over a years worth of data
            #     normalized = eps
            eps['eps'].tail(20).plot(kind='line', ax=ia,
                                     legend=False, alpha=0.5, style='.-')

        # ia.text(0.5, 0.5, 'EPS', transform=ia.transAxes,
        #     fontsize=40, color='gray', alpha=0.25,
        #     ha='center', va='center', rotation='30')
        # ia.set_axis_off()
        # normalized['eps'].plot(kind='line', ax=ia, legend=False, alpha=0.5, style='.-')

    except Exception as e:
        print(" error " + df['Ticker'][0] + " " + str(e), file=sys.stderr)
        # just don't do anything - maybe it's an etf, who cares
        pass


def draw_calendar(ax, special_day, description, title, alpha):
    '''
    draws a little calendar onto ox of the month containg date placinge
    description within the month of the date given
    fig: a figure from matplotlib
    ax: an ax from matplotlib
    date: the date object representing the important date (e.g. earnings)
    description; blurb of text to place in the date box in the calendar (e.g. 'bmo')

    '''

    # code originally from
    # https://medium.com/@shimo164/lets-plot-your-own-calendar-with-matplotlib-af6265f50831
    # modified heavily
    #
    # seems like overkill at the moment, why not just make a 4x5 orray of
    # 28-30 days before the earnings and highlight today and earnings ?
    #   M T W T F
    #  +---------+
    #  | | | | | |
    #  +---------+
    #  | | | | | |
    #  +---------+
    #  | | |t| | |
    #  +---------+
    #  | | | |e| |
    #  +---------+

    ia = inset_axes(ax,
                    height="15%",  # set height
                    width="15%",  # and width
                    loc="lower center")  # center, you can check the different codes in plt.legend?
    # ia.set_axis_off()
    ia.axis([0, 5, 0, 5])
    ia.axis("off")

    today = dt.date.today()
    start_cal = special_day - dt.timedelta(21)
    # get first monday
    start_cal = start_cal - dt.timedelta(start_cal.weekday())
    # print(start_cal)
    # weekday, num_days = calendar.monthrange(earnings_day.year, earnings_day.month)

    # fix weekday so sunday's the first day
    # weekday = (weekday + 1) % 7

    # adjust by 0.5 to set text at the ceter of grid square
    x_start = 1 - 0.5
    y_start = 5 + 0.5
    x_offset_rate = 1
    y_offset = -1

    # label_month(year, month, ax, x_start, y_start + 2, 'black', alpha)
    ia.text(x_start, y_start, title, color='red',
            va="center", fontsize='xx-small', alpha=alpha)
    x_offset_rate = 1
    i = x_start
    for weekday in ["M", "T", "W", "T", "F"]:
        ia.text(i, y_start - 1, weekday, ha="center", va="center",
                color='black', fontsize='xx-small', alpha=alpha)
        i += 1

    # first determine the first monday before start_date

    j = y_start - 1  # kludge

    for day in range(0, 28):
        d = start_cal + dt.timedelta(day)
        weekday = d.weekday()
        i = x_start + weekday * x_offset_rate
        if weekday == 0:
            j += y_offset
        # color = check_color_day(year, month, day, fill_days, today )

        # if fill and check_fill_day(year, month, day, weekday, fill_days):
        #     fill_box(ax, i, j)
        # color = 'black'

        patch_color = None
        fill = False
        edge_color = None

        if d == special_day:
            # special case of when the earnings are that very day
            if d == today:
                color = 'blue'
                patch_color = 'red'
                fill = True
            else:  # if d < special_day  don't highlight?
                color = 'red'
                if today > special_day:
                    fill = False
                else:
                    patch_color = 'yellow'
                    fill = True
        elif d == today:
            color = 'blue'
            patch_color = 'blue'
            edge_color = 'blue'
            fill = False
        else:
            color = 'black'

        if not patch_color is None:
            # edgecolor="blue"
            ia.add_patch(patches.Rectangle((i - 0.5, j - 0.5), 1, 1,
                         facecolor=patch_color, alpha=.25, edgecolor=edge_color, fill=fill))

        # label_day(ax, day, i, j, color, alpha)
        if weekday < 5:
            ia.text(i, j, int(d.day), ha="center", va="center",
                    color=color, fontsize='xx-small', alpha=alpha)

    # # old
    # ia = inset_axes(ax,
    #                 height="15%", # set height
    #                 width="15%", # and width
    #                 loc="lower right") # center, you can check the different codes in plt.legend?
    # # ia.set_axis_off()
    # ia.axis([0, 5, 0, 5])
    # ia.axis("off")
    # cal.month_calendar(title, ia, date.year, date.month, True, [(date.month, date.day)], alpha=0.5)


def add_earnings_date(ticker, fig, ax):
    n = earnings.get_next_earnings(ticker)
    if not (n is None):
        (d, t) = n
        # title = "earnings: " +  d + " " + t
        # d.strftime("%A %d. %B %Y")
        d2 = dt.date.fromisoformat(d)
        title = d2.strftime("Earnings %a %b %d " + t.upper())
        draw_calendar(ax, d2, t, title, alpha=0.5)
        # x = .83
        # y = .05
        # color = 'red'
        # alpha = .5
        # ax.text(x, y, "earnings: " +  d + " " + t, transform=ax.transAxes,
        #     fontsize="small", color=color, alpha=alpha,
        #     ha='left', va='top', rotation='0')
        # ax.text( 5, 5, d + " " + t)


def add_option_volume(ticker_df, fig, ax, call_put, color):
    '''
    adds open interest to the side of the graph at the appropriate price
    sort of like tho volume profile

    '''


    # we only want to add open interest provided it is within the current
    # graph bounds

    ymin, ymax = ax.get_ylim()
    oi_bars_needed = 50

    #   df_options = option_data.get_volume_sum_df(ticker_df['Ticker'][0], call_put, ymin, ymax, 90)
    df_options = option_data. get_latest_option_info_df(
        ticker_df['Ticker'][0], call_put, ymin, ymax, 90)

    if len(df_options) > 0:
        price_slot = (max(ticker_df['Close']) -
                      min(ticker_df['Close'])) / oi_bars_needed
        # oiprofile  = df_options['csum'].groupby(df_options['strike'].apply(lambda x: price_slot*round(x/price_slot,0))).sum()
        oiprofile = df_options['open_interest'].groupby(
            df_options['strike'].apply(lambda x: price_slot*round(x/price_slot, 0))).sum()

        oi_y = oiprofile.keys().values
        oi_x = oiprofile.values / 50000000

        # originial from website
        # vpax = fig.add_axes(axlist[0].get_position())
        # vpax.set_axis_off()
        # vpax.set_xlim(right=1.2*max(volprofile.values))
        # vpax.barh( volprofile.keys().values, volprofile.values, height=0.75*bucket_size, align='center', color='cyan', alpha=0.45)

        oiax = fig.add_axes(ax.get_position())
        oiax.set_axis_off()
        # oiax.sex_xlim(left=0)
        oiax.set_xlim(right=(20 * max(oi_x)))
        oiax.set_ylim(ymin, ymax)
        oiax.barh(oi_y, oi_x, height=0.75*price_slot,
                  align='center', color=color, zorder=-5, alpha=0.25)
        # oiax.invert_xaxis()


def add_volume_profile(ticker_df, fig, ax):
    '''
    adds a volume profile to the fig in accordance with ticker_df
    ticker_df: dataframe of teh origiganal stack containing the days intended to graph

    info : https://github.com/matplotlib/mplfinance/issues/162

    '''

    # FIXME: codes' kind of a mess but it is currently working
    # we use the minute data to make the volume profile
    # which is stored in the database

    # Note that intead of doing a 'volume shelf' just a
    # volume profile in the right gutter that doesnt encroach
    # on the candles would work fine, maybe even better really,
    # as its just like volume below but turned on its side;
    # in this case it could be made the same blue as the
    # main volume graph

    begin_date = ticker_df.index[0]
    end_date = ticker_df.index[-1]

    # note that internally the next function turns the dates into strings
    # and the 'date' column (not the index) is already in string format so
    # this could be simplified
    df_minute = minute_data.get_minute_data_df(
        ticker_df['Ticker'][0], begin_date, end_date)

    if len(df_minute) == 0:
        return

    days_to_graph = (end_date - begin_date).days + 1
    vp_bars_needed = 50
    price_slot = (max(ticker_df['Close']) -
                  min(ticker_df['Close'])) / vp_bars_needed
    volprofile = df_minute['volume'].groupby(df_minute['close'].apply(
        lambda x: price_slot*round(x/price_slot, 0))).sum()
    #volprofile  = df_minute['volume'].groupby(df_minute['close'].apply(lambda x: price_slot*math.floor(x/price_slot))).sum()
    vp_y = volprofile.keys().values
    vp_x = volprofile.values / 50000000
    # vp_x = volprofile.values / 50000
    # fig, axlist = mpf.plot(df_daily.tail(days_to_graph),type='candle',returnfig=True, volume=True)

    # axlist[0].barh( vp_y, vp_x, height=0.75*price_slot, align='center', color='cyan', alpha=0.9)
    # axlist[0].invert_xaxis()

    # bb1 = axlist[0].get_position()
    # (x0, y0, w, h) = bb1.bounds

    b = (dt.datetime.fromisoformat(df_minute.iloc[0]['date'])).date()
    e = (dt.datetime.fromisoformat(df_minute.iloc[-1]['date'])).date()
    num_days_in_minute_data = (e-b).days + 1  # inclusive

    ymin, ymax = ax.get_ylim()

    vpax = fig.add_axes(ax.get_position())
    vpax.set_axis_off()
    # 5 days in complete graph == vpax.set_xlim(right=10*max(vp_x))
    # all days == vpax.set_xlim(right=10*max(vp_x))
    # note 10/18 is an empiric value that may need to be adjusted
    # * (12/17)
    # note dosen't really look right; it dosen't cover the appropriate days
    # but I'm not sure how it would really work right what with the ratio
    # being necessary (when equal to one it should cover the graph, which
    # it currently does; if adding another ratio what would happen?)
    # vpax.set_xlim(right=(days_to_graph/num_days_in_minute_data *  max(vp_x)))
    vpax.set_xlim(right=(20 * max(vp_x)))
    #vpax.set_ylim( min(df_daily.tail(90)['Low']), max(df_daily.tail(90)['High']) )
    vpax.set_ylim(ymin, ymax)
    vpax.barh(vp_y, vp_x, height=0.75*price_slot, align='center',
              color='blue', zorder=-5, alpha=0.25)
    vpax.invert_xaxis()


def make_standard_plot_of_stock(df, num_days, pdf=None, additions=None, show_option_info=True, show_volume_profile=True):
    '''
    makes the general/standard plot of a single stock (passed in as a
    DataFrame)'s past num_days to the pdf (if given) and adds the additions
    onto the plot
    df: the single stock data as a DataFrame
    num_days: the last number of days of the given df to show
    pdf: an instance of a PDF document to write to, use None for general output
    additons: a list of plots (as returned from mpf.make_addplot) to add to the
    stock plot 
    '''
    global spy

    # note that the caching mechanism later caused a bug when there was a discrepancy between
    # the oldest date of the various passed in dataframes of stock data - which is only
    # germane in regard to the portfolio stuff in check_my_portfolio
    # fixed by insuring that SPY's oldest date is as old or older than the stock dataframe

    if spy is None or spy.index[0] > df.index[0]:
        # kind of a cludge but works for now
        lcd = df.index[-1].date()
        n = (lcd - df.index[0].date()).days

        spy = get_daily_stock_data.fetch('SPY', n, last_close_date=lcd)

    ticker = df['Ticker'][0]

    sma50 = df['Close'].rolling(50).mean()
    sma150 = df['Close'].rolling(150).mean()

    # don't plot any extra plots if they contain any NaNs
    add2plots = []

    if not sma50.tail(num_days).isnull().any():
        add2plots.append(mpf.make_addplot(sma50.tail(num_days), color='y'))

    if not sma150.tail(num_days).isnull().any():
        add2plots.append(mpf.make_addplot(
            sma150.tail(num_days), color='orange'))

    # and for volume to
    volume_sma50 = df['Volume'].rolling(50).mean()

    if not volume_sma50.tail(num_days).isnull().any():
        add2plots.append(mpf.make_addplot(
            volume_sma50.tail(num_days), panel=1, color='y', width=1))

    # adjust the spy to make similar to our stock

    spy_adj1 = spy['Adj Close'].tail(num_days)

    # scale
    spy_adj2 = spy_adj1 * \
        (df["Adj Close"].tail(num_days).mean()/spy_adj1.mean())

    # doesn't look good:
    # flatten or expand as compared to df
    # should this be variance?
    # spy_adj2 = spy_adj1 * (df["Adj Close"].max()-df["Adj Close"].min())/(spy_adj1.max() - spy_adj1.min())

    # set first day if graph equal
    # spy_adj3 = spy_adj2 + (df["Adj Close"].tail(plot_days_adj)[0] - spy_adj2[0])
    # spy_adj3 = spy_adj2

    if not spy_adj2.isnull().any():
        add2plots.append(mpf.make_addplot(
            spy_adj2, color='gray', width=1, alpha=0.7))

    # fig = mpf.figure()

    if not (additions is None):
        add2plots.extend(additions)

    # try block was added to catch the SPY error mentioned above and show
    # an error instead of canceling the whole run

    try:
        fig, axlist = mpf.plot(
            df.tail(num_days),
            title=ticker,
            type="candle",
            ylabel='Price ($)',
            figratio=(12, 6),
            style=style,
            volume=True,
            returnfig=True,
            addplot=add2plots
        )

        # ax = fig.subplots()
        if show_option_info:
            udf = uoa.get_uoa(ticker)
            if len(udf.index):
                mn = udf['strike'].min()
                mx = udf['strike'].max()
                (y0, y1) = axlist[0].get_ylim()
                new_min = y0
                new_max = y1
                if mn < new_min:
                    new_min = mn * 0.93
                    axlist[0].set_ylim(bottom=new_min)
                if mx > y1:
                    new_max = y1 * 1.07
                    axlist[0].set_ylim(top=new_max)

                arrow_width = (new_max-new_min)/100
                for index, row in udf.iterrows():
                    color = 'green' if row['call_put'] == 'CALL' else 'RED'
                    # transform=axlist[0].transAxes
                    # axlist[0].arrow(3, row['strike'], -2, 0, color=color, width=arrow_width)
                    # x1 = df.tail(num_days).iloc[3]['date']
                    # x2 = df.tail(num_days).iloc[2]['date']
                    x1 = 3
                    x2 = -2
                    # axlist[0].arrow(x1, row['strike'], x2, 0, color=color, width=arrow_width)
                    axlist[0].annotate("", xy=(0, row['strike']), xytext=(4, row['strike']),
                                    arrowprops=dict(arrowstyle="->", color=color))

                    # break
                    #axlist[0].arrow(0, row['strike'], -1, 0, color=color, width=arrow_width)

        add_earnings_date(ticker, fig, axlist[0])
        add_attrition(axlist[2], 0.05, 0.07)
        add_little_longer_price_graph(df, num_days, axlist[0])
        if show_volume_profile:
            add_volume_profile(df.tail(num_days), fig, axlist[0])

        if show_option_info:
            add_option_volume(df.tail(num_days), fig, axlist[0], 'CALL', 'green')
            add_option_volume(df.tail(num_days), fig, axlist[0], 'PUT', 'red')

        add_earnings(df, axlist[0])

        # check if this stock has UOA

        if not (pdf is None):
            pdf.savefig(fig)
            fig.clear()
            plt.close(fig)

    except Exception as e:
        print("Plot Error (skipping) " + ticker + " " + str(e), file=sys.stderr)
        # raise


# @profile
def make_standard_plots_of_stocks(stocks, pdf=None, last_close_date=None, show_option_info=True, show_volume_profile=True):
    '''
    generate a standard candlestick charts of given list
    ofvstock ticjer names which are plotted into the given
    pdf data object

    this function is a decoupling of the pdf creation and plotting
    functions into solely plotting functions so that te generated
    pdf file can contain more things in te fytre if need be

    '''

    PLOT_NUM_DAYS = 90

    for i in range(len(stocks)):
        print(" " + stocks[i] + "(" + str(i+1) + "/" +
              str(len(stocks)) + ")", file=sys.stderr)
        try:
            df = get_daily_stock_data.fetch(
                stocks[i], last_close_date=last_close_date)
        except Exception as e:
            print("Error " + stocks[i] + " " + str(e), file=sys.stderr)
        else:

            # make adjustment for stocks having < PLOT_NUM_DAYS
            if df.shape[0] < PLOT_NUM_DAYS:
                plot_days_adj = df.shape[0]
            else:
                plot_days_adj = PLOT_NUM_DAYS

            make_standard_plot_of_stock(df, plot_days_adj, pdf, show_option_info=show_option_info, show_volume_profile=show_volume_profile)


def create_single_plot_of_a_bunch_of_stocks(stocks, pdf=None, stock_names=None, days=30, title=None, last_close_date=None):
    '''
    expects a list of stock ticker symbols and returns a 
    '''

    # LINE_STYLES = ['solid', 'dashed', 'dashdot', 'dotted']
    LINE_STYLES = ['solid', 'dashed', 'dotted']
    NUM_STYLES = len(LINE_STYLES)
    NUM_COLORS = int(len(stocks)/NUM_STYLES) + 1

    (stocks_df, good_stocks) = get_daily_stock_data.fetch_close_of_a_bunch_of_stocks(
        stocks, days, last_close_date=last_close_date)

    returns = stocks_df.apply(lambda x: (x / x[0] * 100))

    # color vstuff from https://stackoverflow.com/questions/8389636/creating-over-20-unique-legend-colors-using-matplotlib

    sns.reset_orig()  # get default matplotlib styles back
    # a list of RGB tuples
    clrs = sns.color_palette('hls', n_colors=NUM_COLORS)

    fig = plt.figure(figsize=(10, 6))

    # https://stackoverflow.com/questions/7125009/how-to-change-legend-size-with-matplotlib-pyplot?rq=1
    plt.rc('legend', fontsize='xx-small')
    plt.rc('legend', loc='upper left')

    if stock_names is None:
        stock_names = good_stocks

    # Plot the returns
    style = 0
    for i, stock in enumerate(good_stocks):
        lines = plt.plot(returns[stock], label=stock_names[i])
        lines[0].set_color(clrs[i % NUM_COLORS])
        lines[0].set_linestyle(LINE_STYLES[style])
        # print(i % NUM_COLORS, style)
        if i % NUM_COLORS == (NUM_COLORS - 1):
            style = style + 1
            if style >= NUM_STYLES:
                style = 0

    # We need to call .legend() to show the legend.
    plt.legend()
    # Give the axes labels
    plt.ylabel('Cumulative Returns %')
    plt.xlabel('Time')
    if not title is None:
        plt.title(title)
    # plt.show()
    add_attrition(plt.gca(), 0, 0.02, "gray", 0.5)
    if not (pdf is None):
        pdf.savefig(fig)
        fig.clear()
        plt.close(fig)


def make_simple_plot_of_security(df, title, num_days=365*2, pdf=None, embellishments=[]):
    '''
    making this to show index data for as long as the given dataframe
    so this is not embelished with anpthing like the make_standard_plot_of_stock
    is

    note that this dosen't plot to a PDF file - must be dealt with somewhere else
    so as to acomodate plotting of many things to a single page

    df: the security info to plot

    '''

    # some indices don't have volume so don't request it if it dosen't have it
    # (will have an error if you try to)

    show_volume = True if 'volume' in df.columns else False

    add2plots = []

    for i in embellishments:
        if i == 'sma50':
            add2plots.append(mpf.make_addplot(df['close'].rolling(
                50).mean().tail(num_days), panel=0, color='y', width=1))
        if i == 'sma150':
            add2plots.append(mpf.make_addplot(df['close'].rolling(
                150).mean().tail(num_days), panel=0, color='orange', width=1))
        if i == 'vol50' and show_volume:
            add2plots.append(mpf.make_addplot(df['volume'].rolling(
                50).mean().tail(num_days), panel=1, color='y', width=1))

    # causing an error, don't know why - if an error just skip

    fig, axlist = mpf.plot(
        df.tail(num_days),
        type="candle",
        figratio=(12, 3),
        style=style,
        volume=show_volume,
        tight_layout=True,
        returnfig=True,
        addplot=add2plots
    )

    axlist[0].text(0.5, 0.5, title, transform=axlist[0].transAxes,
                   fontsize=40, color='gray', alpha=0.5,
                   ha='center', va='center', rotation='0')

    # axlist[0].set_axis_off()
    if not (pdf is None):
        pdf.savefig(fig)
        fig.clear()
        plt.close(fig)
