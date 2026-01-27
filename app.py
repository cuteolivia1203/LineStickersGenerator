import streamlit as st
import requests
import io
import urllib.parse
import random
from PIL import Image
from rembg import remove

# --- 基礎設定 ---
st.set_page_config(page_title="Line Sticker Maker V8", layout="wide")
st.title("🎨 Professional Line Sticker Studio V8")

# 初始化 Session
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = []
if 'current_seed' not in st.session_state:
    st.session_state.current_seed = random.randint(1000, 9999)

def process_sticker(img, target_size):
    no_bg = remove(img)
    no_bg.thumbnail(target_size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
    offset = ((target_size[0] - no_bg.size[0]) // 2, (target_size[1] - no_bg.size[1]) // 2)
    canvas.paste(no_bg, offset)
    return canvas

# --- UI 側邊欄 ---
with st.sidebar:
    st.header("1. Character Definition")
    char_base = st.text_input("Who is the main character?", "A cute white rabbit")
    
    st.header("2. Scenario & Details")
    scenario = st.text_input("What is happening? (Optional)", "wearing a blue rosette")
    
    st.header("3. Artistic Style")
    style_choice = st.selectbox("Style Mode:", [
        "3D Pixar Render (High Detail)", 
        "2D Flat Vector", 
        "Traditional Crayon", 
        "Modern Anime"
    ])
    
    st.header("4. Batch Control")
    num_to_gen = st.slider("Quantity:", 1, 8, 8)
    if st.button("🔄 Change Character Identity"):
        st.session_state.current_seed = random.randint(1000, 9999)
        st.session_state.generated_images = []

# --- 主生成邏輯 ---
col_main, col_process = st.columns([3, 1])

with col_main:
    if st.button("🚀 Start Production"):
        # 強化的風格關鍵字矩陣
        style_keywords = {
            "3D Pixar Render (High Detail)": "3D render, Disney Pixar style, unreal engine 5, octan render, high detail, volumetric lighting, subsurface scattering",
            "2D Flat Vector": "flat vector illustration, minimalist, solid colors, clean lines",
            "Traditional Crayon": "crayon drawing, textured paper, hand-drawn, soft edges",
            "Modern Anime": "anime style, cel shaded, vibrant colors, expressive eyes"
        }
        
        actions = ["Happy", "Laughing", "Angry", "Sad", "Thinking", "Surprised", "Love", "Thumbs Up"]
        batch_actions = actions[:num_to_gen]
        
        with st.spinner(f"Manufacturing {num_to_gen} stickers..."):
            new_batch = []
            for i, action in enumerate(batch_actions):
                # 組合終極 Prompt
                full_prompt = f"Line sticker, {char_base}, {action} expression, {scenario}, {style_keywords[style_choice]}, white background, bold outlines, centered"
                encoded = urllib.parse.quote(full_prompt)
                
                # 固定 Seed 是維持一致性的關鍵
                seed = st.session_state.current_seed + i
                url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true&seed={seed}"
                
                try:
                    res = requests.get(url, timeout=30)
                    if res.status_code == 200:
                        img = Image.open(io.BytesIO(res.content))
                        new_batch.append({"img": img, "action": action})
                except:
                    continue
            st.session_state.generated_images = new_batch

    # 網格顯示
    if st.session_state.generated_images:
        rows = (len(st.session_state.generated_images) + 3) // 4
        for r in range(rows):
            cols = st.columns(4)
            for c in range(4):
                idx = r * 4 + c
                if idx < len(st.session_state.generated_images):
                    item = st.session_state.generated_images[idx]
                    with cols[c]:
                        st.image(item['img'], caption=f"#{idx+1} {item['action']}")
                        if st.button(f"Choose #{idx+1}", key=f"sel_{idx}"):
                            st.session_state.selected_img = item['img']

# --- 加工區 (保持不變但優化介面) ---
with col_process:
    st.subheader("⚙️ Final Export")
    if 'selected_img' in st.session_state:
        st.image(st.session_state.selected_img, use_container_width=True)
        # ... (其餘下載按鈕邏輯與 V7 相同)
