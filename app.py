import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import time

session = requests.Session()

# =========================
# 🧠 جلب العملات
# =========================
def get_all_coins(pages=2):
    coins = []

    for page in range(1, pages + 1):
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "volume_desc",
            "per_page": 100,
            "page": page
        }

        try:
            data = session.get(url, params=params, timeout=15)

            if data.status_code != 200:
                continue

            data = data.json()
            coins.extend([c['id'] for c in data])

        except:
            continue

    return coins

# =========================
# 📊 بيانات العملة
# =========================
def get_data(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"

    params = {
        "vs_currency": "usd",
        "days": "7",
        "interval": "hourly"
    }

    try:
        data = session.get(url, params=params, timeout=15)

        if data.status_code != 200:
            return None

        data = data.json()

        if "prices" not in data:
            return None

        prices = data['prices']
        volumes = data['total_volumes']

        df = pd.DataFrame(prices, columns=['time', 'price'])
        df['volume'] = [v[1] for v in volumes]

        df['high'] = df['price'].rolling(3).max()
        df['low'] = df['price'].rolling(3).min()

        return df.dropna()

    except:
        return None

# =========================
# 📉 VCP
# =========================
def detect_vcp(df):
    if df is None or len(df) < 50:
        return False

    df = df.copy()
    df['volatility'] = (df['high'] - df['low']) / df['low']

    recent = df.tail(30)

    v1 = recent['volatility'].iloc[:10].mean()
    v2 = recent['volatility'].iloc[10:20].mean()
    v3 = recent['volatility'].iloc[20:30].mean()

    vol1 = recent['volume'].iloc[:10].mean()
    vol2 = recent['volume'].iloc[10:20].mean()
    vol3 = recent['volume'].iloc[20:30].mean()

    return v1 > v2 > v3 and vol1 > vol2 > vol3

# =========================
# 🔍 تحليل عملة
# =========================
def analyze_coin(coin):
    print(f"🔎 فحص: {coin}")

    df = get_data(coin)

    if detect_vcp(df):
        print(f"🔥 فرصة VCP: {coin}")
        return coin

    return None

# =========================
# 🚀 Scan
# =========================
def scan():
    coins = get_all_coins(pages=2)

    print(f"\n🚀 عدد العملات: {len(coins)}")
    print("⏳ جاري الفحص...\n")

    results = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        outputs = executor.map(analyze_coin, coins)

    for r in outputs:
        if r:
            results.append(r)

    return results

# =========================
# ▶️ تشغيل
# =========================
if __name__ == "__main__":
    coins = scan()

    print("\n====================")
    print("🔥 أفضل عملات VCP:")
    print("====================")

    if not coins:
        print("❌ مفيش فرص حالياً")
    else:
        for c in coins:
            print("✔", c)

    input("\nاضغط Enter للخروج...")
