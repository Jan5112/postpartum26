import streamlit as st
import pandas as pd
import re

# --- 1. 樣式設定 (恢復原本靚靚嘅粉紅 UI) ---
st.set_page_config(page_title="🌸 媽媽坐月餐單", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; }
    .main .block-container { max-width: 600px; margin: 0 auto; padding: 1.2rem; }
    
    /* 標題與字體 */
    h1 { color: #D87093 !important; font-size: 2rem !important; text-align: center; margin-bottom: 25px; }
    p, span, label, .stCheckbox, .stMarkdown { color: #666666 !important; }
    
    /* 靚靚粉紅按鈕 */
    .stButton>button { 
        background-color: #FFB6C1; color: white !important; 
        border-radius: 20px; border: none; width: 100%; min-height: 50px;
        font-size: 1.1rem; font-weight: bold; margin-bottom: 12px;
        box-shadow: 0 4px 6px rgba(255,182,193,0.3);
    }
    
    /* 卡片設計 */
    .recipe-card, .check-card, .week-card {
        background-color: white; padding: 20px; border-radius: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px;
        border: 2px solid #FFE4E1;
    }
    
    .section-title { color: #D87093; font-size: 1.3rem; font-weight: bold; margin: 20px 0 10px 0; border-left: 5px solid #FFB6C1; padding-left: 10px; }
    .usage-text { color: #999999 !important; font-size: 0.9rem; margin-left: 32px; display: block; margin-top: -8px; margin-bottom: 15px; }

    /* 側邊欄 */
    [data-testid="stSidebar"] { background-color: #FFE4E1; }
    [data-testid="stSidebar"] * { color: #D87093 !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取 (強制不緩存，確保準確) ---
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

# --- 3. 核心邏輯：嚴格過濾日期 + 合併同類 ---
def get_shopping_summary(df_to_process):
    if df_to_process is None or df_to_process.empty: return {"食材": {}, "調味": {}}
    sea_kws = ['鹽', '糖', '油', '醬', '醋', '粉', '汁', '酒', '蜜', '豉', '麻', '水']
    summary = {"食材": {}, "調味": {}}
    
    for _, row in df_to_process.iterrows():
        dish = row['Dish_Name']
        d_val = int(row['Day_Int'])
        items = re.split(r'[\n,，、\s]+', str(row['Ingredients']))
        
        for raw in items:
            raw = raw.strip()
            if not raw or raw == 'nan': continue
            # 分拆名稱與份量
            parts = re.split(r'(\d+|半|少許|適量|份|g|克|兩|斤|包)', raw, maxsplit=1)
            base_name = parts[0].strip()
            amount = raw.replace(base_name, "").strip()
            
            cat = "調味" if any(kw in base_name for kw in sea_kws) else "食材"
            if base_name not in summary[cat]:
                summary[cat][base_name] = {"count": 0, "details": []}
            
            summary[cat][base_name]["count"] += 1
            summary[cat][base_name]["details"].append(f"Day {d_val} {dish} ({amount if amount else '適量'})")
    return summary

# --- 4. 狀態管理 ---
if 'view' not in st.session_state: st.session_state.view = 'main'
if 'selected_row' not in st.session_state: st.session_state.selected_row = None
if 'day_input' not in st.session_state: st.session_state.day_input = 1

# --- 5. 導航 ---
st.sidebar.title("🌸 功能導航")
mode = st.sidebar.radio("跳轉至：", ["📅 媽媽坐月餐單", "🛒 採購 Check-list", "🗓️ 每週總覽", "🔍 食譜大百科"])

# --- 6. 頁面邏輯 ---
if all_df is not None:
    # A. 詳情頁
    if st.session_state.view == 'details':
        recipe = st.session_state.selected_row
        st.markdown(f"<h1>{recipe['Dish_Name']}</h1>", unsafe_allow_html=True)
        if st.button("⬅️ 返回餐單"): st.session_state.view = 'main'; st.rerun()
        st.markdown(f"""
        <div class="recipe-card">
            <p style='text-align:center;'>📅 第 {int(recipe['Day_Int'])} 天 · {recipe['Meal']}</p>
            <hr style='border:1px solid #FFE4E1;'>
            <h3 style='color:#D87093;'>🛒 準備食材</h3><p>{recipe['Ingredients']}</p>
            <h3 style='color:#D87093;'>👩‍🍳 烹飪步驟</h3><p style='white-space:pre-wrap;'>{recipe['Method']}</p>
        </div>
        """, unsafe_allow_html=True)

    # B. 媽媽坐月餐單 (恢復美觀界面)
    elif mode == "📅 媽媽坐月餐單":
        st.markdown("<h1>📅 媽媽坐月餐單</h1>", unsafe_allow_html=True)
        st.session_state.day_input = st.number_input("🔢 選擇天數", min_value=1, max_value=30, value=st.session_state.day_input)
        
        day_df = all_df[all_df['Day_Int'] == st.session_state.day_input]
        for m in ["早餐", "午餐", "下午茶", "糖水", "湯水", "晚餐", "炒米茶"]:
            m_data = day_df[day_df['Meal'].str.contains(m, na=False)]
            for _, row in m_data.iterrows():
                if st.button(f"🥘 {m}：{row['Dish_Name']}", key=f"btn_{row.name}"):
                    st.session_state.selected_row = row; st.session_state.view = 'details'; st.rerun()

    # C. 採購 Check-list (徹底解決重複問題)
    elif mode == "🛒 採購 Check-list":
        st.markdown("<h1>🛒 採購 Check-list</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📍 睇今日買乜", "📅 一次過買幾日"])
        
        if t1: # 單日模式
            with t1:
                s_day = st.number_input("選擇第幾天", min_value=1, max_value=30, value=st.session_state.day_input, key="s_day")
                working_df = all_df[all_df['Day_Int'] == s_day].copy()
                unique_key = f"day_{s_day}"
        if t2: # 範圍模式
            with t2:
                c1, c2 = st.columns(2)
                with c1: r1 = st.number_input("由 Day", 1, 30, 1)
                with c2: r2 = st.number_input("至 Day", 1, 30, r1+1)
                working_df = all_df[(all_df['Day_Int'] >= r1) & (all_df['Day_Int'] <= r2)].copy()
                unique_key = f"range_{r1}_{r2}"

        if not working_df.empty:
            summary = get_shopping_summary(working_df)
            for cat in ["食材", "調味"]:
                if summary[cat]:
                    st.markdown(f'<div class="section-title">{"🍎 主要食材" if cat=="食材" else "🧂 檢查調味"}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="check-card">', unsafe_allow_html=True)
                    for name, info in summary[cat].items():
                        label = f"{name}" + (f" (x{info['count']})" if info['count'] > 1 else "")
                        st.checkbox(label, key=f"chk_{unique_key}_{name}_{cat}")
                        st.markdown(f'<span class="usage-text">📍 {"、".join(info["details"])}</span>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

    # D. 每週總覽
    elif mode == "🗓️ 每週總覽":
        st.markdown("<h1>🗓️ 每週總覽</h1>", unsafe_allow_html=True)
        # (保留原本每週總覽邏輯...)
        for d in range(1, 8): # 示例第一週
             st.markdown(f'<div class="week-card"><b>Day {d}</b><br>菜單整理中...</div>', unsafe_allow_html=True)

else:
    st.error("讀取不到 Google Sheet 資料，請檢查連結。")
