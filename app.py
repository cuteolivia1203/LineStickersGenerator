import streamlit as st
import requests
import io
from PIL import Image, ImageOps
from rembg import remove

# --- 初始化設定 ---
st.set_page_config(page_title="Line Sticker Maker", layout="centered")
st.title("🎨 Line 貼圖自動生成器")

# 請確保在 Streamlit Cloud 的 Secrets 中設定了 HF_TOKEN
HF_TOKEN = st.secrets.get("HF_TOKEN", "")
API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def generate_image(prompt):
    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
    return response.content

def process_for_line(img, target_size):
    # 去背
    no_bg = remove(img)
    # 保持比例縮放，並填入透明背景
    no_bg.thumbnail(target_size, Image.Resampling.LANCZOS)
    new_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
    # 置中貼上
    upper = (target_size[0] - no_bg.size[0]) // 2
    left = (target_size[1] - no_bg.size[1]) // 2
    new_img.paste(no_bg, (upper, left))
    return new_img

# --- UI 介面 ---
with st.expander("✨ 角色設定", expanded=True):
    char_desc = st.text_input("你想設計什麼角色？", placeholder="例如：穿著西裝的橘貓、愛笑的珍珠奶茶...")
    style = st.selectbox("風格選擇", ["Flat Vector (簡約平面)", "Crayon (蠟筆手繪)", "3D Cartoon (立體卡通)"])

if st.button("🚀 開始生成專屬貼圖"):
    if not HF_TOKEN:
        st.error("請先在 Streamlit Secrets 中設定 HF_TOKEN！")
    elif not char_desc:
        st.warning("請輸入角色描述喔！")
    else:
        with st.spinner("AI 正在繪製並自動裁切尺寸中..."):
            # 組合 Prompt
            full_prompt = f"Line sticker style, {char_desc}, {style}, white background, thick outlines, expressive, centered."
            
            raw_data = generate_image(full_prompt)
            main_image = Image.open(io.BytesIO(raw_data))

            # 處理三種 Line 規範尺寸
            stk_img = process_for_line(main_image, (370, 320))
            main_icon = process_for_line(main_image, (240, 240))
            tab_icon = process_for_line(main_image, (96, 74))

            # 展示結果
            st.success("生成成功！請右鍵另存圖片 (手機長按)")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.image(stk_img, caption="貼圖 (370x320)")
            with col2:
                st.image(main_icon, caption="主圖 (240x240)")
            with col3:
                st.image(tab_icon, caption="標籤 (96x74)")

st.info("💡 提示：生成後直接下載即可符合 Line 上架規範。")
