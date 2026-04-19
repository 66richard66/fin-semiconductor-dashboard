import yfinance as yf
import pandas as pd
import requests
import os
from sqlalchemy import create_engine

# 1. 從環境變數讀取機密資訊 (這是為了安全，不把密碼寫在程式碼裡)
# 我們等一下會在 GitHub 設定這兩個變數
FRED_API_KEY = os.getenv("FRED_API_KEY")
DB_URL = os.getenv("DB_URL")

def run_pipeline():
    print("🚀 啟動自動更新管線...")
    
    # --- Extract & Transform (跟之前一樣) ---
    print("正在抓取最新數據...")
    tsmc = yf.Ticker("2330.TW")
    tsmc_df = tsmc.history(period="6mo")
    tsmc_close = tsmc_df[['Close']].rename(columns={'Close': 'TSMC_Close'})
    tsmc_close.index = tsmc_close.index.tz_localize(None).normalize()

    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key={FRED_API_KEY}&file_type=json"
    fred_data = requests.get(url).json()
    fred_df = pd.DataFrame(fred_data['observations'])[['date', 'value']]
    fred_df['date'] = pd.to_datetime(fred_df['date']).dt.normalize()
    fred_df = fred_df[fred_df['value'] != '.'].set_index('date')
    fred_df['value'] = fred_df['value'].astype(float)
    fred_df = fred_df.rename(columns={'value': 'US_10Y_Yield'})

    # 合併與清洗
    merged_df = tsmc_close.join(fred_df, how='left').ffill().dropna()

    # --- Load ---
    print("正在寫入雲端資料庫...")
    engine = create_engine(DB_URL)
    merged_df.to_sql("macro_stock_data", engine, if_exists="replace", index=True)
    print("✅ 自動更新完成！")

if __name__ == "__main__":
    run_pipeline()