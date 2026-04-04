import streamlit as st

# 1. 網頁頁面基本設定
st.set_page_config(page_title="💕 靚靚媽咪坐月餐單", layout="wide")

# 2. CSS 樣式 (粉紅主題)
st.markdown("""
    <style>
    .stApp { background-color: #FFF0F5; }
    h1 { color: #FF69B4; text-align: center; font-family: 'Comic Sans MS'; }
    .menu-card {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 15px;
        border: 2px solid #FFB6C1;
        margin-bottom: 10px;
    }
    .search-box {
        background-color: #FFF;
        padding: 20px;
        border-radius: 20px;
        border: 2px solid #FF69B4;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎀 坐月食譜搜尋助手 🎀")

# 3. 定義完整的食譜資料庫 (加咗番茄例子)
recipes = {
    "番茄紅蘿蔔瘦肉湯": "🍅 **材料**：番茄3個、紅蘿蔔1條、瘦肉、薑片。<br>👩‍🍳 **做法**：所有材料切塊，加水煲1.5小時。生津開胃。",
    "番茄炒蛋": "🍅 **材料**：番茄2個、雞蛋3隻、少許糖。<br>👩‍🍳 **做法**：先炒蛋，再煮爛番茄，最後混合加糖調味。",
    "木耳炒肉片": "🌸 **材料**：雲耳、瘦肉、薑片。<br>👩‍🍳 **做法**：瘦肉切片醃好，雲耳浸發，大火快炒。",
    "青木瓜魚湯": "🌸 **材料**：青木瓜、花生、鯽魚、薑。<br>👩‍🍳 **做法**：魚煎香後加滾水，煲至奶白色。",
    "番茄薯仔鮮魚湯": "🍅 **材料**：番茄、薯仔、大眼雞魚、薑。<br>👩‍🍳 **做法**：魚煎香後加水，放入番茄薯仔煲1小時。",
}

# --- 🆕 新增：搜尋引擎部分 ---
st.markdown('<div class="search-box">', unsafe_allow_html=True)
search_query = st.text_input("💖 想搵邊種材料嘅食譜？(例如：番茄、木耳)", placeholder="輸入材料名稱...")
st.markdown('</div>', unsafe_allow_html=True)

if search_query:
    st.subheader(f"✨ 關於「{search_query}」的搜尋結果：")
    # 邏輯：檢查關鍵字是否在菜名或做法入面
    found_results = {name: detail for name, detail in recipes.items() if search_query in name or search_query in detail}
    
    if found_results:
        for name, method in found_results.items():
            with st.expander(f"✅ 搵到咗：{name}", expanded=True):
                st.markdown(method, unsafe_allow_html=True)
    else:
        st.write("😥 搵唔到相關食譜，試吓其他材料？")

st.divider()

# --- 4. 顯示原本的餐單表格 ---
st.header("🗓️ 每週固定餐單")
menu_data = {
    "星期一 🌸": {"早餐": "番茄紅蘿蔔瘦肉湯", "午餐": "木耳炒肉片", "湯水": "青木瓜魚湯", "晚餐": "番茄炒蛋"},
    # 這裡可以繼續加...
}

cols = st.columns(len(menu_data))
for i, (day, meals) in enumerate(menu_data.items()):
    with cols[i]:
        st.markdown(f'<div class="menu-card"><h3 style="color:#FF69B4;">{day}</h3>', unsafe_allow_html=True)
        for m_type, dish in meals.items():
            st.markdown(f"**{m_type}**: {dish}")
        st.markdown('</div>', unsafe_allow_html=True)
