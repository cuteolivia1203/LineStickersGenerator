import streamlit as st
import requests
import io
import time
from PIL import Image
from rembg import remove

# --- Configuration ---
st.set_page_config(page_title="One-Click Sticker V3", layout="wide")
st.title("🎨 One-Click Sticker V3")
st.markdown("Upload your own photo or generate a unique character!")

# 從 Secrets 讀取 Token
HF_TOKEN = st.secrets.get("HF_TOKEN", "")
# 更換為更輕量且穩定的模型 API
API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def generate_image(prompt):
    # 增加更多重試次數與更長的等待時間
    for i in range(5):
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
        if response.status_code == 200:
            return response.content
        elif response.status_code == 503: # 模型正在加載
            time.sleep(5)
        else:
            time.sleep(2)
    return None

def process_for_line(img, target_size):
    # 去背處理
    no_bg = remove(img)
    # 保持比例縮放
    no_bg.thumbnail(target_size, Image.Resampling.LANCZOS)
    # 建立透明畫布並置中
    new_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
    offset = ((target_size[0] - no_bg.size[0]) // 2, (target_size[1] - no_bg.size[1]) // 2)
    new_img.paste(no_bg, offset)
    return new_img

# --- UI Interface ---
with st.sidebar:
    st.header("1. Source Selection")
    source_type = st.radio("Choose Source:", ["AI Generation", "My Photo Upload"])
    
    st.header("2. Character Design")
    if source_type == "AI Generation":
        char_input = st.text_area("Character Description (English is better):", "A cute white chubby bunny")
        user_prompt = st.text_input("Additional Prompts:", placeholder="wearing a crown, pixel art...")
    else:
        uploaded_file = st.file_uploader("Upload Image:", type=["png", "jpg", "jpeg"])
        char_input = "User Upload"

    st.header("3. Expression")
    emotion = st.selectbox("Select Emotion:", ["Happy", "Angry", "Sad", "Laughing", "Surprised", "Thinking"])

# --- Main Logic ---
if st.button("🚀 Generate & Process"):
    with st.spinner("Processing... The AI might need 10-20 seconds to wake up."):
        source_img = None
        
        if source_type == "My Photo Upload":
            if uploaded_file:
                source_img = Image.open(uploaded_file)
            else:
                st.warning("Please upload a file first!")
        else:
            # AI 生成路徑：組合更強大的提示詞
            full_prompt = f"Line sticker style, {char_input}, {emotion} expression, white background, bold lines, flat color, high resolution."
            raw_data = generate_image(full_prompt)
            if raw_data:
                try:
                    source_img = Image.open(io.BytesIO(raw_data))
                except:
                    st.error("Received data but cannot convert to image. Please try again.")
            else:
                st.error("AI is currently overloaded. Please wait 1 minute and try again.")

        if source_img:
            # 自動縮放至 Line 三種規範尺寸
            stk_img = process_for_line(source_img, (370, 320))
            main_icon = process_for_line(source_img, (240, 240))
            tab_icon = process_for_line(source_img, (96, 74))

            st.success("Success! Click buttons below to download.")
            
            # 展示結果與下載按鈕
            col1, col2, col3 = st.columns(3)
            with col1:
                st.image(stk_img, caption="Sticker (370x320)")
                buf = io.BytesIO()
                stk_img.save(buf, format="PNG")
                st.download_button("Download Sticker", buf.getvalue(), "sticker.png", "image/png")
            
            with col2:
                st.image(main_icon, caption="Main (240x240)")
            with col3:
                st.image(tab_icon, caption="Tab (96x74)")
