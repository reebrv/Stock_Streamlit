import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title="Real-Time Stock Dashboard", layout="wide")

st.title("📈 Real-Time Stock Market Dashboard")

# Sidebar inputs
st.sidebar.header("Stock Selection")
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL, TSLA, RELIANCE.NS)", "AAPL")
period = st.sidebar.selectbox("Select Period", ["1d", "5d", "1mo", "6mo", "1y", "5y", "max"], index=1)
interval = st.sidebar.selectbox("Select Interval", ["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"], index=6)

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.experimental_rerun()

# Fetch data
@st.cache_data(ttl=60)
def load_data(ticker, period, interval):
    data = yf.download(ticker, period=period, interval=interval)
    data.reset_index(inplace=True)
    return data

try:
    data = load_data(ticker, period, interval)

    if data.empty:
        st.error("No data found for the given ticker. Try another symbol.")
    else:
        # Show latest price
        st.subheader(f"Latest Data for {ticker}")
        latest_price = data["Close"].iloc[-1]
        st.metric(label=f"{ticker} Price", value=f"${latest_price:.2f}")

        # Candlestick chart
        st.subheader("Candlestick Chart with Bollinger Bands")
        data["MA20"] = data["Close"].rolling(window=20).mean()
        rolling_std = data["Close"].rolling(window=20).std()
        data["BB_up"] = data["MA20"] + (2 * rolling_std)
        data["BB_low"] = data["MA20"] - (2 * rolling_std)

        fig = go.Figure(data=[go.Candlestick(
            x=data["Date"],
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name="Candlestick"
        )])
        fig.add_trace(go.Scatter(x=data["Date"], y=data["BB_up"], name="Bollinger Upper", line=dict(color='rgba(255,0,0,0.5)')))
        fig.add_trace(go.Scatter(x=data["Date"], y=data["BB_low"], name="Bollinger Lower", line=dict(color='rgba(0,0,255,0.5)')))
        fig.update_layout(xaxis_rangeslider_visible=False, height=500)
        st.plotly_chart(fig, use_container_width=True)

        # Moving averages
        st.subheader("Moving Averages")
        data["SMA_20"] = data["Close"].rolling(window=20).mean()
        data["SMA_50"] = data["Close"].rolling(window=50).mean()

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=data["Date"], y=data["Close"], mode="lines", name="Close Price"))
        fig2.add_trace(go.Scatter(x=data["Date"], y=data["SMA_20"], mode="lines", name="SMA 20"))
        fig2.add_trace(go.Scatter(x=data["Date"], y=data["SMA_50"], mode="lines", name="SMA 50"))
        st.plotly_chart(fig2, use_container_width=True)

        # RSI
        st.subheader("RSI (Relative Strength Index)")
        delta = data['Close'].diff()
        gain = delta.mask(delta < 0, 0)
        loss = -delta.mask(delta > 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        data['RSI'] = 100 - (100 / (1 + rs))

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=data["Date"], y=data["RSI"], mode="lines", name="RSI"))
        fig3.add_hline(y=70, line_dash="dash", line_color="red")
        fig3.add_hline(y=30, line_dash="dash", line_color="green")
        st.plotly_chart(fig3, use_container_width=True)

        # MACD
        st.subheader("MACD (Moving Average Convergence Divergence)")
        ema12 = data['Close'].ewm(span=12, adjust=False).mean()
        ema26 = data['Close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = ema12 - ema26
        data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()

        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=data["Date"], y=data["MACD"], mode="lines", name="MACD"))
        fig4.add_trace(go.Scatter(x=data["Date"], y=data["Signal"], mode="lines", name="Signal"))
        st.plotly_chart(fig4, use_container_width=True)

        # Raw data
        st.subheader("Recent Data")
        st.dataframe(data.tail(20))

except Exception as e:
    st.error(f"Error fetching data: {e}")
