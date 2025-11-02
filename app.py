from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
import requests, random, re
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'rahasia123'

# ========== KONFIGURASI DATABASE MYSQL ==========
# Ganti 'YOUR_PASS' dengan password MySQL kamu
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/funquiz'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ========== MODEL DATABASE ==========
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    score = db.Column(db.Integer, default=0)

with app.app_context():
    db.create_all()

# ========== HALAMAN BERANDA (CUACA) ==========
# 🔹 Daftarkan filter datetimeformat sebelum route manapun
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%A, %d %B %Y'):
    return datetime.fromtimestamp(value).strftime(format)

    

@app.route('/', methods=['GET', 'POST'])
def home():
    weather_data = None
    city = None

    if request.method == 'POST':
        city = request.form['city']
        api_key = "7caaf5bf53c37b1f07c2a4c9bcec1e48"
        url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=id&cnt=40"

        response = requests.get(url).json()

        if "list" in response:
            weather_data = []
            for i in range(0, len(response['list']), 8):  # tiap 8 data = 1 hari
                day_data = response['list'][i]
                temps = [entry['main']['temp'] for entry in response['list'][i:i+8]]

                temp_day = max(temps[:4]) if len(temps) >= 4 else max(temps)
                temp_night = min(temps[4:]) if len(temps) >= 4 else min(temps)

                weather_data.append({
                    'dt': day_data['dt'],
                    'main': {
                        'temp_day': round(temp_day, 1),
                        'temp_night': round(temp_night, 1),
                    },
                    'weather': day_data['weather'],
                })
        else:
            weather_data = None

    return render_template('index.html', weather=weather_data, city=city)


# ========== REGISTRASI ==========
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        confirm = request.form['confirm']

        # Cek username unik
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error="Username sudah terdaftar.")

        # Validasi username (huruf + angka)
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{5,}$', username):
            return render_template('register.html', error="Username harus mengandung huruf dan angka (min 5 karakter).")

        # Validasi password (huruf besar, angka, simbol)
        if not re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password):
            return render_template('register.html', error="Password harus mengandung huruf besar, angka, dan 1 simbol (min 8 karakter).")

        # Cek konfirmasi password
        if password != confirm:
            return render_template('register.html', error="Password dan konfirmasi tidak cocok.")

        # Simpan user baru
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

# ========== LOGIN ==========
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user'] = user.username
            return redirect(url_for('quiz'))
        else:
            return render_template('login.html', error="Username atau password salah.")

    return render_template('login.html')


# ========== KONTEKS GLOBAL LOGIN ==========
@app.context_processor
def inject_login_status():
    return dict(logged_in=('user' in session))

# ========== LOGOUT ==========
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))


# ========== DATA KUIS ==========

questions = [
    {
        "question": "Apa kepanjangan dari NLP?",
        "options": ["Natural Language Processing", "Neural Language Programming", "Natural Logic Processing", "Network Language Parsing"],
        "answer": "Natural Language Processing"
    },
    {
        "question": "Tujuan utama NLP adalah…",
        "options": ["Membuat komputer bisa memahami bahasa manusia", "Menghitung jumlah kata dalam teks", "Menerjemahkan bahasa manusia ke bahasa hewan", "Mengoptimalkan database"],
        "answer": "Membuat komputer bisa memahami bahasa manusia"
    },
    {
        "question": "Tokenization adalah…",
        "options": ["Proses memecah teks menjadi unit kecil", "Menghapus kata-kata umum", "Mengubah kata menjadi bentuk dasarnya", "Menentukan jenis kata"],
        "answer": "Proses memecah teks menjadi unit kecil"
    },
    {
        "question": "Fungsi Stopword Removal adalah…",
        "options": ["Menghapus kata-kata yang tidak banyak memberi informasi", "Mempercepat eksekusi model", "Mengubah kata menjadi angka", "Menyimpan teks ke database"],
        "answer": "Menghapus kata-kata yang tidak banyak memberi informasi"
    },
    {
        "question": "Apa itu Stemming?",
        "options": ["Stemming proses mengubah kata ke bentuk dasarnya", 
                    "Menghapus kata-kata yang tidak banyak memberi informasi", 
                    "Mempercepat eksekusi model", 
                    "Stemming proses mengubah kata bahasa Indonesia menjadi bahasa Inggris"],
        "answer": "Stemming proses mengubah kata ke bentuk dasarnya"
    },
    {
        "question": "Part-of-Speech Tagging digunakan untuk…",
        "options": ["Mengidentifikasi fungsi kata dalam kalimat (kata benda, kata kerja, kata sifat, dsb.)", "Mengidentifikasi kata-kata penting", "Mengubah kata menjadi vektor", "Menerjemahkan bahasa"],
        "answer": "Mengidentifikasi fungsi kata dalam kalimat (kata benda, kata kerja, kata sifat, dsb.)"
    },
    {
        "question": "Word Embedding adalah…",
        "options": ["Representasi kata dalam bentuk vektor angka yang menangkap makna kata", 
                    "Proses memecah teks menjadi kata", 
                    "Menghapus stopword", 
                    "Memberi bobot kata menggunakan TF-IDF"], 
        "answer": "Representasi kata dalam bentuk vektor angka yang menangkap makna kata"
    },
    {
        "question": "TF-IDF digunakan untuk…",
        "options": ["Memberi bobot kata berdasarkan frekuensi di dokumen dan korpus", 
                    "Menghapus kata umum", 
                    "Mengubah kata menjadi angka", 
                    "Menyimpan teks"],
        "answer": "Memberi bobot kata berdasarkan frekuensi di dokumen dan korpus"
    },
    {
        "question": "Contoh word embedding adalah…",
        "options": ["Word2Vec", "Tokenizer", "Stopword Removal", "TF-IDF"],
        "answer": "Word2Vec"
    },
    {
        "question": "Model berbasis transformer contohnya adalah…",
        "options": ["BERT dan GPT", "Word2Vec dan GloVe", "NLTK dan spaCy", "TF-IDF dan Bag of Words"],
        "answer": "BERT dan GPT"
    },
    {
       "question": "Salah satu aplikasi NLP di kehidupan sehari-hari adalah…",
        "options": ["Chatbot dan virtual assistant", "Menyimpan database Excel", "Membuat file PDF", "Menginstal library Python"], 
        "answer": "Chatbot dan virtual assistant"
    },
    {
        "question": "Analisis sentimen termasuk aplikasi NLP untuk…",
        "options": ["Menilai opini teks menjadi positif, negatif, atau netral", "Memecah teks menjadi kata", "Menyimpan data teks", "Menghapus stopword"],
        "answer": "Menilai opini teks menjadi positif, negatif, atau netral"
    },
    {
        "question": "Kalau komputer menghapus kata seperti 'yang', 'dan', 'di', itu namanya…",
        "options": ["Stopword Removal", "POS Tagging", "Word Embedding", "TF-IDF"],
        "answer": "Stopword Removal"
    },
    {
       "question": "Kalau kata 'berlari' diubah menjadi 'lari', itu disebut…",
        "options": ["Stemming", "Lemmatization", "NER", "BoW"],
        "answer": "Stemming"
    },
    {
        "question": "Kalau kita ngobrol dengan chatbot seperti Siri atau Google Assistant, itu contoh…",
        "options": ["Aplikasi NLP", "Memasak kue", "Menyiram tanaman", "Menggambar gambar"],
        "answer": "Aplikasi NLP"
    }
]


# ========== HALAMAN KUIS ==========
@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['user']).first()
    question = random.choice(questions)

    if request.method == 'POST':
        selected = request.form['option']
        correct = request.form['correct']

        if selected == correct:
            user.score += 10
            db.session.commit()

        return redirect(url_for('quiz'))

    return render_template('quiz.html', q=question, user=user)

# ========== PAPAN PERINGKAT ==========
@app.route('/leaderboard')
def leaderboard():
    users = User.query.order_by(User.score.desc()).all()
    return render_template('leaderboard.html', users=users)

# ========== CEK USERNAME (AJAX) ==========
@app.route('/check_username', methods=['POST'])
def check_username():
    data = request.get_json()
    username = data.get('username', '').strip()

    exists = User.query.filter_by(username=username).first() is not None
    return jsonify({'exists': exists})



# ========== JALANKAN APP ==========
if __name__ == '__main__':
    app.run(debug=True)
    