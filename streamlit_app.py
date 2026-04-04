import streamlit as st
import pandas as pd

# --- 1. 少女風自定義樣式 (粉紅 + 深灰) ---
st.set_page_config(page_title="🌸 媽咪 30 日坐月食譜", layout="centered")

st.markdown("""
    <style>
    /* 全局背景與字體 */
    .stApp { background-color: #FFF5F7; } 
    h1, h2, h3, p, span, label, .stMarkdown { 
        color: #4F4F4F !important; 
        font-family: "Microsoft JhengHei", "Heiti TC", sans-serif; 
    }
    
    /* 按鈕樣式：粉紅圓角 */
    .stButton>button { 
        background-color: #FFB6C1; color: white !important; 
        border-radius: 20px; border: none; width: 100%; height: 55px;
        font-size: 18px; font-weight: bold; transition: 0.3s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stButton>button:hover { 
        background-color: #FF9EB5; transform: translateY(-2px);
        color: white !important; border: none;
    }
    
    /* 食譜詳情卡片 */
    .recipe-card {
        background-color: white; padding: 30px; border-radius: 25px; 
        box-shadow: 0 10px 20px rgba(255,182,193,0.2); 
        border-left: 12px solid #FFB6C1; margin-top: 20px;
    }
    
    /* 搜尋框樣式 */
    .stTextInput>div>div>input {
        border-radius: 15px; border: 2px solid #FFB6C1;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取與自動標題對齊 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZesALwN_63zG-ULARgSgu2zX44qpxYud8Y4qco_4IFI/edit?usp=sharing"
CSV_URL = SHEET_URL.split('/edit')[0] + '/export?format=csv'

@st.cache_data(ttl=30) # 30秒快取，方便你改完 Sheet 快速看到效果
def load_data():
    try:
        data = pd.read_csv(CSV_URL)
        data.columns = data.columns.str.strip() # 清除標題空格
        
        # 自動建立對照表：不管你用中文定英文標題，程式都會對應返
        col_map = {
            'Day': 'Day', '天數': 'Day',
            'Meal': 'Meal', '餐次': 'Meal',
            'Dish_Name': 'Dish_Name', '菜品名': 'Dish_Name', '菜名': 'Dish_Name',
            'Ingredients': 'Ingredients', '食材': 'Ingredients',
            'Method': 'Method', '做法': 'Method', '詳細做法': 'Method'
        }
        # 重新命名欄位以便程式統一處理
        new_cols = {c: col_map[c] for c in data.columns if c in col_map}
        data = data.rename(columns=new_cols)
        return data
    except Exception as e:
        st.error(f"讀取失敗：{e}")
        return None

df = load_data()

# --- 3. 頁面切換與狀態管理 ---
if 'view' not in st.session_state: st.session_state.view = 'list'
if 'selected_row' not in st.session_state: st.session_state.selected_row = None

# --- 4. 詳情頁面渲染 ---
def show_details():
    recipe = st.session_state.selected_row
    if st.button("⬅️ 返回主列表"):
        st.session_state.view = 'list'
        st.rerun()
    
    st.markdown(f"""
    <div class="recipe-card">
        <h1 style='color:#D87093 !important; margin-bottom:5px;'>{recipe['Dish_Name']}</h1>
        <p style='color:#A0A0A0 !important; font-size:1.1rem;'>📅 第 {recipe['Day']} 天 · {recipe['Meal']}</p>
        <hr style='border: 1px solid #FFF0F5;'>
        <h3 style='color:#FFB6C1 !important;'>🛒 準備食材</h3>
        <p style='line-height:1.6;'>{str(recipe['Ingredients'])}</p>
        <br>
        <h3 style='color:#FFB6C1 !important;'>👩‍🍳 烹飪步驟</h3>
        <p style='line-height:1.8;'>{str(recipe['Method']).replace('\\n', '<br>').replace('\n', '<br>')}</p>
    </div>
    """, unsafe_allow_html=True)

# --- 5. 主列表頁面渲染 ---
def show_list():
    st.title("🌸 媽咪坐月 30 日食譜")
    st.write("陪伴妳度過溫暖、滋補的每一天")
    
    # --- 搜尋功能 ---
    query = st.text_input("🔍 搜尋食材或菜名 (例如：番茄、雞蛋)", placeholder="想食咩呢？")
    
    if query:
        # 在 Dish_Name 同 Ingredients 入面搵
        results = df[df['Ingredients'].astype(str).str.contains(query, na=False, case=False) | 
                     df['Dish_Name'].astype(str).str.contains(query, na=False, case=False)]
        
        st.subheader(f"找到 {len(results)} 個相關推薦：")
        for i, row in results.iterrows():
            if st.button(f"✨ {row['Dish_Name']}", key=f"search_{i}"):
                st.session_state.selected_row = row
                st.session_state.view = 'details'
                st.rerun()
        if results.empty:
            st.warning("暫時找不到相關食譜，換個關鍵字試試看？")
            
    else:
        # --- 按日期瀏覽 ---
        day = st.select_slider("💖 選擇坐月天數", options=list(range(1, 31)), value=1)
        st.markdown(f"### 📅 第 {day} 天 · 全日餐單")
        
        # 確保天數過濾正確
        day_df = df[df['Day'].astype(str).str.strip() == str(day)]
        
        meals = ["早餐", "午餐", "下午茶", "糖水", "晚餐", "宵夜", "炒米茶"]
        
        for m in meals:
            m_data = day_df[day_df['Meal'].str.strip() == m]
            if not m_data.empty:
                row = m_data.iloc[0]
                if st.button(f"🥘 {m}：{row['Dish_Name']}", key=f"m_{m}"):
                    st.session_state.selected_row = row
                    st.session_state.view = 'details'
                    st.rerun()
            else:
                # 淡淡的顯示尚未排餐
                st.markdown(f"<span style='color:#CCC;'>◽ {m}：食譜準備中...</span>", unsafe_allow_html=True)

# --- 6. 啟動頁面 ---
if df is not None:
    if st.session_state.view == 'details':
        show_details()
    else:
        show_list()
else:
    st.error("⚠️ 讀取數據失敗，請確認你的 Google Sheet 權限已開啟（知道連結的人即可查看）。")
