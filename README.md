Just a simple stock screener. Couple of caveats:
1) stock data comes from financialmodelingprep.com - so you need a key, and
2) option data comes from TDAmeritrade (for which you need a key as well)

I don't really mantain this anymore. Let me know if you have any questions. Hope someone likes it :-)

I use cron to run the main stock screener early in the morning after the market has closed, the gather option script at the end of the trading day (one hour before the market closes but isn't strictly necessary), and the simple screen script on the weekend.