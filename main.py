import os
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from linebot import LineBotApi
from linebot.models import TextSendMessage

# --- 設定エリア ---
TICKERS = ["7267.T", "1678.T", "7795.T", "5388.T", "6857.T", "3565.T"]

def get_stock_data(ticker):
    # RSI13日とMA25算出のため取得
    df = yf.download(ticker, period="60d", interval="1d")
    
    # 指標の計算
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA25'] = df['Close'].rolling(window=25).mean()
    df['RSI'] = ta.rsi(df['Close'], length=13)
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
        
        # 1. RSI 13日 70以上の過熱確認
        is_overheated = rsi >= 70
        
        # 2. 5日線割れ
        if is_overheated and price < ma5:
            messages.append(f"⚠️【一部利確検討】RSI13日が{rsi:.1f}で70超。5日線を割り込み。")
            
        # 3. 25日線割れ
        if price < ma25 and previous['Close'] < previous['MA25']:
            messages.append(f"🚨【警戒】25日線を2日連続で下回っています。")

        # 4. 出来高の急増
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
