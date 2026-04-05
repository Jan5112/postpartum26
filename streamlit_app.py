import streamlit as st
import pandas as pd
import re

# --- 1. 樣式設定 (保持粉紅靚樣 + 灰色細字) ---
st.set_page_config(page_title="🌸 媽媽坐月餐單", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; }
    .main .block-container { max-width: 600px; margin: 0 auto; padding: 1.2rem; }
    h1 { color: #D87093 !important; font-size: 2rem !important; text-align: center; }
    p, span, label, .stCheckbox, .stMarkdown { color: #666666 !important; }
    .stButton>button { 
        background-color: #FFB6C1; color: white !important; 
        border-radius: 20px; border: none; width: 100%; min-height: 50px;
        font-size: 1.1rem; font-weight: bold; margin-bottom: 12px;
        box-shadow: 0 4px 6px rgba(255,182,193,0.3);
    }
    .check-card {
        background-color: white; padding: 18px; border-radius: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 15px;
        border: 2px solid #FFE4E1;
    }
    .section-title { color: #D87093; font-size: 1.3rem; font-weight: bold; margin: 20px 0 10px 0; border-left: 5px solid #FFB6C1; padding-left: 10px; }
    .usage-text { color: #999999 !important; font-size: 0.85rem; margin-left: 32px; display: block; margin-top: -8px; margin-bottom: 15px; line-height: 1.4; }
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

# --- 3. 採購邏輯：去重 + 瘦身 ---
def get_shopping_summary(df_to_process):
    if df_to_process is None or df_to_process.empty: return {"食材": {}, "調味": {}}
    sea_kws = ['鹽', '糖', '油', '醬', '醋', '粉', '汁', '酒', '蜜', '豉', '麻', '水', '油']
    summary = {"食材": {}, "調味": {}}
    
    for _, row in df_to_process.iterrows():
        dish = row['Dish_Name']
        d_val = int(row['Day_Int'])
        
        # 拆開食材並清理 (處理換行、逗號、數字編號)
        raw_text = str(row['Ingredients']).replace('\n', ' ').replace(',', ' ').replace('，', ' ')
        items = re.split(r'[、\s]+', raw_text)
        
        # 同一個菜式內的食材去重，避免出現多次 "豬肉 (少許)"
        seen_in_this_dish = set()

        for raw in items:
            raw = raw.strip()
            # 清理掉 "1." "2." 這種編號
            raw = re.sub(r'^\d+[\.\s]*', '', raw)
            if not raw or raw == 'nan' or len(raw) < 1: continue
            
            # 分拆名稱與份量
            parts = re.split(r'(\d+|半|少許|適量|份|g|克|兩|斤|包)', raw, maxsplit=1)
            base_name = parts[0].strip()
            amount = raw.replace(base_name, "").strip()
            
            # 如果同一個菜式已經計過呢樣野，就跳過
            if base_name in seen_in_this_dish: continue
            seen_in_this_dish.add(base_name)
            
            cat = "調味" if any(kw in base_name for kw in sea_kws) else "食材"
            if base_name not in summary[cat]:
                summary[cat][base_name] = {"count": 0, "details": []}
            
            summary[cat][base_name]["count"] += 1
            summary[cat][base_name]["details"].append(f"Day {d_val} {dish} ({amount if amount else '適量'})")
            
    return summary

# --- 4. 頁面邏輯 ---
if all_df is not None:
    st.sidebar.title("🌸 功能導航")
    mode = st.sidebar.radio("跳轉至：", ["📅 媽媽坐月餐單", "🛒 採購 Check-list", "🗓️ 每週總覽", "🔍 食譜大百科"])

    # --- A. 詳情頁 ---
    if 'view' not in st.session_state: st.session_state.view = 'main'
    
    if st.session_state.view == 'details':
        recipe = st.session_state.selected_row
        st.markdown(f"<h1>{recipe['Dish_Name']}</h1>", unsafe_allow_html=True)
        if st.button("⬅️ 返回"): st.session_state.view = 'main'; st.rerun()
        st.markdown(f'<div class="recipe-card"><p>🛒 <b>食材：</b><br>{recipe["Ingredients"]}</p><p>👩‍🍳 <b>做法：</b><br>{recipe["Method"]}</p></div>', unsafe_allow_html=True)

    # --- B. 採購 Check-list (瘦身版) ---
    elif mode == "🛒 採購 Check-list":
        st.markdown("<h1>🛒 採購 Check-list</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📍 睇今日買乜", "📅 一次過買幾日"])
        
        with t1:
            s_day = st.number_input("選擇第幾天", 1, 30, 1, key="s_day_check")
            working_df = all_df[all_df['Day_Int'] == s_day].copy()
            u_key = f"day_{s_day}"
        with t2:
            c1, c2 = st.columns(2)
            with c1: r1 = st.number_input("由 Day", 1, 30, 1)
            with c2: r2 = st.number_input("至 Day", 1, 30, r1+1)
            working_df = all_df[(all_df['Day_Int'] >= r1) & (all_df['Day_Int'] <= r2)].copy()
            u_key = f"range_{r1}_{r2}"

        if not working_df.empty:
            summary = get_shopping_summary(working_df)
            for cat in ["食材", "調味"]:
                if summary[cat]:
                    st.markdown(f'<div class="section-title">{"🍎 主要食材" if cat=="食材" else "🧂 檢查調味"}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="check-card">', unsafe_allow_html=True)
                    for name, info in summary[cat].items():
                        # 只取前幾項顯示，或者直接合併去重後的 details
                        unique_details = list(dict.fromkeys(info["details"]))
                        label = f"{name}" + (f" (x{len(unique_details)})" if len(unique_details) > 1 else "")
                        st.checkbox(label, key=f"chk_{u_key}_{name}")
                        st.markdown(f'<span class="usage-text">📍 {" / ".join(unique_details)}</span>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

    # --- C. 媽媽坐月餐單 (維持靚靚樣式) ---
    elif mode == "📅 媽媽坐月餐單":
        st.markdown("<h1>📅 媽媽坐月餐單</h1>", unsafe_allow_html=True)
        sel_d = st.number_input("🔢 選擇天數", 1, 30, 1)
        day_df = all_df[all_df['Day_Int'] == sel_d]
        meals = ["早餐", "午餐", "下午茶", "糖水", "湯水", "晚餐", "炒米茶"]
        for m in meals:
            m_data = day_df[day_df['Meal'].str.contains(m, na=False)]
            for _, row in m_data.iterrows():
                if st.button(f"🥘 {m}：{row['Dish_Name']}", key=f"btn_{row.name}"):
                    st.session_state.selected_row = row; st.session_state.view = 'details'; st.rerun()
