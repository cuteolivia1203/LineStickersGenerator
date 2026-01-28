import streamlit as st
import requests
import io
import urllib.parse
import time
import random
from PIL import Image
from rembg import remove

# --- 基礎配置 ---
st.set_page_config(page_title="Line Sticker Studio V15", layout="wide")

# --- 進階 CSS 美化 ---
st.markdown("""
    <style>
    /* 天藍色按鈕 (Sky Blue) */
    div.stButton > button:first-child {
        background-color: #00BFFF !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #1E90FF !important;
    }
    /* 灰色標籤樣式 (情緒選擇) */
    .stMultiSelect div[role="listbox"] span {
        background-color: #f0f2f6 !important;
        color: #31333F !important;
    }
    /* 強制網格高度，防止跑版 */
    .stImage > img {
        border-radius: 10px;
        aspect-ratio: 1 / 1;
        object-fit: cover;
    }
    /* 虛線框美化 */
    .placeholder-box {
        border: 2px dashed #00BFFF;
        border-radius: 12px;
        height: 200px;
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
    "title": "🎨 專業 LINE 貼圖製作 V15" if lang=="繁體中文" else "LINE Sticker Studio V15",
    "who": "主角描述 (Character)" if lang=="繁體中文" else "Who is the character?",
    "action": "細節 (Details)" if lang=="繁體中文" else "Actions & Details",
    "style": "風格 (Style)" if lang=="繁體中文" else "Art Style",
    "custom": "自訂風格 (Optional)" if lang=="繁體中文" else "Custom Style (Optional)",
    "mood_hint": "選擇情緒 (最多 8 個)" if lang=="繁體中文" else "Select Moods (Max 8)",
    "gen_btn": "🚀 開始批量生成" if lang=="繁體中文" else "🚀 Start Batch Generation",
    "export": "⚙️ 匯出中心 Export Center" if lang=="繁體中文" else "⚙️ Export Center",
    "redo": "🔄 重製" if lang=="繁體中文" else "🔄 Redo",
    "pick": "🎯 選取" if lang=="繁體中文" else "🎯 Pick"
}

st.title(cur["title"])

# --- UI 分欄配置 ---
col_left, col_right = st.columns([3, 1], gap="large")

with col_left:
    # 1. 輸入與控制區
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            char = st.text_area(cur["who"], "A cute baby giraffe", height=80)
            style_choice = st.selectbox(cur["style"], ["3D Pixar Render", "2D Flat Vector", "Crayon Style", "Custom"])
        with c2:
            detail = st.text_area(cur["action"], "wearing a blue hoodie", height=80)
            custom_input = st.text_input(cur["custom"], placeholder="e.g. Claymation, Oil Painting...")

    # 2. 情緒選擇 (平鋪排列感)
    mood_list = ["Hi", "OK", "Thank you", "Yes", "No", "Tired", "Sad", "Angry", "Surprise", "Happy"]
    selected_moods = st.multiselect(cur["mood_hint"], mood_list, default=["Happy", "OK", "Thank you"])
    
    # 數量限制防呆
    if len(selected_moods) > 8:
        st.error("⚠️ 一次最多隻能選擇 8 個情緒。" if lang=="繁體中文" else "⚠️ Max 8 moods allowed.")
        gen_disabled = True
    else:
        gen_disabled = False

    if st.button(cur["gen_btn"], disabled=gen_disabled):
        st.session_state.imgs = [None] * 8
        final_style = custom_input if (style_choice == "Custom" or custom_input) else style_choice
        
        for i, mood in enumerate(selected_moods):
            prompt = f"{char}, {mood}, {detail}, {final_style}, white background, isolated"
            # 簡化進度顯示字樣
            with st.spinner("Creating..."):
                time.sleep(2) # 減少伺服器頻率限制風險
                url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?nologo=true&seed={random.randint(1,9999)}&width=512&height=512"
                try:
                    r = requests.get(url, timeout=20)
                    if r.status_code == 200:
                        st.session_state.imgs[i] = {"img": Image.open(io.BytesIO(r.content)), "mood": mood, "p": prompt}
                        st.rerun() # 即時更新 Overview
                except: continue

    # 3. 圖片展示網格 (2x4 佈局)
    st.divider()
    m_cols = st.columns(4)
    for i in range(8):
        with m_cols[i % 4]:
            item = st.session_state.imgs[i]
            if item:
                st.image(item['img'], caption=f"#{i+1} {item['mood']}")
                # 小功能鍵
                b1, b2 = st.columns(2)
                if b1.button(cur["redo"], key=f"rd_{i}"):
                    with st.spinner("Creating..."):
                        new_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(item['p'])}?nologo=true&seed={random.randint(1,9999)}&width=512&height=512"
                        res = requests.get(new_url)
                        if res.status_code == 200:
                            st.session_state.imgs[i]['img'] = Image.open(io.BytesIO(res.content))
                            st.rerun()
                if b2.button(cur["pick"], key=f"pk_{i}"):
                    st.session_state.selected = item['img']
            else:
                # 虛線格佔位符
                st.markdown('<div class="placeholder-box">Slot</div>', unsafe_allow_html=True)

# --- 4. 右側匯出中心 ---
with col_right:
    st.subheader(cur["export"])
    exp_box = st.container(border=True)
    if st.session_state.selected:
        exp_box.image(st.session_state.selected, use_container_width=True)
        
        with st.spinner("Processing..."):
            def process_and_dl(lbl, size, filename):
                # 自動去背與尺寸調整
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
        exp_box.info("Pick an image to start." if lang=="English" else "請先點選圖片下方的 '選取' 按鈕。")
