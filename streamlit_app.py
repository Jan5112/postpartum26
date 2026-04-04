import streamlit as st
import pandas as pd

# --- 1. 樣式設定 (加入置中對齊邏輯) ---
st.set_page_config(page_title="🌸 媽媽坐月餐單", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; } 
    html { font-size: 14px; }
    
    /* 全局文字置中 */
    .main .block-container {
        max-width: 800px; /* 限制寬度，令電腦睇落唔會太散 */
        margin: 0 auto;
        text-align: center;
    }
    
    /* 標題置中 */
    h1 { 
        font-size: 2rem !important; 
        color: #D87093 !important; 
        text-align: center !important;
        margin-bottom: 20px !important;
    }
    
    /* 按鈕樣式 (置中並限制寬度) */
    .stButton>button { 
        background-color: #FFB6C1; color: white !important; 
        border-radius: 15px; border: none; 
        width: 100%; max-width: 400px; /* 電腦版唔會太闊，手機版會自動填滿 */
        height: 50px;
        margin: 5px auto !important; 
        display: block;
        font-size: 16px;
        font-weight: bold;
    }
    .stButton>button:hover { background-color: #FF9EB5; color: white !important; }
    
    /* 詳情頁卡片樣式 (內容改返左對齊方便閱讀) */
    .recipe-card {
        background-color: white; padding: 25px; border-radius: 15px; 
        box-shadow: 0 5px 15px rgba(255,182,193,0.1); 
        border-left: 10px solid #FFB6C1;
        text-align: left !important; /* 做法同食材左對齊比較好睇 */
    }
    
    .recipe-meta { color: #A0A0A0 !important; font-size: 1.1rem; text-align: center; }
    .recipe-content { color: #666666 !important; line-height: 1.8; font-size: 1.05rem; }
    
    /* 滑桿置中調整 */
    .stSelectSlider, .stNumberInput {
        text-align: left; /* 控件內部維持左對齊比較標準 */
    }

    [data-testid="stSidebar"] { background-color: #FFE4E1; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZesALwN_63zG-ULARgSgu2zX44qpxYud8Y4qco_4IFI/edit?usp=sharing"
CSV_URL = SHEET_URL.split('/edit')[0] + '/export?format=csv'

@st.cache_data(ttl=10)
def load_data():
    try:
        data = pd.read_csv(CSV_URL)
        data.columns = data.columns.str.strip()
        col_map = {'天數': 'Day', 'Day': 'Day', '餐次': 'Meal', 'Meal': 'Meal', '菜品名': 'Dish_Name', 'Dish_Name': 'Dish_Name', '食材': 'Ingredients', '做法': 'Method'}
        data = data.rename(columns=col_map)
        for col in ['Day', 'Meal', 'Dish_Name', 'Ingredients', 'Method']:
            if col in data.columns:
                data[col] = data[col].astype(str).str.strip().replace('nan', '')
        return data
    except: return None

df = load_data()

# --- 3. 狀態管理 ---
if 'view' not in st.session_state: st.session_state.view = 'main'
if 'selected_row' not in st.session_state: st.session_state.selected_row = None
if 'day_input' not in st.session_state: st.session_state.day_input = 1

# --- 4. 側邊欄 ---
st.sidebar.title("🌸 選單")
mode = st.sidebar.radio("跳轉至：", ["📅 媽媽坐月餐單", "🗓️ 每週總覽", "🔍 食譜大百科"], index=0)

# --- 5. 詳情頁面 ---
if st.session_state.view == 'details':
    recipe = st.session_state.selected_row
    st.markdown(f"<h1 style='text-align:center;'>{recipe['Dish_Name']}</h1>", unsafe_allow_html=True)
    if st.button("⬅️ 返回"):
        st.session_state.view = 'main'; st.rerun()
    
    st.markdown(f"""
    <div class="recipe-card">
        <p class="recipe-meta">📅 第 {recipe['Day']} 天 · {recipe['Meal']}</p>
        <hr style='border: 1px solid #FFF0F5;'>
        <h3 style='color:#FFB6C1;'>🛒 準備食材</h3>
        <div class="recipe-content">{recipe['Ingredients']}</div>
        <br>
        <h3 style='color:#FFB6C1;'>👩‍🍳 烹飪步驟</h3>
        <div class="recipe-content">{recipe['Method'].replace('\\n', '<br>').replace('\n', '<br>')}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 6. 媽媽坐月餐單 (置中版) ---
elif mode == "📅 媽媽坐月餐單":
    st.markdown("<h1>📅 媽媽坐月餐單</h1>", unsafe_allow_html=True)
    
    # 令 Slider 同 NumberInput 喺中間
    c1, c2, c3 = st.columns([1, 4, 1])
    with c2:
        try: curr_day = int(st.session_state.day_input)
        except: curr_day = 1
        
        d_slider = st.select_slider("💖 選擇天數", options=[str(i) for i in range(1, 31)], value=str(curr_day))
        d_num = st.number_input("🔢 直接輸入天數", min_value=1, max_value=30, value=int(d_slider))
        st.session_state.day_input = d_num

    st.markdown("<br>", unsafe_allow_html=True)
    
    day_df = df[df['Day'] == str(st.session_state.day_input)]
    meals = ["早餐", "午餐", "下午茶", "糖水", "湯水", "晚餐", "炒米茶"]
    
    for m in meals:
        m_data = day_df[day_df['Meal'].str.contains(m, na=False)]
        if not m_data.empty:
            row = m_data.iloc[0]
            if st.button(f"🥘 {m}：{row['Dish_Name']}", key=f"d_{row.name}"):
                st.session_state.selected_row = row; st.session_state.view = 'details'; st.rerun()
        else:
            st.markdown(f"<p style='color:#CCC; text-align:center;'>◽ {m}：資料準備中...</p>", unsafe_allow_html=True)

# --- 7. 每週總覽 ---
elif mode == "🗓️ 每週總覽":
    st.markdown("<h1>🗓️ 每週總覽</h1>", unsafe_allow_html=True)
    week = st.selectbox("選擇星期：", ["第 1 週 (Day 1-7)", "第 2 週 (Day 8-14)", "第 3 週 (Day 15-21)", "第 4 週 (Day 22-30)"])
    week_map = {"第 1 週 (Day 1-7)": (1, 7), "第 2 週 (Day 8-14)": (8, 14), "第 3 週 (Day 15-21)": (15, 21), "第 4 週 (Day 22-30)": (22, 30)}
    start, end = week_map[week]
    
    table_list = []
    for m in ["早餐", "午餐", "下午茶", "糖水", "湯水", "晚餐", "炒米茶"]:
        row = {"餐次": m}
        for d in range(start, end+1):
            t = df[(df['Day'] == str(d)) & (df['Meal'].str.contains(m, na=False))]
            row[f"D{d}"] = t['Dish_Name'].iloc[0] if not t.empty else "-"
        table_list.append(row)
    st.table(pd.DataFrame(table_list).set_index('餐次'))

# --- 8. 食譜大百科 ---
else:
    st.markdown("<h1>🔍 食譜大百科</h1>", unsafe_allow_html=True)
    cats = {"🥣 粥品": "粥", "🍜 麵食": "麵|粉", "🍚 飯食": "飯", "🍲 湯水": "湯", "🍵 茶飲": "茶"}
    for name, kw in cats.items():
        cat_df = df[df['Dish_Name'].str.contains(kw, na=False)]
        if not cat_df.empty:
            with st.expander(name):
                for i, row in cat_df.iterrows():
                    if st.button(f"✨ {row['Dish_Name']}", key=f"c_{i}"):
                        st.session_state.selected_row = row; st.session_state.view = 'details'; st.rerun()
