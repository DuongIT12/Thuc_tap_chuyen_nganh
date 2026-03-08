from PIL import Image, ImageDraw, ImageFont
import textwrap

def create_avatar(bg_color, text_color, filename):
    # Kích thước vuông chuẩn HD (1200x1200)
    width, height = 1200, 1200
    image = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(image)

    # Cố gắng load font đậm, dễ đọc
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 110)
    except:
        font = ImageFont.load_default()

    # Nội dung giữ nguyên ý nhưng ngắt dòng lại cho lọt lòng hình tròn
    text = "TÀI KHOẢN\nBỊ HACK\nVUI LÒNG KHÔNG\nCHUYỂN KHOẢN\nVÀ CUNG CẤP OTP"
    
    lines = text.split('\n')
    
    # Tính toán độ cao để căn giữa theo chiều dọc
    total_height = 0
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        h = bbox[3] - bbox[1]
        line_heights.append(h)
        total_height += h
    
    # Khoảng cách giữa các dòng
    padding = 30
    total_height += padding * (len(lines) - 1)
    
    current_y = (height - total_height) / 2

    # Vẽ từng dòng
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) / 2
        draw.text((x, current_y), line, font=font, fill=text_color)
        current_y += line_heights[i] + padding

    image.save(filename)

# Tạo ảnh nền đỏ
create_avatar('#D32F2F', 'white', 'canh_bao_hack_red.png')
# Tạo ảnh nền trắng
create_avatar('white', 'black', 'canh_bao_hack_white.png')