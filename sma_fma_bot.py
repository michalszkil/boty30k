import binance
import pandas as pd
import numpy as np
import time
from datetime import datetime
import re

def get_data(asset):
    candles = client.get_klines(symbol=asset, interval='1m')
    df = pd.DataFrame(candles, columns=['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 
									'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 
									'Taker buy quote asset volume', 'Ignore']).astype('float') # bo domyślnie to są stringi xd
    # Wzór na RSI kradziony z https://www.learnpythonwithrune.org/pandas-calculate-the-relative-strength-index-rsi-on-a-stock/
    delta = df['Close'].diff()
    up = delta.clip(lower=0)
    down = -1*delta.clip(upper=0)
    ema_up = up.ewm(com=13, adjust=False).mean()
    ema_down = down.ewm(com=13, adjust=False).mean()
    rs = ema_up/ema_down
    df['RSI'] = 100 - (100/(1 + rs))
    # Średnie kroczące 
    # Przykładowe długości okien https://www.investopedia.com/articles/active-trading/010116/perfect-moving-averages-day-trading.asp
    df['FMA'] = df['Close'].rolling(window=5).mean()
    df['SMA'] = df['Close'].rolling(window=13).mean()
    # Wyrzucamy pierwsze 14 dni żeby mieć wiarygodne wartości RSI
    df = df.iloc[14:]
    return df

client = binance.Client()

starting_cash = 1000.0 # USDT
cash = starting_cash
crypto = 0.0
symbol = 'ACMUSDT'

hs = open('log_' + symbol + '_' + 
re.sub('[^0-9a-zA-Z]+', '_', datetime.fromtimestamp(time.time()).strftime('%m/%d/%Y, %H:%M:%S')) + 
'.txt','a+')
text = ('Bot started running. ' + datetime.fromtimestamp(time.time()).strftime('%m/%d/%Y, %H:%M:%S') + '\n' + 
'Cash = ' + str(cash) + ' Crypto = ' + str(crypto) +'\n\n')
print(text)
hs.write(text)

try:
    while True:
        data = get_data(symbol)
        # generowanie sygnałów buy/sell
        data['signal'] = 0.0
        data['signal'] = np.where(data['FMA'] > data['SMA'], 1.0, 0.0)
        data['position'] = data['signal'].diff()
        data['position'] = data['position'].map({1: 'buy', -1: 'sell'})

        if data.iloc[-1]['position'] == 'buy' and cash != 0:
            crypto = cash/data.iloc[-1]['Close']
            cash = 0
            text = (datetime.fromtimestamp(time.time()).strftime('%m/%d/%Y, %H:%M:%S') + '\n' + 
            'FMA = ' + str(data.iloc[-1]['FMA']) + ' SMA = ' + str(data.iloc[-1]['SMA']) + '\n' +
            'Bought for a price of ' + str(data.iloc[-1]['Close']) + '\n' + 
            'Cash = ' + str(cash) + ' Crypto = ' + str(crypto) + '\n\n') 
            print(text)
            hs.write(text)
        elif data.iloc[-1]['position'] == 'sell' and crypto != 0:
            cash = crypto*data.iloc[-1]['Close']
            crypto = 0
            text = (datetime.fromtimestamp(time.time()).strftime('%m/%d/%Y, %H:%M:%S') + '\n' + 
            'FMA = ' + str(data.iloc[-1]['FMA']) + ' SMA = ' + str(data.iloc[-1]['SMA']) + '\n' +
            'Sold for a price of ' + str(data.iloc[-1]['Close']) + '\n' + 
            'Cash = ' + str(cash) + ' Crypto = ' + str(crypto) + '\n\n')
            print(text)
            hs.write(text)
        else:
            text = (datetime.fromtimestamp(time.time()).strftime('%m/%d/%Y, %H:%M:%S') + '\n' + 
            'FMA = ' + str(data.iloc[-1]['FMA']) + ' SMA = ' + str(data.iloc[-1]['SMA']) + '\n' + 
            'No signal. Current price = ' + str(data.iloc[-1]['Close']) + '\n' +  
            'Cash = ' + str(cash) + ' Crypto = ' + str(crypto) + '\n\n')
            print(text)
            hs.write(text)
        time.sleep(60)
except KeyboardInterrupt:
    if cash == 0:
        cash = crypto*data.iloc[-1]['Close']
        crypto = 0
        text = "Sold all crypto for a price of " + str(data.iloc[-1]['Close']) + '\n'
        print(text)
        hs.write(text)
    if cash > starting_cash:
        text = "You made a profit of " + str(cash - starting_cash) + '\n'
        print(text)
        hs.write(text)
    elif cash == starting_cash:
        text = "You made no profit or loss" + '\n'
        print(text)
        hs.write(text)
    else:
        text = "Congratulations! You lost money xD" + '\n'
        print(text)
        hs.write(text)

    text = ('Bot interrupted' + '\n' +  
    'Cash = ' + str(cash) + ' Crypto = ' + str(crypto) + '\n' + 
    'Wallet value = ' + str(cash + crypto*data.iloc[-1]['Close']))
    print(text)
    hs.write(text)
    
hs.close() 