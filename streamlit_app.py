import streamlit as st
import pandas as pd
import re

# --- 1. 樣式設定 (保持灰色字體與手機優化) ---
st.set_page_config(page_title="🌸 智能採購助手", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; }
    .main .block-container { max-width: 600px; margin: 0 auto; padding: 1rem; }
    
    h1 { color: #D87093 !important; font-size: 1.8rem !important; text-align: center; }
    .section-title { color: #D87093; font-size: 1.2rem; font-weight: bold; margin: 15px 0 10px 0; }
    
    /* 灰色字體鎖定 */
    p, span, label, .stCheckbox { color: #666666 !important; }

    /* 卡片設計 */
    .check-card {
        background-color: white; padding: 15px; border-radius: 18px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 15px;
        border: 1px solid #FFE4E1;
    }

    /* 用途與份量標籤 */
    .usage-text {
        color: #999999 !important; font-size: 0.85rem; margin-left: 32px; 
        display: block; margin-top: -8px; margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心邏輯：聰明合併同類食材 ---
def get_shopping_summary(df_range):
    sea_kws = ['鹽', '糖', '油', '醬', '醋', '粉', '汁', '露', '酒', '蜜', '精', '豉', '麻', '水']
    summary = {"食材": {}, "調味": {}}
    
    for _, row in df_range.iterrows():
        dish = row['Dish_Name']
        # 拆分食材字串
        items = re.split(r'[\n,，、\s]+', str(row['Ingredients']))
        
        for raw_item in items:
            raw_item = raw_item.strip()
            if not raw_item or raw_item == 'nan': continue
            
            # 【關鍵優化】分離「名稱」同「份量」
            # 假設格式係「糙米 1份」或「豬肉 200g」，我哋攞第一個詞做 Key
            parts = re.split(r'(\d+|半|少許|適量|份|g|克|兩|斤)', raw_item, maxsplit=1)
            base_name = parts[0].strip() # 攞到「糙米」
            amount = raw_item.replace(base_name, "").strip() # 攞到「1份」
            
            cat = "調味" if any(kw in base_name for kw in sea_kws) else "食材"
            
            if base_name not in summary[cat]:
                summary[cat][base_name] = {"total_count": 0, "details": []}
            
            summary[cat][base_name]["total_count"] += 1
            # 紀錄呢餐用幾多，同埋係邊個菜式
            summary[cat][base_name]["details"].append(f"{dish} ({amount if amount else '適量'})")
                
    return summary

# --- 3. 數據讀取 (與之前相同) ---
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

# --- 5. 🛒 智能採購清單頁面 ---
if mode == "🛒 採購 Check-list":
    st.markdown("<h1>🛒 採購 Check-list</h1>", unsafe_allow_html=True)

    tab_single, tab_range = st.tabs(["📍 指定某一日", "📅 選擇日期範圍"])

    with tab_single:
        target_day = st.number_input("你想睇邊一日？", min_value=1, max_value=30, value=1)
        shop_df = df[df['Day_Int'] == target_day]

    with tab_range:
        c1, c2 = st.columns(2)
        with c1: start_d = st.number_input("由第幾天", min_value=1, max_value=30, value=1)
        with c2: end_d = st.number_input("至第幾天", min_value=1, max_value=30, value=start_d + 1)
        shop_df = df[(df['Day_Int'] >= start_d) & (df['Day_Int'] <= end_d)]

    if shop_df is not None and not shop_df.empty:
        data_summary = get_shopping_summary(shop_df)
        
        # --- 🍎 主要食材顯示 ---
        st.markdown('<div class="section-title">🍎 主要食材</div>', unsafe_allow_html=True)
        st.markdown('<div class="check-card">', unsafe_allow_html=True)
        for base_name, info in data_summary["食材"].items():
            # Checkbox 淨係顯示食材大名同出現次數
            st.checkbox(f"{base_name} (x{info['total_count']})", key=f"chk_{base_name}")
            # 下方灰色細字：列出每一餐嘅份量同菜式名
            details_str = "、".join(info['details'])
            st.markdown(f'<span class="usage-text">📍 {details_str}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # --- 🧂 調味料顯示 ---
        st.markdown('<div class="section-title">🧂 檢查調味</div>', unsafe_allow_html=True)
        st.markdown('<div class="check-card">', unsafe_allow_html=True)
        for base_name, info in data_summary["調味"].items():
            st.checkbox(base_name, key=f"sea_{base_name}")
            details_str = "、".join(info['details'])
            st.markdown(f'<span class="usage-text">📍 {details_str}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.info("💡 買咗就 Tick 一下，買餸更輕鬆！")
    else:
        st.warning("請確保 Google Sheet 已經填好資料。")

else:
    st.info("請使用左邊選單切換頁面。")
