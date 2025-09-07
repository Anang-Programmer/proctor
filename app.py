from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/ujian_proctor'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='siswa')  # admin, siswa
    nama_lengkap = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BankSoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pertanyaan = db.Column(db.Text, nullable=False)
    pilihan_a = db.Column(db.String(255), nullable=False)
    pilihan_b = db.Column(db.String(255), nullable=False)
    pilihan_c = db.Column(db.String(255), nullable=False)
    pilihan_d = db.Column(db.String(255), nullable=False)
    jawaban_benar = db.Column(db.String(1), nullable=False)  # A, B, C, D
    kategori = db.Column(db.String(50), nullable=False)
    tingkat_kesulitan = db.Column(db.String(20), default='sedang')  # mudah, sedang, sulit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Ujian(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_ujian = db.Column(db.String(100), nullable=False)
    kategori = db.Column(db.String(50), nullable=False)
    jumlah_soal = db.Column(db.Integer, nullable=False)
    durasi_menit = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='aktif')  # aktif, nonaktif
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HasilUjian(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ujian_id = db.Column(db.Integer, db.ForeignKey('ujian.id'), nullable=False)
    jawaban = db.Column(db.Text, nullable=False)  # JSON format
    nilai = db.Column(db.Float, nullable=False)
    waktu_mulai = db.Column(db.DateTime, nullable=False)
    waktu_selesai = db.Column(db.DateTime, nullable=False)
    jumlah_pelanggaran = db.Column(db.Integer, default=0)
    status_ujian = db.Column(db.String(20), default='selesai')  # selesai, diskualifikasi
    
    user = db.relationship('User', backref=db.backref('hasil_ujian', lazy=True))
    ujian = db.relationship('Ujian', backref=db.backref('hasil_ujian', lazy=True))

class LogPelanggaran(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ujian_id = db.Column(db.Integer, db.ForeignKey('ujian.id'), nullable=False)
    jenis_pelanggaran = db.Column(db.String(100), nullable=False)
    tingkat_pelanggaran = db.Column(db.String(20), nullable=False)  # ringan, berat
    screenshot_path = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('log_pelanggaran', lazy=True))
    ujian = db.relationship('Ujian', backref=db.backref('log_pelanggaran', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('siswa_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('siswa_dashboard'))
        else:
            flash('Username atau password salah!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('siswa_dashboard'))
    
    total_soal = BankSoal.query.count()
    total_ujian = Ujian.query.count()
    total_siswa = User.query.filter_by(role='siswa').count()
    total_hasil = HasilUjian.query.count()
    
    return render_template('admin/dashboard.html', 
                         total_soal=total_soal,
                         total_ujian=total_ujian, 
                         total_siswa=total_siswa,
                         total_hasil=total_hasil)

@app.route('/siswa/dashboard')
@login_required
def siswa_dashboard():
    if current_user.role != 'siswa':
        return redirect(url_for('admin_dashboard'))
    
    ujian_tersedia = Ujian.query.filter_by(status='aktif').all()
    hasil_ujian = HasilUjian.query.filter_by(user_id=current_user.id).all()
    
    return render_template('siswa/dashboard.html', 
                         ujian_tersedia=ujian_tersedia,
                         hasil_ujian=hasil_ujian)

# Admin Routes
@app.route('/admin/bank-soal')
@login_required
def admin_bank_soal():
    if current_user.role != 'admin':
        return redirect(url_for('siswa_dashboard'))
    
    soal_list = BankSoal.query.all()
    return render_template('./admin/bank_soal.html', soal_list=soal_list)

@app.route('/admin/ujian')
@login_required
def admin_ujian():
    if current_user.role != 'admin':
        return redirect(url_for('siswa_dashboard'))
    
    ujian_list = Ujian.query.all()
    return render_template('admin/ujian.html', ujian_list=ujian_list)

@app.route('/admin/peserta')
@login_required
def admin_peserta():
    if current_user.role != 'admin':
        return redirect(url_for('siswa_dashboard'))
    
    peserta_list = User.query.filter_by(role='siswa').all()
    return render_template('admin/peserta.html', peserta_list=peserta_list)

@app.route('/admin/hasil')
@login_required
def admin_hasil():
    if current_user.role != 'admin':
        return redirect(url_for('siswa_dashboard'))
    
    hasil_list = HasilUjian.query.all()
    return render_template('admin/hasil.html', hasil_list=hasil_list)

@app.route('/admin/pelanggaran')
@login_required
def admin_pelanggaran():
    if current_user.role != 'admin':
        return redirect(url_for('siswa_dashboard'))
    
    pelanggaran_list = LogPelanggaran.query.order_by(LogPelanggaran.timestamp.desc()).all()
    return render_template('admin/pelanggaran.html', pelanggaran_list=pelanggaran_list)

# Siswa Ujian Routes
@app.route('/siswa/ujian/<int:ujian_id>/mulai')
@login_required
def mulai_ujian(ujian_id):
    if current_user.role != 'siswa':
        return redirect(url_for('admin_dashboard'))
    
    ujian = Ujian.query.get_or_404(ujian_id)
    
    # Check if already taken
    existing_result = HasilUjian.query.filter_by(user_id=current_user.id, ujian_id=ujian_id).first()
    if existing_result:
        flash('Anda sudah mengerjakan ujian ini!', 'error')
        return redirect(url_for('siswa_dashboard'))
    
    # Get random questions
    import random
    all_soal = BankSoal.query.filter_by(kategori=ujian.kategori).all()
    if len(all_soal) < ujian.jumlah_soal:
        flash('Soal tidak mencukupi untuk ujian ini!', 'error')
        return redirect(url_for('siswa_dashboard'))
    
    selected_soal = random.sample(all_soal, ujian.jumlah_soal)
    
    # Store in session
    session['ujian_active'] = {
        'ujian_id': ujian_id,
        'soal_ids': [s.id for s in selected_soal],
        'start_time': datetime.utcnow().isoformat()
    }
    
    return render_template('siswa/ujian.html', ujian=ujian, soal_list=selected_soal)

# API Routes for AJAX
@app.route('/api/ujian/submit', methods=['POST'])
@login_required
def api_submit_ujian():
    data = request.get_json()
    ujian_id = data.get('ujian_id')
    jawaban = data.get('jawaban', {})
    pelanggaran_count = data.get('pelanggaran_count', 0)
    
    if 'ujian_active' not in session:
        return jsonify({'error': 'Ujian tidak aktif'}), 400
    
    ujian = Ujian.query.get_or_404(ujian_id)
    start_time = datetime.fromisoformat(session['ujian_active']['start_time'])
    
    # Calculate score
    soal_ids = session['ujian_active']['soal_ids']
    correct_answers = 0
    
    for soal_id in soal_ids:
        soal = BankSoal.query.get(soal_id)
        if str(soal_id) in jawaban and jawaban[str(soal_id)] == soal.jawaban_benar:
            correct_answers += 1
    
    nilai = (correct_answers / len(soal_ids)) * 100
    
    # Save result
    hasil = HasilUjian(
        user_id=current_user.id,
        ujian_id=ujian_id,
        jawaban=json.dumps(jawaban),
        nilai=nilai,
        waktu_mulai=start_time,
        waktu_selesai=datetime.utcnow(),
        jumlah_pelanggaran=pelanggaran_count,
        status_ujian='diskualifikasi' if pelanggaran_count >= 3 else 'selesai'
    )
    
    db.session.add(hasil)
    db.session.commit()
    
    # Clear session
    session.pop('ujian_active', None)
    
    return jsonify({'nilai': nilai, 'status': 'success'})

@app.route('/api/proctor/violation', methods=['POST'])
@login_required
def api_proctor_violation():
    data = request.get_json()
    ujian_id = data.get('ujian_id')
    message = data.get('message')
    level = data.get('level')
    
    # Save violation log
    violation = LogPelanggaran(
        user_id=current_user.id,
        ujian_id=ujian_id,
        jenis_pelanggaran=message,
        tingkat_pelanggaran=level
    )
    
    db.session.add(violation)
    db.session.commit()
    
    return jsonify({'status': 'success'})

def create_sample_data():
    """Create sample data for testing"""
    # Create admin user
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            nama_lengkap='Administrator'
        )
        db.session.add(admin)
    
    # Create sample student
    siswa = User.query.filter_by(username='siswa1').first()
    if not siswa:
        siswa = User(
            username='siswa1',
            email='siswa1@example.com',
            password_hash=generate_password_hash('siswa123'),
            role='siswa',
            nama_lengkap='Siswa Contoh'
        )
        db.session.add(siswa)
    
    # Create sample questions
    if BankSoal.query.count() == 0:
        sample_questions = [
            {
                'pertanyaan': 'Apa kepanjangan dari HTML?',
                'pilihan_a': 'Hyper Text Markup Language',
                'pilihan_b': 'High Tech Modern Language',
                'pilihan_c': 'Home Tool Markup Language',
                'pilihan_d': 'Hyperlink and Text Markup Language',
                'jawaban_benar': 'A',
                'kategori': 'Informatika'
            },
            {
                'pertanyaan': 'Bahasa pemrograman apa yang digunakan untuk web development?',
                'pilihan_a': 'Python',
                'pilihan_b': 'JavaScript',
                'pilihan_c': 'Java',
                'pilihan_d': 'C++',
                'jawaban_benar': 'B',
                'kategori': 'Informatika'
            },
            {
                'pertanyaan': 'Apa fungsi dari CSS?',
                'pilihan_a': 'Membuat database',
                'pilihan_b': 'Styling halaman web',
                'pilihan_c': 'Membuat server',
                'pilihan_d': 'Mengolah data',
                'jawaban_benar': 'B',
                'kategori': 'Informatika'
            }
        ]
        
        for q in sample_questions:
            soal = BankSoal(**q)
            db.session.add(soal)
    
    # Create sample exam
    if Ujian.query.count() == 0:
        ujian = Ujian(
            nama_ujian='Ujian Informatika Dasar',
            kategori='Informatika',
            jumlah_soal=3,
            durasi_menit=30
        )
        db.session.add(ujian)
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_sample_data()
    app.run(debug=True)