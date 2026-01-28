import streamlit as st
import requests
import io
import urllib.parse
import time
import random
from PIL import Image
from rembg import remove

# --- 基礎配置 ---
st.set_page_config(page_title="Line Sticker Pro V14", layout="wide")

# --- 自定義 CSS (強制修改按鍵顏色與美化虛線) ---
st.markdown("""
    <style>
    /* 天藍色按鈕樣式 */
    div.stButton > button {
        background-color: #00BFFF !important;
        color: white !important;
        border: None !important;
        border-radius: 8px !important;
    }
    div.stButton > button:hover {
        background-color: #1E90FF !important;
        color: white !important;
    }
    /* 針對情緒標籤的選中狀態美化 */
    .mood-tag-active {
        background-color: #00BFFF;
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        display: inline-block;
        margin: 5px;
        cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

# --- 狀態初始化 ---
if 'imgs' not in st.session_state: st.session_state.imgs = [None] * 8
if 'selected' not in st.session_state: st.session_state.selected = None
if 'active_moods' not in st.session_state: st.session_state.active_moods = []

# 語言選擇
lang = st.sidebar.selectbox("🌐 Language", ["English", "繁體中文"], index=1)
cur = {
    "who": "主角描述" if lang=="繁體中文" else "Who is the character?",
    "action": "額外細節" if lang=="繁體中文" else "Details",
    "style": "預設風格" if lang=="繁體中文" else "Art Style",
    "custom": "自訂風格 (選填 Optional)" if lang=="繁體中文" else "Custom Style (Optional)",
    "mood_hint": "點選情緒 (最多 8 個)" if lang=="繁體中文" else "Select Moods (Max 8)",
    "gen_btn": "🚀 開始批量生成" if lang=="繁體中文" else "🚀 Start Batch Generation",
    "redo": "🔄 重試" if lang=="繁體中文" else "🔄 Redo",
    "pick": "🎯 選取" if lang=="繁體中文" else "🎯 Pick"
}

st.title(f"🎨 {('專業 LINE 貼圖製作' if lang=='繁體中文' else 'Pro Line Sticker Studio')}")

# --- UI 配置 ---
col_left, col_right = st.columns([3, 1], gap="large")

with col_left:
    # 1. 輸入區
    c1, c2 = st.columns(2)
    with c1:
        char = st.text_area(cur["who"], "A cute baby giraffe", height=80)
        style_choice = st.selectbox(cur["style"], ["3D Pixar Render", "2D Flat Vector", "Crayon Style", "Custom"])
    with c2:
        detail = st.text_area(cur["action"], "wearing a hoodie", height=80)
        # 修復：讓自訂輸入框永遠可用，但在標籤上註明 Optional
        custom_input = st.text_input(cur["custom"], placeholder="e.g. Oil Painting, Cyberpunk...")

    # 2. 情緒勾選區 (平鋪式設計)
    st.write(f"**{cur['mood_hint']}**")
    mood_list = ["Hi", "OK", "Thank you", "Yes", "No", "Tired", "Sad", "Angry", "Surprise", "Happy"]
    
    # 這裡使用多選框但限制數量
    selected_moods = st.multiselect("Mood Tags", mood_list, default=["Happy", "OK"], label_visibility="collapsed")
    
    if len(selected_moods) > 8:
        st.error("⚠️ 已超過上限！一次最多隻能選擇 8 個情緒。 (Max 8 selection allowed)" if lang=="繁體中文" else "⚠️ Limit reached! Max 8 selection.")
        gen_disabled = True
    else:
        gen_disabled = False

    if st.button(cur["gen_btn"], use_container_width=True, disabled=gen_disabled):
        st.session_state.imgs = [None] * 8
        final_style = custom_input if (style_choice == "Custom" or custom_input) else style_choice
        
        for i, mood in enumerate(selected_moods):
            prompt = f"{char}, {mood}, {detail}, {final_style}, white background, isolated"
            with st.spinner(f"Creating {mood}..."):
                time.sleep(2)
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
                st.image(item['img'], caption=item['mood'])
                b1, b2 = st.columns(2)
                if b1.button(cur["redo"], key=f"rd_{i}"):
                    # 重新生成單張
                    new_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(item['p'])}?nologo=true&seed={random.randint(1,9999)}&width=512&height=512"
                    res = requests.get(new_url)
                    if res.status_code == 200:
                        st.session_state.imgs[i]['img'] = Image.open(io.BytesIO(res.content))
                        st.rerun()
                if b2.button(cur["pick"], key=f"pk_{i}"):
                    st.session_state.selected = item['img']
            else:
                # 虛線格
                st.markdown('<div style="border: 2px dashed #00BFFF; border-radius: 12px; height: 180px; display: flex; align-items: center; justify-content: center; color: #00BFFF; opacity: 0.5;">Empty Slot</div>', unsafe_allow_html=True)

# --- 4. 右側匯出中心 ---
with col_right:
    st.subheader("⚙️ Export Center")
    exp_box = st.container(border=True)
    if st.session_state.selected:
        exp_box.image(st.session_state.selected, use_container_width=True)
        
        def process_and_dl(lbl, size, filename):
            no_bg = remove(st.session_state.selected)
            no_bg.thumbnail(size, Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", size, (0,0,0,0))
            canvas.paste(no_bg, ((size[0]-no_bg.size[0])//2, (size[1]-no_bg.size[1])//2))
            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            exp_box.download_button(lbl, buf.getvalue(), filename, "image/png", use_container_width=True)

        process_and_dl("💾 Sticker (370x320)", (370, 320), "sticker.png")
        process_and_dl("🖼️ Main Icon (240x240)", (240, 240), "main.png")
        process_and_dl("🔖 Tab Icon (96x74)", (96, 74), "tab.png")
    else:
        exp_box.info("Pick an image to export.")
