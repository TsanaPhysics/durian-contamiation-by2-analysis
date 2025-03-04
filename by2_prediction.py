import streamlit as st
import cv2
import numpy as np
from PIL import Image
from skimage.feature import local_binary_pattern
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

# ตั้งค่า UI แบบ Custom
st.set_page_config(page_title="ตรวจสอบ BY2 ทุเรียน", layout="wide")

# CSS สำหรับปรับแต่ง UI
st.markdown(
    """
    <style>
    body {
        background: linear-gradient(to right, #ffefba, #ffffff);
        font-family: 'Arial', sans-serif;
    }
    .stApp {
        background: linear-gradient(120deg, #ff9a9e, #fad0c4);
    }
    .title {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #ffffff;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    .risk-label {
        font-size: 1.2rem;
        font-weight: bold;
    }
    .uploaded-file {
        display: flex;
        justify-content: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<h1 class="title">🔍 ระบบวิเคราะห์โอกาสปนเปื้อน BY2 ในทุเรียน  🍌</h1>', unsafe_allow_html=True)

# เลือกโหมดการวิเคราะห์
mode = st.radio("เลือกโหมด:", ["📤 อัปโหลดภาพ", "📷 กล้อง Live"], horizontal=True)

def analyze_durian(image):
    img = np.array(image.convert('RGB'))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    avg_hue = np.mean(hsv[:, :, 0])  
    avg_saturation = np.mean(hsv[:, :, 1])  

    color_risk = 1 if (20 < avg_hue < 35 and avg_saturation > 120) else 0
    color_warning = "พบสีเหลืองผิดปกติ!" if color_risk else "สีปกติ"

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lbp = local_binary_pattern(gray, 8, 1, method='uniform')
    texture_score = np.histogram(lbp, bins=10)[0].var()

    texture_risk = 1 if texture_score < 500 else 0
    texture_warning = "พบพื้นผิวเรียบผิดปกติ!" if texture_risk else "พื้นผิวปกติ"

    contamination_risk = (color_risk + texture_risk) / 2 * 100

    return color_warning, texture_warning, contamination_risk

if mode == "📤 อัปโหลดภาพ":
    uploaded_file = st.file_uploader("📤 อัปโหลดภาพทุเรียน", type=["jpg", "png"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="📷 ภาพต้นฉบับ", use_column_width=True)

        color_warning, texture_warning, contamination_risk = analyze_durian(image)

        # แสดงผลลัพธ์
        st.markdown(f"### 🔬 **ผลการวิเคราะห์**")
        st.error(f"**สี:** {color_warning}")
        st.error(f"**พื้นผิว:** {texture_warning}")

        # แสดงระดับความเสี่ยง
        st.progress(int(contamination_risk))
        if contamination_risk > 70:
            st.error(f"🚨 **โอกาสการปนเปื้อนสูง: {contamination_risk:.2f}%**")
        elif contamination_risk > 30:
            st.warning(f"⚠️ **โอกาสการปนเปื้อนปานกลาง: {contamination_risk:.2f}%**")
        else:
            st.success(f"✅ **โอกาสการปนเปื้อนต่ำ: {contamination_risk:.2f}%**")

elif mode == "📷 กล้อง Live":
    class VideoTransformer(VideoTransformerBase):
        def transform(self, frame):
            img = frame.to_ndarray(format="bgr24")
            image_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            _, _, contamination_risk = analyze_durian(image_pil)

            # แสดงความเสี่ยงบนวิดีโอ
            color = (0, 255, 0) if contamination_risk < 30 else (0, 165, 255) if contamination_risk < 70 else (0, 0, 255)
            label = f"Risk: {contamination_risk:.2f}%"
            cv2.putText(img, label, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)
            
            return img

    webrtc_streamer(key="live", video_transformer_factory=VideoTransformer)
    
    
    # แสดงคำเตือนเรื่องความแม่นยำ
st.warning("⚠️ หมายเหตุ: การวิเคราะห์นี้เป็นการประเมินเบื้องต้น อาจมีความคลาดเคลื่อนขึ้นอยู่กับคุณภาพของภาพ กรุณาใช้ควบคู่กับการตรวจสอบด้วยตาเปล่า")

# ส่วนแนะนำการใช้งาน
with st.expander("ℹ️ คำแนะนำการใช้งาน"):
    st.markdown("""
    ✅ **วิธีถ่ายภาพเพื่อให้ได้ผลลัพธ์ที่แม่นยำ**  
    - **ระยะถ่ายภาพ**: ควรอยู่ห่างจากทุเรียนประมาณ **30-50 ซม.**  
    - **มุมกล้อง**: ถ่ายจากด้านบนตรงๆ หรือเอียงไม่เกิน **45 องศา**  
    - **แสง**: ใช้แสงธรรมชาติหรือแสงไฟสีขาว หลีกเลี่ยงแสงสีเหลืองหรือแสงน้อย  
    - **ความคมชัด**: ภาพต้องไม่เบลอและต้องโฟกัสที่พื้นผิวของทุเรียน  
    """)

# เพิ่มคำแนะนำสำหรับโหมด Live
if mode == "📷 กล้อง Live":
    st.info("📷 **เคล็ดลับการใช้โหมดกล้อง Live**\n- ถือกล้องให้นิ่งที่สุด\n- ใช้แสงที่เพียงพอ\n- วางทุเรียนในพื้นที่ที่ไม่มีเงาบัง")