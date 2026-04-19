import yfinance as yf
import pandas as pd
import requests

# ---------------------------------------------------------
# 1. 抓取台股半導體數據 (以台積電 2330.TW 為例)
# ---------------------------------------------------------
print("正在抓取台積電 (2330.TW) 股價資料...")
# 設定抓取近 6 個月的資料
tsmc = yf.Ticker("2330.TW")
tsmc_df = tsmc.history(period="6mo")

# 我們只需要「收盤價 (Close)」
tsmc_close = tsmc_df[['Close']].rename(columns={'Close': 'TSMC_Close'})
# 把時區資訊去掉，方便後續對齊日期
tsmc_close.index = tsmc_close.index.tz_localize(None) 
print("✅ 台積電資料抓取成功！前五筆資料：")
print(tsmc_close.head(), "\n")

# ---------------------------------------------------------
# 2. 抓取美國總經數據 (美國 10 年期公債殖利率, 代號: DGS10)
# ---------------------------------------------------------
print("正在抓取美國 10 年期公債殖利率資料...")
FRED_API_KEY = "d1ac722dacb2e76c74968b01083ddec3"
SERIES_ID = "DGS10" # 10-Year Treasury Constant Maturity Rate

# 呼叫 FRED API
url = f"https://api.stlouisfed.org/fred/series/observations?series_id={SERIES_ID}&api_key={FRED_API_KEY}&file_type=json"
response = requests.get(url)
data = response.json()

# 將 JSON 轉為 Pandas DataFrame
fred_df = pd.DataFrame(data['observations'])
fred_df = fred_df[['date', 'value']] # 只取日期和數值
fred_df['date'] = pd.to_datetime(fred_df['date']) # 轉換為日期格式
fred_df.set_index('date', inplace=True)

# 清理無效的數值 (FRED 有時會用 '.' 代表假日無交易)
fred_df = fred_df[fred_df['value'] != '.']
fred_df['value'] = fred_df['value'].astype(float)
fred_df = fred_df.rename(columns={'value': 'US_10Y_Yield'})

print("✅ FRED 資料抓取成功！最近五筆資料：")
print(fred_df.tail())

# ---------------------------------------------------------
# 3. 資料轉換與合併 (Transform)
# ---------------------------------------------------------
print("\n正在進行時間軸對齊與資料清洗...")

# 確保兩邊的 Index 都是標準的 Datetime 格式
tsmc_close.index = pd.to_datetime(tsmc_close.index).normalize()
fred_df.index = pd.to_datetime(fred_df.index).normalize()

# 將兩張表合併 (以台股交易日為主，使用 left join)
merged_df = tsmc_close.join(fred_df, how='left')

# 處理空值：如果遇到美國放假但台灣有開盤，我們直接沿用前一個交易日的殖利率 (Forward Fill)
merged_df['US_10Y_Yield'] = merged_df['US_10Y_Yield'].ffill()

# 刪除最前面可能無法對應填補的極少數空值列
merged_df = merged_df.dropna()

print("✅ 資料清洗與合併成功！這就是我們儀表板要用的最終資料集 (最後五筆)：")
print(merged_df.tail())

# 先在本地端存成 CSV 檔，方便我們等一下直接做前端測試
merged_df.to_csv("dashboard_data.csv")
print("📁 完美！乾淨的資料已儲存為 dashboard_data.csv")