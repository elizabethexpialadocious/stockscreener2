# session_setup

# all the session handling routines in one place (cache name, etc.)

import datetime as dt
import requests_cache

todays_date_as_string = dt.datetime.now().strftime("%y-%m-%d")
cache_name = "cache-" + todays_date_as_string
'''
the cache becomes unweildingly large rather quickly and it is redundant daily
seeing that it caches whole web pages not simply stock prices - e.g. it does
not go out an pick up the latest stock price if we have all it's old stock values.
So, to counteract this, a new cache shall be made daily. Of course, it'll need to be removed
on a regular basis.

'''
expire_after = dt.timedelta(hours=24)
session = requests_cache.CachedSession(cache_name=cache_name, backend='sqlite', expire_after=expire_after)
session.headers = {     'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',     'Accept': 'application/json;charset=utf-8'     }
