import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time

# Configuration
BASE_URL = "https://fapi.binance.com"
INTERVALS = {
    "5min": "5m",
    "15min": "15m", 
    "1hour": "1h"
}
SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]

# Streamlit Setup
st.set_page_config(page_title="BTC Analysis Panel", layout="wide")
st.title("📊 Real-Time Bitcoin Technical Analysis")

def fetch_data(symbol, interval, limit=100):
    """Fetch market data from Binance API"""
    try:
        url = f"{BASE_URL}/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        df = pd.DataFrame(response.json(), columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", 
            "taker_buy_base", "taker_buy_quote", "ignore"
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        df[numeric_cols] = df[numeric_cols].astype(float)
        return df
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return pd.DataFrame()

def calculate_indicators(df):
    """Calculate technical indicators"""
    # RSI Calculation
    for period in [6, 14, 24]:
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
    
    # Moving Averages
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
    df['sma_50'] = df['close'].rolling(50).mean()
    
    return df.dropna()

def main():
    """Main application logic"""
    col1, col2 = st.columns([1, 3])
    
    with col1:
        symbol = st.selectbox("Select Symbol:", SYMBOLS)
        refresh = st.radio("Refresh Rate:", ["Manual", "Auto-Refresh (60s)"], index=1)
    
    analysis_data = {}
    
    try:
        for tf_name, tf_code in INTERVALS.items():
            raw_df = fetch_data(symbol, tf_code)
            if not raw_df.empty:
                processed_df = calculate_indicators(raw_df)
                analysis_data[tf_name] = processed_df
        
        with col2:
            st.header("Real-Time Analysis")
            
            for timeframe, data in analysis_data.items():
                with st.expander(f"{timeframe} Analysis", expanded=True):
                    st.write(f"**Last Price:** ${data['close'].iloc[-1]:,.2f}")
                    st.write(f"**RSI-14:** {data['rsi_14'].iloc[-1]:.1f}")
                    st.write(f"**EMA Cross:** {'Bullish' if data['ema_9'].iloc[-1] > data['ema_21'].iloc[-1] else 'Bearish'}")
                    st.line_chart(data[['close', 'ema_9', 'ema_21']].tail(50))
            
            st.caption(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
    
    if refresh == "Auto-Refresh (60s)":
        time.sleep(60)
        st.experimental_rerun()

if __name__ == "__main__":
    main()
