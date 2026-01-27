import streamlit as st
import requests
import io
import urllib.parse
import time
import random
from PIL import Image
from rembg import remove

# --- 基礎設定 ---
st.set_page_config(page_title="Line Sticker Pro V10", layout="wide")
st.title("🎨 專業 LINE 貼圖製作 Studio V10")

# 初始化 Session
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = []
if 'current_seed' not in st.session_state:
    st.session_state.current_seed = random.randint(1000, 9999)

def get_sticker_file(img, size):
    # 自動去背並縮放
    no_bg = remove(img)
    no_bg.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    offset = ((size[0] - no_bg.size[0]) // 2, (size[1] - no_bg.size[1]) // 2)
    canvas.paste(no_bg, offset)
    
    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue(), canvas

# --- UI 側邊欄 ---
with st.sidebar:
    st.header("1. 主角與情境")
    char_base = st.text_input("主角 (例如: 橘貓)", "A cute orange cat")
    scenario = st.text_input("細節 (例如: 拿著咖啡)", "holding a coffee cup")
    
    st.header("2. 風格選單")
    style_choice = st.selectbox("風格：", ["3D Pixar Render", "2D Flat Vector", "Crayon Style"])
    
    st.header("3. 控制項")
    num_to_gen = st.slider("生成數量：", 1, 8, 4)
    if st.button("🔄 更換角色長相 (New Seed)"):
        st.session_state.current_seed = random.randint(1000, 9999)
        st.session_state.generated_images = []

# --- 主生成邏輯 ---
col_main, col_process = st.columns([3, 1])

with col_main:
    if st.button("🚀 開始生成貼圖批次"):
        style_map = {
            "3D Pixar Render": "3D Disney Pixar render, high detail, white background, isolated",
            "2D Flat Vector": "flat vector illustration, bold lines, white background, isolated",
            "Crayon Style": "crayon drawing, hand-drawn texture, white background, isolated"
        }
        actions = ["Happy", "Laughing", "Angry", "Sad", "Thinking", "Surprised", "Love", "ThumbsUp"]
        
        st.session_state.generated_images = []
        progress_bar = st.progress(0)
        
        for i in range(num_to_gen):
            action = actions[i % len(actions)]
            full_prompt = f"{char_base}, {action}, {scenario}, {style_map[style_choice]}"
            encoded = urllib.parse.quote(full_prompt)
            seed = st.session_state.current_seed + i
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true&seed={seed}"
            
            try:
                time.sleep(2.5) # 延長間隔避免 Rate Limit
                res = requests.get(url, timeout=30)
                if res.status_code == 200:
                    img = Image.open(io.BytesIO(res.content))
                    st.session_state.generated_images.append({"img": img, "action": action})
                progress_bar.progress((i + 1) / num_to_gen)
            except:
                st.error(f"第 {i+1} 張生成失敗，伺服器忙碌中。")
        st.success("生成結束！請從下方挑選喜歡的貼圖。")

    # 顯示網格
    if st.session_state.generated_images:
        cols = st.columns(4)
        for idx, item in enumerate(st.session_state.generated_images):
            with cols[idx % 4]:
                st.image(item['img'], caption=item['action'])
                if st.button(f"🎯 加工此張 #{idx+1}", key=f"sel_{idx}"):
                    st.session_state.selected_raw = item['img']

# --- 右側加工與下載區 ---
with col_process:
    st.subheader("⚙️ 匯出中心")
    if 'selected_raw' in st.session_state:
        st.image(st.session_state.selected_raw, use_container_width=True)
        
        # Sticker 下載
        st_data, st_img = get_sticker_file(st.session_state.selected_raw, (370, 320))
        st.download_button("💾 下載 Sticker (370x320)", st_data, "sticker.png", "image/png")
        
        st.divider()
        
        # Main 下載
        main_data, main_img = get_sticker_file(st.session_state.selected_raw, (240, 240))
        st.download_button("🖼️ 下載 Main Icon (240x240)", main_data, "main.png", "image/png")
        
        # Tab 下載
        tab_data, tab_img = get_sticker_file(st.session_state.selected_raw, (96, 74))
        st.download_button("🔖 下載 Tab Icon (96x74)", tab_data, "tab.png", "image/png")
    else:
        st.write("請先在左側點擊「🎯 加工此張」。")
