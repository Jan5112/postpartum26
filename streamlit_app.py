import streamlit as st
import pandas as pd
import re

# --- 1. 樣式與手機優化 ---
st.set_page_config(page_title="🌸 媽媽坐月餐單", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; }
    .main .block-container { max-width: 600px; margin: 0 auto; padding: 1.2rem; }
    h1 { color: #D87093 !important; font-size: 1.8rem !important; text-align: center; }
    .section-title { color: #D87093; font-size: 1.2rem; font-weight: bold; margin: 15px 0 10px 0; }
    p, span, label, .stCheckbox, .stMarkdown { color: #666666 !important; }
    .check-card {
        background-color: white; padding: 15px; border-radius: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04); margin-bottom: 15px;
        border: 1.5px solid #FFE4E1;
    }
    .usage-text { color: #888888 !important; font-size: 0.9rem; margin-left: 32px; display: block; margin-top: -8px; margin-bottom: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取 (加入強制刷新) ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZesALwN_63zG-ULARgSgu2zX44qpxYud8Y4qco_4IFI/edit?usp=sharing"
CSV_URL = SHEET_URL.split('/edit')[0] + '/export?format=csv'

@st.cache_data(ttl=1) # 設為 1 秒確保近乎即時更新
def load_data():
    try:
        data = pd.read_csv(CSV_URL)
        data.columns = data.columns.str.strip()
        data['Day_Int'] = pd.to_numeric(data['Day'], errors='coerce').fillna(0).astype(int)
        return data
    except: return None

all_df = load_data()

# --- 3. 採購邏輯：嚴格只限傳入的 DF ---
def get_shopping_summary(df_to_process):
    if df_to_process is None or df_to_process.empty: return {"食材": {}, "調味": {}}
    
    sea_kws = ['鹽', '糖', '油', '醬', '醋', '粉', '汁', '酒', '蜜', '豉', '麻']
    summary = {"食材": {}, "調味": {}}
    
    # 呢個 Loop 只會行傳入嚟嗰幾行資料
    for _, row in df_to_process.iterrows():
        dish = row['Dish_Name']
        d_val = int(row['Day_Int'])
        
        # 拆開食材
        items = re.split(r'[\n,，、\s]+', str(row['Ingredients']))
        for raw in items:
            raw = raw.strip()
            if not raw or raw == 'nan': continue
            
            # 分拆名稱 (例如: 糙米 1份 -> 糙米)
            match = re.match(r'^([^\d\s\(\)g克份包兩斤]+)', raw)
            base_name = match.group(1).strip() if match else raw
            amount = raw.replace(base_name, "").strip()
            
            cat = "調味" if any(kw in base_name for kw in sea_kws) else "食材"
            
            if base_name not in summary[cat]:
                summary[cat][base_name] = {"count": 0, "details": []}
            
            summary[cat][base_name]["count"] += 1
            summary[cat][base_name]["details"].append(f"Day {d_val} {dish} ({amount if amount else '適量'})")
            
    return summary

# --- 4. 側邊欄與導航 ---
st.sidebar.title("🌸 選單")
mode = st.sidebar.radio("跳轉至：", ["📅 媽媽坐月餐單", "🛒 採購 Check-list", "🗓️ 每週總覽", "🔍 食譜大百科"], index=1)

if all_df is not None:
    if mode == "🛒 採購 Check-list":
        st.markdown("<h1>🛒 採購 Check-list</h1>", unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["📍 睇今日買乜", "📅 一次過買幾日"])
        
        with t1:
            s_day = st.number_input("選擇天數", min_value=1, max_value=30, value=1, key="input_s")
            # 【終極過濾】只攞選定日子的數據
            working_df = all_df[all_df['Day_Int'] == s_day].copy()
            # 建立一個唯一的 ID 用嚟區分 Checkbox
            scope_id = f"day_{s_day}"

        with t2:
            c1, c2 = st.columns(2)
            with c1: r1 = st.number_input("由 Day", min_value=1, max_value=30, value=1, key="input_r1")
            with c2: r2 = st.number_input("至 Day", min_value=1, max_value=30, value=r1+1, key="input_r2")
            working_df = all_df[(all_df['Day_Int'] >= r1) & (all_df['Day_Int'] <= r2)].copy()
            scope_id = f"range_{r1}_{r2}"

        if not working_df.empty:
            data_sum = get_shopping_summary(working_df)
            for cat_name in ["食材", "調味"]:
                if data_sum[cat_name]:
                    st.markdown(f'<div class="section-title">{"🍎 主要食材" if cat_name=="食材" else "🧂 檢查調味"}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="check-card">', unsafe_allow_html=True)
                    for b_name, info in data_sum[cat_name].items():
                        # 顯示名稱加次數
                        display_label = b_name + (f" (x{info['count']})" if info['count'] > 1 else "")
                        # 【關鍵】Checkbox Key 加入 scope_id，切換日子時會強制重繪
                        st.checkbox(display_label, key=f"chk_{scope_id}_{cat_name}_{b_name}")
                        st.markdown(f'<span class="usage-text">📍 {"、".join(info["details"])}</span>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("揀選嘅日子暫時冇資料。")

    elif mode == "📅 媽媽坐月餐單":
        # (此處保留原本餐單代碼...)
        st.markdown("<h1>📅 媽媽坐月餐單</h1>", unsafe_allow_html=True)
        sel_d = st.number_input("🔢 選擇天數", min_value=1, max_value=30, value=1)
        day_items = all_df[all_df['Day_Int'] == sel_d]
        for _, r in day_items.iterrows():
            with st.expander(f"🥘 {r['Meal']}：{r['Dish_Name']}"):
                st.write(f"🛒 食材：{r['Ingredients']}")
                st.write(f"👩‍🍳 做法：{r['Method']}")
    
    # ... 其餘功能 (每週總覽、百科) 依此類推 ...
else:
    st.error("未能讀取資料，請檢查 Google Sheet 權限。")
