import streamlit as st
import requests
import io
import urllib.parse
import time
import random
from PIL import Image
from rembg import remove

# --- 設定 ---
st.set_page_config(page_title="Line Sticker Pro V12", layout="wide")

# --- 語言與介面設定 ---
if 'lang' not in st.session_state: st.session_state.lang = "English"

# 頂部切換欄
t1, t2 = st.columns([9, 1])
with t2:
    st.session_state.lang = st.selectbox("🌐", ["English", "繁體中文"], index=0 if st.session_state.lang=="English" else 1)

L = {
    "title": "Pro LINE Sticker Generator" if st.session_state.lang=="English" else "專業 LINE 貼圖生成器",
    "who": "Who is the character?" if st.session_state.lang=="English" else "主角是誰？",
    "action": "Actions & Details" if st.session_state.lang=="English" else "動作與細節描述",
    "style": "Art Style" if st.session_state.lang=="English" else "美術風格",
    "custom": "Custom Style (Optional)" if st.session_state.lang=="English" else "自訂風格 (選填)",
    "gen_btn": "🚀 Start Batch Generation" if st.session_state.lang=="English" else "🚀 開始批次生成",
    "export": "⚙️ Export Center" if st.session_state.lang=="English" else "⚙️ 匯出中心",
    "redo": "🔄 Redo" if st.session_state.lang=="English" else "🔄 重試",
}

st.title(f"✨ {L['title']}")

# 初始化狀態
if 'imgs' not in st.session_state: st.session_state.imgs = [None] * 8
if 'seed' not in st.session_state: st.session_state.seed = random.randint(1000, 9999)

def get_img(prompt, s):
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?nologo=true&seed={s}&width=512&height=512"
    try:
        r = requests.get(url, timeout=20)
        return Image.open(io.BytesIO(r.content)) if r.status_code == 200 else None
    except: return None

# --- UI 配置 ---
col_left, col_right = st.columns([3, 1], gap="large")

with col_left:
    # 第一排：輸入區
    c1, c2 = st.columns(2)
    with c1:
        char = st.text_area(L['who'], "A cute baby giraffe", height=100)
    with c2:
        detail = st.text_area(L['action'], "wearing a hoodie, studying with a laptop", height=100)
    
    # 第二排：風格與數量
    s1, s2, s3 = st.columns([1, 1, 1])
    with s1:
        preset_style = st.selectbox(L['style'], ["3D Pixar Render", "2D Flat Vector", "Crayon Style", "Custom"])
    with s2:
        custom_style = st.text_input(L['custom'], disabled=(preset_style != "Custom"))
    with s3:
        num = st.slider("Quantity", 1, 8, 4)

    if st.button(L['gen_btn'], use_container_width=True, type="primary"):
        st.session_state.imgs = [None] * 8 # 重置
        final_style = custom_style if preset_style == "Custom" else preset_style
        style_p = f"{final_style}, white background, isolated, high quality"
        actions = ["Happy", "Angry", "Sad", "Surprised", "Love", "Laughing", "Thinking", "Fighting"]
        
        for i in range(num):
            prompt = f"{char}, {actions[i]}, {detail}, {style_p}"
            # 逐張生成的視覺效果
            with st.spinner(f"Creating {actions[i]}..."):
                time.sleep(2) # 減少 Rate Limit 風險
                res = get_img(prompt, st.session_state.seed + i)
                if res: st.session_state.imgs[i] = {"img": res, "act": actions[i], "p": prompt}
                st.rerun()

# --- 中間下方：貼圖展示區 ---
st.divider()
if any(st.session_state.imgs):
    m_cols = st.columns(4)
    for i in range(8):
        item = st.session_state.imgs[i]
        if item:
            with m_cols[i % 4]:
                st.image(item['img'], caption=item['act'])
                # 單張重製與選取
                b1, b2 = st.columns(2)
                if b1.button(L['redo'], key=f"redo_{i}"):
                    with st.spinner("Refining..."):
                        new_res = get_img(item['p'], random.randint(1, 9999))
                        if new_res: 
                            st.session_state.imgs[i]['img'] = new_res
                            st.rerun()
                if b2.button("🎯 Pick", key=f"pick_{i}"):
                    st.session_state.selected = item['img']

# --- 右側：匯出中心 ---
with col_right:
    st.subheader(L['export'])
    container = st.container(border=True)
    if 'selected' in st.session_state:
        container.image(st.session_state.selected)
        
        def dl_btn(lbl, size, key):
            # 自動去背與縮放邏輯
            processed = remove(st.session_state.selected)
            processed.thumbnail(size, Image.Resampling.LANCZOS)
            bg = Image.new("RGBA", size, (0,0,0,0))
            bg.paste(processed, ((size[0]-processed.size[0])//2, (size[1]-processed.size[1])//2))
            buf = io.BytesIO()
            bg.save(buf, format="PNG")
            container.download_button(lbl, buf.getvalue(), f"{key}.png", "image/png", use_container_width=True)

        dl_btn("💾 Sticker (370x320)", (370, 320), "stk")
        dl_btn("🖼️ Main Icon (240x240)", (240, 240), "main")
        dl_btn("🔖 Tab Icon (96x74)", (96, 74), "tab")
    else:
        container.info("Click 'Pick' on any image to export.")
