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
        border-radius: 20px; border: none; width: 100%; height: 55px;
        font-size: 18px; font-weight: bold; transition: 0.3s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
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
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取與自動對位 ---
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
            'Method': 'Method', '做法': 'Method', '詳細做法': 'Method'
        }
        new_cols = {c: col_map[c] for c in data.columns if c in col_map}
        data = data.rename(columns=new_cols)
        
        if 'Meal' in data.columns:
            data['Meal'] = data['Meal'].astype(str).str.strip()
        if 'Day' in data.columns:
            data['Day'] = data['Day'].astype(str).str.strip()
            
        return data
    except Exception as e:
        return None

df = load_data()

if 'view' not in st.session_state: st.session_state.view = 'list'
if 'selected_row' not in st.session_state: st.session_state.selected_row = None

# --- 3. 詳情頁面 ---
if st.session_state.view == 'details':
    recipe = st.session_state.selected_row
    if st.button("⬅️ 返回主列表"):
        st.session_state.view = 'list'
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

# --- 4. 主列表頁面 ---
else:
    st.title("🌸 媽咪坐月 30 日食譜")
    query = st.text_input("🔍 搜尋食材或菜名 (例如：番茄)", placeholder="想食咩呢？")
    
    if query:
        results = df[df['Ingredients'].astype(str).str.contains(query, na=False, case=False) | 
                     df['Dish_Name'].astype(str).str.contains(query, na=False, case=False)]
        for i, row in results.iterrows():
            if st.button(f"✨ {row['Dish_Name']}", key=f"search_{i}"):
                st.session_state.selected_row = row
                st.session_state.view = 'details'
                st.rerun()
    else:
        day = st.select_slider("💖 選擇坐月天數", options=list(range(1, 31)), value=1)
        st.markdown(f"### 📅 第 {day} 天 · 全日餐單")
        
        day_df = df[df['Day'] == str(day)]
        
        # --- 這裡將宵夜改成了 "滋補湯水" ---
        # 只要你在 Google Sheet 的「餐次」欄位寫「湯水」或「滋補湯水」，App 就能抓到
        meals = ["早餐", "午餐", "下午茶", "糖水", "湯水", "晚餐", "炒米茶"]
        
        for m in meals:
            # 加入模糊匹配，如果 Sheet 寫「滋補湯水」或「湯水」都能對應
            m_data = day_df[day_df['Meal'].str.contains(m, na=False)]
            
            if not m_data.empty:
                row = m_data.iloc[0]
                if st.button(f"🥣 {m}：{row['Dish_Name']}", key=f"m_{m}"):
                    st.session_state.selected_row = row
                    st.session_state.view = 'details'
                    st.rerun()
            else:
                st.markdown(f"<span style='color:#CCC;'>◽ {m}：資料準備中...</span>", unsafe_allow_html=True)

if df is None:
    st.error("⚠️ 讀取數據失敗，請確認 Google Sheet 權限。")
