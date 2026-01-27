import streamlit as st
import requests
import io
import urllib.parse
from PIL import Image
from rembg import remove

# --- 設定 ---
st.set_page_config(page_title="Line Sticker Maker V5", layout="wide")
st.title("🎨 AI Line Sticker Maker (Free & Stable)")

def process_sticker(img, target_size):
    # 自動去背
    no_bg = remove(img)
    # 縮放並保持比例
    no_bg.thumbnail(target_size, Image.Resampling.LANCZOS)
    # 建立透明背景畫布並置中
    canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
    offset = ((target_size[0] - no_bg.size[0]) // 2, (target_size[1] - no_bg.size[1]) // 2)
    canvas.paste(no_bg, offset)
    return canvas

# --- UI 介面 ---
with st.sidebar:
    st.header("1. Create Character")
    char_desc = st.text_input("Character description:", "A cute orange cat")
    emotion = st.selectbox("Emotion:", ["Happy", "Laughing", "Angry", "Sad", "Shocked", "Thinking"])
    custom_prompt = st.text_input("Custom Prompts (Optional):", placeholder="wearing a hat, galaxy style...")
    
    st.header("2. Or Upload Photo")
    uploaded_file = st.file_uploader("Upload for background removal:", type=["png", "jpg", "jpeg"])

# --- 生成邏輯 ---
if st.button("🚀 Start Generating"):
    with st.spinner("Processing... Please wait about 10 seconds."):
        raw_img = None
        
        if uploaded_file:
            # 優先處理上傳的照片
            raw_img = Image.open(uploaded_file)
        else:
            # 組合嵌入式系統 Prompt
            # 這裡就是您要的：將複雜的貼圖規範 Prompt 隱藏在後端
            base_prompt = f"Line sticker style, {char_desc}, {emotion}, {custom_prompt}, white background, bold outlines, flat vector illustration, high resolution, centered"
            encoded_prompt = urllib.parse.quote(base_prompt)
            
            # 使用 Pollinations 免費 API (無需 Key)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
            
            response = requests.get(image_url)
            if response.status_code == 200:
                raw_img = Image.open(io.BytesIO(response.content))
            else:
                st.error("Service is temporarily busy. Please try again.")

        if raw_img:
            # 執行去背與 LINE 規格縮放
            stk = process_sticker(raw_img, (370, 320))
            main = process_sticker(raw_img, (240, 240))
            tab = process_sticker(raw_img, (96, 74))

            st.success("Successfully created! Long-press or right-click to save.")
            
            # 顯示結果與下載
            c1, c2, c3 = st.columns(3)
            with c1:
                st.image(stk, caption="Sticker (370x320)")
                buf = io.BytesIO()
                stk.save(buf, format="PNG")
                st.download_button("Download Sticker", buf.getvalue(), "sticker.png", "image/png")
            with c2:
                st.image(main, caption="Main Icon (240x240)")
            with c3:
                st.image(tab, caption="Tab Icon (96x74)")
