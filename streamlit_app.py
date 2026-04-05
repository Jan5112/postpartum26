import streamlit as st
import pandas as pd
import re

# --- 1. 樣式設定 (手機直覺式優化) ---
st.set_page_config(page_title="🌸 採購清單", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; }
    .main .block-container { max-width: 600px; margin: 0 auto; padding: 1rem; }
    
    /* 標題 */
    h1 { color: #D87093 !important; font-size: 1.8rem !important; text-align: center; margin-bottom: 20px; }
    .section-title { color: #D87093; font-size: 1.2rem; font-weight: bold; margin: 15px 0 10px 0; }
    
    /* 灰色字體鎖定 */
    p, span, label, .stCheckbox { color: #666666 !important; }

    /* 卡片設計 */
    .check-card {
        background-color: white; padding: 15px; border-radius: 18px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 15px;
        border: 1px solid #FFE4E1;
    }

    /* 用途標籤 (細灰色字) */
    .usage-text {
        color: #999999 !important; font-size: 0.85rem; margin-left: 32px; 
        display: block; margin-top: -8px; margin-bottom: 12px;
    }

    /* Checkbox 大細優化 */
    .stCheckbox label p { font-size: 1.1rem !important; line-height: 1.4; }
    
    /* Tab 標籤顏色 */
    .stTabs [data-baseweb="tab"] { color: #888; }
    .stTabs [aria-selected="true"] { color: #D87093 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據處理核心 (支援單日或多日) ---
def get_shopping_summary(df_range):
    sea_kws = ['鹽', '糖', '油', '醬', '醋', '粉', '汁', '露', '酒', '蜜', '精', '豉', '麻', '水']
    summary = {"食材": {}, "調味": {}}
    
    for _, row in df_range.iterrows():
        dish = row['Dish_Name']
        # 兼容各種分隔符
        items = re.split(r'[\n,，、\s]+', str(row['Ingredients']))
        
        for item in items:
            item = item.strip()
            if not item or item == 'nan': continue
            
            cat = "調味" if any(kw in item for kw in sea_kws) else "食材"
            
            if item not in summary[cat]:
                summary[cat][item] = {"count": 0, "dishes": []}
            
            summary[cat][item]["count"] += 1
            if dish not in summary[cat][item]["dishes"]:
                summary[cat][item]["dishes"].append(dish)
                
    return summary

# --- 3. 數據讀取 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZesALwN_63zG-ULARgSgu2zX44qpxYud8Y4qco_4IFI/edit?usp=sharing"
CSV_URL = SHEET_URL.split('/edit')[0] + '/export?format=csv'

@st.cache_data(ttl=5)
def load_data():
    try:
        data = pd.read_csv(CSV_URL)
        data.columns = data.columns.str.strip()
        data['Day_Int'] = pd.to_numeric(data['Day'], errors='coerce').fillna(0).astype(int)
        return data
    except: return None

df = load_data()

# --- 4. 側邊欄 ---
st.sidebar.title("🌸 選單")
mode = st.sidebar.radio("跳轉至：", ["📅 媽媽坐月餐單", "🛒 採購 Check-list", "🔍 食譜大百科"], index=1)

# --- 5. 🛒 智能採購清單 ---
if mode == "🛒 採購 Check-list":
    st.markdown("<h1>🛒 採購 Check-list</h1>", unsafe_allow_html=True)

    # 核心功能：切換「單日」或「範圍」
    tab_single, tab_range = st.tabs(["📍 指定某一日", "📅 選擇日期範圍"])

    with tab_single:
        target_day = st.number_input("你想睇邊一日？", min_value=1, max_value=30, value=1, key="single_day")
        shop_df = df[df['Day_Int'] == target_day]

    with tab_range:
        c1, c2 = st.columns(2)
        with c1: start_d = st.number_input("由第幾天", min_value=1, max_value=30, value=1, key="start_d")
        with c2: end_d = st.number_input("至第幾天", min_value=1, max_value=30, value=start_d + 2, key="end_d")
        shop_df = df[(df['Day_Int'] >= start_d) & (df['Day_Int'] <= end_d)]

    if shop_df is not None and not shop_df.empty:
        data_summary = get_shopping_summary(shop_df)
        
        # --- 🍎 主要食材區 ---
        st.markdown('<div class="section-title">🍎 主要食材 (買咗就 Tick)</div>', unsafe_allow_html=True)
        st.markdown('<div class="check-card">', unsafe_allow_html=True)
        for item, info in data_summary["食材"].items():
            # 顯示格式：食材名 (x出現次數)
            label = f"{item}" if info['count'] == 1 else f"{item} (x{info['count']})"
            st.checkbox(label, key=f"chk_{item}")
            # 下方灰色細字顯示用途
            st.markdown(f'<span class="usage-text">📍 用於：{"、".join(info["dishes"])}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # --- 🧂 調味料區 ---
        st.markdown('<div class="section-title">🧂 檢查調味料</div>', unsafe_allow_html=True)
        st.markdown('<div class="check-card">', unsafe_allow_html=True)
        for item, info in data_summary["調味"].items():
            st.checkbox(item, key=f"sea_{item}")
            st.markdown(f'<span class="usage-text">📍 用於：{"、".join(info["dishes"])}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.info("💡 提示：打咗剔嘅項目會一直保持，直到你刷新網頁。")
    else:
        st.warning("暫時未有呢幾日嘅餐單資料，快啲去 Google Sheet 填返啦！")

# --- 6. 其他模組 (維持原本功能) ---
elif mode == "📅 媽媽坐月餐單":
    # 這裡放你原本的餐單代碼...
    st.info("請返回側邊欄切換至「採購清單」體驗新功能")
