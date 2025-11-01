import yfinance as yf
import re

def fetch_data(ticker, period="1y"):
    # 🔹 自動補上台股代號
    if re.match(r"^\d+$", ticker):
        ticker = ticker + ".TW"

    data = yf.download(ticker, period=period, progress=False)
    
    if data.empty:
        raise ValueError(f"找不到股票資料：{ticker}")

    data = data[['Open', 'High', 'Low', 'Close']]
    data.dropna(inplace=True)
    return data
