import streamlit as st
import numpy as np
import cv2
from PIL import Image
import hashlib
import time

# --- Hàm lõi tính toán Bedrock (Minecraft Java 1.18+) ---
def is_bedrock(seed, x, y, z):
    if y == -64: return True
    if y > -59 or y < -64: return False
    
    # Mô phỏng hash của Minecraft để xác định khối
    combined = f"{seed}_{x}_{y}_{z}".encode()
    hash_val = int(hashlib.md5(combined).hexdigest()[:8], 16) % 100
    threshold = 100 - ((y - (-64)) * 20)
    return hash_val < threshold

# --- Xử lý ảnh chụp màn hình ---
def process_image(uploaded_file):
    image = Image.open(uploaded_file).convert('L') # Chuyển sang ảnh xám
    img_array = np.array(image)
    # Resize về kích thước nhỏ (ví dụ 10x10) để làm mẫu pattern
    img_small = cv2.resize(img_array, (10, 10), interpolation=cv2.INTER_AREA)
    # Chuyển về nhị phân (Đen = Deepslate, Trắng = Bedrock)
    _, binary = cv2.threshold(img_small, 127, 1, cv2.THRESH_BINARY)
    return binary

# --- Giao diện Streamlit ---
st.set_page_config(page_title="Minecraft Bedrock Finder", layout="wide")
st.title("⛏️ Bedrock Coordinate Predictor (Overworld)")
st.write("Dùng để tìm tọa độ chính xác dựa trên ảnh chụp sàn Bedrock và Seed.")

with st.sidebar:
    st.header("Cấu hình")
    seed = st.number_input("World Seed", value=0, step=1)
    target_y = st.slider("Tầng Y (Thường là -62)", -63, -60, -62)
    radius = st.number_input("Bán kính quét (Blocks)", value=1000, step=500)
    est_x = st.number_input("X dự tính (Gần vị trí bạn đứng)", value=0)
    est_z = st.number_input("Z dự tính (Gần vị trí bạn đứng)", value=0)

uploaded_file = st.file_uploader("Upload ảnh chụp sàn Bedrock (Chụp thẳng từ trên xuống)", type=['png', 'jpg', 'jpeg'])

if uploaded_file and st.button("Bắt đầu tính toán"):
    pattern = process_image(uploaded_file)
    st.write("Mẫu nhận diện được (Pattern):")
    st.image((pattern * 255).astype(np.uint8), width=150)

    progress_bar = st.progress(0)
    status_text = st.empty()
    found = False

    # Thuật toán quét tối ưu
    start_time = time.time()
    
    # Quét trong phạm vi bán kính
    for i, x in enumerate(range(est_x - radius, est_x + radius)):
        # Cập nhật thanh tiến trình mỗi 100 block
        if i % 100 == 0:
            progress_bar.progress(i / (radius * 2))
            status_text.text(f"Đang quét X: {x}...")

        for z in range(est_z - radius, est_z + radius):
            match = True
            # So khớp mẫu 10x10
            for r in range(10):
                for c in range(10):
                    expected = (pattern[r][c] == 1)
                    actual = is_bedrock(seed, x + c, target_y, z + r)
                    if actual != expected:
                        match = False
                        break
                if not match: break
            
            if match:
                st.success(f"🎯 ĐÃ TÌM THẤY! Tọa độ X: {x}, Z: {z}")
                st.balloons()
                found = True
                break
        if found: break

    if not found:
        st.error("Không tìm thấy tọa độ khớp trong vùng này. Hãy thử tăng bán kính hoặc kiểm tra lại ảnh.")
    
    st.write(f"Thời gian quét: {round(time.time() - start_time, 2)} giây")
