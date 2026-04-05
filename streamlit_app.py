import streamlit as st
import pandas as pd
import re

# --- 1. 樣式設定 (手機全優化：大字體、粉紅卡片) ---
st.set_page_config(page_title="🌸 媽媽坐月餐單", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; } 
    html { font-size: 16px; } /* 手機版字體稍微加大 */
    .main .block-container { max-width: 800px; margin: 0 auto; }
    
    h1 { font-size: 2rem !important; color: #D87093 !important; text-align: center !important; }
    
    /* 按鈕樣式 */
    .stButton>button { 
        background-color: #FFB6C1; color: white !important; 
        border-radius: 20px; border: none; width: 100%; min-height: 50px;
        font-size: 1.1rem; font-weight: bold; margin-bottom: 10px;
    }

    /* 左邊選單 */
    [data-testid="stSidebar"] { background-color: #FFE4E1; }
    [data-testid="stSidebar"] * { color: #D87093 !important; font-weight: bold !important; }

    /* 🔢 Number Input (輸入框) */
    div[data-baseweb="input"] { border-color: #FFB6C1 !important; border-radius: 10px; }
    div[data-baseweb="input"] input { color: #D87093 !important; font-size: 1.2rem !important; }

    /* 🛒 採購清單卡片 (手機優化) */
    .shopping-day-title { 
        background-color: #D87093; color: white; padding: 10px 15px; 
        border-radius: 12px; font-weight: bold; margin: 20px 0 10px 0; 
    }
    .dish-box {
        background-color: white; padding: 15px; border-radius: 15px;
        border: 1.5px solid #FFB6C1; margin-bottom: 15px;
    }
    .dish-name { color: #D87093; font-weight: bold; font-size: 1.1rem; margin-bottom: 8px; border-bottom: 1px solid #FFF0F5; padding-bottom: 5px; }
    
    .cat-tag { 
        display: inline-block; padding: 2px 8px; border-radius: 8px; 
        font-size: 0.85rem; font-weight: bold; margin-top: 10px;
    }
    .tag-ing { background-color: #FFE4E1; color: #D87093; }
    .tag-sea { background-color: #F0F0F0; color: #888888; }
    
    .item-text { color: #555555; font-size: 1rem; line-height: 1.6; margin: 5px 0 0 5px; }

    /* 📊 總結區樣式 */
    .summary-box {
        background-color: #FFF0F5; padding: 20px; border-radius: 20px;
        border: 2px dashed #D87093; margin-top: 30px;
    }
    .summary-title { color: #D87093; font-weight: bold; font-size: 1.3rem; text-align: center; margin-bottom: 15px; }
    .summary-item { color: #666666; font-size: 1.05rem; margin-bottom: 8px; display: flex; align-items: center; }
    .pink-dot { color: #FFB6C1; margin-right: 10px; font-size: 1.2rem; }
    
    /* 摺疊面板 */
    .stExpander { border: 1px solid #FFB6C1 !important; border-radius: 15px !important; background-color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據處理與分類邏輯 ---
def split_ingredients(text):
    # 調味料關鍵字庫
    sea_kws = ['鹽', '糖', '油', '醬', '醋', '粉', '汁', '露', '酒', '蜜', '精', '豉', '麻', '水']
    ings, seas = [], []
    items = re.split(r'[\n,，、\s]+', str(text))
    for item in items:
        item = item.strip()
        if not item: continue
        if any(kw in item for kw in sea_kws): seas.append(item)
        else: ings.append(item)
    return ings, seas

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
        return data
    except: return None

df = load_data()

# --- 3. 頁面狀態管理 ---
if 'view' not in st.session_state: st.session_state.view = 'main'
if 'selected_row' not in st.session_state: st.session_state.selected_row = None
if 'day_input' not in st.session_state: st.session_state.day_input = "1"

# --- 4. 側邊欄 ---
st.sidebar.title("🌸 選單")
mode = st.sidebar.radio("跳轉至：", ["📅 媽媽坐月餐單", "🗓️ 每週總覽", "🛒 採購清單", "🔍 食譜大百科"], index=0)

# --- 5. 🛒 採購清單 (手機優化版) ---
if mode == "🛒 採購清單":
    st.markdown("<h1>🛒 採購清單</h1>", unsafe_allow_html=True)
    
    # 手機版輸入框
    st.write("📅 **選擇天數範圍：**")
    c1, c2 = st.columns(2)
    with c1: start_d = st.number_input("開始", min_value=1, max_value=30, value=1)
    with c2: end_d = st.number_input("結束", min_value=1, max_value=30, value=start_d)
    
    if start_d <= end_d:
        mask = (df['Day_Int'] >= start_d) & (df['Day_Int'] <= end_d)
        shop_df = df[mask]
        
        if not shop_df.empty:
            total_ing, total_sea = [], []
            
            # 按天顯示詳細清單
            for d in range(start_d, end_d + 1):
                day_items = shop_df[shop_df['Day_Int'] == d]
                if not day_items.empty:
                    st.markdown(f'<div class="shopping-day-title">📅 第 {d} 天</div>', unsafe_allow_html=True)
                    for _, row in day_items.iterrows():
                        ings, seas = split_ingredients(row['Ingredients'])
                        total_ing.extend(ings); total_sea.extend(seas)
                        
                        box_html = f'<div class="dish-box"><div class="dish-name">🥘 {row["Dish_Name"]}</div>'
                        if ings:
                            box_html += f'<span class="cat-tag tag-ing">🛒 食材</span><div class="item-text">{" · ".join(ings)}</div>'
                        if seas:
                            box_html += f'<span class="cat-tag tag-sea">🧂 調味</span><div class="item-text">{" · ".join(seas)}</div>'
                        box_html += '</div>'
                        st.markdown(box_html, unsafe_allow_html=True)
            
            # --- 📊 份量總結區 (手機重點) ---
            st.markdown(f"""
            <div class="summary-box">
                <div class="summary-title">📊 採購總結 (第 {start_d}-{end_d} 天)</div>
            """, unsafe_allow_html=True)
            
            # 主要食材總結
            st.markdown('<p style="color:#D87093; font-weight:bold; margin-top:10px;">🍎 主要食材匯總：</p>', unsafe_allow_html=True)
            for item in sorted(list(set(total_ing))):
                count = total_ing.count(item)
                st.markdown(f'<div class="summary-item"><span class="pink-dot">●</span>{item} <small style="margin-left:10px; color:#A0A0A0;">(出現 {count} 次)</small></div>', unsafe_allow_html=True)
            
            # 調味料總結
            st.markdown('<p style="color:#888; font-weight:bold; margin-top:20px;">🧂 調味料匯總：</p>', unsafe_allow_html=True)
            for item in sorted(list(set(total_sea))):
                st.markdown(f'<div class="summary-item" style="color:#888;"><span class="pink-dot" style="color:#DDD;">●</span>{item}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("所選範圍內無資料")
    else:
        st.error("結束天數不可小於開始天數")

# --- 其餘模組 (保持原樣，僅放入對應位置) ---
elif mode == "📅 媽媽坐月餐單":
    st.markdown("<h1>📅 媽媽坐月餐單</h1>", unsafe_allow_html=True)
    d_slider = st.select_slider("💖 選擇天數", options=[str(i) for i in range(1, 31)], value=st.session_state.day_input)
    d_num = st.number_input("🔢 直接輸入", min_value=1, max_value=30, value=int(d_slider))
    st.session_state.day_input = str(d_num)
    day_df = df[df['Day_Int'] == int(st.session_state.day_input)]
    for m in ["早餐", "午餐", "下午茶", "糖水", "湯水", "晚餐", "炒米茶"]:
        m_data = day_df[day_df['Meal'].str.contains(m, na=False)]
        for _, row in m_data.iterrows():
            if st.button(f"🥘 {m}：{row['Dish_Name']}", key=f"d_{row.name}"):
                st.session_state.selected_row = row; st.session_state.view = 'details'; st.rerun()

elif mode == "🗓️ 每週總覽":
    st.markdown("<h1>🗓️ 每週總覽</h1>", unsafe_allow_html=True)
    week = st.selectbox("選擇星期", ["第 1 週 (Day 1-7)", "第 2 週 (Day 8-14)", "第 3 週 (Day 15-21)", "第 4 週 (Day 22-30)"])
    # (此處保留你原本的每週總覽邏輯...)

elif mode == "🔍 食譜大百科":
    st.markdown("<h1>🔍 食譜大百科</h1>", unsafe_allow_html=True)
    # (此處保留你原本的食譜百科邏輯...)

# 詳情頁處理
if st.session_state.view == 'details':
    recipe = st.session_state.selected_row
    st.markdown(f"<h1>{recipe['Dish_Name']}</h1>", unsafe_allow_html=True)
    if st.button("⬅️ 返回"): st.session_state.view = 'main'; st.rerun()
    st.markdown(f'<div class="recipe-card"><div class="recipe-content">{recipe["Ingredients"]}</div><hr><div class="recipe-content">{recipe["Method"]}</div></div>', unsafe_allow_html=True)
