import streamlit as st
import pandas as pd

# --- 1. 少女風主題設定 ---
st.set_page_config(page_title="🌸 媽咪 30 日坐月食譜", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; } 
    h1, h2, h3, p, span, label, .stMarkdown { 
        color: #4F4F4F !important; 
        font-family: "Microsoft JhengHei", "Heiti TC", sans-serif; 
    }
    .stButton>button { 
        background-color: #FFB6C1; color: white !important; 
        border-radius: 20px; border: none; width: 100%; height: 50px;
        font-size: 16px; font-weight: bold; transition: 0.3s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 8px;
    }
    .stButton>button:hover { 
        background-color: #FF9EB5; transform: translateY(-2px);
        color: white !important; border: none;
    }
    .recipe-card {
        background-color: white; padding: 30px; border-radius: 25px; 
        box-shadow: 0 10px 20px rgba(255,182,193,0.2); 
        border-left: 12px solid #FFB6C1; margin-top: 20px;
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
        col_map = {
            'Day': 'Day', '天數': 'Day',
            'Meal': 'Meal', '餐次': 'Meal',
            'Dish_Name': 'Dish_Name', '菜品名': 'Dish_Name', '菜名': 'Dish_Name',
            'Ingredients': 'Ingredients', '食材': 'Ingredients',
            'Method': 'Method', '做法': 'Method'
        }
        data = data.rename(columns=col_map)
        data['Dish_Name'] = data['Dish_Name'].astype(str).str.strip()
        data['Day'] = data['Day'].astype(str).str.strip()
        return data
    except:
        return None

df = load_data()

# --- 3. 狀態管理 ---
if 'view' not in st.session_state: st.session_state.view = 'main'
if 'selected_row' not in st.session_state: st.session_state.selected_row = None

# --- 4. 側邊欄導航 ---
st.sidebar.title("🌸 選單")
mode = st.sidebar.radio("你想點搵食譜？", ["📅 每日餐單", "🔍 按類型搵 (粥/湯/飯)"])

# --- 5. 詳情頁面 ---
def show_details():
    recipe = st.session_state.selected_row
    if st.button("⬅️ 返回列表"):
        st.session_state.view = 'main'
        st.rerun()
    
    st.markdown(f"""
    <div class="recipe-card">
        <h1 style='color:#D87093 !important;'>{recipe['Dish_Name']}</h1>
        <p style='color:#A0A0A0 !important;'>📅 第 {recipe['Day']} 天 · {recipe['Meal']}</p>
        <hr style='border: 1px solid #FFF0F5;'>
        <h3 style='color:#FFB6C1 !important;'>🛒 準備食材</h3>
        <p>{str(recipe['Ingredients'])}</p>
        <br>
        <h3 style='color:#FFB6C1 !important;'>👩‍🍳 烹飪步驟</h3>
        <p>{str(recipe['Method']).replace('\\n', '<br>').replace('\n', '<br>')}</p>
    </div>
    """, unsafe_allow_html=True)

# --- 6. 每日餐單頁面 ---
def show_daily_view():
    st.title("📅 每日養生餐單")
    day = st.select_slider("💖 選擇坐月天數", options=list(range(1, 31)), value=1)
    
    day_df = df[df['Day'] == str(day)]
    meals = ["早餐", "午餐", "下午茶", "糖水", "湯水", "晚餐", "炒米茶"]
    
    for m in meals:
        m_data = day_df[day_df['Meal'].str.contains(m, na=False)]
        if not m_data.empty:
            row = m_data.iloc[0]
            if st.button(f"🥘 {m}：{row['Dish_Name']}", key=f"daily_{row.name}"):
                st.session_state.selected_row = row
                st.session_state.view = 'details'
                st.rerun()

# --- 7. 按類型搵食譜頁面 ---
def show_type_view():
    st.title("🔍 食譜大百科")
    st.write("想食粥、食麵、定飲湯？喺度一目了然！")

    # 定義分類關鍵字
    categories = {
        "🥣 暖心粥品": "粥",
        "🍜 滋味麵食": "麵|粉|米粉|河粉",
        "🍚 營養飯食": "飯|燉飯|炒飯",
        "🍲 滋補湯水": "湯",
        "🥬 精選時蔬": "菜|蔬",
        "🥚 蛋/肉類": "蛋|雞|豬|牛|魚",
        "🍡 甜品糖水": "糖水|甜",
        "🍵 養生茶飲": "茶"
    }

    search_query = st.text_input("💡 直接輸入關鍵字搜尋 (例如：黑豆)", "")

    if search_query:
        search_results = df[df['Dish_Name'].str.contains(search_query, na=False) | 
                            df['Ingredients'].str.contains(search_query, na=False)]
        st.subheader(f"找到「{search_query}」相關食譜：")
        for i, row in search_results.iterrows():
            if st.button(f"✨ {row['Dish_Name']}", key=f"search_{i}"):
                st.session_state.selected_row = row
                st.session_state.view = 'details'
                st.rerun()
    else:
        # 顯示分類摺疊選單
        for cat_name, keywords in categories.items():
            cat_df = df[df['Dish_Name'].str.contains(keywords, na=False)]
            if not cat_df.empty:
                with st.expander(cat_name, expanded=False):
                    cols = st.columns(2)
                    for idx, (i, row) in enumerate(cat_df.iterrows()):
                        with cols[idx % 2]:
                            if st.button(row['Dish_Name'], key=f"cat_{i}"):
                                st.session_state.selected_row = row
                                st.session_state.view = 'details'
                                st.rerun()

# --- 8. 主邏輯 ---
if df is not None:
    if st.session_state.view == 'details':
        show_details()
    elif mode == "📅 每日餐單":
        show_daily_view()
    else:
        show_type_view()
