import streamlit as st
import pandas as pd
import re

# --- 1. 樣式設定 (樣式鎖死，保證唔會變返黑色) ---
st.set_page_config(page_title="🌸 媽媽坐月餐單", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; }
    .main .block-container { max-width: 600px; margin: 0 auto; padding: 1.2rem; }
    
    /* 強制 Heading 變回粉紅色 */
    h1, h2, h3 { color: #D87093 !important; text-align: center; font-weight: bold !important; }
    
    .meal-label { color: #FF99AA !important; font-weight: bold !important; font-size: 1.1rem; }
    
    /* 確保內文係深灰色，唔好變白色 */
    p, span, label, .stCheckbox, .stMarkdown, div { color: #555555 !important; }
    
    .stButton>button { 
        background-color: #FFB6C1; color: white !important; 
        border-radius: 20px; border: none; width: 100%; min-height: 50px;
        font-size: 1.1rem; font-weight: bold; margin-bottom: 12px;
    }
    
    .recipe-card, .check-card, .week-card {
        background-color: white !important; padding: 25px; border-radius: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px;
        border: 2px solid #FFE4E1;
    }
    
    .section-title { color: #D87093 !important; font-size: 1.3rem; font-weight: bold; margin: 20px 0 10px 0; border-left: 5px solid #FFB6C1; padding-left: 10px; }
    .usage-text { color: #888888 !important; font-size: 0.85rem; margin-left: 32px; display: block; margin-top: -6px; margin-bottom: 15px; }

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

# --- 3. 採購邏輯 (真正斷絕第2日滲透) ---
def get_shopping_summary(df_to_process, target_days):
    # 只拿目標日子的資料
    clean_df = df_to_process[df_to_process['Day_Int'].isin(target_days)].copy()
    sea_kws = ['鹽', '糖', '油', '醬', '醋', '粉', '汁', '酒', '蜜', '豉', '麻', '水', '露']
    summary = {"食材": {}, "調味": {}}
    
    for _, row in clean_df.iterrows():
        dish = row['Dish_Name']
        d_val = int(row['Day_Int'])
        
        # 再次檢查：如果這行不屬於 target_days，直接跳過 (雙重保險)
        if d_val not in target_days: continue
        
        raw_ings = str(row['Ingredients']).replace('\n', ' ').replace(',', ' ').replace('，', ' ')
        items = re.split(r'[、\s]+', raw_ings)
        for raw in items:
            raw = raw.strip()
            raw = re.sub(r'^\d+[\.\s]*', '', raw)
            if not raw or raw == 'nan': continue
            base_name = re.split(r'(\d+|半|少許|適量|份|g|克|兩|斤|包|隻|支|盒|ml)', raw)[0].strip()
            base_name = re.sub(r'[\(（].*[\)）]', '', base_name)
            if not base_name: continue
            
            amount = raw.replace(base_name, "").strip()
            cat = "調味" if any(kw in base_name for kw in sea_kws) else "食材"
            
            if base_name not in summary[cat]:
                summary[cat][base_name] = {"details": []}
            
            summary[cat][base_name]["details"].append(f"Day {d_val} {dish} {amount}")
    return summary

# --- 4. 狀態管理 ---
if 'view' not in st.session_state: st.session_state.view = 'main'
if 'selected_row' not in st.session_state: st.session_state.selected_row = None

# --- 5. 導覽分流 ---
if all_df is not None:
    st.sidebar.title("🌸 功能導航")
    mode = st.sidebar.radio("跳轉至：", ["📅 媽媽坐月餐單", "🗓️ 每週總覽", "🛒 採購 Check-list", "🔍 食譜大百科"])

    # A. 詳情頁 (核心修復：還原換行格式)
    if st.session_state.view == 'details':
        r = st.session_state.selected_row
        st.markdown(f"<h1>{r['Dish_Name']}</h1>", unsafe_allow_html=True)
        if st.button("⬅️ 返回列表"): st.session_state.view = 'main'; st.rerun()
        
        st.markdown('<div class="recipe-card">', unsafe_allow_html=True)
        st.markdown(f"<span class='meal-label'>📅 第 {int(r['Day_Int'])} 天 · {r['Meal']}</span>", unsafe_allow_html=True)
        st.markdown('<hr style="border:1px solid #FFE4E1; margin: 15px 0;">', unsafe_allow_html=True)
        
        # 關鍵修正：.replace('\\n', '\n') 處理 Google Sheet 的換行，並用 st.markdown 顯示
        st.markdown("<span class='meal-label'>🛒 準備食材：</span>", unsafe_allow_html=True)
        st.markdown(str(r['Ingredients']).replace('\\n', '\n'))
        
        st.markdown("<br><span class='meal-label'>👩‍🍳 烹飪步驟：</span>", unsafe_allow_html=True)
        st.markdown(str(r['Method']).replace('\\n', '\n'))
        st.markdown('</div>', unsafe_allow_html=True)

    # B. 📅 媽媽坐月餐單
    elif mode == "📅 媽媽坐月餐單":
        st.markdown("<h1>📅 媽媽坐月餐單</h1>", unsafe_allow_html=True)
        sel_d = st.number_input("🔢 選擇天數", 1, 30, 1)
        day_df = all_df[all_df['Day_Int'] == sel_d]
        for m in ["早餐", "午餐", "下午茶", "糖水", "湯水", "晚餐", "炒米茶"]:
            m_data = day_df[day_df['Meal'].str.contains(m, na=False)]
            for _, row in m_data.iterrows():
                if st.button(f"🥘 {m}：{row['Dish_Name']}", key=f"btn_main_{row.name}"):
                    st.session_state.selected_row = row; st.session_state.view = 'details'; st.rerun()

    # C. 🗓️ 每週總覽
    elif mode == "🗓️ 每週總覽":
        st.markdown("<h1>🗓️ 每週總覽</h1>", unsafe_allow_html=True)
        week = st.selectbox("選擇範圍", ["第 1 週 (1-7)", "第 2 週 (8-14)", "第 3 週 (15-21)", "第 4 週 (22-30)"])
        w_map = {"第 1 週 (1-7)": (1, 7), "第 2 週 (8-14)": (8, 14), "第 3 週 (15-21)": (15, 21), "第 4 週 (22-30)": (22, 30)}
        s, e = w_map[week]
        for d in range(s, e + 1):
            d_data = all_df[all_df['Day_Int'] == d]
            if not d_data.empty:
                items = "".join([f"· <span class='meal-label'>{r['Meal']}</span>: {r['Dish_Name']}<br>" for _, r in d_data.iterrows()])
                st.markdown(f'<div class="week-card"><b style="color:#D87093;">📅 第 {d} 天</b><br>{items}</div>', unsafe_allow_html=True)

    # D. 🛒 採購 Check-list (修正隔離邏輯)
    elif mode == "🛒 採購 Check-list":
        st.markdown("<h1>🛒 採購 Check-list</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📍 睇今日買乜", "📅 一次過買幾日"])
        with t1:
            s_d = st.number_input("選擇天數", 1, 30, 1, key="chk_single")
            target = [s_d]; u_key = f"s_{s_d}"
        with t2:
            c1, c2 = st.columns(2); r1 = c1.number_input("由 Day", 1, 30, 1, key="chk_r1"); r2 = c2.number_input("至 Day", 1, 30, r1+1, key="chk_r2")
            target = list(range(r1, r2 + 1)); u_key = f"r_{r1}_{r2}"
        
        data_sum = get_shopping_summary(all_df, target)
        for cat in ["食材", "調味"]:
            if data_sum[cat]:
                st.markdown(f'<div class="section-title">{"🍎 主要食材" if cat=="食材" else "🧂 檢查調味"}</div>', unsafe_allow_html=True)
                st.markdown('<div class="check-card">', unsafe_allow_html=True)
                for name, info in data_sum[cat].items():
                    # 再次確保 details 入面只有符合 target_days 嘅內容
                    final_details = [d for d in info["details"] if any(f"Day {t} " in d for t in target)]
                    if not final_details: continue
                    
                    details_str = " / ".join(list(dict.fromkeys(final_details)))
                    label = f"{name} (x{len(final_details)})" if len(final_details) > 1 else name
                    st.checkbox(label, key=f"chk_{u_key}_{name}_{cat}")
                    st.markdown(f'<span class="usage-text">📍 {details_str}</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    # E. 🔍 食譜大百科 (維持分類)
    elif mode == "🔍 食譜大百科":
        st.markdown("<h1>🔍 食譜大百科</h1>", unsafe_allow_html=True)
        q = st.text_input("🔍 搜尋食材或菜名：")
        if q:
            s_df = all_df[all_df['Dish_Name'].str.contains(q, na=False, case=False) | all_df['Ingredients'].str.contains(q, na=False, case=False)]
            for _, row in s_df.iterrows():
                if st.button(f"✨ Day {int(row['Day_Int'])} | {row['Dish_Name']}", key=f"q_search_{row.name}"):
                    st.session_state.selected_row = row; st.session_state.view = 'details'; st.rerun()
        st.markdown("<hr>", unsafe_allow_html=True)
        cats = {"🥣 營養粥類": ["粥"], "🍝 麵食/主食": ["麵", "米粉", "河粉", "飯"], "🥘 精選菜式": ["雞", "豬", "牛", "魚", "蛋"], "🥣 滋補湯水": ["湯"], "🍵 甜品/炒米茶": ["糖水", "茶"]}
        for cat_name, kw in cats.items():
            with st.expander(cat_name):
                cat_df = all_df[all_df['Dish_Name'].str.contains('|'.join(kw), na=False, case=False)]
                unique_dishes = cat_df.drop_duplicates(subset=['Dish_Name'])
                for _, row in unique_dishes.iterrows():
                    if st.button(f"▪️ {row['Dish_Name']}", key=f"cat_v2_{cat_name}_{row.name}"):
                        st.session_state.selected_row = row; st.session_state.view = 'details'; st.rerun()
else:
    st.error("載入失敗。")
