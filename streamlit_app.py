import streamlit as st
import pandas as pd
import re

# --- 1. 樣式設定 (恢復粉紅標籤) ---
st.set_page_config(page_title="🌸 媽媽坐月餐單", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; }
    .main .block-container { max-width: 600px; margin: 0 auto; padding: 1.2rem; }
    h1 { color: #D87093 !important; font-size: 2rem !important; text-align: center; }
    .meal-label { color: #FF99AA !important; font-weight: bold !important; font-size: 1.1rem; }
    p, span, label, .stCheckbox, .stMarkdown { color: #666666 !important; }
    .stButton>button { 
        background-color: #FFB6C1; color: white !important; 
        border-radius: 20px; border: none; width: 100%; min-height: 50px;
        font-size: 1.1rem; font-weight: bold; margin-bottom: 12px;
    }
    .check-card, .recipe-card, .week-card {
        background-color: white; padding: 20px; border-radius: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px;
        border: 2px solid #FFE4E1;
    }
    .section-title { color: #D87093; font-size: 1.3rem; font-weight: bold; margin: 20px 0 10px 0; border-left: 5px solid #FFB6C1; padding-left: 10px; }
    .usage-text { color: #999999 !important; font-size: 0.85rem; margin-left: 32px; display: block; margin-top: -8px; margin-bottom: 15px; }
    [data-testid="stSidebar"] { background-color: #FFE4E1; }
    [data-testid="stSidebar"] * { color: #D87093 !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZesALwN_63zG-ULARgSgu2zX44qpxYud8Y4qco_4IFI/edit?usp=sharing"
CSV_URL = SHEET_URL.split('/edit')[0] + '/export?format=csv'

@st.cache_data(ttl=0)
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        df.columns = df.columns.str.strip()
        df['Day_Int'] = pd.to_numeric(df['Day'], errors='coerce').fillna(0).astype(int)
        return df
    except: return None

all_df = load_data()

# --- 3. 採購邏輯：物理級數據過濾 ---
def get_shopping_summary(df_to_process):
    # 確保傳入嘅 df 係乾淨嘅 (雖然出面過濾咗，呢度再做一次安全檢查)
    if df_to_process is None or df_to_process.empty: return {"食材": {}, "調味": {}}
    
    sea_kws = ['鹽', '糖', '油', '醬', '醋', '粉', '汁', '酒', '蜜', '豉', '麻', '水', '露']
    summary = {"食材": {}, "調味": {}}
    
    for _, row in df_to_process.iterrows():
        dish = row['Dish_Name']
        d_val = int(row['Day_Int'])
        # 拆開食材
        raw_content = str(row['Ingredients']).replace('\n', ' ').replace(',', ' ').replace('，', ' ')
        items = re.split(r'[、\s]+', raw_content)
        
        seen_in_dish = set()
        for raw in items:
            raw = raw.strip()
            # 移除 1. 2. 等編號
            raw = re.sub(r'^\d+[\.\s]*', '', raw)
            if not raw or raw == 'nan' or len(raw) < 1: continue
            
            # 提取純名稱：遇到數字或單位就切斷
            base_name = re.split(r'(\d+|半|少許|適量|份|g|克|兩|斤|包|隻|支|盒|ml)', raw)[0].strip()
            # 移除括號
            base_name = re.sub(r'[\(（].*[\)）]', '', base_name)
            
            if not base_name or base_name in seen_in_dish: continue
            seen_in_dish.add(base_name)
            
            amount = raw.replace(base_name, "").strip()
            cat = "調味" if any(kw in base_name for kw in sea_kws) else "食材"
            
            if base_name not in summary[cat]:
                summary[cat][base_name] = {"count": 0, "details": []}
            
            summary[cat][base_name]["count"] += 1
            summary[cat][base_name]["details"].append(f"Day {d_val} {dish} {amount}")
            
    return summary

# --- 4. 頁面導航 ---
if all_df is not None:
    st.sidebar.title("🌸 功能導航")
    mode = st.sidebar.radio("跳轉至：", ["📅 媽媽坐月餐單", "🗓️ 每週總覽", "🛒 採購 Check-list", "🔍 食譜大百科"])

    if 'view' not in st.session_state: st.session_state.view = 'main'

    # A. 詳情頁
    if st.session_state.view == 'details':
        recipe = st.session_state.selected_row
        st.markdown(f"<h1>{recipe['Dish_Name']}</h1>", unsafe_allow_html=True)
        if st.button("⬅️ 返回"): st.session_state.view = 'main'; st.rerun()
        st.markdown(f'<div class="recipe-card"><p><span class="meal-label">📅 第 {int(recipe["Day_Int"])} 天 · {recipe["Meal"]}</span></p><hr style="border:1px solid #FFE4E1;"><p><span class="meal-label">🛒 食材：</span><br>{recipe["Ingredients"]}</p><p><span class="meal-label">👩‍🍳 做法：</span><br>{recipe["Method"]}</p></div>', unsafe_allow_html=True)

    # B. 🛒 採購 Check-list (終極物理過濾版)
    elif mode == "🛒 採購 Check-list":
        st.markdown("<h1>🛒 採購 Check-list</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📍 睇今日買乜", "📅 一次過買幾日"])
        
        with t1:
            s_day = st.number_input("選擇第幾天", 1, 30, 1, key="shop_s_day")
            # 【核心修正】呢度直接將 all_df 斬開，只留嗰一日
            working_df = all_df[all_df['Day_Int'] == s_day].copy()
            u_key = f"s_{s_day}"

        with t2:
            c1, c2 = st.columns(2)
            r1 = c1.number_input("由 Day", 1, 30, 1, key="shop_r1")
            r2 = c2.number_input("至 Day", 1, 30, r1+1, key="shop_r2")
            # 【核心修正】只留範圍內嘅 Row
            working_df = all_df[(all_df['Day_Int'] >= r1) & (all_df['Day_Int'] <= r2)].copy()
            u_key = f"r_{r1}_{r2}"

        if not working_df.empty:
            data_sum = get_shopping_summary(working_df)
            for cat in ["食材", "調味"]:
                if data_sum[cat]:
                    st.markdown(f'<div class="section-title">{"🍎 主要食材" if cat=="食材" else "🧂 檢查調味"}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="check-card">', unsafe_allow_html=True)
                    for name, info in data_sum[cat].items():
                        clean_details = list(dict.fromkeys(info["details"]))
                        # 顯示數量
                        label = f"{name}" + (f" (x{len(clean_details)})" if len(clean_details) > 1 else "")
                        st.checkbox(label, key=f"chk_{u_key}_{name}")
                        st.markdown(f'<span class="usage-text">📍 {" / ".join(clean_details)}</span>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

    # C. 📅 媽媽坐月餐單 (恢復粉紅字)
    elif mode == "📅 媽媽坐月餐單":
        st.markdown("<h1>📅 媽媽坐月餐單</h1>", unsafe_allow_html=True)
        sel_d = st.number_input("🔢 選擇天數", 1, 30, 1, key="main_day")
        day_df = all_df[all_df['Day_Int'] == sel_d]
        meals = ["早餐", "午餐", "下午茶", "糖水", "湯水", "晚餐", "炒米茶"]
        for m in meals:
            m_data = day_df[day_df['Meal'].str.contains(m, na=False)]
            for _, row in m_data.iterrows():
                if st.button(f"🥘 {m}：{row['Dish_Name']}", key=f"btn_{row.name}"):
                    st.session_state.selected_row = row; st.session_state.view = 'details'; st.rerun()

    # D. 其餘功能恢復
    elif mode == "🗓️ 每週總覽":
        st.markdown("<h1>🗓️ 每週總覽</h1>", unsafe_allow_html=True)
        week = st.selectbox("選擇範圍", ["第 1 週 (1-7)", "第 2 週 (8-14)", "第 3 週 (15-21)", "第 4 週 (22-30)"])
        w_map = {"第 1 週 (1-7)": (1, 7), "第 2 週 (8-14)": (8, 14), "第 3 週 (15-21)": (15, 21), "第 4 週 (22-30)": (22, 30)}
        start, end = w_map[week]
        for d in range(start, end + 1):
            day_data = all_df[all_df['Day_Int'] == d]
            if not day_data.empty:
                items_html = "".join([f"· <span class='meal-label'>{r['Meal']}</span>: {r['Dish_Name']}<br>" for _, r in day_data.iterrows()])
                st.markdown(f'<div class="week-card"><b style="color:#D87093;">📅 第 {d} 天</b><br>{items_html}</div>', unsafe_allow_html=True)

    elif mode == "🔍 食譜大百科":
        st.markdown("<h1>🔍 食譜大百科</h1>", unsafe_allow_html=True)
        query = st.text_input("🔍 搜尋食材或菜式：")
        if query:
            search_df = all_df[all_df['Dish_Name'].str.contains(query, na=False) | all_df['Ingredients'].str.contains(query, na=False)]
            for _, row in search_df.iterrows():
                if st.button(f"✨ {row['Dish_Name']} (Day {int(row['Day_Int'])})", key=f"q_{row.name}"):
                    st.session_state.selected_row = row; st.session_state.view = 'details'; st.rerun()
else:
    st.error("讀取不到資料。")
