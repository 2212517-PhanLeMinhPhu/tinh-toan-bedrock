import streamlit as st
import numpy as np
from PIL import Image
import hashlib
import time

# --- Hàm tính toán Bedrock (Mô phỏng Java) ---
def is_bedrock(seed, x, y, z):
    if y == -64: return True
    if y > -59 or y < -64: return False
    
    # Logic Hashing của Minecraft
    combined = f"{seed}_{x}_{y}_{z}".encode()
    hash_val = int(hashlib.md5(combined).hexdigest()[:8], 16) % 100
    threshold = 100 - ((y - (-64)) * 20)
    return hash_val < threshold

# --- Xử lý ảnh bằng Pillow (Thay thế OpenCV) ---
def process_image_pil(uploaded_file, size=(10, 10)):
    img = Image.open(uploaded_file).convert('L') # Chuyển ảnh xám
    img = img.resize(size, Image.Resampling.LANCZOS) # Resize về mẫu nhỏ
    img_array = np.array(img)
    # Ngưỡng nhị phân: Trên 128 là trắng (Bedrock), dưới là đen
    binary_pattern = (img_array > 128).astype(int)
    return binary_pattern

# --- Giao diện Streamlit ---
st.set_page_config(page_title="Minecraft Bedrock Finder", page_icon="⛏️")
st.title("⛏️ Bedrock Finder (Overworld 1.18+)")

with st.sidebar:
    st.header("⚙️ Cấu hình")
    seed = st.number_input("World Seed", value=0)
    target_y = st.slider("Tầng Y cần quét", -63, -60, -62)
    st.divider()
    st.info("Vì diện tích 500k x 500k rất lớn, hãy nhập tọa độ gần đúng để thu hẹp vùng tìm kiếm.")
    est_x = st.number_input("X gần đúng", value=0)
    est_z = st.number_input("Z gần đúng", value=0)
    radius = st.number_input("Bán kính quét (nên < 2000)", value=500, step=100)

uploaded_file = st.file_uploader("Upload ảnh chụp sàn Bedrock", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    pattern = process_image_pil(uploaded_file)
    st.subheader("Mẫu nhận diện (10x10):")
    st.image(Image.fromarray((pattern * 255).astype(np.uint8)), width=150)

    if st.button("🚀 Bắt đầu quét tọa độ"):
        found = False
        start_time = time.time()
        progress_bar = st.progress(0)
        status = st.empty()

        # Quét khu vực quanh tọa độ dự đoán
        total_steps = radius * 2
        for i, x in enumerate(range(est_x - radius, est_x + radius)):
            # Cập nhật UI mỗi 50 hàng để tăng tốc độ
            if i % 50 == 0:
                progress_bar.progress(i / total_steps)
                status.text(f"🔍 Đang kiểm tra cột X: {x}...")

            for z in range(est_z - radius, est_z + radius):
                match = True
                # So khớp nhanh mẫu 10x10
                for r in range(10):
                    for c in range(10):
                        if is_bedrock(seed, x + c, target_y, z + r) != (pattern[r][c] == 1):
                            match = False
                            break
                    if not match: break
                
                if match:
                    st.success(f"🎯 TÌM THẤY! Tọa độ chính xác: X: {x}, Z: {z}")
                    st.code(f"/tp @s {x} {target_y} {z}")
                    st.balloons()
                    found = True
                    break
            if found: break

        if not found:
            st.warning("❌ Không tìm thấy mẫu khớp. Hãy thử tăng bán kính hoặc đổi tầng Y.")
        
        st.write(f"⏱️ Thời gian thực thi: {round(time.time() - start_time, 2)} giây")
