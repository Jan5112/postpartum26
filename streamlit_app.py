import streamlit as st
import pandas as pd
import re

# --- 1. 樣式設定 (樣式鎖死，確保框框同文字顏色正確) ---
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

# --- 3. 採購邏輯 (徹底解決滲漏) ---
def get_shopping_summary(df_to_process, target_days):
    # 只取目標日期的資料
    clean_df = df_to_process[df_to_process['Day_Int'].isin(target_days)].copy()
    
    sea_kws = ['鹽', '糖', '油', '醬', '醋', '粉', '汁', '酒', '蜜', '豉', '麻', '水', '露']
    summary = {"食材": {}, "調味": {}}
    
    for _, row in clean_df.iterrows():
        # 雙重檢查：確保日子絕對匹配
        if int(row['Day_Int']) not in target_days: continue
        
        dish = row['Dish_Name']
        d_val = int(row['Day_Int'])
        
        # 拆解食材
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
            
            # 建立食材條目
            if base_name not in summary[cat]:
                summary[cat][base_name] = {"details": []}
            
            # 只加入該食材在「目標日子」內的用途
            summary[cat][base_name]["details"].append(f"📍 Day {d_val} | {dish} ({amount if amount else '適量'})")
            
    return summary

# --- 4. 狀態管理 ---
if 'view' not in st.session_state: st.session_state.view = 'main'
if 'selected_row' not in st.session_state: st.session_state.selected_row = None
if 'last_mode' not in st.session_state: st.session_state.last_mode = "📅 媽媽坐月餐單"

# --- 5. 主程式 ---
if all_df is not None:
    st.sidebar.title("🌸 功能導航")
    mode = st.sidebar.radio("跳轉至：", ["📅 媽媽坐月餐單", "🗓️ 每週總覽", "🛒 採購 Check-list", "🔍 食譜大百科"])

    # 【核心修正】如果使用者在左側換了功能，自動重設視圖為 'main'
    if mode != st.session_state.last_mode:
        st.session_state.view = 'main'
        st.session_state.last_mode = mode
        st.rerun()

    # --- 分流處理 ---
    if st.session_state.view == 'details':
        r = st.session_state.selected_row
        st.markdown(f"<h1>{r['Dish_Name']}</h1>", unsafe_allow_html=True)
        if st.button("⬅️ 返回列表"): 
            st.session_state.view = 'main'
            st.rerun()
        
        # 詳情框內文處理
        ing_html = str(r['Ingredients']).replace('\\n', '<br>').replace('\n', '<br>')
        met_html = str(r['Method']).replace('\\n', '<br>').replace('\n', '<br>')
        
        st.markdown(f"""
        <div class="recipe-card">
            <span class="meal-label">📅 第 {int(r['Day_Int'])} 天 · {r['Meal']}</span>
            <hr style="border:1px solid #FFE4E1; margin: 15px 0;">
            <p><span class="meal-label">🛒 準備食材：</span><br>{ing_html}</p>
            <p><span class="meal-label">👩‍🍳 烹飪步驟：</span><br>{met_html}</p>
        </div>
        """, unsafe_allow_html=True)

    elif mode == "📅 媽媽坐月餐單":
        st.markdown("<h1>📅 媽媽坐月餐單</h1>", unsafe_allow_html=True)
        sel_d = st.number_input("🔢 選擇天數", 1, 30, 1)
        day_df = all_df[all_df['Day_Int'] == sel_d]
        for m in ["早餐", "午餐", "下午茶", "糖水", "湯水", "晚餐", "炒米茶"]:
            m_data = day_df[day_df['Meal'].str.contains(m, na=False)]
            for _, row in m_data.iterrows():
                if st.button(f"🥘 {m}：{row['Dish_Name']}", key=f"btn_m_{row.name}"):
                    st.session_state.selected_row = row
                    st.session_state.view = 'details'
                    st.rerun()

    elif mode == "🗓️ 每週總覽":
        st.markdown("<h1>🗓️ 每週總覽</h1>", unsafe_allow_html=True)
        week = st.selectbox("範圍", ["第 1 週 (1-7)", "第 2 週 (8-14)", "第 3 週 (15-21)", "第 4 週 (22-30)"])
        w_map = {"第 1 週 (1-7)": (1, 7), "第 2 週 (8-14)": (8, 14), "第 3 週 (15-21)": (15, 21), "第 4 週 (22-30)": (22, 30)}
        s, e = w_map[week]
        for d in range(s, e + 1):
            d_data = all_df[all_df['Day_Int'] == d]
            if not d_data.empty:
                items = "".join([f"· <span class='meal-label'>{r['Meal']}</span>: {r['Dish_Name']}<br>" for _, r in d_data.iterrows()])
                st.markdown(f'<div class="week-card"><b style="color:#D87093;">📅 第 {d} 天</b><br>{items}</div>', unsafe_allow_html=True)

    elif mode == "🛒 採購 Check-list":
        st.markdown("<h1>🛒 採購 Check-list</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📍 睇今日買乜", "📅 一次過買幾日"])
        with t1:
            s_d = st.number_input("選擇天數", 1, 30, 1, key="s_d_input")
            target = [s_d]
        with t2:
            c1, c2 = st.columns(2)
            r1 = c1.number_input("由 Day", 1, 30, 1, key="r1_input")
            r2 = c2.number_input("至 Day", 1, 30, r1+1, key="r2_input")
            target = list(range(int(r1), int(r2) + 1))
        
        data_sum = get_shopping_summary(all_df, target)
        for cat in ["食材", "調味"]:
            if data_sum[cat]:
                st.markdown(f'<div class="section-title">{"🍎 主要食材" if cat=="食材" else "🧂 檢查調味"}</div>', unsafe_allow_html=True)
                st.markdown('<div class="check-card">', unsafe_allow_html=True)
                for name, info in data_sum[cat].items():
                    # 這裡再次過濾 details，確保只顯示符合選定日子的原因
                    final_details = list(dict.fromkeys(info["details"]))
                    if not final_details: continue
                    
                    col_cb, col_exp = st.columns([0.1, 0.9])
                    with col_cb: 
                        st.checkbox("", key=f"cb_{name}_{cat}_{target[0]}")
                    with col_exp:
                        label = f"{name} (共 {len(final_details)} 份)" if len(final_details) > 1 else name
                        with st.expander(label):
                            for d in final_details:
                                st.markdown(f'<span class="usage-text">{d}</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

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
            with st.expander(cat_name):
                cat_df = all_df[all_df['Dish_Name'].str.contains('|'.join(kw), na=False, case=False)]
                unique_dishes = cat_df.drop_duplicates(subset=['Dish_Name'])
                for _, row in unique_dishes.iterrows():
                    if st.button(f"▪️ {row['Dish_Name']}", key=f"cat_{cat_name}_{row.name}"):
                        st.session_state.selected_row = row
                        st.session_state.view = 'details'
                        st.rerun()
else:
    st.error("載入失敗。")
