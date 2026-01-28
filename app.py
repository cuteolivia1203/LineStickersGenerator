import streamlit as st
import requests
import io
import urllib.parse
import time
import random
from PIL import Image
from rembg import remove

# --- 基礎配置 ---
st.set_page_config(page_title="Line Sticker Pro V13", layout="wide")

# --- 語言與狀態初始化 ---
if 'lang' not in st.session_state: st.session_state.lang = "繁體中文"
if 'imgs' not in st.session_state: st.session_state.imgs = [None] * 8
if 'seed' not in st.session_state: st.session_state.seed = random.randint(1000, 9999)
if 'selected' not in st.session_state: st.session_state.selected = None

# 介面文字字典
L = {
    "繁體中文": {
        "title": "🎨 專業 LINE 貼圖製作 Studio V13",
        "tab_ai": "🤖 AI 全自動生成", "tab_upload": "📤 上傳現成圖片",
        "who": "主角是誰？", "action": "動作細節", "style": "藝術風格",
        "mood_title": "選擇情緒文字 (最多 8 個)", "gen_btn": "🚀 開始批量生成",
        "export": "⚙️ 匯出中心", "redo": "🔄 重試", "pick": "🎯 選取",
        "placeholder": "點擊下方 'Pick' 預覽並匯出",
    },
    "English": {
        "title": "🎨 Pro LINE Sticker Studio V13",
        "tab_ai": "🤖 AI Generation", "tab_upload": "📤 Upload Photo",
        "who": "Character?", "action": "Details", "style": "Art Style",
        "mood_title": "Quick Mood Tags (Max 8)", "gen_btn": "🚀 Start Batch Generation",
        "export": "⚙️ Export Center", "redo": "🔄 Redo", "pick": "🎯 Pick",
        "placeholder": "Click 'Pick' to preview & export",
    }
}
cur = L[st.session_state.lang]

# --- 頂部導航欄 ---
t1, t2 = st.columns([8, 2])
with t1: st.title(cur["title"])
with t2:
    st.session_state.lang = st.selectbox("🌐 Language", ["繁體中文", "English"])

# --- 主要內容區 ---
col_left, col_right = st.columns([3.2, 1], gap="medium")

with col_left:
    tab1, tab2 = st.tabs([cur["tab_ai"], cur["tab_upload"]])
    
    with tab1:
        # 輸入區
        c1, c2 = st.columns(2)
        with c1:
            char = st.text_area(cur["who"], "A cute baby giraffe", height=80)
            style_choice = st.selectbox(cur["style"], ["3D Pixar Render", "2D Flat Vector", "Crayon Style", "Custom"])
        with c2:
            detail = st.text_area(cur["action"], "wearing a yellow hoodie", height=80)
            custom_style = st.text_input("Custom Style Input", disabled=(style_choice != "Custom"))

        # 情緒快捷勾選
        st.write(f"**{cur['mood_title']}**")
        mood_options = ["Hi", "OK", "Thank you", "Yes", "No", "Tired", "Sad", "Angry", "Surprise", "Happy"]
        selected_moods = st.multiselect("Select Moods", mood_options, default=["Happy", "OK", "Thank you", "Hi"])
        
        if st.button(cur["gen_btn"], type="primary", use_container_width=True):
            if len(selected_moods) > 8:
                st.warning("請最多選擇 8 個情緒。")
            else:
                st.session_state.imgs = [None] * 8 # 重置
                final_style = custom_style if style_choice == "Custom" else style_choice
                
                for i, mood in enumerate(selected_moods):
                    prompt = f"{char}, {mood}, {detail}, {final_style}, white background, isolated"
                    with st.spinner(f"Generating {mood}..."):
                        time.sleep(2.5) # 避開 Rate Limit
                        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?nologo=true&seed={st.session_state.seed + i}&width=512&height=512"
                        try:
                            r = requests.get(url, timeout=25)
                            if r.status_code == 200:
                                img = Image.open(io.BytesIO(r.content))
                                st.session_state.imgs[i] = {"img": img, "mood": mood, "prompt": prompt}
                                st.rerun() # 達成一張張跳出來的效果
                        except: continue

    with tab2:
        uploaded_file = st.file_uploader("上傳圖片進行去背與 LINE 規格化", type=["png", "jpg", "jpeg"])
        if uploaded_file:
            up_img = Image.open(uploaded_file)
            st.image(up_img, width=300)
            if st.button("🎯 加工此上傳圖"):
                st.session_state.selected = up_img

    # --- 圖片展示網格 (Overview) ---
    st.divider()
    m_cols = st.columns(4)
    for i in range(8):
        with m_cols[i % 4]:
            item = st.session_state.imgs[i]
            if item:
                # 已生成圖片展示
                st.image(item['img'], caption=item['mood'])
                b1, b2 = st.columns(2)
                if b1.button(cur["redo"], key=f"rd_{i}"):
                    # 單張重製邏輯
                    new_seed = random.randint(1, 9999)
                    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(item['prompt'])}?nologo=true&seed={new_seed}&width=512&height=512"
                    new_r = requests.get(url)
                    if new_r.status_code == 200:
                        st.session_state.imgs[i]['img'] = Image.open(io.BytesIO(new_r.content))
                        st.rerun()
                if b2.button(cur["pick"], key=f"pk_{i}"):
                    st.session_state.selected = item['img']
            else:
                # 預想的虛線格子
                st.markdown(
                    f'<div style="border: 2px dashed #ccc; border-radius: 10px; height: 180px; display: flex; align-items: center; justify-content: center; color: #ccc;">Placeholder {i+1}</div>', 
                    unsafe_allow_html=True
                )

# --- 右側匯出中心 ---
with col_right:
    st.subheader(cur["export"])
    exp_container = st.container(border=True)
    if st.session_state.selected:
        exp_container.image(st.session_state.selected, use_container_width=True)
        
        with st.spinner("Processing..."):
            # 自動處理三種規格
            def process_and_dl(lbl, size, filename):
                # 去背
                no_bg = remove(st.session_state.selected)
                no_bg.thumbnail(size, Image.Resampling.LANCZOS)
                canvas = Image.new("RGBA", size, (0,0,0,0))
                canvas.paste(no_bg, ((size[0]-no_bg.size[0])//2, (size[1]-no_bg.size[1])//2))
                buf = io.BytesIO()
                canvas.save(buf, format="PNG")
                exp_container.download_button(lbl, buf.getvalue(), filename, "image/png", use_container_width=True)

            process_and_dl("💾 Sticker (370x320)", (370, 320), "sticker.png")
            process_and_dl("🖼️ Main Icon (240x240)", (240, 240), "main.png")
            process_and_dl("🔖 Tab Icon (96x74)", (96, 74), "tab.png")
    else:
        exp_container.info(cur["placeholder"])
