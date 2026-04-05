import streamlit as st
import pandas as pd
import re

# --- 1. 樣式設定 (全域粉紅標籤回歸) ---
st.set_page_config(page_title="🌸 媽媽坐月餐單", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; }
    .main .block-container { max-width: 600px; margin: 0 auto; padding: 1.2rem; }
    h1 { color: #D87093 !important; font-size: 2rem !important; text-align: center; margin-bottom: 25px; }
    
    /* 粉紅字體標籤 */
    .meal-label { color: #FF99AA !important; font-weight: bold !important; font-size: 1.1rem; }
    
    /* 內容文字 */
    p, span, label, .stCheckbox, .stMarkdown { color: #666666 !important; }

    /* 粉紅按鈕 */
    .stButton>button { 
        background-color: #FFB6C1; color: white !important; 
        border-radius: 20px; border: none; width: 100%; min-height: 50px;
        font-size: 1.1rem; font-weight: bold; margin-bottom: 12px;
        box-shadow: 0 4px 6px rgba(255,182,193,0.2);
    }
    
    /* 卡片設計 */
    .recipe-card, .check-card, .week-card {
        background-color: white; padding: 20px; border-radius: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px;
        border: 2px solid #FFE4E1;
    }
    
    .section-title { color: #D87093; font-size: 1.3rem; font-weight: bold; margin: 20px 0 10px 0; border-left: 5px solid #FFB6C1; padding-left: 10px; }
    .usage-text { color: #999999 !important; font-size: 0.85rem; margin-left: 32px; display: block; margin-top: -6px; margin-bottom: 15px; }

    /* 側邊欄 */
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

# --- 3. 採購邏輯：嚴格限定日期 ---
def get_shopping_summary(df_to_process, target_days):
    if df_to_process is None or df_to_process.empty: return {"食材": {}, "調味": {}}
    df_clean = df_to_process[df_to_process['Day_Int'].isin(target_days)].copy()
    sea_kws = ['鹽', '糖', '油', '醬', '醋', '粉', '汁', '酒', '蜜', '豉', '麻', '水', '露']
    summary = {"食材": {}, "調味": {}}
    
    for _, row in df_clean.iterrows():
        dish = row['Dish_Name']
        d_val = int(row['Day_Int'])
        items = re.split(r'[、\s\n,，]+', str(row['Ingredients']))
        seen_this_dish = set()
        for raw in items:
            raw = raw.strip()
            raw = re.sub(r'^\d+[\.\s]*', '', raw)
            if not raw or raw == 'nan': continue
            base_name = re.split(r'(\d+|半|少許|適量|份|g|克|兩|斤|包|隻|支|盒|ml)', raw)[0].strip()
            base_name = re.sub(r'[\(（].*[\)）]', '', base_name)
            if not base_name or base_name in seen_this_dish: continue
            seen_this_dish.add(base_name)
            amount = raw.replace(base_name, "").strip()
            cat = "調味" if any(kw in base_name for kw in sea_kws) else "食材"
            if base_name not in summary[cat]:
                summary[cat][base_name] = {"details": []}
            summary[cat][base_name]["details"].append(f"Day {d_val} {dish} {amount}")
    return summary

# --- 4. 狀態管理 ---
if 'view' not in st.session_state: st.session_state.view = 'main'
if 'selected_row' not in st.session_state: st.session_state.selected_row = None

# --- 5. 導航與頁面分流 ---
if all_df is not None:
    st.sidebar.title("🌸 功能導航")
    mode = st.sidebar.radio("跳轉至：", ["📅 媽媽坐月餐單", "🗓️ 每週總覽", "🛒 採購 Check-list", "🔍 食譜大百科"])

    # --- A. 詳情頁 (所有功能共用) ---
    if st.session_state.view == 'details':
        recipe = st.session_state.selected_row
        st.markdown(f"<h1>{recipe['Dish_Name']}</h1>", unsafe_allow_html=True)
        if st.button("⬅️ 返回列表"): st.session_state.view = 'main'; st.rerun()
        st.markdown(f"""
        <div class="recipe-card">
            <p><span class="meal-label">📅 第 {int(recipe['Day_Int'])} 天 · {recipe['Meal']}</span></p>
            <hr style="border:1px solid #FFE4E1;">
            <p><span class="meal-label">🛒 準備食材：</span><br>{recipe['Ingredients']}</p>
            <p><span class="meal-label">👩‍🍳 烹飪步驟：</span><br>{recipe['Method']}</p>
        </div>
        """, unsafe_allow_html=True)

    # --- B. 📅 媽媽坐月餐單 ---
    elif mode == "📅 媽媽坐月餐單":
        st.markdown("<h1>📅 媽媽坐月餐單</h1>", unsafe_allow_html=True)
        sel_d = st.number_input("🔢 選擇天數", 1, 30, 1)
        day_df = all_df[all_df['Day_Int'] == sel_d]
        for m in ["早餐", "午餐", "下午茶", "糖水", "湯水", "晚餐", "炒米茶"]:
            m_data = day_df[day_df['Meal'].str.contains(m, na=False)]
            for _, row in m_data.iterrows():
                if st.button(f"🥘 {m}：{row['Dish_Name']}", key=f"btn_{row.name}"):
                    st.session_state.selected_row = row; st.session_state.view = 'details'; st.rerun()

    # --- C. 🗓️ 每週總覽 (完整補回) ---
    elif mode == "🗓️ 每週總覽":
        st.markdown("<h1>🗓️ 每週總覽</h1>", unsafe_allow_html=True)
        week = st.selectbox("選擇顯示範圍", ["第 1 週 (Day 1-7)", "第 2 週 (Day 8-14)", "第 3 週 (Day 15-21)", "第 4 週 (Day 22-30)"])
        w_map = {"第 1 週 (Day 1-7)": (1, 7), "第 2 週 (Day 8-14)": (8, 14), "第 3 週 (Day 15-21)": (15, 21), "第 4 週 (Day 22-30)": (22, 30)}
        start, end = w_map[week]
        for d in range(start, end + 1):
            day_data = all_df[all_df['Day_Int'] == d]
            if not day_data.empty:
                items_html = "".join([f"· <span class='meal-label'>{r['Meal']}</span>: {r['Dish_Name']}<br>" for _, r in day_data.iterrows()])
                st.markdown(f'<div class="week-card"><b style="color:#D87093; font-size:1.15rem;">📅 第 {d} 天</b><br>{items_html}</div>', unsafe_allow_html=True)

    # --- D. 🛒 採購 Check-list ---
    elif mode == "🛒 採購 Check-list":
        st.markdown("<h1>🛒 採購 Check-list</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📍 睇今日買乜", "📅 一次過買幾日"])
        with t1:
            s_day = st.number_input("選擇天數", 1, 30, 1, key="s_input")
            target = [s_day]; u_key = f"single_{s_day}"
        with t2:
            c1, c2 = st.columns(2)
            r1 = c1.number_input("由 Day", 1, 30, 1, key="r1_in")
            r2 = c2.number_input("至 Day", 1, 30, r1+1, key="r2_in")
            target = list(range(r1, r2 + 1)); u_key = f"range_{r1}_{r2}"
        
        data_sum = get_shopping_summary(all_df, target)
        for cat in ["食材", "調味"]:
            if data_sum[cat]:
                st.markdown(f'<div class="section-title">{"🍎 主要食材" if cat=="食材" else "🧂 檢查調味"}</div>', unsafe_allow_html=True)
                st.markdown('<div class="check-card">', unsafe_allow_html=True)
                for name, info in data_sum[cat].items():
                    details = list(dict.fromkeys(info["details"]))
                    label = f"{name}" + (f" (x{len(details)})" if len(details) > 1 else "")
                    st.checkbox(label, key=f"chk_{u_key}_{name}")
                    st.markdown(f'<span class="usage-text">📍 {" / ".join(details)}</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    # --- E. 🔍 食譜大百科 (完整補回) ---
    elif mode == "🔍 食譜大百科":
        st.markdown("<h1>🔍 食譜大百科</h1>", unsafe_allow_html=True)
        query = st.text_input("🔍 輸入食材或菜名搜尋：", placeholder="例如：豬肉、銀耳...")
        if query:
            search_df = all_df[all_df['Dish_Name'].str.contains(query, na=False, case=False) | all_df['Ingredients'].str.contains(query, na=False, case=False)]
            if not search_df.empty:
                for _, row in search_df.iterrows():
                    if st.button(f"✨ Day {int(row['Day_Int'])} | {row['Meal']}：{row['Dish_Name']}", key=f"search_{row.name}"):
                        st.session_state.selected_row = row; st.session_state.view = 'details'; st.rerun()
            else:
                st.write("找不到相關食譜，換個關鍵字試試？")
else:
    st.error("未能載入資料。")
