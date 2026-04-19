import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 網頁基本設定
st.set_page_config(page_title="總經與半導體儀表板", layout="wide")
st.title("📈 台股半導體 vs 美國總經連動看板")
st.markdown("這是一個自動追蹤台積電股價與美國 10 年期公債殖利率的互動式儀表板。")

# 2. 讀取我們剛剛清洗好的資料
# 使用 @st.cache_data 讓網頁記住資料，不用每次重整都重讀一次 CSV
@st.cache_data
def load_data():
    df = pd.read_csv("dashboard_data.csv", index_col=0)
    df.index = pd.to_datetime(df.index)
    return df

df = load_data()

# 3. 側邊欄：讓教授可以自己調整時間區間 (互動性加分)
st.sidebar.header("📊 參數設定")
start_date = st.sidebar.date_input("開始日期", df.index.min())
end_date = st.sidebar.date_input("結束日期", df.index.max())

# 根據側邊欄的日期過濾資料
mask = (df.index >= pd.to_datetime(start_date)) & (df.index <= pd.to_datetime(end_date))
filtered_df = df.loc[mask]

# 4. 繪製雙 Y 軸互動圖表
fig = go.Figure()

# 左 Y 軸：台積電股價
fig.add_trace(go.Scatter(
    x=filtered_df.index, y=filtered_df['TSMC_Close'],
    name='台積電收盤價', line=dict(color='#1f77b4', width=2)
))

# 右 Y 軸：美國 10 年期公債殖利率
fig.add_trace(go.Scatter(
    x=filtered_df.index, y=filtered_df['US_10Y_Yield'],
    name='美債10年期殖利率 (%)', line=dict(color='#d62728', width=2), yaxis='y2'
))

# 排版與雙軸設定
fig.update_layout(
    height=500,
    hovermode='x unified', # 滑鼠移過去會同時顯示兩邊的數值
    yaxis=dict(
        title=dict(text='台積電股價 (TWD)', font=dict(color='#1f77b4')), 
        tickfont=dict(color='#1f77b4')
    ),
    yaxis2=dict(
        title=dict(text='殖利率 (%)', font=dict(color='#d62728')), 
        tickfont=dict(color='#d62728'),
        anchor='x', overlaying='y', side='right'
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

# 5. 顯示圖表
st.plotly_chart(fig, use_container_width=True)

# 6. 隱藏式資料表 (讓教授可以看到 ETL 的成果)
with st.expander("🔍 查看原始清洗資料 (ETL Result)"):
    st.dataframe(filtered_df)