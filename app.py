import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf

# -----------------------------------------------------------------------------
# 1. إعدادات الصفحة والتصميم البصري (CSS)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="منصة الذكاء الاصطناعي وتتبع الهوامير",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .metric-card {
        background: linear-gradient(135deg, #1e2638 0%, #111827 100%);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    .metric-title { color: #9ca3af; font-size: 13px; margin-bottom: 4px; }
    .metric-value { color: #ffffff; font-size: 22px; font-weight: bold; }
    .metric-sub { font-size: 12px; margin-top: 4px; }
    
    .ai-box-buy {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(6, 95, 70, 0.3));
        border: 1px solid #10b981;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .ai-box-sell {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(153, 27, 27, 0.3));
        border: 1px solid #ef4444;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .ai-box-hold {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(180, 83, 9, 0.3));
        border: 1px solid #f59e0b;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. الهيدر الرئيسي
# -----------------------------------------------------------------------------
st.markdown("<h1 style='text-align: right; color: #f3f4f6;'>🤖 منصة التحليل الذكي وتتبع حركة الهوامير (AI Trading Platform)</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: right; color: #9ca3af; font-size: 14px;'>مدعومة بمحرك تحليل البيانات الفنية والرصد اللحظي لسيولة صانعي السوق.</p>", unsafe_allow_html=True)
st.markdown("---")

# -----------------------------------------------------------------------------
# 3. إعدادات لوحة التحكم الجانبية
# -----------------------------------------------------------------------------
st.sidebar.markdown("<h2 style='text-align: right;'>⚙️ لوحة التحكم والتنبيهات</h2>", unsafe_allow_html=True)

preset_coins = {
    "🐕 Dogecoin (DOGE)": "DOGE",
    "☀️ Solana (SOL)": "SOL",
    "💎 Ethereum (ETH)": "ETH",
    "₿ Bitcoin (BTC)": "BTC",
    "🐸 Pepe (PEPE)": "PEPE",
    "⚡ Ripple (XRP)": "XRP",
    "🔍 عملة أخرى...": "CUSTOM"
}

selected_option = st.sidebar.selectbox("اختر العملة المراد تحليلها", list(preset_coins.keys()), index=0)

if preset_coins[selected_option] == "CUSTOM":
    symbol_input = st.sidebar.text_input("ادخل رمز العملة", value="DOGE").upper().strip()
else:
    symbol_input = preset_coins[selected_option]

ticker_symbol = f"{symbol_input}-USD"

interval = st.sidebar.selectbox("الإطار الزمني (Timeframe)", ["1m", "5m", "15m", "1h", "1d"], index=3)
period = st.sidebar.selectbox("النطاق الزمني التاريخي", ["1d", "5d", "1mo", "3mo", "1y"], index=2)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔔 خيارات التنبيهات الذكية")
alert_whale = st.sidebar.checkbox("تنبيه سيولة الهوامير ⭐️", value=True)
alert_rsi = st.sidebar.checkbox("تنبيه مناطق RSI الحرجة 📈", value=True)
alert_ma = st.sidebar.checkbox("تنبيه تقاطع المتوسطات (SMA) 🔄", value=True)

# -----------------------------------------------------------------------------
# 4. جلب البيانات وحساب المؤشرات
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60)
def fetch_market_data(ticker, period, interval):
    try:
        data = yf.download(tickers=ticker, period=period, interval=interval, progress=False)
        if data.empty:
            return None, f"لم يتم العثور على بيانات للرمز {ticker}."
        
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        df = data.reset_index()
        df.rename(columns={
            'Datetime': 'datetime', 
            'Date': 'datetime',
            'Open': 'open', 
            'High': 'high', 
            'Low': 'low', 
            'Close': 'close', 
            'Volume': 'volume'
        }, inplace=True)
        return df, None
    except Exception as e:
        return None, str(e)

def calculate_indicators(df):
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Whale Spikes
    mean_volume = df['volume'].rolling(window=20).mean()
    std_volume = df['volume'].rolling(window=20).std()
    df['Whale_Activity'] = df['volume'] > (mean_volume + 2.2 * std_volume)
    
    return df

# -----------------------------------------------------------------------------
# 5. محرك الذكاء الاصطناعي (AI Signal Generator)
# -----------------------------------------------------------------------------
def run_ai_analysis(df):
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    score = 0 # نقاط التقييم: +1 للشراء, -1 للبيع
    reasons = []
    
    # 1. تحليل SMA 20 vs 50
    if latest['close'] > latest['SMA_20'] > latest['SMA_50']:
        score += 2
        reasons.append("السعر يتحرك في اتجاه صاعد قوي فوق متوسطات 20 و 50.")
    elif latest['close'] < latest['SMA_20'] < latest['SMA_50']:
        score -= 2
        reasons.append("السعر في مسار هابط تحت المتوسطات الرئيسية.")
    else:
        reasons.append("السعر في تذبذب عرضي بالقرب من المتوسطات.")

    # 2. تحليل RSI
    rsi = latest['RSI']
    if rsi < 35:
        score += 2
        reasons.append(f"مؤشر RSI عند ({rsi:.1f}) يظهر وصول السعر لمناطق تشبع بيعي وزهيدة جداً (فرصة ارتداد).")
    elif rsi > 70:
        score -= 2
        reasons.append(f"مؤشر RSI عند ({rsi:.1f}) يظهر وصول السعر لمناطق تضخم وتشبع شرائي مرتفع.")
    else:
        reasons.append(f"مؤشر RSI في المنطقة المتوازنة المحايدة ({rsi:.1f}).")

    # 3. تحليل سيولة الهوامير
    if latest['Whale_Activity']:
        score += 1.5
        reasons.append("تم رصد ضخ سيولة مفاجئة من الهوامير في الشمعة الأخيرة!")

    # تحديد القرار النهائي
    if score >= 2:
        decision = "BUY"
        title = "🟢 قرار الذكاء الاصطناعي: فرصة شراء / تجميع مناسبة"
        box_class = "ai-box-buy"
    elif score <= -2:
        decision = "SELL"
        title = "🔴 قرار الذكاء الاصطناعي: حذر من البيع / مخاطرة مرتفعة"
        box_class = "ai-box-sell"
    else:
        decision = "HOLD"
        title = "🟡 قرار الذكاء الاصطناعي: انتظار ومراقبة (حركة محايدة)"
        box_class = "ai-box-hold"

    support = df['low'].tail(20).min()
    resistance = df['high'].tail(20).max()
    
    return decision, title, reasons, box_class, support, resistance

# -----------------------------------------------------------------------------
# 6. التنفيذ وتوليد الواجهة
# -----------------------------------------------------------------------------
with st.spinner(f"جاري تحليل حركة سوق {ticker_symbol} بواسطة الذكاء الاصطناعي..."):
    df, error = fetch_market_data(ticker_symbol, period, interval)

if error or df is None:
    st.error(f"⚠️ خطأ: {error}")
else:
    df = calculate_indicators(df)
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    price_change = ((latest['close'] - prev['close']) / prev['close']) * 100 if prev['close'] != 0 else 0
    change_color = "#10b981" if price_change >= 0 else "#ef4444"
    change_icon = "▲" if price_change >= 0 else "▼"
    
    # -------------------------------------------------------------------------
    # قسم بطاقات المعلومات الرئيسية
    # -------------------------------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    fmt_price = f"${latest['close']:,.5f}" if latest['close'] < 1 else f"${latest['close']:,.2f}"
    
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">💰 السعر الحالي</div><div class="metric-value">{fmt_price}</div><div class="metric-sub" style="color: {change_color};">{change_icon} {price_change:+.2f}%</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">📊 التداول (Volume)</div><div class="metric-value">{latest["volume"]:,.0f}</div><div class="metric-sub" style="color: #6b7280;">حجم الشمعة الحالية</div></div>', unsafe_allow_html=True)
    with c3:
        rsi_str = f"{latest['RSI']:.1f}" if not np.isnan(latest['RSI']) else "N/A"
        st.markdown(f'<div class="metric-card"><div class="metric-title">📈 RSI (14)</div><div class="metric-value">{rsi_str}</div><div class="metric-sub" style="color: #6b7280;">مقياس الزخم</div></div>', unsafe_allow_html=True)
    with c4:
        whale_status = "🚨 دخول سيولة" if latest['Whale_Activity'] else "🟢 طبيعي"
        st.markdown(f'<div class="metric-card"><div class="metric-title">🐋 نشاط الهوامير</div><div class="metric-value" style="font-size: 18px;">{whale_status}</div><div class="metric-sub" style="color: #6b7280;">حالة التداول الضخم</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # قسم التنبيهات الفورية (Smart Live Alerts Bar)
    # -------------------------------------------------------------------------
    if alert_whale and latest['Whale_Activity']:
        st.error("🚨 **تنبيه سيولة عاجل!** تم رصد قفزة استثنائية في حجم التداول (دخول صانع سوق/هامور).")
    
    if alert_rsi:
        if latest['RSI'] > 70:
            st.warning("⚠️ **تنبيه RSI:** السعر يتداول في منطقة تشبع شرائي زائد (Overbought).")
        elif latest['RSI'] < 30:
            st.success("🟢 **تنبيه RSI:** السعر يتداول في منطقة تشبع بيعي شديد (Oversold - منطقة تجميع).")

    if alert_ma:
        if latest['close'] > latest['SMA_20'] and prev['close'] <= prev['SMA_20']:
            st.info("🔄 **تنبيه تقاطع:** السعر اخترق المتوسط المتحرك 20 لأعلى.")

    # -------------------------------------------------------------------------
    # قسم تحليل الذكاء الاصطناعي (AI Analysis Card)
    # -------------------------------------------------------------------------
    decision, ai_title, reasons, box_class, support, resistance = run_ai_analysis(df)
    
    fmt_sup = f"${support:,.5f}" if support < 1 else f"${support:,.2f}"
    fmt_res = f"${resistance:,.5f}" if resistance < 1 else f"${resistance:,.2f}"

    st.markdown(f"""
    <div class="{box_class}">
        <h3 style="margin-top:0; color:#ffffff;">{ai_title}</h3>
        <p style="font-size: 14px; color: #e5e7eb;"><b>أسباب التوصية واستنتاج الخوارزمية:</b></p>
        <ul style="color: #d1d5db; font-size: 14px;">
            {''.join([f'<li>{r}</li>' for r in reasons])}
        </ul>
        <hr style="border-color: rgba(255,255,255,0.1);">
        <div style="display: flex; justify-content: space-around; text-align: center; margin-top: 10px;">
            <div><b>📉 مستوى الدعم المتوقع:</b> <span style="color:#10b981;">{fmt_sup}</span></div>
            <div><b>📈 مستوى المقاومة المتوقع:</b> <span style="color:#ef4444;">{fmt_res}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # الرسم البياني التفاعلي المتوسع
    # -------------------------------------------------------------------------
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.06, 
        row_heights=[0.72, 0.28],
        subplot_titles=(f"📈 الشارت التفاعلي لـ {ticker_symbol}", "📊 أحجام التداول وتنبيهات السيولة الاستثنائية ⭐️")
    )

    fig.add_trace(go.Candlestick(
        x=df['datetime'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        name="السعر", increasing_line_color='#10b981', decreasing_line_color='#ef4444'
    ), row=1, col=1)

    fig.add_trace(go.Scatter(x=df['datetime'], y=df['SMA_20'], mode='lines', name='SMA 20', line=dict(color='#f59e0b', width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['SMA_50'], mode='lines', name='SMA 50', line=dict(color='#3b82f6', width=1.5)), row=1, col=1)

    colors = ['#ef4444' if df['open'].iloc[i] > df['close'].iloc[i] else '#10b981' for i in range(len(df))]
    fig.add_trace(go.Bar(x=df['datetime'], y=df['volume'], marker_color=colors, name="Volume", opacity=0.8), row=2, col=1)

    whales_df = df[df['Whale_Activity']]
    if not whales_df.empty:
        fig.add_trace(go.Scatter(
            x=whales_df['datetime'], y=whales_df['volume'],
            mode='markers', marker=dict(color='#fbbf24', size=14, symbol='star', line=dict(color='#ffffff', width=1)),
            name='⭐️ سيولة هوامير'
        ), row=2, col=1)

    fig.update_layout(
        height=680, autosize=True, xaxis_rangeslider_visible=False,
        template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111827',
        margin=dict(l=10, r=10, t=35, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
