import streamlit as st
import pandas as pd
import re
from datetime import date, timedelta

# --- 1. 樣式設定 ---
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
    .recipe-card, .check-card, .week-card {
        background-color: white !important; padding: 25px; border-radius: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px;
        border: 2px solid #FFE4E1;
    }
    .usage-text { color: #888888 !important; font-size: 0.9rem; padding: 8px 12px; background: #FFF9FA; border-radius: 10px; margin: 5px 0; display: block; }
    .section-title { color: #D87093 !important; font-size: 1.3rem; font-weight: bold; margin: 20px 0 10px 0; border-left: 5px solid #FFB6C1; padding-left: 10px; }
    [data-testid="stSidebar"] { background-color: #FFE4E1; }
    [data-testid="stSidebar"] * { color: #D87093 !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 設定手術日期 (Day 0) ---
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

# --- 4. 輔助函數：日期轉 Day ---
def date_to_day(selected_date):
    delta = (selected_date - SURGERY_DATE).days
    return delta

def day_to_date(day_num):
    return SURGERY_DATE + timedelta(days=day_num)

# --- 5. 採購邏輯 ---
def get_shopping_summary(df_to_process, target_days):
    clean_df = df_to_process[df_to_process['Day_Int'].isin(target_days)].copy()
    sea_kws = ['鹽', '糖', '油', '醬', '醋', '粉', '汁', '酒', '蜜', '豉', '麻', '水', '露']
    summary = {"食材": {}, "調味": {}}
    
    for _, row in clean_df.iterrows():
        dish = row['Dish_Name']
        d_val = int(row['Day_Int'])
        raw_ings = str(row['Ingredients']).replace('\n', '、').replace(',', '、').replace('，', '、')
        items = [i.strip() for i in raw_ings.split('、') if i.strip()]
        
        for raw in items:
            raw = re.sub(r'^\d+[\.\s]*', '', raw)
            if not raw or raw == 'nan': continue
            base_name = re.split(r'(\d+|半|少許|適量|份|g|克|兩|斤|包|隻|支|盒|ml)', raw)[0].strip()
            base_name = re.sub(r'[\(（].*[\)）]', '', base_name)
            if not base_name: continue
            
            amount = raw.replace(base_name, "").strip()
            cat = "調味" if any(kw in base_name for kw in sea_kws) else "食材"
            if base_name not in summary[cat]: summary[cat][base_name] = {"details": []}
            
            # 同時顯示日期
            d_str = day_to_date(d_val).strftime("%m/%d")
            summary[cat][base_name]["details"].append(f"📍 {d_str} (Day {d_val}) | {dish} ({amount if amount else '適量'})")
    return summary

# --- 6. 狀態管理 ---
if 'view' not in st.session_state: st.session_state.view = 'main'
if 'selected_row' not in st.session_state: st.session_state.selected_row = None
if 'last_mode' not in st.session_state: st.session_state.last_mode = "📅 媽媽坐月餐單"
if 'current_date' not in st.session_state: st.session_state.current_date = date(2026, 4, 14) # 預設術後第一日

# --- 7. 主程式 ---
if all_df is not None:
    st.sidebar.title("🌸 功能導航")
    mode = st.sidebar.radio("跳轉至：", ["📅 媽媽坐月餐單", "🗓️ 每週總覽", "🛒 採購 Check-list", "🔍 食譜大百科"])

    if mode != st.session_state.last_mode:
        st.session_state.view = 'main'
        st.session_state.last_mode = mode
        st.rerun()

    # A. 詳情頁
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

    # B. 📅 媽媽坐月餐單 (日期選擇版)
    elif mode == "📅 媽媽坐月餐單":
        st.markdown("<h1>📅 媽媽坐月餐單</h1>", unsafe_allow_html=True)
        
        # 日期選擇器
        picked_date = st.date_input("📅 選擇日期", value=st.session_state.current_date, min_value=SURGERY_DATE)
        st.session_state.current_date = picked_date
        
        # 計算 Day
        target_day = date_to_day(picked_date)
        
        if target_day == 0:
            st.warning("今天是手術當天 (Day 0)，建議遵循醫護人員禁食或流質飲食指示。")
        
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

    # C. 🗓️ 每週總覽 (日期標註)
    elif mode == "🗓️ 每週總覽":
        st.markdown("<h1>🗓️ 每週總覽</h1>", unsafe_allow_html=True)
        week = st.selectbox("選擇週數", ["第 1 週 (Day 1-7)", "第 2 週 (Day 8-14)", "第 3 週 (Day 15-21)", "第 4 週 (Day 22-30)"])
        w_map = {"第 1 週 (Day 1-7)": (1, 7), "第 2 週 (Day 8-14)": (8, 14), "第 3 週 (Day 15-21)": (15, 21), "第 4 週 (Day 22-30)": (22, 30)}
        s, e = w_map[week]
        
        for d in range(s, e + 1):
            d_data = all_df[all_df['Day_Int'] == d]
            d_real = day_to_date(d).strftime("%m/%d")
            if not d_data.empty:
                items = "".join([f"· <span class='meal-label'>{r['Meal']}</span>: {r['Dish_Name']}<br>" for _, r in d_data.iterrows()])
                st.markdown(f'<div class="week-card"><b style="color:#D87093;">📅 {d_real} (Day {d})</b><br>{items}</div>', unsafe_allow_html=True)

    # D. 🛒 採購 Check-list (日期選擇版)
    elif mode == "🛒 採購 Check-list":
        st.markdown("<h1>🛒 採購 Check-list</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📍 按日期顯示", "📅 一次過買幾日"])
        
        with t1:
            chk_date = st.date_input("選擇採購日期", value=st.session_state.current_date, key="chk_date_v4")
            target_days = [date_to_day(chk_date)]
        with t2:
            c1, c2 = st.columns(2)
            d_start = c1.date_input("由日期", value=SURGERY_DATE + timedelta(days=1))
            d_end = c2.date_input("至日期", value=SURGERY_DATE + timedelta(days=3))
            
            # 將日期範圍轉回 Day List
            s_day = date_to_day(d_start)
            e_day = date_to_day(d_end)
            target_days = list(range(max(0, s_day), max(0, e_day) + 1))
        
        data_sum = get_shopping_summary(all_df, target_days)
        
        for cat in ["食材", "調味"]:
            if data_sum[cat]:
                st.markdown(f'<div class="section-title">{"🍎 主要食材" if cat=="食材" else "🧂 檢查調味"}</div>', unsafe_allow_html=True)
                st.markdown('<div class="check-card">', unsafe_allow_html=True)
                for name, info in data_sum[cat].items():
                    final_details = list(dict.fromkeys(info["details"]))
                    col_cb, col_exp = st.columns([0.15, 0.85])
                    with col_cb: st.checkbox("", key=f"cb_v4_{name}_{cat}_{target_days[0]}")
                    with col_exp:
                        with st.expander(f"{name} (共 {len(final_details)} 份)"):
                            for d in final_details:
                                st.markdown(f'<span class="usage-text">{d}</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    # E. 🔍 食譜大百科
    elif mode == "🔍 食譜大百科":
        st.markdown("<h1>🔍 食譜大百科</h1>", unsafe_allow_html=True)
        q = st.text_input("🔍 搜尋食材或菜名：")
        if q:
            s_df = all_df[all_df['Dish_Name'].str.contains(q, na=False, case=False)]
            for _, row in s_df.iterrows():
                if st.button(f"✨ Day {int(row['Day_Int'])} | {row['Dish_Name']}", key=f"q_v4_{row.name}"):
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
                    if st.button(f"▪️ {row['Dish_Name']}", key=f"cat_v4_{cat_name}_{row.name}"):
                        st.session_state.selected_row = row
                        st.session_state.view = 'details'
                        st.rerun()
else:
    st.error("載入失敗。")
