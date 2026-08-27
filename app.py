import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf

# -----------------------------------------------------------------------------
# 1. إعدادات الصفحة والأسلوب البصري (CSS Custom Styling)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="منصة التحليل المالي وتتبع الهوامير",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# إضافة تنسيقات CSS مخصصة لتحسين شكل المكونات
st.markdown("""
<style>
    /* تنسيق الخلية الرئيسية والبطاقات */
    .stApp {
        background-color: #0e1117;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e2638 0%, #111827 100%);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    .metric-title {
        color: #9ca3af;
        font-size: 14px;
        margin-bottom: 6px;
    }
    .metric-value {
        color: #ffffff;
        font-size: 24px;
        font-weight: bold;
    }
    .metric-sub {
        font-size: 13px;
        margin-top: 4px;
    }
    .status-badge-green {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10b981;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
    }
    .status-badge-red {
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. الهيدر الرئيسي للموقع
# -----------------------------------------------------------------------------
st.markdown("<h1 style='text-align: right; color: #f3f4f6;'>🦅 منصة التحليل المالي وتتبع حركة الهوامير الذكية</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: right; color: #9ca3af; font-size: 15px;'>نظام تحليلي متكامل يجمع بين التحليل الفني، رصد السيولة الكبيرة، ومؤشرات التداول الذكية.</p>", unsafe_allow_html=True)
st.markdown("---")

# -----------------------------------------------------------------------------
# 3. إعدادات شريط الأدوات الجانبي (Sidebar)
# -----------------------------------------------------------------------------
st.sidebar.markdown("<h2 style='text-align: right;'>⚙️ لوحة التحكم</h2>", unsafe_allow_html=True)

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
    symbol_input = st.sidebar.text_input("ادخل رمز العملة (مثال: ADA, NEAR)", value="DOGE").upper().strip()
else:
    symbol_input = preset_coins[selected_option]

ticker_symbol = f"{symbol_input}-USD"

interval = st.sidebar.selectbox("الإطار الزمني (Timeframe)", ["1m", "5m", "15m", "1h", "1d"], index=3)
period = st.sidebar.selectbox("النطاق الزمني التاريخي", ["1d", "5d", "1mo", "3mo", "1y"], index=2)

st.sidebar.markdown("---")
st.sidebar.info("💡 **نصيحة:** استخدم الإطار الزمني `1h` أو `1d` للحصول على أدق إشارات للسيولة والهوامير.")

# -----------------------------------------------------------------------------
# 4. دالة جلب البيانات عبر Yahoo Finance
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

# -----------------------------------------------------------------------------
# 5. دالة حساب المؤشرات الفنية ورصد السيولة
# -----------------------------------------------------------------------------
def calculate_indicators(df):
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Whale Detection (Spike)
    mean_volume = df['volume'].rolling(window=20).mean()
    std_volume = df['volume'].rolling(window=20).std()
    df['Whale_Activity'] = df['volume'] > (mean_volume + 2.2 * std_volume)
    
    return df

# -----------------------------------------------------------------------------
# 6. جلب البيانات والتنفيذ
# -----------------------------------------------------------------------------
with st.spinner(f"جاري جلب البيانات وتحليل {ticker_symbol}..."):
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
    
    # عرض المؤشرات في كروت مُنسقة
    c1, c2, c3, c4 = st.columns(4)
    
    fmt_price = f"${latest['close']:,.5f}" if latest['close'] < 1 else f"${latest['close']:,.2f}"
    
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">💰 السعر الحالي</div>
            <div class="metric-value">{fmt_price}</div>
            <div class="metric-sub" style="color: {change_color};">{change_icon} {price_change:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📊 حجم التداول (Volume)</div>
            <div class="metric-value">{latest['volume']:,.0f}</div>
            <div class="metric-sub" style="color: #6b7280;">نشاط تداول الشمعة</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        rsi_val = latest['RSI']
        rsi_str = f"{rsi_val:.1f}" if not np.isnan(rsi_val) else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📈 مؤشر القوة النسبية RSI</div>
            <div class="metric-value">{rsi_str}</div>
            <div class="metric-sub" style="color: #6b7280;">مقياس تشبع السوق</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c4:
        whale_text = "🚨 ضخ سيولة ضخم" if latest['Whale_Activity'] else "🟢 طبيعي"
        badge_style = "status-badge-red" if latest['Whale_Activity'] else "status-badge-green"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🐋 حركة الهوامير (Whales)</div>
            <div style="margin-top: 10px;"><span class="{badge_style}">{whale_text}</span></div>
            <div class="metric-sub" style="color: #6b7280; margin-top: 12px;">حالة السيولة الكبيرة</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 7. الرسم البياني التفاعلي التوسع والمحسّن (Plotly)
    # -------------------------------------------------------------------------
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.06, 
        row_heights=[0.72, 0.28],
        subplot_titles=(f"📈 حركة الأسعار والمعدلات المتحركة ({ticker_symbol})", "📊 أحجام التداول وتنبيهات السيولة الاستثنائية ⭐️")
    )

    # الشموع اليابانية
    fig.add_trace(go.Candlestick(
        x=df['datetime'],
        open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        name="السعر",
        increasing_line_color='#10b981', 
        decreasing_line_color='#ef4444'
    ), row=1, col=1)

    # المتوسطات المتحركة
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['SMA_20'], mode='lines', name='متوسط 20 (SMA)', line=dict(color='#f59e0b', width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['SMA_50'], mode='lines', name='متوسط 50 (SMA)', line=dict(color='#3b82f6', width=1.5)), row=1, col=1)

    # الفوليوم
    colors = ['#ef4444' if df['open'].iloc[i] > df['close'].iloc[i] else '#10b981' for i in range(len(df))]
    fig.add_trace(go.Bar(x=df['datetime'], y=df['volume'], marker_color=colors, name="Volume", opacity=0.8), row=2, col=1)

    # إضافة نجوم تتبع الهوامير
    whales_df = df[df['Whale_Activity']]
    if not whales_df.empty:
        fig.add_trace(go.Scatter(
            x=whales_df['datetime'], 
            y=whales_df['volume'],
            mode='markers',
            marker=dict(color='#fbbf24', size=14, symbol='star', line=dict(color='#ffffff', width=1)),
            name='⭐️ تنبيه سيولة ضخمة'
        ), row=2, col=1)

    fig.update_layout(
        height=680,
        autosize=True,
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        paper_bgcolor='#0e1117',
        plot_bgcolor='#111827',
        margin=dict(l=15, r=15, t=40, b=15),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_xaxes(gridcolor='#1f2937', showgrid=True)
    fig.update_yaxes(gridcolor='#1f2937', showgrid=True)

    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

    # -------------------------------------------------------------------------
    # 8. قسم التوصية الذكية والقرار
    # -------------------------------------------------------------------------
    st.markdown("<h3 style='text-align: right;'>💡 التوصية والتحليل الفني الذكي</h3>", unsafe_allow_html=True)
    
    col_rec1, col_rec2 = st.columns(2)
    
    with col_rec1:
        st.markdown("##### 📌 وضع المؤشرات الفنية (RSI):")
        if not np.isnan(rsi_val):
            if rsi_val > 70:
                st.warning("⚠️ **تشبع شرائي (Overbought):** السعر متضخم حالياً. ينصح بانتظار تصحيح ولا ينصح بالدخول شرائياً الآن.")
            elif rsi_val < 30:
                st.success("🟢 **تشبع بيعي (Oversold):** السعر في مناطق ارتداد صعودية ممتازة. فرصة مناسبة لمراقبة الشراء.")
            else:
                st.info("⚖️ **منطقة محايدة:** حركة السعر متوازنة حالياً. يفضل متابعة كسر المقاومات أو اختراق الدعم.")
        else:
            st.write("جاري تحميل بيانات المؤشر...")

    with col_rec2:
        st.markdown("##### 🐋 نشاط السيولة والهوامير:")
        if latest['Whale_Activity']:
            st.error("🚨 **تنبيه هامور!** تم رصد ضخ سيولة استثنائية في هذه الشمعة. يرجى توخي الحذر من تقلبات حادة سريعة.")
        else:
            st.write("🟢 **استقرار:** السيولة الحالية ضمن معدلاتها الطبيعية ولا يوجد اندفاع مفاجئ لصانع السوق.")
