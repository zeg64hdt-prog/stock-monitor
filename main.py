import os
import yfinance as yf
import pandas as pd
from linebot import LineBotApi
from linebot.models import TextSendMessage

# --- 設定エリア ---
TICKERS = ["7267.T", "1678.T", "7795.T", "6140.T", "2195.T", "3565.T"]

def calculate_rsi(series, period=13):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_stock_data(ticker):
    df = yf.download(ticker, period="60d", interval="1d")
    
    # 指標の計算
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA25'] = df['Close'].rolling(window=25).mean()
    # RSI13日を計算
    df['RSI'] = calculate_rsi(df['Close'], 13)
    df['Vol_MA5'] = df['Volume'].rolling(window=5).mean()
    
    return df.iloc[-1], df.iloc[-2]

def check_alert(ticker):
    try:
        current, previous = get_stock_data(ticker)
        price = float(current['Close'])
        ma5 = float(current['MA5'])
        ma25 = float(current['MA25'])
        rsi = float(current['RSI'])
        volume = float(current['Volume'])
        vol_ma5 = float(current['Vol_MA5'])
        
        messages = []
        if rsi >= 70 and price < ma5:
            messages.append(f"⚠️【一部利確検討】RSI13日が{rsi:.1f}で70超。5日線を割り込み。")
        if price < ma25 and previous['Close'] < previous['MA25']:
            messages.append(f"🚨【警戒】25日線を2日連続で下回っています。")
        if volume > vol_ma5 * 1.5:
            messages.append(f"📊【出来高急増】直近5日平均の1.5倍以上の商い。")

        if messages:
            header = f"\n【銘柄アラート: {ticker}】\n昨日の終値: {price:.1f}円\n"
            return header + "\n".join(messages)
    except Exception as e:
        print(f"Error checking {ticker}: {e}")
    return None

def send_line(text):
    line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
    user_id = os.environ["USER_ID"]
    line_bot_api.push_message(user_id, TextSendMessage(text=text))

def main():
    all_alerts = []
    for ticker in TICKERS:
        alert = check_alert(ticker)
        if alert:
            all_alerts.append(alert)
    if all_alerts:
        send_line("\n".join(all_alerts))

if __name__ == "__main__":
    main()
