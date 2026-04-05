import streamlit as st
import pandas as pd
import re

# --- 1. 樣式設定 (保持粉紅風格) ---
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
    }

    /* 左邊選單 */
    [data-testid="stSidebar"] { background-color: #FFE4E1; }
    [data-testid="stSidebar"] * { color: #D87093 !important; font-weight: bold !important; }

    /* 🔢 Number Input */
    div[data-baseweb="input"] { border-color: #FFB6C1 !important; }
    div[data-baseweb="input"]:focus-within { border-color: #D87093 !important; box-shadow: 0 0 0 1px #D87093 !important; }
    div[data-baseweb="input"] input { color: #D87093 !important; }

    /* 🛒 採購清單卡片優化 */
    .shopping-card { 
        background-color: white !important; padding: 20px; border-radius: 20px; 
        margin-bottom: 20px; text-align: left; border: 2px solid #FFB6C1 !important; 
    }
    .shopping-day-head { color: #D87093; font-size: 1.4rem; font-weight: bold; border-bottom: 2px dashed #FFE4E1; padding-bottom: 10px; margin-bottom: 15px; }
    .category-label { background-color: #FFF0F5; color: #D87093; padding: 3px 10px; border-radius: 10px; font-weight: bold; font-size: 0.9rem; margin-top: 10px; display: inline-block; }
    .item-list { color: #666666 !important; font-size: 1rem; line-height: 1.6; margin-left: 10px; margin-top: 5px; }

    /* 詳情頁內容 */
    .recipe-card { background-color: white !important; padding: 25px; border-radius: 20px; border-left: 10px solid #FFB6C1; text-align: left !important; }
    .recipe-content { color: #666666 !important; line-height: 1.8; font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取與處理 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZesALwN_63zG-ULARgSgu2zX44qpxYud8Y4qco_4IFI/edit?usp=sharing"
CSV_URL = SHEET_URL.split('/edit')[0] + '/export?format=csv'

@st.cache_data(ttl=5)
def load_data():
    try:
        data = pd.read_csv(CSV_URL)
        data.columns = data.columns.str.strip()
        col_map = {'天數': 'Day', '餐次': 'Meal', '菜品名': 'Dish_Name', '食材': 'Ingredients', '做法': 'Method'}
        data = data.rename(columns=col_map)
        data = data.dropna(subset=['Dish_Name'])
        data['Day_Int'] = pd.to_numeric(data['Day'], errors='coerce').fillna(0).astype(int)
        data['Day'] = data['Day_Int'].astype(str)
        return data
    except: return None

df = load_data()

# --- 3. 食材/調味 分類邏輯 ---
def split_ingredients(text):
    # 定義調味料關鍵字
    seasoning_keywords = ['鹽', '糖', '油', '醬', '醋', '粉', '汁', '露', '酒', '蜜', '精']
    ingredients = []
    seasonings = []
    
    # 根據換行、逗號、空格分拆
    items = re.split(r'[\n,，、\s]+', str(text))
    for item in items:
        item = item.strip()
        if not item: continue
        # 檢查是否含有調味料關鍵字
        if any(kw in item for kw in seasoning_keywords):
            seasonings.append(item)
        else:
            ingredients.append(item)
    return ingredients, seasonings

# --- 4. 側邊欄 ---
st.sidebar.title("🌸 選單")
mode = st.sidebar.radio("跳轉至：", ["📅 媽媽坐月餐單", "🗓️ 每週總覽", "🛒 採購清單", "🔍 食譜大百科"], index=0)

# --- 5. 詳情頁 (略，保持不變) ---
if 'view' not in st.session_state: st.session_state.view = 'main'
if 'selected_row' not in st.session_state: st.session_state.selected_row = None
if 'day_input' not in st.session_state: st.session_state.day_input = "1"

if st.session_state.view == 'details':
    recipe = st.session_state.selected_row
    st.markdown(f"<h1 style='text-align:center;'>{recipe['Dish_Name']}</h1>", unsafe_allow_html=True)
    if st.button("⬅️ 返回"): st.session_state.view = 'main'; st.rerun()
    st.markdown(f'<div class="recipe-card"><div class="recipe-content">{recipe["Ingredients"]}</div><br><div class="recipe-content">{recipe["Method"]}</div></div>', unsafe_allow_html=True)

# --- 6. 🛒 採購清單 (強化版) ---
elif mode == "🛒 採購清單":
    st.markdown("<h1>🛒 採購清單</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1: start_d = st.number_input("開始天數", min_value=1, max_value=30, value=1)
    with col2: end_d = st.number_input("結束天數", min_value=1, max_value=30, value=start_d)
    
    if start_d <= end_d:
        mask = (df['Day_Int'] >= start_d) & (df['Day_Int'] <= end_d)
        shop_df = df[mask]
        
        if not shop_df.empty:
            total_ing = []
            total_sea = []
            
            # 建立分類顯示
            for d in range(start_d, end_d + 1):
                day_items = shop_df[shop_df['Day_Int'] == d]
                if not day_items.empty:
                    st.markdown(f'<div class="shopping-day-head">📅 第 {d} 天 採購清單</div>', unsafe_allow_html=True)
                    
                    for _, row in day_items.iterrows():
                        ings, seas = split_ingredients(row['Ingredients'])
                        total_ing.extend(ings)
                        total_sea.extend(seas)
                        
                        html = f'<div class="shopping-card"><b>🍳 {row["Dish_Name"]}</b><br>'
                        if ings:
                            html += f'<span class="category-label">🛒 主要食材</span><div class="item-list">{" · ".join(ings)}</div>'
                        if seas:
                            html += f'<span class="category-label">🧂 常用調味</span><div class="item-list">{" · ".join(seas)}</div>'
                        html += '</div>'
                        st.markdown(html, unsafe_allow_html=True)
            
            # --- 份量總結區 ---
            st.markdown("---")
            st.markdown("### 📊 份量總計 (預算參考)")
            
            summary_col1, summary_col2 = st.columns(2)
            with summary_col1:
                st.markdown("**🍎 全部食材總匯**")
                for item in sorted(list(set(total_ing))):
                    count = total_ing.count(item)
                    st.write(f"- {item} (出現 {count} 次)")
            with summary_col2:
                st.markdown("**🧂 全部調味總匯**")
                for item in sorted(list(set(total_sea))):
                    count = total_sea.count(item)
                    st.write(f"- {item} (出現 {count} 次)")
        else:
            st.warning("暫無資料")

# (其餘模組 媽媽餐單、每週總覽、食譜百科 保持原本代碼即可)
else:
    # 這裡請保留你原本的各個模組代碼...
    st.info("請參考前次完整代碼填入其他模組")
