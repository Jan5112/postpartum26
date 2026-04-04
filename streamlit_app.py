import streamlit as st
import pandas as pd

# 1. 設置網頁主題顏色 (少女風)
st.set_page_config(page_title="坐月30日食譜", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #FFF0F5; /* 淺粉紅背景 LavenderBlush */
    }
    h1, h2, h3, p, span, label {
        color: #4F4F4F !important; /* 深灰色文字 */
    }
    .stButton>button {
        background-color: #FFB6C1; /* 粉色按鈕 */
        color: white;
        border-radius: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 初始化數據 (實際應用中可讀取 CSV)
if 'recipe_data' not in st.session_state:
    # 這裡建立一個範例數據框架
    st.session_state.recipe_data = pd.DataFrame([
        {"Day": 1, "Meal": "午餐", "Name": "番茄炒蛋", "Ingredients": "番茄, 雞蛋", "Method": "1.切番茄 2.炒蛋..."},
        {"Day": 1, "Meal": "晚餐", "Name": "清蒸鱸魚", "Ingredients": "鱸魚, 薑, 蔥", "Method": "1.洗魚 2.蒸10分鐘..."}
    ])

st.title("🌸 坐月 30 日食譜管理")

# 3. 搜尋功能
search_query = st.text_input("🔍 搜尋食材 (例如：番茄)", "")

if search_query:
    filtered_df = st.session_state.recipe_data[
        st.session_state.recipe_data['Ingredients'].str.contains(search_query) | 
        st.session_state.recipe_data['Name'].str.contains(search_query)
    ]
    st.write(f"找到以下關於 '{search_query}' 的食譜：")
    for index, row in filtered_df.iterrows():
        if st.button(f"查看詳情: {row['Name']}", key=f"search_{index}"):
            st.info(f"**詳細做法：**\n\n{row['Method']}")

st.divider()

# 4. 展示 30 日列表
day_to_show = st.selectbox("選擇天數", range(1, 31))
meals = ["早餐", "午餐", "下午茶", "糖水", "晚餐", "宵夜", "炒米茶"]

st.header(f"第 {day_to_show} 天食譜清單")

for meal in meals:
    # 尋找當天當餐的菜品
    match = st.session_state.recipe_data[
        (st.session_state.recipe_data['Day'] == day_to_show) & 
        (st.session_state.recipe_data['Meal'] == meal)
    ]
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if not match.empty:
            dish_name = match.iloc[0]['Name']
            if st.button(f"{meal}: {dish_name}", key=f"btn_{day_to_show}_{meal}"):
                st.write(f"🥣 **{dish_name} 的做法：**")
                st.write(match.iloc[0]['Method'])
        else:
            st.write(f"{meal}: 尚未設定食譜")

st.divider()

# 5. 修改/加入食譜功能
with st.expander("➕ 加入 / 修改食譜內容"):
    with st.form("recipe_form"):
        new_day = st.number_input("天數", min_value=1, max_value=30)
        new_meal = st.selectbox("餐次", meals)
        new_name = st.text_input("菜品名稱")
        new_ing = st.text_area("食材 (用逗號隔開)")
        new_method = st.text_area("做法詳情")
        
        submit = st.form_submit_button("儲存食譜")
        if submit:
            # 這裡簡單示範更新 Session State
            new_row = {"Day": new_day, "Meal": new_meal, "Name": new_name, "Ingredients": new_ing, "Method": new_method}
            st.session_state.recipe_data = pd.concat([st.session_state.recipe_data, pd.DataFrame([new_row])], ignore_index=True)
            st.success("食譜已更新！")
