import os
import urllib.parse
import pandas as pd
from io import BytesIO
from flask import send_file, Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import random
import requests 

# --- THƯ VIỆN NÂNG CẤP V2.0 ---
from flask_mail import Mail, Message
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.dialects.mssql import NVARCHAR 

# =======================================================
# 1. CẤU HÌNH HỆ THỐNG
# =======================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'khoa-bi-mat-cua-ban-123'

# --- CẤU HÌNH SQL SERVER ---
server_name = 'DUONG-PCC'  
database_name = 'SmartStudy'

params = urllib.parse.quote_plus(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server_name};"
    f"DATABASE={database_name};"
    "Trusted_Connection=yes;"
)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect={params}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- CẤU HÌNH EMAIL TỰ ĐỘNG ---
# ⚠️ Thay bằng Gmail và Mật khẩu ứng dụng của bạn
# --- CẤU HÌNH EMAIL TỰ ĐỘNG ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

# 👇 Điền Gmail của bạn vào đây:
app.config['MAIL_USERNAME'] = 'nguyenduongg24ct@gmail.com' 

# 👇 Dán 16 ký tự Mật khẩu ứng dụng vừa copy vào đây (viết liền, không có dấu cách):
app.config['MAIL_PASSWORD'] = ' kyndmvqhumjokvgp' 

mail = Mail(app)

# Cấu hình Upload
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# =======================================================
# 2. DATABASE MODELS
# =======================================================

class User(UserMixin, db.Model):
    __tablename__ = 'nguoi_dung'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)
    fullname = db.Column(db.NVARCHAR(150)) 
    email = db.Column(db.String(150)) 
    role = db.Column(db.String(50), default='student')

class Resource(db.Model):
    __tablename__ = 'tai_lieu'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.NVARCHAR(200), nullable=False)
    file_path = db.Column(db.String(300), nullable=False)
    file_type = db.Column(db.String(50))
    category = db.Column(db.NVARCHAR(50))
    grade = db.Column(db.NVARCHAR(20))
    uploader_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    uploader = db.relationship('User', backref='resources')
    def to_dict(self):
        return {'title': self.title, 'file_path': self.file_path, 'file_type': self.file_type, 'category': self.category, 'grade': self.grade, 'date': self.created_at.strftime('%d/%m/%Y'), 'uploader': self.uploader.fullname if self.uploader else "Ẩn danh"}

class Assignment(db.Model):
    __tablename__ = 'bai_tap'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.NVARCHAR(200), nullable=False)
    description = db.Column(db.NVARCHAR(None))
    deadline = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False) 
    teacher_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id'))
    submissions = db.relationship('Submission', backref='assignment', lazy=True)
    comments = db.relationship('Comment', backref='assignment', lazy=True)

class Submission(db.Model):
    __tablename__ = 'bai_nop'
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(300))
    student_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id'))
    assignment_id = db.Column(db.Integer, db.ForeignKey('bai_tap.id'))
    score = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.NVARCHAR(None)) 
    submitted_at = db.Column(db.DateTime, default=datetime.now)
    is_late = db.Column(db.Boolean, default=False)
    similarity_score = db.Column(db.Float, default=0.0)
    similar_to_student = db.Column(db.NVARCHAR(150), nullable=True)
    student = db.relationship('User', backref='submissions')

class Comment(db.Model):
    __tablename__ = 'binh_luan'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.NVARCHAR(None), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id'))
    assignment_id = db.Column(db.Integer, db.ForeignKey('bai_tap.id'))
    user = db.relationship('User', backref='comments')

class Quiz(db.Model):
    __tablename__ = 'de_thi'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.NVARCHAR(200), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id'))
    questions = db.relationship('Question', backref='quiz', cascade="all, delete-orphan", lazy=True)
    results = db.relationship('QuizResult', backref='quiz', lazy=True)

class Question(db.Model):
    __tablename__ = 'cau_hoi'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('de_thi.id'))
    question_text = db.Column(db.NVARCHAR(None), nullable=False)
    option_a = db.Column(db.NVARCHAR(200))
    option_b = db.Column(db.NVARCHAR(200))
    option_c = db.Column(db.NVARCHAR(200))
    option_d = db.Column(db.NVARCHAR(200))
    correct_answer = db.Column(db.String(1)) 
    def to_dict(self): return {'id': self.id, 'text': self.question_text, 'a': self.option_a, 'b': self.option_b, 'c': self.option_c, 'd': self.option_d}

class QuizResult(db.Model):
    __tablename__ = 'ket_qua_thi'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id'))
    quiz_id = db.Column(db.Integer, db.ForeignKey('de_thi.id'))
    score = db.Column(db.Float)
    submitted_at = db.Column(db.DateTime, default=datetime.now)
    student = db.relationship('User', backref='quiz_results')

class LearningSession(db.Model):
    __tablename__ = 'phien_hoc'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id'))
    hours = db.Column(db.Float)
    stress_level = db.Column(db.Integer)
    method_pref = db.Column(db.NVARCHAR(50))
    ai_advice = db.Column(db.NVARCHAR(None))
    predicted_score = db.Column(db.Float, nullable=True) 
    created_at = db.Column(db.DateTime, default=datetime.now)

@login_manager.user_loader
def load_user(user_id): return User.query.get(int(user_id))


# =======================================================
# 3. LOGIC XỬ LÝ
# =======================================================

def check_plagiarism_ml(target_submission):
    try:
        with open(os.path.join(app.config['UPLOAD_FOLDER'], target_submission.file_path), 'r', encoding='utf-8', errors='ignore') as f:
            target_content = f.read()
    except: return 0, None

    max_ratio = 0.0; source_student = None
    others = Submission.query.filter(Submission.assignment_id == target_submission.assignment_id, Submission.id != target_submission.id).all()
    
    for other in others:
        try:
            with open(os.path.join(app.config['UPLOAD_FOLDER'], other.file_path), 'r', encoding='utf-8', errors='ignore') as f:
                other_content = f.read()
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([target_content, other_content])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0] * 100
            if similarity > max_ratio:
                max_ratio = similarity
                source_student = other.student.fullname or other.student.username
        except: continue
    return round(max_ratio, 2), source_student

def analyze_and_predict(hours, stress, method):
    advice = ""
    if stress > 7: advice += "⚠️ Stress cao: Hãy áp dụng Pomodoro. "
    if hours < 2: advice += "⏰ Cần học thêm ít nhất 30p mỗi ngày. "
    advice += f"💡 Phong cách {method} rất phù hợp để tư duy."
    predicted_score = round(min(10.0, max(0.0, 5.0 + (hours * 0.8) - (stress * 0.3))), 1)
    return advice, predicted_score

# =======================================================
# 4. ROUTES (TẤT CẢ CHỨC NĂNG)
# =======================================================

@app.route('/')
def index(): 
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form.get('username')).first():
            flash('Tên đăng nhập đã tồn tại!', 'error')
        else:
            db.session.add(User(
                username=request.form.get('username'),
                password=generate_password_hash(request.form.get('password'), method='pbkdf2:sha256'),
                role=request.form.get('role'), fullname=request.form.get('fullname'), email=request.form.get('email')
            ))
            db.session.commit()
            flash('Đăng ký thành công!', 'success'); return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user); return redirect(url_for('dashboard'))
        flash('Sai thông tin.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout(): logout_user(); return redirect(url_for('login'))

# --- ĐÂY LÀ ROUTE CẬP NHẬT PROFILE BỊ THIẾU TRƯỚC ĐÓ ---
@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    current_user.fullname = request.form.get('fullname')
    current_user.email = request.form.get('email')
    if request.form.get('new_password'):
        current_user.password = generate_password_hash(request.form.get('new_password'), method='pbkdf2:sha256')
    db.session.commit()
    flash('Cập nhật hồ sơ thành công!', 'success')
    return redirect(url_for('dashboard'))

# --- TÀI LIỆU ---
@app.route('/upload_resource', methods=['POST'])
@login_required
def upload_resource():
    if current_user.role != 'teacher': return redirect('/')
    file = request.files['file']
    if file:
        filename = secure_filename(f"RES_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        ext = filename.split('.')[-1].lower()
        db.session.add(Resource(title=request.form.get('title'), file_path=filename, file_type=ext, category=request.form.get('category'), grade=request.form.get('grade'), uploader_id=current_user.id))
        db.session.commit()
        flash('Đã đăng tài liệu!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/api/get_resources')
@login_required
def get_resources_api():
    grade = request.args.get('grade', 'all'); category = request.args.get('category', 'all')
    query = Resource.query
    if grade != 'all': query = query.filter_by(grade=grade)
    if category != 'all': query = query.filter(Resource.category.ilike(f"%{category}%"))
    return jsonify([r.to_dict() for r in query.order_by(Resource.created_at.desc()).all()])

# --- BÀI TẬP ---
@app.route('/create_assignment', methods=['POST'])
@login_required
def create_assignment():
    if current_user.role == 'teacher':
        dl = datetime.strptime(request.form.get('deadline'), '%Y-%m-%dT%H:%M') if request.form.get('deadline') else None
        title = request.form.get('title')
        db.session.add(Assignment(title=title, description=request.form.get('description'), deadline=dl, teacher_id=current_user.id))
        db.session.commit()
        try:
            students = User.query.filter_by(role='student').all()
            with mail.connect() as conn:
                for student in students:
                    if student.email:
                        msg = Message(f"[SmartStudy] Có bài tập mới: {title}", sender=app.config['MAIL_USERNAME'], recipients=[student.email])
                        msg.body = f"Chào {student.fullname},\n\nGiáo viên vừa giao bài tập mới: {title}\nHạn nộp: {dl.strftime('%d/%m/%Y %H:%M') if dl else 'Không có'}\n\nHãy đăng nhập hệ thống để làm bài nhé."
                        conn.send(msg)
            flash('Giao bài và Gửi Email thành công!', 'success')
        except Exception as e:
            flash(f'Giao bài thành công! (Lưu ý: Không gửi được Email do chưa cấu hình SMTP)', 'warning')
    return redirect(url_for('dashboard'))

@app.route('/delete_assignment/<int:id>', methods=['POST'])
@login_required
def delete_assignment(id):
    if current_user.role == 'teacher':
        ass = Assignment.query.get(id); ass.is_deleted = True; db.session.commit()
        flash('Đã xóa bài tập (Đưa vào thùng rác).', 'success')
    return redirect(url_for('dashboard'))

@app.route('/submit_assignment/<int:ass_id>', methods=['POST'])
@login_required
def submit_assignment(ass_id):
    file = request.files['file']
    if file:
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        ass = Assignment.query.get(ass_id)
        is_late = True if (ass.deadline and datetime.now() > ass.deadline) else False
        old = Submission.query.filter_by(student_id=current_user.id, assignment_id=ass_id).first()
        if old: db.session.delete(old)
        db.session.add(Submission(file_path=filename, student_id=current_user.id, assignment_id=ass_id, is_late=is_late))
        db.session.commit(); flash('Nộp bài thành công!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/check_all_plagiarism/<int:ass_id>', methods=['POST'])
@login_required
def check_all_plagiarism(ass_id):
    c = 0
    for sub in Submission.query.filter_by(assignment_id=ass_id).all():
        score, source = check_plagiarism_ml(sub)
        sub.similarity_score = score; sub.similar_to_student = source; c += 1
    db.session.commit(); flash(f'Đã dùng AI quét đạo văn {c} bài!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/grade_submission/<int:sub_id>', methods=['POST'])
@login_required
def grade_submission(sub_id):
    sub = Submission.query.get(sub_id)
    sub.score = request.form.get('score')
    if request.form.get('feedback'): sub.feedback = request.form.get('feedback')
    db.session.commit(); flash('Đã lưu điểm!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/post_comment/<int:ass_id>', methods=['POST'])
@login_required
def post_comment(ass_id):
    if request.form.get('content'):
        db.session.add(Comment(content=request.form.get('content'), user_id=current_user.id, assignment_id=ass_id))
        db.session.commit()
    return redirect(url_for('dashboard'))

# --- TRẮC NGHIỆM ---
@app.route('/create_quiz', methods=['POST'])
@login_required
def create_quiz():
    data = request.json
    new_quiz = Quiz(title=data.get('title'), teacher_id=current_user.id)
    db.session.add(new_quiz); db.session.commit()
    for q in data.get('questions'):
        db.session.add(Question(quiz_id=new_quiz.id, question_text=q['text'], option_a=q['a'], option_b=q['b'], option_c=q['c'], option_d=q['d'], correct_answer=q['correct']))
    db.session.commit(); return jsonify({'status': 'success', 'message': 'Đã tạo đề thi thành công!'})

@app.route('/get_shuffled_quiz/<int:quiz_id>')
@login_required
def get_shuffled_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    q_list = [q.to_dict() for q in quiz.questions]; random.shuffle(q_list)
    return jsonify({'title': quiz.title, 'exam_code': random.randint(100, 999), 'questions': q_list})

@app.route('/take_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def take_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id); score = 0
    for q in quiz.questions:
        if request.form.get(f'q_{q.id}') == q.correct_answer: score += 1
    final_score = round((score / len(quiz.questions)) * 10, 2) if quiz.questions else 0
    db.session.add(QuizResult(student_id=current_user.id, quiz_id=quiz_id, score=final_score)); db.session.commit()
    flash(f'Đã nộp bài! Điểm số: {final_score}/10', 'success')
    return redirect(url_for('dashboard'))

@app.route('/get_calendar_events')
@login_required
def get_calendar_events():
    events = []
    asses = Assignment.query.filter_by(is_deleted=False).all() if current_user.role == 'student' else Assignment.query.filter_by(teacher_id=current_user.id, is_deleted=False).all()
    for ass in asses:
        if ass.deadline:
            color = '#3788d8' 
            if current_user.role == 'student':
                if Submission.query.filter_by(student_id=current_user.id, assignment_id=ass.id).first(): color = '#28a745'
                elif datetime.now() > ass.deadline: color = '#dc3545'
                else: color = '#ffc107'
            events.append({'title': ass.title, 'start': ass.deadline.strftime('%Y-%m-%dT%H:%M:%S'), 'color': color})
    return jsonify(events)

@app.route('/ask_ai', methods=['POST'])
def ask_ai_widget():
    data = request.json; question = data.get('question', '').lower()
    
    def offline_ai_response(q):
        if "chào" in q: return "Chào bạn! Mình là AI SmartStudy."
        elif "stress" in q: return "💡 Hãy nghỉ ngơi 15 phút, dùng phương pháp Pomodoro."
        elif "toán" in q or "code" in q: return "📚 Hãy chia nhỏ bài toán và thực hành nhiều hơn."
        return "🤖 Để giải quyết, bạn nên chia nhỏ vấn đề ra thành các bước nhé."

    API_KEY = "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY"
    if API_KEY and "DÁN_" not in API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
            resp = requests.post(url, headers={'Content-Type': 'application/json'}, json={"contents": [{"parts": [{"text": f"Bạn là trợ lý học tập. Trả lời ngắn gọn: {question}"}]}]}, timeout=5)
            if resp.status_code == 200: return jsonify({'answer': resp.json()['candidates'][0]['content']['parts'][0]['text']})
        except: pass
    return jsonify({'answer': offline_ai_response(question)})

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST' and 'analyze' in request.form:
        h = float(request.form.get('hours')); s = int(request.form.get('stress')); m = request.form.get('method')
        advice, pred_score = analyze_and_predict(h, s, m)
        db.session.add(LearningSession(student_id=current_user.id, hours=h, stress_level=s, method_pref=m, ai_advice=advice, predicted_score=pred_score))
        db.session.commit()
    
    data = {}
    data['resources'] = Resource.query.order_by(Resource.created_at.desc()).all()
    
    lb = []
    for stu in User.query.filter_by(role='student').all():
        score = sum([sub.score for sub in stu.submissions if sub.score]) + sum([res.score for res in stu.quiz_results])
        lb.append({'name': stu.fullname or stu.username, 'total_score': round(score, 2)})
    data['leaderboard'] = sorted(lb, key=lambda x: x['total_score'], reverse=True)

    if current_user.role == 'teacher':
        data['assignments'] = Assignment.query.filter_by(teacher_id=current_user.id, is_deleted=False).all()
        data['submissions'] = Submission.query.join(Assignment).filter(Assignment.teacher_id==current_user.id, Assignment.is_deleted==False).all()
        data['quizzes'] = Quiz.query.filter_by(teacher_id=current_user.id).all()
        sessions = LearningSession.query.all()
        data['chart_stress'] = [s.stress_level for s in sessions]
    else: 
        data['assignments'] = Assignment.query.filter_by(is_deleted=False).all()
        data['my_submissions'] = Submission.query.filter_by(student_id=current_user.id).all()
        data['quizzes'] = Quiz.query.all()
        data['quiz_results'] = QuizResult.query.filter_by(student_id=current_user.id).all()
        data['last_analysis'] = LearningSession.query.filter_by(student_id=current_user.id).order_by(LearningSession.id.desc()).first()

    return render_template('dashboard.html', data=data, datetime=datetime)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(username='admin', password=generate_password_hash('admin123'), role='admin', fullname='Administrator'))
            db.session.commit()
    app.run(debug=True)