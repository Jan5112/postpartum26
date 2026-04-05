import streamlit as st
import pandas as pd

# --- 1. 樣式設定 (加入手機版表格優化) ---
st.set_page_config(page_title="🌸 媽媽坐月餐單", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; } 
    html { font-size: 14px; }
    .main .block-container { max-width: 800px; margin: 0 auto; text-align: center; }
    
    h1 { font-size: 2.2rem !important; color: #D87093 !important; text-align: center !important; margin-bottom: 25px !important; }
    
    /* 按鈕樣式 */
    .stButton>button { 
        background-color: #FFB6C1; color: white !important; 
        border-radius: 18px; border: none; width: 100%; max-width: 350px;
        min-height: 45px; margin: 5px auto !important;
        font-size: 15px; font-weight: bold; transition: 0.3s;
        box-shadow: 0 4px 8px rgba(255,182,193,0.2);
    }
    
    /* 每週總覽：手機版卡片樣式 */
    .week-card {
        background-color: white; padding: 15px; border-radius: 15px; 
        margin-bottom: 15px; text-align: left;
        border: 1px solid #FFE4E1;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .week-day-title { color: #D87093; font-weight: bold; font-size: 1.2rem; margin-bottom: 10px; border-bottom: 1px solid #FFF0F5; padding-bottom: 5px; }
    .week-meal-item { color: #666666; font-size: 1rem; margin-bottom: 5px; display: flex; }
    .week-meal-label { color: #FFB6C1; font-weight: bold; min-width: 65px; }

    /* 詳情頁內容 */
    .recipe-card {
        background-color: white; padding: 25px; border-radius: 20px; 
        box-shadow: 0 10px 25px rgba(255,182,193,0.15); 
        border-left: 10px solid #FFB6C1; text-align: left !important;
    }
    .recipe-content { color: #666666 !important; line-height: 1.8; font-size: 1.1rem; white-space: pre-wrap; }
    
    [data-testid="stSidebar"] { background-color: #FFE4E1; }
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
        col_map = {'天數': 'Day', 'Day': 'Day', '餐次': 'Meal', 'Meal': 'Meal', '菜品名': 'Dish_Name', 'Dish_Name': 'Dish_Name', '食材': 'Ingredients', '做法': 'Method'}
        data = data.rename(columns=col_map)
        data = data.dropna(subset=['Dish_Name'])
        for col in ['Day', 'Meal', 'Dish_Name', 'Ingredients', 'Method']:
            if col in data.columns:
                data[col] = data[col].astype(str).str.strip().replace('nan', '')
        data['Day'] = data['Day'].apply(lambda x: str(int(float(x))) if x.replace('.','',1).isdigit() else x)
        return data
    except: return None

df = load_data()

# --- 3. 狀態管理 ---
if 'view' not in st.session_state: st.session_state.view = 'main'
if 'selected_row' not in st.session_state: st.session_state.selected_row = None
if 'day_input' not in st.session_state: st.session_state.day_input = "1"

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
        <p style="text-align:center; color:#A0A0A0;">📅 第 {recipe['Day']} 天 · {recipe['Meal']}</p>
        <hr style='border: 1px solid #FFF0F5;'>
        <h3 style='color:#FFB6C1;'>🛒 準備食材</h3>
        <div class="recipe-content">{recipe['Ingredients']}</div>
        <br>
        <h3 style='color:#FFB6C1;'>👩‍🍳 烹飪步驟</h3>
        <div class="recipe-content">{str(recipe['Method']).replace('\\n', '<br>').replace('\n', '<br>')}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 6. 媽媽坐月餐單 ---
elif mode == "📅 媽媽坐月餐單":
    st.markdown("<h1>📅 媽媽坐月餐單</h1>", unsafe_allow_html=True)
    d_slider = st.select_slider("💖 選擇天數", options=[str(i) for i in range(1, 31)], value=st.session_state.day_input)
    d_num = st.number_input("🔢 直接輸入天數", min_value=1, max_value=30, value=int(d_slider))
    st.session_state.day_input = str(d_num)

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    day_df = df[df['Day'] == st.session_state.day_input]
    meals = ["早餐", "午餐", "下午茶", "糖水", "湯水", "晚餐", "炒米茶"]
    
    for m in meals:
        m_data = day_df[day_df['Meal'].str.contains(m, na=False)]
        if not m_data.empty:
            for idx, (_, row) in enumerate(m_data.iterrows()):
                label = f"🥘 {m}：{row['Dish_Name']}" if len(m_data) == 1 else f"🥘 {m}({idx+1})：{row['Dish_Name']}"
                if st.button(label, key=f"d_{row.name}"):
                    st.session_state.selected_row = row; st.session_state.view = 'details'; st.rerun()
        else:
            st.markdown(f"<p style='color:#DDD; text-align:center; font-size:13px;'>◽ {m}：資料準備中...</p>", unsafe_allow_html=True)

# --- 7. 每週總覽 (手機優化版) ---
elif mode == "🗓️ 每週總覽":
    st.markdown("<h1>🗓️ 每週總覽</h1>", unsafe_allow_html=True)
    week = st.selectbox("選擇星期：", ["第 1 週 (Day 1-7)", "第 2 週 (Day 8-14)", "第 3 週 (Day 15-21)", "第 4 週 (Day 22-30)"])
    week_map = {"第 1 週 (Day 1-7)": (1, 7), "第 2 週 (Day 8-14)": (8, 14), "第 3 週 (Day 15-21)": (15, 21), "第 4 週 (Day 22-30)": (22, 30)}
    start, end = week_map[week]
    
    meals = ["早餐", "午餐", "下午茶", "糖水", "湯水", "晚餐", "炒米茶"]
    
    for d in range(start, end + 1):
        # 為每一天整一個卡片
        html_content = f'<div class="week-card"><div class="week-day-title">📅 第 {d} 天</div>'
        has_content = False
        
        for m in meals:
            target = df[(df['Day'] == str(d)) & (df['Meal'].str.contains(m, na=False))]
            if not target.empty:
                dish_names = "、".join(target['Dish_Name'].tolist())
                html_content += f'<div class="week-meal-item"><span class="week-meal-label">{m}：</span><span>{dish_names}</span></div>'
                has_content = True
        
        if not has_content:
            html_content += '<div style="color:#CCC;">暫無餐單資料</div>'
            
        html_content += '</div>'
        st.markdown(html_content, unsafe_allow_html=True)

# --- 8. 食譜大百科 ---
else:
    st.markdown("<h1>🔍 食譜大百科</h1>", unsafe_allow_html=True)
    cats = {"🥣 粥品": "粥", "🍜 麵食": "麵|粉", "🍚 飯食": "飯", "🍲 湯水": "湯", "🍵 茶飲": "茶"}
    for name, kw in cats.items():
        cat_df = df[df['Dish_Name'].str.contains(kw, na=False)]
        if not cat_df.empty:
            with st.expander(name):
                for i, row in cat_df.iterrows():
                    # 大百科內按鈕文字顏色稍微調淡
                    if st.button(f"✨ {row['Dish_Name']}", key=f"cat_{i}"):
                        st.session_state.selected_row = row; st.session_state.view = 'details'; st.rerun()
