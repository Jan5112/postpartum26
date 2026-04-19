import streamlit as st
import pandas as pd
import re
from datetime import date, timedelta

# --- 1. 樣式設定 (保持粉紅與深灰對比) ---
st.set_page_config(page_title="🌸 媽媽坐月餐單", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; }
    .main .block-container { max-width: 600px; margin: 0 auto; padding: 1.2rem; }
    
    h1, h2, h3 { color: #D87093 !important; text-align: center; font-weight: bold !important; }
    .meal-label { color: #FF99AA !important; font-weight: bold !important; font-size: 1.1rem; }
    
    p, span, label, .stCheckbox, .stMarkdown, div { color: #555555 !important; }
    
    .stButton>button { 
        background-color: #FFB6C1; color: white !important; 
        border-radius: 20px; border: none; width: 100%; min-height: 50px;
        font-size: 1.1rem; font-weight: bold; margin-bottom: 12px;
    }
    
    .recipe-card, .week-card {
        background-color: white !important; padding: 25px; border-radius: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px;
        border: 2px solid #FFE4E1;
    }
    
    .section-title { color: #D87093 !important; font-size: 1.3rem; font-weight: bold; margin: 20px 0 10px 0; border-left: 5px solid #FFB6C1; padding-left: 10px; }
    
    [data-testid="stSidebar"] { background-color: #FFE4E1; }
    [data-testid="stSidebarContent"] { padding-top: 2rem; }
    [data-testid="stSidebar"] * { color: #D87093 !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 設定基準日期 (Day 0) ---
SURGERY_DATE = date(2026, 4, 13)

# --- 3. 數據讀取 ---
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

# --- 4. 輔助函數 ---
def date_to_day(selected_date):
    return (selected_date - SURGERY_DATE).days

def day_to_date(day_num):
    return SURGERY_DATE + timedelta(days=day_num)

# --- 5. 狀態管理 ---
if 'view' not in st.session_state: st.session_state.view = 'main'
if 'selected_row' not in st.session_state: st.session_state.selected_row = None
if 'last_mode' not in st.session_state: st.session_state.last_mode = "📅 媽媽坐月餐單"
if 'current_date' not in st.session_state: st.session_state.current_date = date(2026, 4, 14)

# --- 6. 主程式 ---
if all_df is not None:
    st.sidebar.title("🌸 功能導航")
    # 這裡已將「採購 Check-list」選項刪除
    mode = st.sidebar.radio("跳轉至：", ["📅 媽媽坐月餐單", "🗓️ 每週總覽", "🔍 食譜大百科"])

    # 切換功能時重置頁面
    if mode != st.session_state.last_mode:
        st.session_state.view = 'main'
        st.session_state.last_mode = mode
        st.rerun()

    # A. 詳情頁 (食譜內容)
    if st.session_state.view == 'details':
        r = st.session_state.selected_row
        d_int = int(r['Day_Int'])
        d_real = day_to_date(d_int).strftime("%Y-%m-%d")
        
        st.markdown(f"<h1>{r['Dish_Name']}</h1>", unsafe_allow_html=True)
        if st.button("⬅️ 返回列表"): 
            st.session_state.view = 'main'
            st.rerun()
        
        ing_html = str(r['Ingredients']).replace('\\n', '<br>').replace('\n', '<br>')
        met_html = str(r['Method']).replace('\\n', '<br>').replace('\n', '<br>')
        
        st.markdown(f"""
        <div class="recipe-card">
            <span class="meal-label">📅 {d_real} (術後 Day {d_int}) · {r['Meal']}</span>
            <hr style="border:1px solid #FFE4E1; margin: 15px 0;">
            <p><span class="meal-label">🛒 準備食材：</span><br>{ing_html}</p>
            <p><span class="meal-label">👩‍🍳 烹飪步驟：</span><br>{met_html}</p>
        </div>
        """, unsafe_allow_html=True)

    # B. 📅 媽媽坐月餐單
    elif mode == "📅 媽媽坐月餐單":
        st.markdown("<h1>📅 媽媽坐月餐單</h1>", unsafe_allow_html=True)
        
        picked_date = st.date_input("📅 選擇日期", value=st.session_state.current_date, min_value=SURGERY_DATE)
        st.session_state.current_date = picked_date
        
        target_day = date_to_day(picked_date)
        
        if target_day == 0:
            st.warning("今天是手術當天 (Day 0)，建議遵循醫護指示。")
        
        st.markdown(f"### 🗓️ {picked_date.strftime('%Y年%m月%d日')} (術後 Day {target_day})")
        
        day_df = all_df[all_df['Day_Int'] == target_day]
        
        if day_df.empty and target_day > 0:
            st.info("暫無此日期的餐單數據。")
        else:
            for m in ["早餐", "午餐", "下午茶", "糖水", "湯水", "晚餐", "炒米茶"]:
                m_data = day_df[day_df['Meal'].str.contains(m, na=False)]
                for _, row in m_data.iterrows():
                    if st.button(f"🥘 {m}：{row['Dish_Name']}", key=f"btn_m_{row.name}"):
                        st.session_state.selected_row = row
                        st.session_state.view = 'details'
                        st.rerun()

    # C. 🗓️ 每週總覽
    elif mode == "🗓️ 每週總覽":
        st.markdown("<h1>🗓️ 每週總覽</h1>", unsafe_allow_html=True)
        week = st.selectbox("選擇週數", ["第 1 週 (Day 1-7)", "第 2 週 (Day 8-14)", "第 3 週 (15-21)", "第 4 週 (22-30)"])
        w_map = {"第 1 週 (Day 1-7)": (1, 7), "第 2 週 (Day 8-14)": (8, 14), "第 3 週 (Day 15-21)": (15, 21), "第 4 週 (Day 22-30)": (22, 30)}
        s, e = w_map[week]
        
        for d in range(s, e + 1):
            d_data = all_df[all_df['Day_Int'] == d]
            d_real = day_to_date(d).strftime("%m/%d")
            if not d_data.empty:
                items = "".join([f"· <span class='meal-label'>{r['Meal']}</span>: {r['Dish_Name']}<br>" for _, r in d_data.iterrows()])
                st.markdown(f'<div class="week-card"><b style="color:#D87093;">📅 {d_real} (Day {d})</b><br>{items}</div>', unsafe_allow_html=True)

    # D. 🔍 食譜大百科
    elif mode == "🔍 食譜大百科":
        st.markdown("<h1>🔍 食譜大百科</h1>", unsafe_allow_html=True)
        q = st.text_input("🔍 搜尋食材或菜名：")
        if q:
            s_df = all_df[all_df['Dish_Name'].str.contains(q, na=False, case=False)]
            for _, row in s_df.iterrows():
                if st.button(f"✨ Day {int(row['Day_Int'])} | {row['Dish_Name']}", key=f"q_{row.name}"):
                    st.session_state.selected_row = row
                    st.session_state.view = 'details'
                    st.rerun()
        st.markdown("<hr>", unsafe_allow_html=True)
        cats = {"🥣 營養粥類": ["粥"], "🍝 麵食/主食": ["麵", "米粉", "河粉", "飯"], "🥘 精選菜式": ["雞", "豬", "牛", "魚", "蛋"], "🥣 滋補湯水": ["湯"], "🍵 甜品/炒米茶": ["糖水", "茶"]}
        for cat_name, kw in cats.items():
            with st.expander(cat_name, expanded=False):
                cat_df = all_df[all_df['Dish_Name'].str.contains('|'.join(kw), na=False, case=False)]
                unique_dishes = cat_df.drop_duplicates(subset=['Dish_Name'])
                for _, row in unique_dishes.iterrows():
                    if st.button(f"▪️ {row['Dish_Name']}", key=f"cat_{cat_name}_{row.name}"):
                        st.session_state.selected_row = row
                        st.session_state.view = 'details'
                        st.rerun()
else:
    st.error("載入失敗，請檢查資料來源。")
