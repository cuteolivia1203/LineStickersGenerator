import streamlit as st
import requests
import io
import urllib.parse
import time
import random
from PIL import Image
from rembg import remove

# --- 基礎配置 ---
st.set_page_config(page_title="Line Sticker Studio V19", layout="wide")

# --- CSS 視覺美化 ---
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #00BFFF !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
    }
    span[data-baseweb="tag"] {
        background-color: #555555 !important;
        color: white !important;
    }
    .stImage > img { border-radius: 12px; aspect-ratio: 1 / 1; object-fit: cover; }
    .slot-placeholder {
        border: 2px dashed #00BFFF;
        border-radius: 12px;
        height: 220px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #00BFFF;
        opacity: 0.3;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 語系與文字配置 ---
lang = st.sidebar.selectbox("🌐 Language", ["繁體中文", "English"], index=0)

texts = {
    "繁體中文": {
        "title": "🎨 專業 LINE 貼圖製作 V19",
        "who": "1. 主角描述", "action": "細節/動作", "style": "風格",
        "custom": "自訂風格 (Optional)", "mood_hint": "情緒標籤 (Optional, Max 8)",
        "gen_btn": "🚀 開始批量生成", "qty": "計畫生成張數 (Quantity)",
        "redo": "🔄 重製", "pick": "🎯 選取",
        "upload_title": "2. 或上傳照片 (Or Upload)",
        "err_too_many": "⚠️ 標籤數量 ({}) 大於預計生成張數 ({})。請增加數量或移除標籤。",
        "warn_less": "💡 選取了 {} 個情緒，其餘 {} 張將隨機生成。",
        "pick_info": "請生成或上傳圖片來開始。",
        "creating": "正在生成中..."
    },
    "English": {
        "title": "🎨 Pro Sticker Studio V19",
        "who": "1. Character Description", "action": "Details/Actions", "style": "Art Style",
        "custom": "Custom Style (Optional)", "mood_hint": "Mood Tags (Optional, Max 8)",
        "gen_btn": "🚀 Start Batch Generation", "qty": "Quantity",
        "redo": "🔄 Redo", "pick": "🎯 Pick",
        "upload_title": "2. Or Upload Photo",
        "err_too_many": "⚠️ Tag count ({}) exceeds planned quantity ({}). Please increase Quantity or remove tags.",
        "warn_less": "💡 {} moods selected. Remaining {} will be random.",
        "pick_info": "Generate or upload an image to start.",
        "creating": "Creating..."
    }
}
cur = texts[lang]

# --- 側邊欄：上傳功能 ---
st.sidebar.divider()
st.sidebar.subheader(cur["upload_title"])
uploaded_file = st.sidebar.file_uploader("Upload for background removal", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # 若上傳檔案，直接存入 session_state 的選取狀態
    st.session_state.selected = Image.open(uploaded_file)

# --- 主介面 ---
st.title(cur["title"])
if 'imgs' not in st.session_state: st.session_state.imgs = [None] * 8
if 'selected' not in st.session_state: st.session_state.selected = None

col_left, col_right = st.columns([3, 1], gap="large")

with col_left:
    # 1. 輸入區
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            char = st.text_area(cur["who"], "A cute white rabbit", height=70)
            style_choice = st.selectbox(cur["style"], ["3D Pixar Render", "2D Flat Vector", "Crayon Style", "Custom"])
        with c2:
            detail = st.text_area(cur["action"], "wearing a blue rosette", height=70)
            custom_input = st.text_input(cur["custom"], placeholder="e.g. Cyberpunk...")
        with c3:
            qty = st.slider(cur["qty"], 1, 8, 4)

    # 2. 情緒標籤與防呆
    st.write(f"**{cur['mood_hint']}**")
    mood_list = ["Hi", "OK", "Thank you", "Yes", "No", "Tired", "Sad", "Angry", "Surprise", "Happy"]
    selected_moods = st.multiselect("Mood tags", mood_list, default=["Happy"], label_visibility="collapsed")
    
    mood_count = len(selected_moods)
    gen_disabled = False
    if mood_count > qty:
        st.error(cur["err_too_many"].format(mood_count, qty))
        gen_disabled = True
    elif 0 < mood_count < qty:
        st.warning(cur["warn_less"].format(mood_count, qty - mood_count))

    if st.button(cur["gen_btn"], use_container_width=True, disabled=gen_disabled):
        st.session_state.imgs = [None] * 8
        final_style = custom_input if (style_choice == "Custom" or custom_input) else style_choice
        for i in range(qty):
            m = selected_moods[i] if i < mood_count else ""
            p = f"{char}, {m}, {detail}, {final_style}, white background, isolated"
            with st.spinner(cur["creating"]):
                time.sleep(1)
                url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}?nologo=true&seed={random.randint(1,9999)}&width=512&height=512"
                try:
                    r = requests.get(url, timeout=20)
                    if r.status_code == 200:
                        st.session_state.imgs[i] = {"img": Image.open(io.BytesIO(r.content)), "mood": m, "p": p}
                        st.rerun()
                except: continue

    # 3. 網格展示
    st.divider()
    m_cols = st.columns(4)
    for i in range(8):
        with m_cols[i % 4]:
            item = st.session_state.imgs[i]
            if item:
                st.image(item['img'], caption=item['mood'])
                b1, b2 = st.columns(2)
                if b1.button(cur["redo"], key=f"rd_{i}"):
                    new_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(item['p'])}?nologo=true&seed={random.randint(1,9999)}"
                    st.session_state.imgs[i]['img'] = Image.open(io.BytesIO(requests.get(new_url).content))
                    st.rerun()
                if b2.button(cur["pick"], key=f"pk_{i}"):
                    st.session_state.selected = item['img']
            else:
                st.markdown('<div class="slot-placeholder">Empty Slot</div>', unsafe_allow_html=True)

# --- 4. 匯出中心 ---
with col_right:
    st.subheader("⚙️ Export Center")
    with st.container(border=True):
        if st.session_state.selected:
            st.image(st.session_state.selected, use_container_width=True)
            with st.spinner("Processing..."):
                def dl_btn(lbl, size, fn):
                    no_bg = remove(st.session_state.selected)
                    no_bg.thumbnail(size, Image.Resampling.LANCZOS)
                    canvas = Image.new("RGBA", size, (0,0,0,0))
                    canvas.paste(no_bg, ((size[0]-no_bg.size[0])//2, (size[1]-no_bg.size[1])//2))
                    buf = io.BytesIO()
                    canvas.save(buf, format="PNG")
                    st.download_button(lbl, buf.getvalue(), fn, "image/png", use_container_width=True)
                dl_btn("💾 Sticker (370x320)", (370, 320), "stk.png")
                dl_btn("🖼️ Main Icon (240x240)", (240, 240), "icon.png")
                dl_btn("🔖 Tab Icon (96x74)", (96, 74), "tab.png")
        else:
            st.info(cur["pick_info"])
