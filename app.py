import streamlit as st
import requests
import io
import urllib.parse
import time
import random
from PIL import Image
from rembg import remove

# --- 語言字典設定 ---
LANG = {
    "繁體中文": {
        "title": "🎨 專業 LINE 貼圖製作 Studio V11",
        "char_label": "主角是誰？",
        "char_pld": "例如: 穿西裝的橘貓...",
        "detail_label": "動作與細節 (中英皆可)",
        "detail_pld": "例如: 拿著咖啡杯, 正在工作...",
        "style_label": "風格選擇",
        "gen_btn": "🚀 開始批量生成",
        "proc_btn": "🎯 選擇此張加工",
        "export_title": "⚙️ 匯出中心",
        "dl_stk": "💾 下載 Sticker (370x320)",
        "dl_main": "🖼️ 下載 Main Icon (240x240)",
        "dl_tab": "🔖 下載 Tab Icon (96x74)",
        "refresh": "🔄 更換角色基因",
    },
    "English": {
        "title": "🎨 Pro LINE Sticker Studio V11",
        "char_label": "Who is the character?",
        "char_pld": "e.g., An orange cat in a suit...",
        "detail_label": "Actions & Details",
        "detail_pld": "e.g., holding coffee, working...",
        "style_label": "Art Style",
        "gen_btn": "🚀 Start Batch Generation",
        "proc_btn": "🎯 Process This One",
        "export_title": "⚙️ Export Center",
        "dl_stk": "💾 Download Sticker (370x320)",
        "dl_main": "🖼️ Download Main Icon (240x240)",
        "dl_tab": "🔖 Download Tab Icon (96x74)",
        "refresh": "🔄 Change Character DNA",
    }
}

# --- 基礎設定 ---
st.set_page_config(page_title="Line Sticker Pro", layout="wide")

# 介面語言切換切換
with st.container():
    col_t, col_l = st.columns([8, 2])
    with col_l:
        lang_choice = st.selectbox("🌐 Language", ["繁體中文", "English"])
    cur = LANG[lang_choice]

st.title(cur["title"])

# 初始化狀態
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = []
if 'current_seed' not in st.session_state:
    st.session_state.current_seed = random.randint(1000, 9999)

def get_sticker_file(img, size):
    no_bg = remove(img)
    no_bg.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    offset = ((size[0] - no_bg.size[0]) // 2, (size[1] - no_bg.size[1]) // 2)
    canvas.paste(no_bg, offset)
    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue()

# --- UI 側邊欄 ---
with st.sidebar:
    st.header(cur["char_label"])
    char_base = st.text_input(cur["char_label"], "A cute giraffe", label_visibility="collapsed")
    
    st.header(cur["detail_label"])
    scenario = st.text_input(cur["detail_label"], "holding a coffee cup", label_visibility="collapsed")
    
    style_choice = st.selectbox(cur["style_label"], ["3D Pixar Render", "2D Flat Vector", "Crayon Style"])
    
    num_to_gen = st.slider("Quantity:", 1, 8, 4)
    if st.button(cur["refresh"]):
        st.session_state.current_seed = random.randint(1000, 9999)
        st.session_state.generated_images = []

# --- 生成邏輯 ---
col_main, col_process = st.columns([3, 1])

with col_main:
    if st.button(cur["gen_btn"]):
        # 這裡會自動加上 3D 或 2D 的強效指令，解決您之前 3D 變 2D 的問題
        style_map = {
            "3D Pixar Render": "3D Disney Pixar render, volumetric lighting, high detail, white background, isolated",
            "2D Flat Vector": "flat vector art, clean thick lines, white background, isolated",
            "Crayon Style": "crayon drawing, hand-drawn texture, white background, isolated"
        }
        actions = ["Happy", "Angry", "Sad", "Thinking", "Surprised", "Love", "Laughing", "Fighting"]
        
        st.session_state.generated_images = []
        progress_bar = st.progress(0)
        
        for i in range(num_to_gen):
            action = actions[i % len(actions)]
            # 組合指令
            full_prompt = f"{char_base}, {action}, {scenario}, {style_map[style_choice]}"
            encoded = urllib.parse.quote(full_prompt)
            seed = st.session_state.current_seed + i
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true&seed={seed}"
            
            try:
                time.sleep(3) # 為了躲避 RATE LIMIT，間隔調長一點點
                res = requests.get(url, timeout=30)
                if res.status_code == 200:
                    img = Image.open(io.BytesIO(res.content))
                    st.session_state.generated_images.append({"img": img, "action": action})
                progress_bar.progress((i + 1) / num_to_gen)
            except:
                continue
        st.success("Success!")

    if st.session_state.generated_images:
        cols = st.columns(4)
        for idx, item in enumerate(st.session_state.generated_images):
            with cols[idx % 4]:
                st.image(item['img'], caption=item['action'])
                if st.button(cur["proc_btn"], key=f"sel_{idx}"):
                    st.session_state.selected_raw = item['img']

# --- 加工區 ---
with col_process:
    st.subheader(cur["export_title"])
    if 'selected_raw' in st.session_state:
        st.image(st.session_state.selected_raw, use_container_width=True)
        
        # 下載區域
        with st.spinner("Preparing files..."):
            stk_data = get_sticker_file(st.session_state.selected_raw, (370, 320))
            st.download_button(cur["dl_stk"], stk_data, "sticker.png", "image/png")
            
            main_data = get_sticker_file(st.session_state.selected_raw, (240, 240))
            st.download_button(cur["dl_main"], main_data, "main.png", "image/png")
            
            tab_data = get_sticker_file(st.session_state.selected_raw, (96, 74))
            st.download_button(cur["dl_tab"], tab_data, "tab.png", "image/png")
