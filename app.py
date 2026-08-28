import os
import ccxt

# إعداد الاتصال بـ Bybit وتوجيهه عبر البروكسي
exchange = ccxt.bybit({
    'apiKey': os.getenv('BYBIT_API_KEY'),
    'secret': os.getenv('BYBIT_API_SECRET'),
    'enableRateLimit': True,
    'proxies': {
        'http': 'socks5://127.0.0.1:40000',
        'https': 'socks5://127.0.0.1:40000',
    },
    'options': {
        'defaultType': 'spot',
    }
})

def main():
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"تم الاتصال بنجاح! سعر BTC الحالي: {ticker['last']} USDT")
        
        balance = exchange.fetch_balance()
        usdt_free = balance.get('USDT', {}).get('free', 0)
        print(f"رصيد USDT المتاح: {usdt_free}")
    except Exception as e:
        print("حدث خطأ أثناء الاتصال:", e)

if __name__ == "__main__":
    main()
