import streamlit as st
import requests
import io
import urllib.parse
import time
import random
from PIL import Image
from rembg import remove

st.set_page_config(page_title="Line Sticker Maker V9", layout="wide")
st.title("🎨 AI Line Sticker Studio V9 (Stable & Pro)")

# 初始化狀態
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = []
if 'current_seed' not in st.session_state:
    st.session_state.current_seed = random.randint(1000, 9999)

def process_sticker(img, target_size):
    # 優化去背：針對白背景強化辨識
    no_bg = remove(img)
    no_bg.thumbnail(target_size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
    offset = ((target_size[0] - no_bg.size[0]) // 2, (target_size[1] - no_bg.size[1]) // 2)
    canvas.paste(no_bg, offset)
    return canvas

# --- UI 側邊欄 ---
with st.sidebar:
    st.header("1. 主角設定")
    char_base = st.text_input("主角是誰？", "A super cute giraffe")
    scenario = st.text_input("穿著/特徵 (選填)", "wearing a red scarf")
    
    st.header("2. 風格選擇")
    style_choice = st.selectbox("風格類型：", [
        "3D Render (Pixar Style)", 
        "2D Flat Vector (LINE Style)", 
        "Cute Anime",
        "Hand-drawn Crayon"
    ])
    
    st.header("3. 批量控制")
    num_to_gen = st.slider("生成張數：", 1, 8, 4)
    if st.button("🔄 更換角色基因 (Change Seed)"):
        st.session_state.current_seed = random.randint(1000, 9999)
        st.session_state.generated_images = []

# --- 生成邏輯 ---
col_main, col_process = st.columns([3, 1])

with col_main:
    if st.button("🚀 開始製作貼圖"):
        # 風格關鍵字優化：加入 'no background objects' 確保乾淨
        style_map = {
            "3D Render (Pixar Style)": "3D render, Disney Pixar style, high detail, white background, isolated, single character, no extra objects",
            "2D Flat Vector (LINE Style)": "flat vector art, LINE sticker style, bold outlines, solid colors, white background, isolated",
            "Cute Anime": "kawaii anime style, big eyes, vibrant colors, white background, isolated",
            "Hand-drawn Crayon": "crayon illustration, hand-drawn texture, white background, isolated"
        }
        
        actions = ["Happy", "Laughing", "Angry", "Sad", "Thinking", "Surprised", "Love", "Thumbs Up"]
        batch_actions = actions[:num_to_gen]
        
        st.session_state.generated_images = []
        progress_bar = st.progress(0)
        
        for i, action in enumerate(batch_actions):
            # 組合更嚴謹的 Prompt
            full_prompt = f"{char_base}, {action} expression, {scenario}, {style_map[style_choice]}, sticker set, masterwork, high resolution"
            encoded = urllib.parse.quote(full_prompt)
            seed = st.session_state.current_seed + i
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={seed}"
            
            try:
                # 間隔 2 秒避免被判定為惡意攻擊
                time.sleep(2)
                res = requests.get(url, timeout=30)
                if res.status_code == 200:
                    img = Image.open(io.BytesIO(res.content))
                    # 預先處理去背，讓同仁直接看結果
                    processed_img = process_sticker(img, (370, 320))
                    st.session_state.generated_images.append({"img": processed_img, "action": action})
                progress_bar.progress((i + 1) / len(batch_actions))
            except:
                continue
        st.success(f"完成！已生成 {len(st.session_state.generated_images)} 張穩定貼圖。")

    # 顯示結果
    if st.session_state.generated_images:
        cols = st.columns(4)
        for idx, item in enumerate(st.session_state.generated_images):
            with cols[idx % 4]:
                st.image(item['img'], caption=item['action'])
                if st.button(f"選中這張 #{idx+1}", key=f"sel_{idx}"):
                    st.session_state.selected_img = item['img']

# --- 加工區 (圖標轉換) ---
with col_process:
    st.subheader("⚙️ 圖標匯出")
    if 'selected_img' in st.session_state:
        st.image(st.session_state.selected_img, use_container_width=True)
        # 提供 240x240 與 96x74 的轉換
        if st.button("製作 Main Icon (240x240)"):
            icon = st.session_state.selected_img.resize((240, 240), Image.Resampling.LANCZOS)
            st.image(icon)
            # 下載邏輯...
