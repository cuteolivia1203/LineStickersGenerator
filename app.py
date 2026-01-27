import streamlit as st
import requests
import io
from PIL import Image
from rembg import remove

# --- Configuration ---
st.set_page_config(page_title="Line Sticker Generator", layout="centered")
st.title("🎨 AI Line Sticker Generator")

# Get HF_TOKEN from Streamlit Secrets
HF_TOKEN = st.secrets.get("HF_TOKEN", "")
API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def generate_image(prompt):
    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
    return response.content

def process_for_line(img, target_size):
    # Remove background
    no_bg = remove(img)
    # Resize while maintaining aspect ratio
    no_bg.thumbnail(target_size, Image.Resampling.LANCZOS)
    # Create a transparent canvas
    new_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
    # Paste centered
    offset = ((target_size[0] - no_bg.size[0]) // 2, (target_size[1] - no_bg.size[1]) // 2)
    new_img.paste(no_bg, offset)
    return new_img

# --- UI Interface ---
with st.expander("✨ Character Settings", expanded=True):
    char_desc = st.text_input("Describe your character", placeholder="e.g., A cool shiba inu wearing a hoodie...")
    style = st.selectbox("Style Choice", [
        "Flat Vector (Minimalist)", 
        "Crayon & Hand-drawn", 
        "3D Cartoon Render",
        "Kawaii Anime Style"
    ])

if st.button("🚀 Generate Stickers"):
    if not HF_TOKEN:
        st.error("Missing HF_TOKEN! Please check your Streamlit Secrets.")
    elif not char_desc:
        st.warning("Please enter a character description!")
    else:
        with st.spinner("AI is drawing and resizing for Line regulations..."):
            # Combine Prompt
            full_prompt = f"Line sticker style, {char_desc}, {style}, white background, thick outlines, expressive, centered."
            
            try:
                raw_data = generate_image(full_prompt)
                main_image = Image.open(io.BytesIO(raw_data))

                # Process 3 standard Line sizes
                stk_img = process_for_line(main_image, (370, 320))
                main_icon = process_for_line(main_image, (240, 240))
                tab_icon = process_for_line(main_image, (96, 74))

                st.success("Generated! Right-click or long-press to save.")
                
                # Display Results
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.image(stk_img, caption="Sticker (370x320)")
                with col2:
                    st.image(main_icon, caption="Main Image (240x240)")
                with col3:
                    st.image(tab_icon, caption="Tab Icon (96x74)")
            except Exception as e:
                st.error(f"Error: {e}. Please try again.")

st.info("💡 Tip: Images are automatically resized and background-removed to meet Line's official upload requirements.")
