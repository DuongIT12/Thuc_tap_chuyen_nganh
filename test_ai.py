# File: check_model.py
from google import genai

# Dán API Key của bạn vào đây
API_KEY = "AIzaSyBDFoYmRtRKtO9c4o_MJfQwOSWNybWtBH0"

try:
    client = genai.Client(api_key=API_KEY)
    print("------- DANH SÁCH MODEL KHẢ DỤNG -------")
    # Lấy danh sách model
    for model in client.models.list():
        # Chỉ in ra các model tạo nội dung (generateContent)
        if "generateContent" in model.supported_actions:
            print(f"✅ {model.name}")
            
    print("----------------------------------------")
    print("Hãy copy một trong các tên ở trên (ví dụ: gemini-1.5-flash-001) vào file app.py")

except Exception as e:
    print(f"❌ Lỗi kết nối: {e}")