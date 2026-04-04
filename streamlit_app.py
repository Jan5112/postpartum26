import streamlit as st
import pandas as pd

# 1. 少女風主題設定
st.set_page_config(page_title="坐月30日食譜", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF0F5; } /* 淺粉紅背景 */
    h1, h2, h3, p, span, label, .stMarkdown { color: #4F4F4F !important; } /* 深灰色文字 */
    .stButton>button { 
        background-color: #FFB6C1; color: white; border-radius: 15px; border: none; width: 100%;
    }
    .recipe-card {
        background-color: white; padding: 20px; border-radius: 15px; 
        border-left: 5px solid #FFB6C1; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 連接 Google Sheet (請填入你的網址)
# 注意：要把網址最後的 /edit... 換成 /export?format=csv
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZesALwN_63zG-ULARgSgu2zX44qpxYud8Y4qco_4IFI/edit?gid=0#gid=0"
CSV_URL = SHEET_URL.replace('/edit#gid=', '/export?format=csv&gid=')

@st.cache_data(ttl=600) # 每 10 分鐘自動更新一次數據
def load_data():
    return pd.read_csv(CSV_URL)

try:
    df = load_data()
except:
    st.error("暫時未能讀取數據，請檢查 Google Sheet 連結及權限。")
    df = pd.DataFrame()

# --- App 內容 ---
st.title("🌸 媽咪的 30 日養生餐單")

# 初始化分頁狀態
if 'page' not in st.session_state:
    st.session_state.page = 'list'
if 'selected_recipe' not in st.session_state:
    st.session_state.selected_recipe = None

# --- 功能 A: 詳情頁面 ---
if st.session_state.page == 'detail':
    recipe = st.session_state.selected_recipe
    if st.button("⬅️ 返回列表"):
        st.session_state.page = 'list'
        st.rerun()
    
    st.markdown(f"""
    <div class="recipe-card">
        <h1>{recipe['Dish_Name']}</h1>
        <p><b>✨ 功效：</b>{recipe.get('功效', '滋補養生')}</p>
        <hr>
        <h3>🛒 食材：</h3>
        <p>{recipe['Ingredients']}</p>
        <h3>👩‍🍳 做法：</h3>
        <p>{recipe['Method'].replace('\\n', '<br>')}</p>
    </div>
    """, unsafe_allow_html=True)

# --- 功能 B: 主列表頁面 ---
else:
    # 搜尋欄
    search = st.text_input("🔍 搜尋食材 (例如：雞蛋、黑豆)", "")

    if search:
        search_results = df[df['Ingredients'].str.contains(search, na=False) | df['Dish_Name'].str.contains(search, na=False)]
        st.subheader(f"關於 '{search}' 的搜尋結果：")
        for _, row in search_results.iterrows():
            if st.button(f"查看：{row['Dish_Name']}", key=f"search_{row['Day']}_{row['Meal']}"):
                st.session_state.selected_recipe = row
                st.session_state.page = 'detail'
                st.rerun()
    else:
        # 選擇天數
        day = st.slider("選擇坐月天數", 1, 30, 1)
        st.header(f"📅 第 {day} 天餐單")
        
        day_df = df[df['Day'] == day]
        meals = ["早餐", "午餐", "下午茶", "糖水", "晚餐", "宵夜", "炒米茶"]
        
        for m in meals:
            meal_data = day_df[day_df['Meal'] == m]
            if not meal_data.empty:
                row = meal_data.iloc[0]
                # 按下菜名跳轉
                if st.button(f"{m}：{row['Dish_Name']}", key=f"list_{m}"):
                    st.session_state.selected_recipe = row
                    st.session_state.page = 'detail'
                    st.rerun()
            else:
                st.write(f"⚪ {m}：尚未安排")
