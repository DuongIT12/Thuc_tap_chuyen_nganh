# model_logic.py
import joblib
import numpy as np
import os

# Đường dẫn đến file model (để tránh lỗi không tìm thấy file)
MODEL_PATH = 'saved_model.pkl'
ENCODER_PATH = 'style_encoder.pkl'

def analyze_student(data):
    """
    data: dictionary {'hours': int, 'stress_level': int, 'method_pref': str}
    """
    
    # Kiểm tra xem đã chạy file train_model.py chưa
    if not os.path.exists(MODEL_PATH):
        return {
            "style": "Lỗi hệ thống",
            "recommendations": ["Chưa tìm thấy model AI. Vui lòng chạy file train_model.py trước!"]
        }

    # 1. Tải Model và Encoder
    model = joblib.load(MODEL_PATH)
    le_style = joblib.load(ENCODER_PATH)

    # 2. Chuẩn bị dữ liệu đầu vào
    hours = int(data['hours'])
    stress = int(data['stress_level'])
    pref = data['method_pref'] # Ví dụ: 'visual'

    try:
        # Chuyển đổi phong cách học từ chữ sang số giống lúc train
        pref_encoded = le_style.transform([pref])[0]
    except ValueError:
        # Nếu user hack html gửi giá trị lạ
        pref_encoded = 0 

    # Tạo vector input [Giờ, Stress, Style_Số]
    input_vector = np.array([[hours, stress, pref_encoded]])

    # 3. Dự đoán (Predict)
    prediction = model.predict(input_vector)[0] # Kết quả: Ví dụ "Pomodoro"

    # 4. Sinh lời khuyên chi tiết dựa trên kết quả dự đoán
    recommendations = []
    
    if prediction == "Pomodoro":
        desc = "Phương pháp Quả cà chua (Pomodoro)"
        recommendations = [
            "AI phát hiện bạn có cường độ học hoặc mức stress cao.",
            "Hãy chia nhỏ thời gian: 25 phút học tập trung, 5 phút nghỉ.",
            "Tuyệt đối không dùng điện thoại trong 25 phút học."
        ]
    elif prediction == "MindMap":
        desc = "Sơ đồ tư duy (Mind Map)"
        recommendations = [
            "Bạn thiên về thị giác và thời gian học vừa phải.",
            "Hãy vẽ biểu đồ nối các ý chính lại với nhau.",
            "Sử dụng bút màu để kích thích trí nhớ."
        ]
    elif prediction == "GroupStudy":
        desc = "Học nhóm (Group Study)"
        recommendations = [
            "Bạn học tốt qua thính giác và giao tiếp.",
            "Hãy tìm một người bạn để giảng lại bài cho họ (Kỹ thuật Feynman).",
            "Thảo luận và tranh biện giúp bạn nhớ lâu hơn."
        ]
    else: # ProjectBased
        desc = "Học qua Dự án (Project-based)"
        recommendations = [
            "Bạn thích vận động và thực hành.",
            "Đừng chỉ đọc sách, hãy code hoặc làm bài tập ngay.",
            "Đặt ra một mục tiêu sản phẩm cụ thể để hoàn thành."
        ]

    return {
        "style": f"Mô hình đề xuất: {desc}",
        "recommendations": recommendations
    }