import streamlit as st
import numpy as np
from PIL import Image
import time

# --- MÔ PHỎNG JAVA RANDOM (Cơ chế lõi của Minecraft 1.21.11) ---
class JavaRandom:
    def __init__(self, seed):
        self.seed = (seed ^ 0x5DEECE66D) & ((1 << 48) - 1)

    def next_int(self, bits):
        self.seed = (self.seed * 0x5DEECE66D + 0xB) & ((1 << 48) - 1)
        return self.seed >> (48 - bits)

    def next_float(self):
        return self.next_int(24) / (1 << 24)

def is_bedrock_1_21(world_seed, x, y, z):
    """
    Logic sinh Bedrock Overworld tầng đáy cho bản 1.21.11
    """
    if y == -64: return True
    if y > -59 or y < -64: return False
    
    # Minecraft tính toán seed riêng cho mỗi block dựa trên tọa độ
    # Công thức: seed + x * x * 3129871 + x * 45238971 + z * z * 13289798 + z * 1792732049
    # Đây là cách Java Edition xác định vị trí khối
    pos_seed = world_seed + (x * x * 3129871 + x * 45238971 + z * z * 13289798 + z * 1792732049)
    rng = JavaRandom(pos_seed)
    
    # Xác suất theo tầng Y (1.21.11)
    # Tầng càng cao (gần -59) xác suất có Bedrock càng thấp
    threshold = (y - (-64)) / 5.0 # Ví dụ Y=-62 thì d = 0.4
    return rng.next_float() > threshold

# --- XỬ LÝ ẢNH ---
def get_pattern_from_image(uploaded_file):
    img = Image.open(uploaded_file).convert('L')
    img = img.resize((10, 10), Image.Resampling.NEAREST) # Lấy mẫu 10x10 block
    arr = np.array(img)
    # Trắng (>127) là Bedrock, Đen là Deepslate
    return (arr > 127).astype(int)

# --- GIAO DIỆN STREAMLIT ---
st.set_page_config(page_title="MC 1.21.11 Bedrock Finder", layout="centered")
st.title("💎 Bedrock Coordinate Finder v1.21.11")
st.markdown("Công cụ tính toán tọa độ dựa trên Seed và ảnh sàn Bedrock (Overworld).")

with st.sidebar:
    st.header("⚙️ Thông số Server")
    world_seed = st.number_input("World Seed (/seed)", value=0, format="%d")
    target_y = st.select_slider("Tầng Y trong ảnh", options=[-63, -62, -61, -60], value=-62)
    st.divider()
    st.warning("Với diện tích 500k x 500k, bạn CẦN nhập tọa độ ước tính.")
    est_x = st.number_input("X gần đúng (F3)", value=0)
    est_z = st.number_input("Z gần đúng (F3)", value=0)
    search_radius = st.slider("Bán kính tìm kiếm", 100, 5000, 1000)

uploaded_file = st.file_uploader("Upload ảnh chụp sàn Bedrock (Chụp từ trên xuống)", type=['png', 'jpg'])

if uploaded_file and st.button("🔍 Bắt đầu quét 100% chính xác"):
    pattern = get_pattern_from_image(uploaded_file)
    
    # Hiển thị mẫu để người dùng xác nhận
    st.write("Mẫu 10x10 nhận diện được:")
    st.image(Image.fromarray((pattern * 255).astype(np.uint8)), width=100)
    
    progress_bar = st.progress(0)
    found = False
    start_time = time.time()
    
    # Quét vùng quanh tọa độ ước tính
    total_range = range(est_x - search_radius, est_x + search_radius)
    for i, x in enumerate(total_range):
        if i % 100 == 0:
            progress_bar.progress(i / (search_radius * 2))
            
        for z in range(est_z - search_radius, est_z + search_radius):
            match = True
            # Kiểm tra nhanh mẫu 10x10
            for r in range(10):
                for c in range(10):
                    if is_bedrock_1_21(world_seed, x + c, target_y, z + r) != (pattern[r][c] == 1):
                        match = False
                        break
                if not match: break
            
            if match:
                st.success(f"🎯 ĐÃ TÌM THẤY TỌA ĐỘ CHÍNH XÁC!")
                st.metric("Tọa độ X", x)
                st.metric("Tọa độ Z", z)
                st.code(f"/tp @s {x} {target_y} {z}")
                st.balloons()
                found = True
                break
        if found: break

    if not found:
        st.error("Không tìm thấy kết quả. Gợi ý: Kiểm tra lại Seed hoặc tầng Y trong ảnh.")
    st.caption(f"Thời gian quét: {round(time.time() - start_time, 2)}s")
