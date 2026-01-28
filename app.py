import streamlit as st
import requests
import io
import urllib.parse
import time
import random
from PIL import Image
from rembg import remove

# --- 基礎配置 ---
st.set_page_config(page_title="Line Sticker Studio V17", layout="wide")

# --- 進階 CSS (深灰色標籤與天藍色按鈕) ---
st.markdown("""
    <style>
    /* 天藍色主要按鈕 */
    div.stButton > button:first-child {
        background-color: #00BFFF !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
    }
    /* 修正 Multiselect 標籤顏色為深灰色 */
    span[data-baseweb="tag"] {
        background-color: #555555 !important;
        color: white !important;
        border-radius: 4px !important;
    }
    span[data-baseweb="tag"] svg {
        fill: white !important;
    }
    /* 圖片網格防跑版 */
    .stImage > img {
        border-radius: 12px;
        aspect-ratio: 1 / 1;
        object-fit: cover;
    }
    .dotted-box {
        border: 2px dashed #00BFFF;
        border-radius: 12px;
        height: 220px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #00BFFF;
        opacity: 0.4;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 狀態初始化 ---
if 'imgs' not in st.session_state: st.session_state.imgs = [None] * 8
if 'selected' not in st.session_state: st.session_state.selected = None

# --- 介面文字 ---
lang = st.sidebar.selectbox("🌐 Language", ["繁體中文", "English"], index=0)
cur = {
    "title": "🎨 專業 LINE 貼圖製作 V17",
    "who": "主角描述", "action": "動作細節", "style": "風格",
    "custom": "自訂風格 (Optional)", "mood_hint": "情緒標籤 (Optional, Max 8)",
    "gen_btn": "🚀 開始批量生成", "qty": "計畫生成張數 (Quantity)",
    "redo": "🔄 重製", "pick": "🎯 選取"
} if lang=="繁體中文" else {
    "title": "🎨 Pro Sticker Studio V17",
    "who": "Character", "action": "Details", "style": "Style",
    "custom": "Custom Style (Optional)", "mood_hint": "Mood Tags (Optional, Max 8)",
    "gen_btn": "🚀 Batch Generation", "qty": "Quantity to Generate",
    "redo": "🔄 Redo", "pick": "🎯 Pick"
}

st.title(cur["title"])

# --- 主要佈局 ---
col_left, col_right = st.columns([3, 1], gap="large")

with col_left:
    # 1. 輸入與數量控制
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            char = st.text_area(cur["who"], "A cute baby giraffe", height=70)
            style_choice = st.selectbox(cur["style"], ["3D Pixar Render", "2D Flat Vector", "Crayon Style", "Custom"])
        with c2:
            detail = st.text_area(cur["action"], "wearing a hoodie", height=70)
            custom_input = st.text_input(cur["custom"], placeholder="e.g. Cyberpunk...")
        with c3:
            qty = st.slider(cur["qty"], 1, 8, 4)

    # 2. 情緒標籤與數量防呆邏輯
    st.write(f"**{cur['mood_hint']}**")
    mood_list = ["Hi", "OK", "Thank you", "Yes", "No", "Tired", "Sad", "Angry", "Surprise", "Happy"]
    selected_moods = st.multiselect("Select Moods", mood_list, default=["Happy", "OK"], label_visibility="collapsed")
    
    mood_count = len(selected_moods)
    gen_disabled = False

    # --- 防呆警告邏輯 ---
    if mood_count > qty:
        st.error(f"⚠️ 標籤數量 ({mood_count}) 大於預計生成張數 ({qty})。請增加生成張數或移除部分標籤。")
        gen_disabled = True
    elif mood_count > 0 and mood_count < qty:
        st.warning(f"💡 目前選取了 {mood_count} 個情緒，但預計生成 {qty} 張。其餘 {qty-mood_count} 張將以隨機或預設形式生成。")

    if st.button(cur["gen_btn"], use_container_width=True, disabled=gen_disabled):
        st.session_state.imgs = [None] * 8
        final_style = custom_input if (style_choice == "Custom" or custom_input) else style_choice
        
        for i in range(qty):
            # 分配標籤給每一張圖
            current_mood = selected_moods[i] if i < mood_count else ""
            prompt = f"{char}, {current_mood}, {detail}, {final_style}, white background, isolated"
            
            with st.spinner("Creating..."):
                time.sleep(1) # 穩定請求頻率
                url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?nologo=true&seed={random.randint(1,9999)}&width=512&height=512"
                try:
                    r = requests.get(url, timeout=20)
                    if r.status_code == 200:
                        st.session_state.imgs[i] = {"img": Image.open(io.BytesIO(r.content)), "mood": current_mood, "p": prompt}
                        st.rerun()
                except: continue

    # 3. 圖片網格 (Overview)
    st.divider()
    m_cols = st.columns(4)
    for i in range(8):
        with m_cols[i % 4]:
            item = st.session_state.imgs[i]
            if item:
                st.image(item['img'], caption=f"Slot {i+1}: {item['mood']}")
                b1, b2 = st.columns(2)
                if b1.button(cur["redo"], key=f"rd_{i}"):
                    with st.spinner("Creating..."):
                        new_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(item['p'])}?nologo=true&seed={random.randint(1,9999)}&width=512&height=512"
                        st.session_state.imgs[i]['img'] = Image.open(io.BytesIO(requests.get(new_url).content))
                        st.rerun()
                if b2.button(cur["pick"], key=f"pk_{i}"):
                    st.session_state.selected = item['img']
            else:
                st.markdown('<div class="dotted-box">Waiting</div>', unsafe_allow_html=True)

# --- 4. 匯出中心 ---
with col_right:
    st.subheader("⚙️ Export Center")
    with st.container(border=True):
        if st.session_state.selected:
            st.image(st.session_state.selected, use_container_width=True)
            def dl_link(lbl, size, fn):
                img = st.session_state.selected.copy()
                no_bg = remove(img)
                no_bg.thumbnail(size, Image.Resampling.LANCZOS)
                canvas = Image.new("RGBA", size, (0,0,0,0))
                canvas.paste(no_bg, ((size[0]-no_bg.size[0])//2, (size[1]-no_bg.size[1])//2))
                buf = io.BytesIO()
                canvas.save(buf, format="PNG")
                st.download_button(lbl, buf.getvalue(), fn, "image/png", use_container_width=True)
            
            dl_link("💾 Sticker (370x320)", (370, 320), "stk.png")
            dl_link("🖼️ Main Icon (240x240)", (240, 240), "main.png")
            dl_link("🔖 Tab Icon (96x74)", (96, 74), "tab.png")
        else:
            st.info("Pick an image.")
