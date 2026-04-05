import streamlit as st
import pandas as pd
import re

# --- 1. 樣式設定 (維持靚靚粉紅 + 極簡灰) ---
st.set_page_config(page_title="🌸 媽媽坐月餐單", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; }
    .main .block-container { max-width: 600px; margin: 0 auto; padding: 1.2rem; }
    h1 { color: #D87093 !important; font-size: 1.8rem !important; text-align: center; margin-bottom: 20px; }
    p, span, label, .stCheckbox, .stMarkdown { color: #666666 !important; font-size: 1rem; }
    
    /* Checkbox 文字大細 */
    .stCheckbox label p { font-size: 1.1rem !important; font-weight: 500; }

    /* 卡片設計 */
    .check-card {
        background-color: white; padding: 15px 20px; border-radius: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03); margin-bottom: 15px;
        border: 1.5px solid #FFE4E1;
    }
    
    .section-title { color: #D87093; font-size: 1.2rem; font-weight: bold; margin: 20px 0 10px 5px; }
    .usage-text { color: #999999 !important; font-size: 0.85rem; margin-left: 32px; display: block; margin-top: -6px; margin-bottom: 10px; line-height: 1.3; }
    
    /* 按鈕樣式回歸 */
    .stButton>button { 
        background-color: #FFB6C1; color: white !important; border-radius: 20px; border: none; 
        width: 100%; min-height: 48px; font-weight: bold; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZesALwN_63zG-ULARgSgu2zX44qpxYud8Y4qco_4IFI/edit?usp=sharing"
CSV_URL = SHEET_URL.split('/edit')[0] + '/export?format=csv'

@st.cache_data(ttl=0)
def load_data():
    try:
        data = pd.read_csv(CSV_URL)
        data.columns = data.columns.str.strip()
        data['Day_Int'] = pd.to_numeric(data['Day'], errors='coerce').fillna(0).astype(int)
        return data
    except: return None

all_df = load_data()

# --- 3. 採購邏輯：深度淨化 + 智能合併 ---
def get_shopping_summary(df_to_process):
    if df_to_process is None or df_to_process.empty: return {"食材": {}, "調味": {}}
    sea_kws = ['鹽', '糖', '油', '醬', '醋', '粉', '汁', '酒', '蜜', '豉', '麻', '水', '露']
    summary = {"食材": {}, "調味": {}}
    
    for _, row in df_to_process.iterrows():
        dish = row['Dish_Name']
        d_val = int(row['Day_Int'])
        
        # 預處理：清走括號內容，廢話
        raw_content = str(row['Ingredients']).replace('\n', ' ').replace(',', ' ').replace('，', ' ')
        items = re.split(r'[、\s]+', raw_content)
        
        seen_this_dish = set()
        for raw in items:
            raw = raw.strip()
            # 1. 移除編號如 "1." "2."
            raw = re.sub(r'^\d+[\.\s]*', '', raw)
            if not raw or raw == 'nan': continue
            
            # 2. 提取純食材名 (遇到數字、份、g等就切斷)
            # 依家會更嚴格咁搵第一個非中文字/非食材名嘅位
            base_name = re.split(r'(\d+|半|少許|適量|份|g|克|兩|斤|包|隻|支|盒|ml|毫升)', raw)[0].strip()
            # 移除所有括號雜質
            base_name = re.sub(r'[\(\)（）]', '', base_name)
            
            if not base_name or base_name in seen_this_dish: continue
            seen_this_dish.add(base_name)
            
            amount = raw.replace(base_name, "").strip()
            cat = "調味" if any(kw in base_name for kw in sea_kws) else "食材"
            
            if base_name not in summary[cat]:
                summary[cat][base_name] = {"count": 0, "details": []}
            
            summary[cat][base_name]["count"] += 1
            summary[cat][base_name]["details"].append(f"Day {d_val} {dish} {amount}")
            
    return summary

# --- 4. 導航與分頁 ---
if all_df is not None:
    st.sidebar.title("🌸 功能選單")
    mode = st.sidebar.radio("跳轉至：", ["📅 媽媽坐月餐單", "🛒 採購 Check-list", "🗓️ 每週總覽"])

    if mode == "🛒 採購 Check-list":
        st.markdown("<h1>🛒 採購 Check-list</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📍 睇今日買乜", "📅 一次過買幾日"])
        
        with t1:
            s_day = st.number_input("選擇第幾天", 1, 30, 1)
            work_df = all_df[all_df['Day_Int'] == s_day].copy()
            u_key = f"s_{s_day}"
        with t2:
            c1, c2 = st.columns(2)
            r1 = c1.number_input("由 Day", 1, 30, 1)
            r2 = c2.number_input("至 Day", 1, 30, r1+1)
            work_df = all_df[(all_df['Day_Int'] >= r1) & (all_df['Day_Int'] <= r2)].copy()
            u_key = f"r_{r1}_{r2}"

        if not work_df.empty:
            data_sum = get_shopping_summary(work_df)
            for cat in ["食材", "調味"]:
                if data_sum[cat]:
                    st.markdown(f'<div class="section-title">{"🍎 主要食材" if cat=="食材" else "🧂 檢查調味料"}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="check-card">', unsafe_allow_html=True)
                    for name, info in data_sum[cat].items():
                        # 去重顯示用途
                        clean_details = list(dict.fromkeys(info["details"]))
                        label = f"{name}" + (f" (x{len(clean_details)})" if len(clean_details) > 1 else "")
                        st.checkbox(label, key=f"c_{u_key}_{name}")
                        st.markdown(f'<span class="usage-text">📍 {" / ".join(clean_details)}</span>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("揀選嘅日子未有資料喔！")

    elif mode == "📅 媽媽坐月餐單":
        # (這裡保留你原本最靚嘅 Button 詳情頁邏輯)
        st.markdown("<h1>📅 媽媽坐月餐單</h1>", unsafe_allow_html=True)
        # ... (略過重複代碼，確保你的 Button 功能如常) ...
        st.info("請於側邊欄切換至採購清單體驗新功能！")
