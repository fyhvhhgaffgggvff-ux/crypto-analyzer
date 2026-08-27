import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import ccxt
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. إعدادات الصفحة والواجهة
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="منصة التحليلات المالية الذكية وتتبع الهوامير",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🦅 منصة التحليل المالي وتتبع حركة الهوامير الذكية")
st.caption("نظام تحليلي متكامل يجمع بين التحليل الفني، مشاعر التواصل الاجتماعي، وحركة السيولة الكبيرة.")

# -----------------------------------------------------------------------------
# 2. إعدادات شريط الأدوات الجانبي (Sidebar)
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ إعدادات التحليل")

# استخدام Bybit بدلاً من Binance لتفادي الحظر الجغرافي
symbol = st.sidebar.text_input("رمز الزوج (مثل SOL/USDT أو BTC/USDT)", value="SOL/USDT").upper()
timeframe = st.sidebar.selectbox("الإطار الزمني", ["1m", "5m", "15m", "1h", "4h", "1d"], index=3)
limit = st.sidebar.slider("عدد الشموع المطلوبة للتحليل", min_value=50, max_value=500, value=150)

# -----------------------------------------------------------------------------
# 3. دالة جلب البيانات من منصة Bybit
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60)
def fetch_market_data(symbol, timeframe, limit):
    try:
        exchange = ccxt.bybit({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df, None
    except Exception as e:
        return None, str(e)

# -----------------------------------------------------------------------------
# 4. دالة حساب المؤشرات الفنية
# -----------------------------------------------------------------------------
def calculate_indicators(df):
    # المتوسطات المتحركة
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    
    # مؤشر القوة النسبية RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # تتبع حركة السيولة/الهوامير (Volume Spike Detection)
    mean_volume = df['volume'].rolling(window=20).mean()
    std_volume = df['volume'].rolling(window=20).std()
    df['Whale_Activity'] = df['volume'] > (mean_volume + 2 * std_volume)
    
    return df

# -----------------------------------------------------------------------------
# 5. تنفيـذ جلب البيانات والعرض
# -----------------------------------------------------------------------------
with st.spinner("جاري جلب البيانات وتحليل السوق من Bybit..."):
    df, error = fetch_market_data(symbol, timeframe, limit)

if error:
    st.error(f"خطأ في جلب بيانات السوق عبر Bybit: {error}")
else:
    df = calculate_indicators(df)
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # عرض المؤشرات السريعة (KPIs)
    col1, col2, col3, col4 = st.columns(4)
    price_change = ((latest['close'] - prev['close']) / prev['close']) * 100
    
    col1.metric("السعر الحالي", f"${latest['close']:,.2f}", f"{price_change:+.2f}%")
    col2.metric("حجم التداول (Volume)", f"{latest['volume']:,.0f}")
    col3.metric("مؤشر RSI (14)", f"{latest['RSI']:.1f}")
    
    whale_status = "🚨 نشاط مكثف (دخل هامور)" if latest['Whale_Activity'] else "🟢 طبيعي"
    col4.metric("حركة السيولة الكبيرة", whale_status)

    # -------------------------------------------------------------------------
    # 6. الرسم البياني التفاعلي (Plotly Chart)
    # -------------------------------------------------------------------------
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03, 
        row_heights=[0.7, 0.3],
        subplot_titles=(f"الرسم البياني لـ {symbol}", "حجم التداول والسيولة")
    )

    # شمعات اليابانية (Candlesticks)
    fig.add_trace(go.Candlestick(
        x=df['datetime'],
        open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        name="السعر"
    ), row=1, col=1)

    # المتوسطات المتحركة
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['SMA_20'], mode='lines', name='SMA 20', line=dict(color='orange', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['SMA_50'], mode='lines', name='SMA 50', line=dict(color='blue', width=1)), row=1, col=1)

    # أحجام التداول وتحديد الهوامير
    colors = ['red' if df['open'].iloc[i] > df['close'].iloc[i] else 'green' for i in range(len(df))]
    fig.add_trace(go.Bar(x=df['datetime'], y=df['volume'], marker_color=colors, name="Volume"), row=2, col=1)

    # إبراز نقاط دخول الهوامير باللون الأصفر
    whales_df = df[df['Whale_Activity']]
    if not whales_df.empty:
        fig.add_trace(go.Scatter(
            x=whales_df['datetime'], 
            y=whales_df['volume'],
            mode='markers',
            marker=dict(color='gold', size=10, symbol='star'),
            name='تنبيه دخول سيولة ضخمة'
        ), row=2, col=1)

    fig.update_layout(
        height=650, 
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------------------------------------------------------------------------
    # 7. ملخص التحليل الفني والقرار الذكي
    # -------------------------------------------------------------------------
    st.subheader("💡 ملخص التوصية الذكية")
    if latest['RSI'] > 70:
        st.warning("⚠️ المؤشر في منطقة تشبع شرائي (Overbought)، احذر من التصحيح الهبوطي.")
    elif latest['RSI'] < 30:
        st.success("🟢 المؤشر في منطقة تشبع بيعي (Oversold)، فرصة ارتداد صعودي محتملة.")
    else:
        st.info("⚖️ حركة الحركة الفنية متوازنة حالياً في النطاق المحايد.")

    if latest['Whale_Activity']:
        st.error("🚨 تم اكتشاف دخول سيولة استثنائية (Whale Spike) في الشمعة الأخيرة!")
