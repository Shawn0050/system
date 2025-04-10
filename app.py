import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# from fredapi import Fred

# === 頁面設定 ===
st.set_page_config(page_title="Stock Dashboard App", layout="wide")
st_autorefresh(interval=10000, key="auto_refresh")  # 每 10 秒自動刷新
st.title("📊 Stock Dashboard")

# === Sidebar：資料參數選擇 ===
st.sidebar.header("🔧 資料設定")
period = st.sidebar.selectbox("選擇時間範圍 (period)", [
    "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
], index=0)

interval = st.sidebar.selectbox("選擇資料頻率 (interval)", [
    "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"
], index=3)

if interval in ['1m', '2m'] and period not in ['1d', '5d', '7d']:
    st.warning("⚠️ 選擇的頻率僅支援近幾日資料，請搭配 1d/5d/7d 等短期時間範圍使用。")
    st.stop()

st.sidebar.markdown(f"📅 目前設定：`period={period}`，`interval={interval}`")

# === 技術指標計算器 ===
class IndicatorCalculator:
    def __init__(self, df):
        self.df = df

    def add_ma(self, period):
        self.df[f"MA{period}"] = self.df['Close'].rolling(window=period).mean()

    def add_ema(self, period):
        self.df[f"EMA{period}"] = self.df['Close'].ewm(span=period, adjust=False).mean()

    def add_rsi(self, period=14):
        delta = self.df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        self.df['RSI'] = 100 - (100 / (1 + rs))

# === 技術指標選擇 ===
st.sidebar.header("📈 技術指標選擇")
selected_indicators = st.sidebar.multiselect(
    "請選擇要顯示的技術指標",
    ["MA1","MA5", "MA20", "MA60", "MA200", "EMA10", "EMA30", "RSI"],
    default=["MA1"]
)

# === 每行顯示幾個標的 ===
col_num = st.sidebar.slider("每一列顯示幾個標的？", min_value=1, max_value=4, value=2)

# === 自選報價清單 ===
tw_dict = {
    "台積電 (2330.TW)": "2330.TW",
    "聯發科 (2454.TW)": "2454.TW",
    "鴻海 (2317.TW)": "2317.TW",
    "台達電 (2308.TW)": "2308.TW",
    "富邦金 (2881.TW)": "2881.TW",
    "中信金 (2891.TW)": "2891.TW",
    "國泰金 (2882.TW)": "2882.TW",
    "0050 (0050.TW)": "0050.TW",
    "006208 (006208.TW)": "006208.TW"
}

us_dict = {
    "Apple (AAPL)": "AAPL",
    "Tesla (TSLA)": "TSLA",
    "Microsoft (MSFT)": "MSFT",
    "Amazon (AMZN)": "AMZN",
    "NVIDIA (NVDA)": "NVDA",
    "SPDR彭博1-3月美國國庫券ETF (BIL)": "BIL",
    "Vanguard總體債券市場ETF (BND)": "BND",
    "Vanguard全世界債券ETF (BNDW)": "BNDW",
    "SPDR道瓊工業平均指數ETF (DIA)": "DIA",
    "iShares 7-10年期美國公債ETF (IEF)": "IEF",
    "Invesco納斯達克100指數ETF (QQQ)": "QQQ",
    "iShares半導體ETF (SOXX)": "SOXX",
    "SPDR標普500指數ETF (SPY)": "SPY",
    "iShares抗通膨債券ETF (TIP)": "TIP",
    "iShares 20年期以上美國公債ETF (TLT)": "TLT",
    "Vanguard標普600小型價值股ETF (VIOV)": "VIOV",
    "Vanguard房地產ETF (VNQ)": "VNQ",
    "Vanguard標普500指數ETF (VOO)": "VOO",
    "Vanguard通訊服務ETF (VOX)": "VOX",
    "Vanguard全世界股票ETF (VT)": "VT",
    "SPDR原物料類股ETF (XLB)": "XLB",
    "SPDR能源類股ETF (XLE)": "XLE",
    "SPDR必需性消費類股ETF (XLP)": "XLP",
    "SPDR健康照護類股ETF (XLV)": "XLV",
    "SPDR非必需消費類股ETF (XLY)": "XLY"
}

bond_dict = {
    "美國-2年期公債殖利率": "^IRX",   # 其實是 13-week T-Bill（最接近短債）
    "美國-10年期公債殖利率": "^TNX",  # 10Y CBOE 債券殖利率（×10）
    "美國-30年期公債殖利率": "^TYX",  # 30Y CBOE 債券殖利率（×10）
    "10Y2Y美國公債殖利率差": "^TNX-^IRX",
    "30Y10Y美國公債殖利率差": "^TYX-^TNX",
}

# api_key = '17d3395bc92f36deca763d0abed77bd4'
# fred = Fred(api_key=api_key)

tw_selected = st.sidebar.multiselect("自選報價 1：台股", options=list(tw_dict.keys()))
us_selected = st.sidebar.multiselect("自選報價 2：美股", options=list(us_dict.keys()))
bond_selected = st.sidebar.multiselect("自選報價 3：債券", options=list(bond_dict.keys()))
watchlist = {
    **{k: tw_dict[k] for k in tw_selected},
    **{k: us_dict[k] for k in us_selected},
    **{k: bond_dict[k] for k in bond_selected}
}

for i, (name, code) in enumerate(watchlist.items()):
    if i % col_num == 0:
        cols = st.columns(col_num)
    with cols[i % col_num]:
        st.subheader(f"{name}（{code}）")

        try:
            if code in bond_dict.values():
                if code == "^TNX-^IRX":
                    df1 = yf.download("^TNX", period=period, interval="1h")
                    df1.columns = df1.columns.droplevel(1)
                    df2 = yf.download("^IRX", period=period, interval="1h")
                    df2.columns = df2.columns.droplevel(1)
                    df = df1 - df2
                elif code == "^TYX-^TNX":
                    df1 = yf.download("^TYX", period=period, interval="1h")
                    df1.columns = df1.columns.droplevel(1)
                    df2 = yf.download("^TNX", period=period, interval="1h")
                    df2.columns = df2.columns.droplevel(1)
                    df = df1 - df2
                else:
                    df = yf.download(code, period=period, interval="1h")
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.droplevel(1)
            else:
                df = yf.download(code, period=period, interval=interval, group_by="ticker", threads=False)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.droplevel(0)

            if not df.empty:
                df.dropna(inplace=True)
                last_price = df['Close'].iloc[-1]
                st.metric(label="最新價格", value=f"{last_price:.2f}")

                calc = IndicatorCalculator(df)
                for indicator in selected_indicators:
                    if indicator.startswith("MA"):
                        calc.add_ma(int(indicator.replace("MA", "")))
                    elif indicator.startswith("EMA"):
                        calc.add_ema(int(indicator.replace("EMA", "")))
                    elif indicator == "RSI":
                        calc.add_rsi()

                volume_scaled = df['Volume'] / df['Volume'].max() * df['Close'].max() * 0.3
                volume_axis_upper = volume_scaled.max() * 5

                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'
                ))

                for indicator in selected_indicators:
                    if indicator in df.columns:
                        fig.add_trace(go.Scatter(x=df.index, y=df[indicator], mode='lines', name=indicator))

                fig.add_trace(go.Bar(
                    x=df.index, y=volume_scaled, name='成交量 (縮放)', yaxis='y2',
                    marker=dict(color='rgba(100, 100, 100, 0.3)')
                ))

                fig.update_layout(
                    xaxis=dict(domain=[0, 1]),
                    yaxis=dict(title="價格"),
                    yaxis2=dict(title="縮放成交量", overlaying='y', side='right', showgrid=False, range=[0, volume_axis_upper]),
                    margin=dict(l=0, r=0, t=30, b=0), height=500,
                    xaxis_rangeslider_visible=False
                )

                st.plotly_chart(fig, use_container_width=True)

            else:
                st.warning("⚠️ 無法取得資料（可能非盤中或資料源限制）")
        except Exception as e:
            st.warning(f"⚠️ 資料處理錯誤：{e}")

# streamlit run /home/shawn/side_pj/system/main.py