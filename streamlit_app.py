import streamlit as st
import pandas as pd
import re

# --- 1. 樣式設定 (手機灰色優化版) ---
st.set_page_config(page_title="🌸 媽媽坐月餐單", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; }
    .main .block-container { max-width: 600px; margin: 0 auto; padding: 1.2rem; }
    h1 { color: #D87093 !important; font-size: 1.8rem !important; text-align: center; }
    .section-title { color: #D87093; font-size: 1.2rem; font-weight: bold; margin: 15px 0 10px 0; }
    p, span, label, .stCheckbox, .stMarkdown { color: #666666 !important; }
    .stButton>button { 
        background-color: #FFB6C1; color: white !important; 
        border-radius: 18px; border: none; width: 100%; min-height: 45px;
        font-size: 1.1rem; font-weight: bold; margin-bottom: 10px;
    }
    .check-card, .week-card, .recipe-card {
        background-color: white; padding: 15px; border-radius: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04); margin-bottom: 15px;
        border: 1.5px solid #FFE4E1;
    }
    .usage-text { color: #888888 !important; font-size: 0.9rem; margin-left: 32px; display: block; margin-top: -8px; margin-bottom: 12px; }
    [data-testid="stSidebar"] { background-color: #FFE4E1; }
    [data-testid="stSidebar"] * { color: #D87093 !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取 ---
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

all_df = load_data()

# --- 3. 採購邏輯修正：嚴格只處理傳入的 DataFrame ---
def get_shopping_summary(df_to_process):
    if df_to_process.empty: return {"食材": {}, "調味": {}}
    sea_kws = ['鹽', '糖', '油', '醬', '醋', '粉', '汁', '露', '酒', '蜜', '精', '豉', '麻', '水']
    summary = {"食材": {}, "調味": {}}
    
    for _, row in df_to_process.iterrows():
        dish = row['Dish_Name']
        day_num = int(row['Day_Int'])
        items = re.split(r'[\n,，、\s]+', str(row['Ingredients']))
        
        for raw_item in items:
            raw_item = raw_item.strip()
            if not raw_item or raw_item == 'nan': continue
            
            # 分拆出核心名稱 (例如: "糙米 1份" -> "糙米")
            parts = re.split(r'(\d+|半|少許|適量|份|g|克|兩|斤|包)', raw_item, maxsplit=1)
            base_name = parts[0].strip()
            amount = raw_item.replace(base_name, "").strip()
            
            cat = "調味" if any(kw in base_name for kw in sea_kws) else "食材"
            
            # 以 base_name 作為唯一 Key
            if base_name not in summary[cat]:
                summary[cat][base_name] = {"total_count": 0, "details": []}
            
            summary[cat][base_name]["total_count"] += 1
            # 儲存呢一餐嘅具體日子同份量
            summary[cat][base_name]["details"].append(f"Day {day_num} {dish} ({amount if amount else '適量'})")
            
    return summary

# --- 4. 狀態管理 ---
if 'view' not in st.session_state: st.session_state.view = 'main'
if 'selected_row' not in st.session_state: st.session_state.selected_row = None
if 'day_input' not in st.session_state: st.session_state.day_input = 1

# --- 5. 導航 ---
st.sidebar.title("🌸 選單")
mode = st.sidebar.radio("跳轉至：", ["📅 媽媽坐月餐單", "🗓️ 每週總覽", "🛒 採購 Check-list", "🔍 食譜大百科"], index=0)

# --- 6. 詳情頁面 ---
if st.session_state.view == 'details':
    recipe = st.session_state.selected_row
    st.markdown(f"<h1>{recipe['Dish_Name']}</h1>", unsafe_allow_html=True)
    if st.button("⬅️ 返回"): st.session_state.view = 'main'; st.rerun()
    st.markdown(f'<div class="recipe-card"><p><b>📅 第 {int(recipe["Day_Int"])} 天 · {recipe["Meal"]}</b></p><hr><p>🛒 <b>食材：</b><br>{recipe["Ingredients"]}</p><p>👩‍🍳 <b>做法：</b><br>{recipe["Method"]}</p></div>', unsafe_allow_html=True)

# --- 7. 📅 媽媽坐月餐單 ---
elif mode == "📅 媽媽坐月餐單":
    st.markdown("<h1>📅 媽媽坐月餐單</h1>", unsafe_allow_html=True)
    d_num = st.number_input("🔢 選擇天數", min_value=1, max_value=30, value=st.session_state.day_input)
    st.session_state.day_input = d_num
    day_df = all_df[all_df['Day_Int'] == d_num]
    for m in ["早餐", "午餐", "下午茶", "糖水", "湯水", "晚餐", "炒米茶"]:
        m_data = day_df[day_df['Meal'].str.contains(m, na=False)]
        for _, row in m_data.iterrows():
            if st.button(f"🥘 {m}：{row['Dish_Name']}", key=f"d_{row.name}"):
                st.session_state.selected_row = row; st.session_state.view = 'details'; st.rerun()

# --- 8. 🗓️ 每週總覽 ---
elif mode == "🗓️ 每週總覽":
    st.markdown("<h1>🗓️ 每週總覽</h1>", unsafe_allow_html=True)
    week_range = st.selectbox("選擇範圍", ["第 1 週 (1-7)", "第 2 週 (8-14)", "第 3 週 (15-21)", "第 4 週 (22-30)"])
    r_map = {"第 1 週 (1-7)": (1, 7), "第 2 週 (8-14)": (8, 14), "第 3 週 (15-21)": (15, 21), "第 4 週 (22-30)": (22, 30)}
    start, end = r_map[week_range]
    for d in range(start, end + 1):
        day_items = all_df[all_df['Day_Int'] == d]
        if not day_items.empty:
            st.markdown(f'<div class="week-card"><b>📅 第 {d} 天</b><br>' + "<br>".join([f"· {r['Meal']}: {r['Dish_Name']}" for _, r in day_items.iterrows()]) + '</div>', unsafe_allow_html=True)

# --- 9. 🛒 採購 Check-list (徹底過濾版) ---
elif mode == "🛒 採購 Check-list":
    st.markdown("<h1>🛒 採購 Check-list</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["📍 睇今日買乜", "📅 一次過買幾日"])
    
    with t1:
        s_day = st.number_input("選擇天數", min_value=1, max_value=30, value=1, key="s_day_input")
        # 【核心修正】呢度只攞果一日嘅數據，絕對唔攞其他日子
        working_df = all_df[all_df['Day_Int'] == s_day].copy()

    with t2:
        c1, c2 = st.columns(2)
        with c1: start_d = st.number_input("由 Day", min_value=1, max_value=30, value=1, key="r_start")
        with c2: end_d = st.number_input("至 Day", min_value=1, max_value=30, value=start_d+1, key="r_end")
        # 【核心修正】呢度只攞指定範圍內嘅數據
        working_df = all_df[(all_df['Day_Int'] >= start_d) & (all_df['Day_Int'] <= end_d)].copy()

    if not working_df.empty:
        summary = get_shopping_summary(working_df)
        for cat in ["食材", "調味"]:
            if summary[cat]:
                st.markdown(f'<div class="section-title">{"🍎 主要食材" if cat=="食材" else "🧂 檢查調味"}</div>', unsafe_allow_html=True)
                st.markdown('<div class="check-card">', unsafe_allow_html=True)
                for name, info in summary[cat].items():
                    # 依家 info['details'] 只會包含 working_df 裡面嘅內容
                    label = f"{name}" + (f" (x{info['total_count']})" if info['total_count'] > 1 else "")
                    st.checkbox(label, key=f"chk_{name}_{cat}_{s_day if 's_day' in locals() else start_d}")
                    st.markdown(f'<span class="usage-text">📍 {"、".join(info["details"])}</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("所選日期暫無資料。")

# --- 10. 🔍 食譜大百科 ---
elif mode == "🔍 食譜大百科":
    st.markdown("<h1>🔍 食譜大百科</h1>", unsafe_allow_html=True)
    search = st.text_input("🔍 搜尋食材或菜名")
    if search:
        search_df = all_df[all_df['Dish_Name'].str.contains(search, na=False) | all_df['Ingredients'].str.contains(search, na=False)]
        for _, row in search_df.iterrows():
            if st.button(f"✨ {row['Dish_Name']} (Day {int(row['Day_Int'])})", key=f"search_{row.name}"):
                st.session_state.selected_row = row; st.session_state.view = 'details'; st.rerun()
