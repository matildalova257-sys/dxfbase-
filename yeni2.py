# DXFBase.com - Render için Tam Çalışan Versiyon
from flask import Flask, render_template_string, request, redirect, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import bcrypt, uuid, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'gizli-anahtar-uret-guvende-ol')

# PostgreSQL için veritabanı ayarı
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Klasörleri oluştur
os.makedirs('uploads', exist_ok=True)
os.makedirs('previews', exist_ok=True)

# ---------- VERİTABANI ----------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True)
    sifre_hash = db.Column(db.String(200))
    rol = db.Column(db.String(20), default='user')

class Dosya(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dosya_adi = db.Column(db.String(200))
    orijinal_adi = db.Column(db.String(200))
    png_adi = db.Column(db.String(200))
    token = db.Column(db.String(100), unique=True, default=lambda: str(uuid.uuid4()))
    kategori = db.Column(db.String(50))
    indirme = db.Column(db.Integer, default=0)

@login_manager.user_loader
def load_user(id): 
    return User.query.get(int(id))

# ---------- TEMA ----------
TEMA = """
<!DOCTYPE html>
<html>
<head>
    <title>DXFBase</title>
    <style>
        body{background:#000;color:#0f0;font-family:'Courier New';margin:0;}
        .bar{background:#0a0a0a;border-bottom:1px solid #0f0;padding:15px}
        .bar a{color:#0f0;margin:0 15px;text-decoration:none}
        .container{display:flex;max-width:1200px;margin:20px auto;gap:20px}
        .sidebar{width:200px;background:#0a0a0a;border:1px solid #0f0;padding:15px}
        .content{flex:1;background:#050505;border:1px solid #0f0;padding:20px}
        .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:15px}
        .card{background:#0a0a0a;border:2px solid #0f0;padding:20px;text-align:center}
        .card img{max-width:100%;height:200px;object-fit:cover}
        button,input,select{background:#1a1a1a;border:1px solid #0f0;color:#0f0;padding:8px;margin:5px}
        button:hover{background:#0f0;color:#000}
        .flash{padding:10px;margin:10px 0;border:1px solid}
        a{color:#fff; text-decoration:none;}
    </style>
</head>
<body>
<div class="bar">
   <a href="/">
        <img src="/static/cover.png" alt="DXFBase" style="height: 80px; vertical-align: middle;">
    </a>
    <div style="float:right">
        <a href="/">ANA SAYFA</a>
        {% if current_user.is_authenticated %}
            <a href="/admin">YÖNETİM</a>
            <a href="/logout">ÇIKIŞ</a>
        {% else %}
            <a href="/login">GİRİŞ</a>
            <a href="/register">KAYIT</a>
        {% endif %}
    </div>
</div>
<div class="container">
    <div class="sidebar">
        <h3>KATEGORİLER</h3>
       <a href="/?kat=Tüm" style="color: white;">Tümü</a><br>
       <a href="/?kat=DXF" style="color: white;">DXF</a><br>
       <a href="/?kat=DWG" style="color: white;">DWG</a><br>
       <a href="/?kat=SVG" style="color: white;">SVG</a><br>
       <a href="/?kat=Mimari" style="color: white;">Mimari</a><br>
       <a href="/?kat=Mekanik" style="color: white;">Mekanik</a><br>
    </div>
    <div class="content">
        {% with m = get_flashed_messages(with_categories=true) %}
            {% for c,msg in m %}<div class="flash flash-{{ c }}">{{ msg }}</div>{% endfor %}
        {% endwith %}
        <h2>> {{ kat }}</h2>
        <div class="grid">
        {% for d in dosyalar %}
        <div class="card">
            <img src="/preview/{{ d.png_adi or 'noimg.png' }}" onerror="this.src='data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20100%20100%22%3E%3Crect%20width%3D%22100%22%20height%3D%22100%22%20fill%3D%22%23000%22%2F%3E%3Ctext%20x%3D%2250%22%20y%3D%2255%22%20fill%3D%22%230f0%22%20text-anchor%3D%22middle%22%20font-family%3D%22monospace%22%3E{{ d.orijinal_adi.split('.')[-1] }}%3C%2Ftext%3E%3C%2Fsvg%3E'">
            <b>{{ d.orijinal_adi[:15] }}</b><br>
            📥 {{ d.indirme }}<br>
            <a href="/indir/{{ d.token }}"><button>İNDİR</button></a>
        </div>
        {% endfor %}
        </div>
    </div>
</div>
</body>
</html>
"""

ADMIN = """
<!DOCTYPE html>
<html>
<head><title>Admin</title>
<style>body{background:#000;color:#0f0;font-family:monospace;padding:20px}
input,select{background:#1a1a1a;border:1px solid #0f0;color:#0f0;padding:8px}
button{background:#1a1a1a;border:1px solid #0f0;color:#0f0;padding:8px 16px;cursor:pointer}
</style></head>
<body>
<h1>ADMIN PANEL</h1>
<form method=post action="/yukle" enctype=multipart/form-data>
    Dosya: <input type=file name=dosya accept=".dxf,.dwg,.svg" required><br>
    PNG: <input type=file name=png accept="image/png"><br>
    Kategori: <select name=kat>
        <option>DXF</option><option>DWG</option><option>SVG</option>
        <option>Mimari</option><option>Mekanik</option>
    </select><br>
    <button>YÜKLE</button>
</form>
<h2>İSTATİSTİKLER</h2>
<p>👥 Kullanıcı: {{ k }}</p>
<p>📁 Dosya: {{ d }}</p>
<h2>📋 DOSYALAR</h2>
{% for dosya in dosyalar %}
<div style="background:#0a0a0a;margin:10px 0;padding:10px">
    {{ dosya.orijinal_adi }} - 📥 {{ dosya.indirme }}
    <form method=post action="/sil/{{ dosya.id }}" style=display:inline>
        <button onclick="return confirm('Sil?')">🗑️</button>
    </form>
</div>
{% endfor %}
</body></html>
"""

FORM = """
<!DOCTYPE html>
<html><head><title>DXFBase</title>
<style>body{background:#000;color:#0f0;font-family:monospace;padding:50px}</style>
</head>
<body>
<h1>> {{ baslik }}</h1>
<form method=post>
    {% if 'ad' in form %}
    Ad: <input name=ad required><br>
    Soyad: <input name=soyad required><br>
    {% endif %}
    Email: <input type=email name=email required><br>
    Şifre: <input type=password name=sifre required><br>
    {% if 'ulke' in form %}
    Ülke: <input name=ulke><br>
    Şehir: <input name=sehir><br>
    {% endif %}
    <button>{{ buton }}</button>
</form>
<a href="/{{ link }}">{{ link_yazi }}</a>
</body></html>
"""

# ---------- ROUTE'LAR ----------
@app.route('/')
def index():
    kat = request.args.get('kat', 'Tum')
    dosyalar = Dosya.query.all() if kat == 'Tum' else Dosya.query.filter_by(kategori=kat).all()
    return render_template_string(TEMA, dosyalar=dosyalar, kat=kat)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email kayıtlı!', 'error')
            return redirect('/register')
        hashli = bcrypt.hashpw(request.form['sifre'].encode(), bcrypt.gensalt()).decode()
        user = User(ad=request.form['ad'], email=request.form['email'], sifre_hash=hashli)
        db.session.add(user)
        db.session.commit()
        flash('Kayıt başarılı!', 'success')
        return redirect('/login')
    return render_template_string(FORM, baslik='KAYIT', form=['ad','soyad','email','sifre','ulke','sehir'],
                                 buton='KAYDET', link='login', link_yazi='Giriş yap')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.checkpw(request.form['sifre'].encode(), user.sifre_hash.encode()):
            login_user(user)
            session['rol'] = user.rol
            flash('Hoşgeldin!', 'success')
            return redirect('/')
        flash('Hatalı giriş!', 'error')
    return '''
    <style>body{background:#000;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;font-family:Arial}.kutu{background:#0a0a0a;border:1px solid #0f0;border-radius:12px;padding:40px;width:380px}h1{color:#0f0;text-align:center;margin-bottom:30px}.google{background:#1a1a1a;border:1px solid #333;border-radius:8px;padding:12px;text-align:center;margin-bottom:20px;cursor:pointer}.ayrac{text-align:center;color:#666;margin:20px 0}input{width:100%;background:#1a1a1a;border:1px solid #333;border-radius:8px;padding:12px;margin:8px 0 20px;color:#fff;box-sizing:border-box}.sifre_unuttum{text-align:right;margin-bottom:25px}.sifre_unuttum a{color:#666;text-decoration:none}button{width:100%;background:#0f0;border:none;border-radius:8px;padding:12px;color:#000;font-weight:bold;cursor:pointer}.kayit{text-align:center;color:#666;margin-top:20px}.kayit a{color:#0f0;text-decoration:none}</style>
    <div class=kutu><h1>Oturum aç</h1>
    <div class=google onclick="alert('Yakında')">
    <span>Google ile devam et</span>
</div>
    <div class=ayrac>Veya e-posta ile giriş yapın</div>
    <form method=post>
        <div>E-posta adresiniz</div><input type=email name=email required>
        <div>Şifreniz</div><input type=password name=sifre required>
        <div class=sifre_unuttum><a href="#">Parolanızı mı unuttunuz?</a></div>
        <button type=submit>Oturum aç</button>
    </form>
    <div class=kayit>Hesabınız yok mu? <a href="/register">Kayıt ol</a></div>
    </div>
    '''

@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect('/')

@app.route('/indir/<token>')
def indir(token):
    dosya = Dosya.query.filter_by(token=token).first()
    if dosya:
        dosya.indirme += 1
        db.session.commit()
        return send_from_directory('uploads', dosya.dosya_adi, as_attachment=True)
    return 'Dosya yok', 404

@app.route('/preview/<png>')
def preview(png):
    return send_from_directory('previews', png)

@app.route('/admin')
def admin():
    if not current_user.is_authenticated or session.get('rol') != 'admin':
        flash('Admin yetkisi gerekli!', 'error')
        return redirect('/')
    return render_template_string(ADMIN, k=User.query.count(), d=Dosya.query.count(), 
                                 dosyalar=Dosya.query.all())

@app.route('/yukle', methods=['POST'])
def yukle():
    if not current_user.is_authenticated or session.get('rol') != 'admin':
        return 'Yetkisiz!', 403
    dosya = request.files['dosya']
    if dosya.filename:
        orijinal = secure_filename(dosya.filename)
        uzanti = os.path.splitext(orijinal)[1]
        yeni_adi = f"{uuid.uuid4().hex}{uzanti}"
        dosya.save(f'uploads/{yeni_adi}')
        
        png_adi = None
        if 'png' in request.files and request.files['png'].filename:
            png = request.files['png']
            png_adi = f"{uuid.uuid4().hex}.png"
            png.save(f'previews/{png_adi}')
        
        yeni = Dosya(dosya_adi=yeni_adi, orijinal_adi=orijinal, png_adi=png_adi,
                    kategori=request.form.get('kat', 'DXF'))
        db.session.add(yeni)
        db.session.commit()
        flash('Dosya yüklendi!', 'success')
    return redirect('/admin')

@app.route('/sil/<int:id>', methods=['POST'])
def sil(id):
    if not current_user.is_authenticated or session.get('rol') != 'admin':
        return 'Yetkisiz!', 403
    dosya = Dosya.query.get(id)
    if dosya:
        if os.path.exists(f'uploads/{dosya.dosya_adi}'):
            os.remove(f'uploads/{dosya.dosya_adi}')
        if dosya.png_adi and os.path.exists(f'previews/{dosya.png_adi}'):
            os.remove(f'previews/{dosya.png_adi}')
        db.session.delete(dosya)
        db.session.commit()
        flash('Silindi!', 'success')
    return redirect('/admin')

# ---------- BAŞLAT ----------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Varsayılan admin
        if not User.query.filter_by(email='admin@dxfbase.com').first():
            admin_hash = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
            admin = User(ad='Admin', email='admin@dxfbase.com', sifre_hash=admin_hash, rol='admin')
            db.session.add(admin)
            db.session.commit()
    
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
    