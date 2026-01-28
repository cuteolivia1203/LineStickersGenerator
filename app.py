import streamlit as st
import requests
import io
import urllib.parse
import time
import random
from PIL import Image
from rembg import remove

# --- 基礎配置 ---
st.set_page_config(page_title="Line Sticker Studio V16", layout="wide")

# --- 進階 CSS (標籤與按鈕樣式) ---
st.markdown("""
    <style>
    /* 天藍色主要按鈕 */
    div.stButton > button:first-child {
        background-color: #00BFFF !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
    }
    /* 模擬平鋪標籤按鈕 (深灰色) */
    .mood-btn {
        display: inline-block;
        background-color: #555555;
        color: white;
        padding: 5px 15px;
        margin: 4px;
        border-radius: 15px;
        font-size: 14px;
        cursor: pointer;
        border: none;
    }
    /* 圖片格子固定比例與美化 */
    .stImage > img {
        border-radius: 12px;
        aspect-ratio: 1 / 1;
        object-fit: cover;
        border: 1px solid #eee;
    }
    /* 虛線格佔位 */
    .dotted-box {
        border: 2px dashed #00BFFF;
        border-radius: 12px;
        height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #00BFFF;
        opacity: 0.4;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 狀態初始化 ---
if 'imgs' not in st.session_state: st.session_state.imgs = [None] * 8
if 'selected' not in st.session_state: st.session_state.selected = None
if 'active_moods' not in st.session_state: st.session_state.active_moods = []

# --- 介面文字與語言 ---
lang = st.sidebar.selectbox("🌐 Language", ["繁體中文", "English"], index=0)
cur = {
    "title": "🎨 專業 LINE 貼圖製作 V16",
    "who": "主角描述", "action": "動作/細節", "style": "預設風格",
    "custom": "自訂風格 (Optional)", "mood_hint": "點選情緒 (Optional, Max 8)",
    "gen_btn": "🚀 開始批量生成", "qty": "生成張數 (Quantity)",
    "redo": "🔄 重製", "pick": "🎯 選取"
} if lang=="繁體中文" else {
    "title": "🎨 Pro Sticker Studio V16",
    "who": "Character", "action": "Details", "style": "Art Style",
    "custom": "Custom Style (Optional)", "mood_hint": "Select Moods (Optional, Max 8)",
    "gen_btn": "🚀 Start Batch Generation", "qty": "Quantity",
    "redo": "🔄 Redo", "pick": "🎯 Pick"
}

st.title(cur["title"])

# --- 主要佈局 ---
col_left, col_right = st.columns([3, 1], gap="large")

with col_left:
    # 1. 核心輸入區
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            char = st.text_area(cur["who"], "A cute baby giraffe", height=70)
            style_choice = st.selectbox(cur["style"], ["3D Pixar Render", "2D Flat Vector", "Crayon Style", "Custom"])
        with c2:
            detail = st.text_area(cur["action"], "wearing a hoodie", height=70)
            custom_input = st.text_input(cur["custom"], placeholder="e.g. Cyberpunk...")
        with c3:
            # 找回生成張數選項
            qty = st.slider(cur["qty"], 1, 8, 4)

    # 2. 平鋪式情緒標籤 (Optional)
    st.write(f"**{cur['mood_hint']}**")
    mood_list = ["Hi", "OK", "Thank you", "Yes", "No", "Tired", "Sad", "Angry", "Surprise", "Happy"]
    
    # 使用 multiselect 但透過 CSS 模擬深灰色標籤外觀
    selected_moods = st.multiselect("Mood tags picker", mood_list, default=["Happy", "OK"], label_visibility="collapsed")
    
    if len(selected_moods) > 8:
        st.error("⚠️ 一次最多只能選擇 8 個。")
        gen_disabled = True
    else:
        gen_disabled = False

    if st.button(cur["gen_btn"], use_container_width=True, disabled=gen_disabled):
        st.session_state.imgs = [None] * 8
        final_style = custom_input if (style_choice == "Custom" or custom_input) else style_choice
        
        # 依照張數(qty)或選中的情緒進行生成
        loop_count = max(len(selected_moods), qty)
        if loop_count > 8: loop_count = 8

        for i in range(loop_count):
            mood = selected_moods[i] if i < len(selected_moods) else ""
            prompt = f"{char}, {mood}, {detail}, {final_style}, white background, isolated"
            
            with st.spinner("Creating..."):
                time.sleep(1.5)
                url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?nologo=true&seed={random.randint(1,9999)}&width=512&height=512"
                try:
                    r = requests.get(url, timeout=20)
                    if r.status_code == 200:
                        st.session_state.imgs[i] = {"img": Image.open(io.BytesIO(r.content)), "mood": mood, "p": prompt}
                        st.rerun()
                except: continue

    # 3. 圖片網格 (Overview)
    st.divider()
    m_cols = st.columns(4)
    for i in range(8):
        with m_cols[i % 4]:
            item = st.session_state.imgs[i]
            if item:
                st.image(item['img'], caption=f"{item['mood']}")
                b1, b2 = st.columns(2)
                if b1.button(cur["redo"], key=f"rd_{i}"):
                    with st.spinner("Creating..."):
                        new_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(item['p'])}?nologo=true&seed={random.randint(1,9999)}&width=512&height=512"
                        st.session_state.imgs[i]['img'] = Image.open(io.BytesIO(requests.get(new_url).content))
                        st.rerun()
                if b2.button(cur["pick"], key=f"pk_{i}"):
                    st.session_state.selected = item['img']
            else:
                st.markdown('<div class="dotted-box">Empty Slot</div>', unsafe_allow_html=True)

# --- 4. 右側匯出中心 ---
with col_right:
    st.subheader("⚙️ Export Center")
    with st.container(border=True):
        if st.session_state.selected:
            st.image(st.session_state.selected, use_container_width=True)
            
            def export_img(lbl, size, fname):
                no_bg = remove(st.session_state.selected)
                no_bg.thumbnail(size, Image.Resampling.LANCZOS)
                canvas = Image.new("RGBA", size, (0,0,0,0))
                canvas.paste(no_bg, ((size[0]-no_bg.size[0])//2, (size[1]-no_bg.size[1])//2))
                buf = io.BytesIO()
                canvas.save(buf, format="PNG")
                st.download_button(lbl, buf.getvalue(), fname, "image/png", use_container_width=True)

            export_img("💾 Sticker (370x320)", (370, 320), "sticker.png")
            export_img("🖼️ Main Icon (240x240)", (240, 240), "icon.png")
            export_img("🔖 Tab Icon (96x74)", (96, 74), "tab.png")
        else:
            st.info("Pick an image to start." if lang=="English" else "請先選取圖片。")
