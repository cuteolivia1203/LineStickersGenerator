import streamlit as st
import requests
import io
import time
from PIL import Image
from rembg import remove

# --- Configuration ---
st.set_page_config(page_title="One-Click Sticker V2", layout="wide")
st.title("🎨 One-Click Sticker V2")
st.markdown("Upload your own photo or generate a character from scratch!")

HF_TOKEN = st.secrets.get("HF_TOKEN", "")
# 使用更穩定的模型 API
API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def generate_image(prompt):
    # 增加重試機制，防止 "cannot identify image file" 錯誤
    for i in range(3):
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
        if response.status_code == 200:
            return response.content
        time.sleep(2)
    return None

def process_for_line(img, target_size):
    no_bg = remove(img)
    no_bg.thumbnail(target_size, Image.Resampling.LANCZOS)
    new_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
    offset = ((target_size[0] - no_bg.size[0]) // 2, (target_size[1] - no_bg.size[1]) // 2)
    new_img.paste(no_bg, offset)
    return new_img

# --- Sidebar: User Inputs ---
with st.sidebar:
    st.header("1. Choose Source")
    source_type = st.radio("Source:", ["Generate by AI", "Upload My Photo"])
    
    st.header("2. Character & Style")
    if source_type == "Generate by AI":
        char_input = st.text_area("Describe Character:", "A cute chubby white rabbit")
    else:
        uploaded_file = st.file_uploader("Upload your photo:", type=["png", "jpg", "jpeg"])
        char_input = "Original User Photo"

    user_prompt = st.text_input("Custom Prompt (Optional):", placeholder="e.g. wearing a crown, galaxy background")
    
    st.header("3. Emotion / Action")
    emotion = st.selectbox("Select Expression:", 
                          ["Happy", "Angry", "Sad", "Love", "Surprised", "Thinking", "Laughing", "Sleepy"])

# --- Main Logic ---
if st.button("🚀 Create My Sticker"):
    with st.spinner("Processing... This may take a moment."):
        source_img = None
        
        if source_type == "Upload My Photo":
            if uploaded_file:
                source_img = Image.open(uploaded_file)
            else:
                st.warning("Please upload a photo first!")
        else:
            # AI Generation Path
            full_prompt = f"Line sticker style, {char_input}, {emotion} expression, {user_prompt}, white background, bold outlines, flat design."
            raw_data = generate_image(full_prompt)
            if raw_data:
                source_img = Image.open(io.BytesIO(raw_data))
            else:
                st.error("AI is busy or loading. Please try again in 10 seconds.")

        if source_img:
            # Process Sizes
            stk_img = process_for_line(source_img, (370, 320))
            main_icon = process_for_line(source_img, (240, 240))
            tab_icon = process_for_line(source_img, (96, 74))

            # Display
            st.success("Successfully Processed!")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.image(stk_img, caption="Sticker (370x320)")
                # 下載按鈕 (Streamlit 下載邏輯)
                buf = io.BytesIO()
                stk_img.save(buf, format="PNG")
                st.download_button("Download Sticker", buf.getvalue(), "sticker.png", "image/png")
            
            with col2:
                st.image(main_icon, caption="Main (240x240)")
            with col3:
                st.image(tab_icon, caption="Tab (96x74)")

st.info("💡 Note: For uploaded photos, the AI currently only performs background removal and resizing. It won't 'change' your face to a different emotion yet.")
