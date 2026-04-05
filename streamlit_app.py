import streamlit as st
import pandas as pd
import re

# --- 1. 樣式設定 (手機灰色優化版) ---
st.set_page_config(page_title="🌸 採購 Check-list", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; }
    .main .block-container { max-width: 600px; margin: 0 auto; padding: 1.2rem; }
    
    h1 { color: #D87093 !important; font-size: 1.8rem !important; text-align: center; margin-bottom: 20px; }
    .section-title { color: #D87093; font-size: 1.2rem; font-weight: bold; margin: 15px 0 10px 0; }
    
    /* 灰色字體鎖定 */
    p, span, label, .stCheckbox { color: #666666 !important; }

    /* 卡片設計 */
    .check-card {
        background-color: white; padding: 15px; border-radius: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04); margin-bottom: 15px;
        border: 1.5px solid #FFE4E1;
    }

    /* 用途與份量標籤 (深灰色細字) */
    .usage-text {
        color: #888888 !important; font-size: 0.9rem; margin-left: 32px; 
        display: block; margin-top: -8px; margin-bottom: 12px;
        line-height: 1.4;
    }

    /* Checkbox 大細優化 */
    .stCheckbox label p { font-size: 1.15rem !important; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心邏輯：嚴格日期鎖定 + 合併 ---
def get_shopping_summary(df_filtered):
    # 如果過濾後冇數據，直接返去
    if df_filtered.empty:
        return {"食材": {}, "調味": {}}

    sea_kws = ['鹽', '糖', '油', '醬', '醋', '粉', '汁', '露', '酒', '蜜', '精', '豉', '麻', '水']
    summary = {"食材": {}, "調味": {}}
    
    for _, row in df_filtered.iterrows():
        dish = row['Dish_Name']
        day_label = f"Day {int(row['Day_Int'])}"
        
        # 拆分食材字串
        items = re.split(r'[\n,，、\s]+', str(row['Ingredients']))
        
        for raw_item in items:
            raw_item = raw_item.strip()
            if not raw_item or raw_item == 'nan': continue
            
            # 分離名稱同份量 (例如: "糙米 1份" -> "糙米" & "1份")
            parts = re.split(r'(\d+|半|少許|適量|份|g|克|兩|斤|包)', raw_item, maxsplit=1)
            base_name = parts[0].strip()
            amount = raw_item.replace(base_name, "").strip()
            
            cat = "調味" if any(kw in base_name for kw in sea_kws) else "食材"
            
            if base_name not in summary[cat]:
                summary[cat][base_name] = {"total_count": 0, "details": []}
            
            summary[cat][base_name]["total_count"] += 1
            # 依家會包含埋日子，方便多日採購時辨識
            summary[cat][base_name]["details"].append(f"{day_label} {dish} ({amount if amount else '適量'})")
                
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

# --- 5. 🛒 智能採購清單頁面 ---
if mode == "🛒 採購 Check-list":
    st.markdown("<h1>🛒 採購 Check-list</h1>", unsafe_allow_html=True)

    tab_single, tab_range = st.tabs(["📍 睇今日買乜", "📅 一次過買幾日"])

    with tab_single:
        target_day = st.number_input("選擇第幾天？", min_value=1, max_value=30, value=1)
        # 嚴格過濾：只攞呢一日嘅數據
        filtered_df = df[df['Day_Int'] == target_day].copy()

    with tab_range:
        c1, c2 = st.columns(2)
        with c1: start_d = st.number_input("由 Day", min_value=1, max_value=30, value=1)
        with c2: end_d = st.number_input("至 Day", min_value=1, max_value=30, value=start_d + 2)
        # 嚴格過濾：只攞呢個區間嘅數據
        filtered_df = df[(df['Day_Int'] >= start_d) & (df['Day_Int'] <= end_d)].copy()

    if df is not None and not filtered_df.empty:
        data_summary = get_shopping_summary(filtered_df)
        
        # --- 🍎 主要食材 ---
        if data_summary["食材"]:
            st.markdown('<div class="section-title">🍎 主要食材 (買咗就 Tick)</div>', unsafe_allow_html=True)
            st.markdown('<div class="check-card">', unsafe_allow_html=True)
            for name, info in data_summary["食材"].items():
                label = f"{name}" if info['total_count'] == 1 else f"{name} (x{info['total_count']})"
                st.checkbox(label, key=f"ing_{name}_{info['total_count']}")
                st.markdown(f'<span class="usage-text">📍 {"、".join(info["details"])}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # --- 🧂 調味料 ---
        if data_summary["調味"]:
            st.markdown('<div class="section-title">🧂 檢查調味料</div>', unsafe_allow_html=True)
            st.markdown('<div class="check-card">', unsafe_allow_html=True)
            for name, info in data_summary["調味"].items():
                st.checkbox(name, key=f"sea_{name}")
                st.markdown(f'<span class="usage-text">📍 {"、".join(info["details"])}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.success("買齊晒就可以返屋企大展身手喇！🍜")
    else:
        st.warning("揀選嘅日子暫時冇餐單，請檢查 Google Sheet。")
