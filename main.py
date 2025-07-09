# نصب کتابخانه‌ها (در محیط local یا render اجرا شود)
# pip install ccxt schedule requests

import ccxt
import random
import requests
import time
import schedule
import pandas as pd

# ----------- تنظیمات API -----------
KCEX_API_KEY = 'YOUR_KCEX_API_KEY'
KCEX_SECRET = 'YOUR_KCEX_API_SECRET'

TELEGRAM_TOKEN = "8176342507:AAHtFPLhRRgajROKsg1rBzkT_6jFhG59LyM"
TELEGRAM_CHAT_ID = "1614623845"

# ----------- اتصال به KCEX با CCXT -----------
exchange = ccxt.kcex({
    'apiKey': KCEX_API_KEY,
    'secret': KCEX_SECRET,
    'enableRateLimit': True,
})

# ----------- گرفتن لیست 200 نماد برتر -----------
def get_top_symbols():
    try:
        markets = exchange.load_markets()
        symbols = list(markets.keys())
        usdt_symbols = [s for s in symbols if "/USDT" in s]
        return usdt_symbols[:200]  # اولین 200 تا
    except Exception as e:
        print("Error fetching symbols:", e)
        return []

# ----------- گرفتن دیتا کندل -----------
def get_ohlcv(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

# ----------- تحلیل ICT ساده -----------
def analyze_with_ict(df):
    try:
        if df.empty:
            return None

        last_close = df['close'].iloc[-1]
        previous_high = df['high'].iloc[-5:-1].max()
        previous_low = df['low'].iloc[-5:-1].min()

        msb = last_close > previous_high  # MSB صعودی ساده

        if msb:
            signal = "Buy"
            tp1 = last_close + (last_close - previous_low) * 1
            tp2 = last_close + (last_close - previous_low) * 2
            sl = previous_low
        else:
            signal = "Sell"
            tp1 = last_close - (previous_high - last_close) * 1
            tp2 = last_close - (previous_high - last_close) * 2
            sl = previous_high

        return {
            'signal': signal,
            'entry': last_close,
            'tp1': round(tp1, 4),
            'tp2': round(tp2, 4),
            'sl': round(sl, 4)
        }

    except Exception as e:
        print("Error analyzing ICT:", e)
        return None

# ----------- ارسال به تلگرام -----------
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram Error:", e)

# ----------- اجرای تحلیل و ارسال سیگنال -----------
def process():
    symbols = get_top_symbols()
    if not symbols:
        return

    selected = random.sample(symbols, 5)

    for symbol in selected:
        df = get_ohlcv(symbol)
        analysis = analyze_with_ict(df)
        if analysis:
            msg = f"\n📊 {symbol}\n📈 سیگنال: {analysis['signal']}\n💰 ورود: {analysis['entry']}\n🎯 TP1: {analysis['tp1']}\n🎯 TP2: {analysis['tp2']}\n🛑 SL: {analysis['sl']}"
            send_telegram_message(msg)
        else:
            send_telegram_message(f"⚠️ تحلیل {symbol} انجام نشد.")

# ----------- زمانبندی اجرای هر 5 دقیقه -----------
schedule.every(5).minutes.do(process)

if __name__ == "__main__":
    print("🚀 Bot started!")
    while True:
        schedule.run_pending()
        time.sleep(1)
# Update for deploy
