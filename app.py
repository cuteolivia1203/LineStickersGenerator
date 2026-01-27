import streamlit as st
import requests
import io
import urllib.parse
import random
from PIL import Image
from rembg import remove

# --- 設定 ---
st.set_page_config(page_title="Line Sticker Maker V7", layout="wide")
st.title("🎨 Professional Line Sticker Studio")

# 初始化 Session State (用來儲存生成結果和 Seed)
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = []
if 'current_seed' not in st.session_state:
    st.session_state.current_seed = random.randint(1, 999999)

def process_sticker(img, target_size):
    no_bg = remove(img)
    no_bg.thumbnail(target_size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
    offset = ((target_size[0] - no_bg.size[0]) // 2, (target_size[1] - no_bg.size[1]) // 2)
    canvas.paste(no_bg, offset)
    return canvas

# --- UI 側邊欄 ---
with st.sidebar:
    st.header("1. Design")
    char_desc = st.text_input("Character:", "A cute white rabbit")
    style_choice = st.selectbox("Style:", ["2D Vector", "3D Cartoon", "Crayon", "Anime"])
    
    st.header("2. Control")
    num_to_gen = st.slider("How many to generate?", 1, 12, 4)
    if st.button("🔄 Refresh Seed (Change Character)"):
        st.session_state.current_seed = random.randint(1, 999999)
        st.session_state.generated_images = []
    
    st.info(f"Current Character ID: {st.session_state.current_seed}")

# --- 主畫面 ---
col_main, col_process = st.columns([3, 1])

with col_main:
    if st.button("🚀 Generate New Batch"):
        actions = ["Happy", "Laughing", "Angry", "Sad", "Thinking", "Surprised", "Love", "Thumbs Up", "Cool", "Sleepy", "Fighting", "Running"]
        batch_actions = actions[:num_to_gen]
        
        with st.spinner("AI is creating..."):
            new_imgs = []
            for action in batch_actions:
                base_prompt = f"Line sticker, {char_desc}, {action}, {style_choice}, white background, bold outlines"
                encoded = urllib.parse.quote(base_prompt)
                # 使用固定的 Seed + 動作偏移量，確保主角一致
                seed = st.session_state.current_seed + len(new_imgs)
                url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true&seed={seed}"
                
                res = requests.get(url)
                if res.status_code == 200:
                    img = Image.open(io.BytesIO(res.content))
                    new_imgs.append({"img": img, "action": action})
            
            st.session_state.generated_images.extend(new_imgs)

    # 顯示所有生成的圖片 (每列 4 張)
    if st.session_state.generated_images:
        st.subheader("Pick your favorites (Basic 370x320 px)")
        cols = st.columns(4)
        for idx, item in enumerate(st.session_state.generated_images):
            with cols[idx % 4]:
                st.image(item['img'], caption=f"{item['action']}")
                if st.button(f"Pick #{idx+1}", key=f"pick_{idx}"):
                    st.session_state.selected_img = item['img']
                    st.success(f"Selected #{idx+1} for Icon processing!")

# --- 處理選中的圖片 ---
with col_process:
    st.subheader("⚙️ Icon Converter")
    if 'selected_img' in st.session_state:
        st.image(st.session_state.selected_img, caption="Processing this one...")
        
        if st.button("Convert to Main (240x240)"):
            icon = process_sticker(st.session_state.selected_img, (240, 240))
            st.image(icon)
            buf = io.BytesIO()
            icon.save(buf, format="PNG")
            st.download_button("Download Main Icon", buf.getvalue(), "main_icon.png")
            
        if st.button("Convert to Tab (96x74)"):
            tab = process_sticker(st.session_state.selected_img, (96, 74))
            st.image(tab)
            buf = io.BytesIO()
            tab.save(buf, format="PNG")
            st.download_button("Download Tab Icon", buf.getvalue(), "tab_icon.png")
