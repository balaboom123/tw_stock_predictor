import requests
import datetime
import pandas as pd
import io
import numpy as np

# 下載某天的資料
date = datetime.date(2019, 1, 2)
datestr = date.strftime("%Y%m%d")

res = requests.get(
    "https://www.twse.com.tw/exchangeReport/MI_5MINS_INDEX?response=csv&date=" + datestr + "&_=1631534526262")
# print(res.text[:1000])

# 將資料用pandas整理成表格
df = pd.read_csv(io.StringIO(res.text.replace("=", "")), header=1, index_col="時間")

# 資料處理
df = df.dropna(how="all", axis=0).dropna(how="all", axis=1)
df.index = pd.to_datetime(datestr + ' ' + df.index)
df = df.applymap(lambda s: float(str(s).replace(",", "")))

from finlab.data import Data

data = Data()
twii = data.get("發行量加權股價指數")
twii = twii['台股指數']

# 加權指數 1分k
twii = twii[twii.index.second == 0]

twii_daily = twii.groupby([twii.index.date]).first()
twii_daily.index = pd.to_datetime(twii_daily.index)

# 60日平均
twii_average = twii_daily.rolling(60).mean()
twii_bias = twii_daily / twii_average
# 後60日漲跌
twii_profit = twii_daily.shift(-60) / twii_daily

df = pd.DataFrame({
    'price': twii_daily,
    'sma': twii_average,
    'bias': twii_bias,
    'profit': twii_profit,
    'year': twii_daily.index.year,
})
df = df.dropna(how='any')


# 以標準差製作選股策略
# 優化後參數 1300 2300 1 1
def strategy(sma_min=1300, bound_rolling=2300, up_std=1, lower_std=1):
    sma = twii.rolling(sma_min).mean()
    bias = twii / sma
    up_bound = 1 + bias.rolling(bound_rolling).std() * up_std
    lower_bound = 1 - bias.rolling(bound_rolling).std() * lower_std

    buy = bias > up_bound
    sell = bias < lower_bound

    hold = pd.Series(np.nan, index=sell.index)
    hold[buy] = 1
    hold[sell] = 0
    hold = hold.ffill()

    ret = twii.shift(-2) / twii.shift(-1)

    ret[hold == 0] = 1
    ret -= hold.diff().abs() * 3 / twii
    creturn = ret.cumprod()
    print(creturn.dropna()[-1])

strategy()

open_ = data.get_adj("開盤價")
close = data.get_adj('收盤價')

profit1 = open_.shift(-2) / open_.shift(-1)
profit5 = open_.shift(-6) / open_.shift(-1)
profit10 = open_.shift(-11) / open_.shift(-1)
profit60 = open_.shift(-61) / open_.shift(-1)
profit1 = profit1.unstack()
profit5 = profit5.unstack()
profit10 = profit10.unstack()
profit60 = profit60.unstack()

# results = {}
# counts = {}
from talib import abstract

# for fname in [fname for fname in dir(abstract) if fname[:3] == 'CDL']:
#     df = data.talib(fname)
#     df = df.unstack()
#     pos = df > 0
#     neg = df < 0
#
#     results['NEG_' + fname] = {
#         'profit1': profit1[neg].mean(),
#         'profit5': profit5[neg].mean(),
#         'profit10': profit10[neg].mean(),
#         'profit60': profit60[neg].mean(),
#         'count': sum(neg),
#     }
#     results['POS_' + fname] = {
#         'profit1': profit1[pos].mean(),
#         'profit5': profit5[pos].mean(),
#         'profit10': profit10[pos].mean(),
#         'profit60': profit60[pos].mean(),
#         'count': sum(pos),
#     }
#     print(fname)