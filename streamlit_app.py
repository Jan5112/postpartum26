import streamlit as st
import pandas as pd

# --- 1. 手機優化版樣式 ---
st.set_page_config(page_title="🌸 媽咪 30 日坐月食譜", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; } 
    /* 手機版字體縮放 */
    html { font-size: 14px; }
    h1 { font-size: 1.8rem !important; color: #D87093 !important; }
    
    .stButton>button { 
        background-color: #FFB6C1; color: white !important; 
        border-radius: 12px; border: none; width: 100%; height: 45px;
        margin-bottom: 5px; font-size: 14px;
    }
    
    /* 詳情頁卡片：縮小 Padding 方便手機顯示 */
    .recipe-card {
        background-color: white; padding: 15px; border-radius: 15px; 
        box-shadow: 0 5px 15px rgba(255,182,193,0.1); 
        border-left: 8px solid #FFB6C1;
    }

    /* 令表格喺手機可以左右滑動 */
    .stTable { overflow-x: auto; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取 (保持不變) ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZesALwN_63zG-ULARgSgu2zX44qpxYud8Y4qco_4IFI/edit?usp=sharing"
CSV_URL = SHEET_URL.split('/edit')[0] + '/export?format=csv'

@st.cache_data(ttl=10)
def load_data():
    try:
        data = pd.read_csv(CSV_URL)
        data.columns = data.columns.str.strip()
        col_map = {'天數': 'Day', 'Day': 'Day', '餐次': 'Meal', 'Meal': 'Meal', '菜品名': 'Dish_Name', 'Dish_Name': 'Dish_Name', '食材': 'Ingredients', '做法': 'Method'}
        data = data.rename(columns=col_map)
        data['Day'] = pd.to_numeric(data['Day'], errors='coerce')
        return data.dropna(subset=['Day'])
    except: return None

df = load_data()

# --- 3. 狀態管理 ---
if 'view' not in st.session_state: st.session_state.view = 'main'
if 'selected_row' not in st.session_state: st.session_state.selected_row = None
if 'day_input' not in st.session_state: st.session_state.day_input = 1

# --- 4. 側邊欄 ---
st.sidebar.title("🌸 選單")
mode = st.sidebar.radio("跳轉至：", ["📅 每日餐單", "🗓️ 每週總覽", "🔍 按類型搵"])

# --- 5. 詳情頁面 ---
if st.session_state.view == 'details':
    recipe = st.session_state.selected_row
    if st.button("⬅️ 返回"):
        st.session_state.view = 'main'; st.rerun()
    st.markdown(f"""<div class="recipe-card">
        <h1>{recipe['Dish_Name']}</h1>
        <p>📅 第 {int(recipe['Day'])} 天 · {recipe['Meal']}</p><hr>
        <b style='color:#FFB6C1;'>🛒 食材：</b><p>{recipe['Ingredients']}</p>
        <b style='color:#FFB6C1;'>👩‍🍳 做法：</b><p>{str(recipe['Method']).replace('\\n', '<br>')}</p>
    </div>""", unsafe_allow_html=True)

# --- 6. 每日餐單 ---
elif mode == "📅 每日餐單":
    st.title("📅 每日餐單")
    # 手機版會自動將 columns 疊成上下
    c1, c2 = st.columns([2, 1])
    with c1:
        d_slider = st.select_slider("💖 選擇天數", options=list(range(1, 31)), value=st.session_state.day_input)
    with c2:
        d_num = st.number_input("🔢 輸入天數", min_value=1, max_value=30, value=d_slider)
    
    st.session_state.day_input = d_num
    day_df = df[df['Day'] == d_num]
    
    for m in ["早餐", "午餐", "下午茶", "糖水", "湯水", "晚餐", "炒米茶"]:
        m_data = day_df[day_df['Meal'].str.contains(m, na=False)]
        if not m_data.empty:
            row = m_data.iloc[0]
            if st.button(f"🥘 {m}：{row['Dish_Name']}", key=f"d_{row.name}"):
                st.session_state.selected_row = row; st.session_state.view = 'details'; st.rerun()

# --- 7. 每週總覽 ---
elif mode == "🗓️ 每週總覽":
    st.title("🗓️ 每週總覽")
    week = st.selectbox("選擇星期：", ["第 1 週 (Day 1-7)", "第 2 週 (Day 8-14)", "第 3 週 (Day 15-21)", "第 4 週 (Day 22-30)"])
    week_map = {"第 1 週 (Day 1-7)": (1, 7), "第 2 週 (Day 8-14)": (8, 14), "第 3 週 (Day 15-21)": (15, 21), "第 4 週 (Day 22-30)": (22, 30)}
    start, end = week_map[week]
    
    # 建立精簡版表格
    week_df = df[(df['Day'] >= start) & (df['Day'] <= end)]
    table_list = []
    for m in ["早餐", "午餐", "下午茶", "糖水", "湯水", "晚餐", "炒米茶"]:
        row = {"餐次": m}
        for d in range(start, end+1):
            t = week_df[(week_df['Day'] == d) & (week_df['Meal'].str.contains(m, na=False))]
            row[f"D{d}"] = t['Dish_Name'].iloc[0] if not t.empty else "-"
        table_list.append(row)
    st.table(pd.DataFrame(table_list).set_index('餐次'))

# --- 8. 按類型搵 ---
else:
    st.title("🔍 食譜大百科")
    cats = {"🥣 粥品": "粥", "🍜 麵食": "麵|粉", "🍚 飯食": "飯", "🍲 湯水": "湯", "🍵 茶飲": "茶"}
    for name, kw in cats.items():
        cat_df = df[df['Dish_Name'].str.contains(kw, na=False)]
        if not cat_df.empty:
            with st.expander(name):
                for i, row in cat_df.iterrows():
                    if st.button(f"✨ {row['Dish_Name']}", key=f"c_{i}"):
                        st.session_state.selected_row = row; st.session_state.view = 'details'; st.rerun()
