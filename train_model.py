# train_model.py
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
import joblib

# 1. Tạo dữ liệu giả định (Dataset)
# Quy ước style: visual, auditory, kinesthetic
# Quy ước output: Pomodoro, MindMap, GroupStudy, ProjectBased
data = {
    'hours':        [1, 8, 2, 5, 9, 1, 6, 3, 10, 4],  # Số giờ học
    'stress':       [2, 9, 8, 4, 8, 1, 5, 7, 10, 3],  # Mức độ stress
    'style_raw':    ['visual', 'visual', 'auditory', 'kinesthetic', 'auditory', 'kinesthetic', 'visual', 'auditory', 'visual', 'kinesthetic'],
    'method_label': ['MindMap', 'Pomodoro', 'GroupStudy', 'ProjectBased', 'Pomodoro', 'ProjectBased', 'MindMap', 'GroupStudy', 'Pomodoro', 'ProjectBased']
}

df = pd.DataFrame(data)

# 2. Xử lý dữ liệu (Chuyển chữ thành số)
# Máy tính không hiểu chữ "visual", cần chuyển thành số (0, 1, 2)
le_style = LabelEncoder()
df['style_encoded'] = le_style.fit_transform(df['style_raw'])

# Input (X): Giờ, Stress, Style(số)
X = df[['hours', 'stress', 'style_encoded']]
# Output (y): Phương pháp học
y = df['method_label']

# 3. Huấn luyện Model (Dùng thuật toán Cây quyết định)
model = DecisionTreeClassifier()
model.fit(X, y)

# 4. Lưu Model và Bộ mã hóa (Encoder) ra file
joblib.dump(model, 'saved_model.pkl')
joblib.dump(le_style, 'style_encoder.pkl')

print("✅ Đã huấn luyện xong! File 'saved_model.pkl' đã được tạo.")
print("Mapping phong cách:", dict(zip(le_style.classes_, le_style.transform(le_style.classes_))))