# DXFBase.com - Render için Tam Çalışan Versiyon
from flask import Flask, render_template_string, request, redirect, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import bcrypt, uuid, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'gizli-anahtar-uret-guvende-ol')
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"): DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
os.makedirs('uploads', exist_ok=True)
os.makedirs('previews', exist_ok=True)

class User(UserMixin, db.Model): id = db.Column(db.Integer, primary_key=True); ad = db.Column(db.String(50)); email = db.Column(db.String(100), unique=True); sifre_hash = db.Column(db.String(200)); rol = db.Column(db.String(20), default='user')
class Dosya(db.Model): id = db.Column(db.Integer, primary_key=True); dosya_adi = db.Column(db.String(200)); orijinal_adi = db.Column(db.String(200)); png_adi = db.Column(db.String(200)); token = db.Column(db.String(100), unique=True, default=lambda: str(uuid.uuid4())); kategori = db.Column(db.String(50)); indirme = db.Column(db.Integer, default=0)

@login_manager.user_loader
def load_user(id): return User.query.get(int(id))

# ---------- TEMA ----------
TEMA = """<!DOCTYPE html><html><head><title>DXFBase</title><style>body{background:#000;color:#0f0;font-family:'Courier New';margin:0;}.bar{background:#0a0a0a;border-bottom:1px solid #0f0;padding:15px}.bar a{color:#0f0;margin:0 15px;text-decoration:none;cursor:pointer}.lang-selector{position:relative;float:right;margin-right:20px}.lang-button{background:#1a1a1a;border:1px solid #0f0;color:#0f0;padding:8px 12px;border-radius:8px;cursor:pointer;display:inline-flex;align-items:center;gap:8px}.lang-panel{display:none;position:absolute;top:42px;right:0;background:#0a0a0a;border:1px solid #0f0;border-radius:8px;padding:10px;z-index:1001;min-width:160px;box-shadow:0 0 15px rgba(0,255,0,0.3)}.lang-panel.active{display:block}.lang-panel a{display:block;color:#0f0;padding:8px;border-radius:6px;text-decoration:none}.lang-panel a:hover{background:#0f0;color:#000}.container{display:flex;max-width:1200px;margin:20px auto;gap:20px}.sidebar{width:200px;background:#0a0a0a;border:1px solid #0f0;padding:15px}.content{flex:1;background:#050505;border:1px solid #0f0;padding:20px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:15px}.card{background:#0a0a0a;border:2px solid #0f0;padding:20px;text-align:center;display:flex;flex-direction:column;justify-content:space-between;word-break:break-word;overflow-wrap:break-word;white-space:normal}.card img{max-width:100%;height:200px;object-fit:cover}.card b{display:block;word-break:break-word;overflow-wrap:break-word;white-space:normal;font-size:16px;margin-bottom:10px}.kat-link{display:block;background:#000;color:#fff;padding:10px;margin:5px 0;text-align:center;font-size:18px;border:2px solid #0f0;border-radius:5px;text-decoration:none;word-break:break-word;overflow-wrap:break-word;white-space:normal;}.kat-link:hover{background:#0a0a0a;color:#fff;border:2px solid #0f0;}.modal{display:none;position:fixed;top:0;left:0;width:25%;height:100%;background:rgba(0,0,0,0.7);z-index:1000}.modal.active{display:flex;align-items:center;justify-content:flex-start}.modal-content{background:#0a0a0a;border:2px solid #0f0;width:400px;margin-left:0px;padding:20px;position:relative;overflow-y:auto}.modal-close{position:absolute;top:10px;right:10px;color:#0f0;cursor:pointer;font-size:24px}.modal-tabs{display:flex;flex-direction:column;gap:10px}.modal-tab{background:#000;color:#fff;padding:12px;text-align:center;font-size:16px;border:2px solid #0f0;border-radius:5px;cursor:pointer;text-decoration:none}.modal-tab:hover{background:#0a0a0a;color:#0f0}</style></head><body><div class="bar"><a onclick="toggleModal()" style="cursor:pointer;"><img src="/static/cover.png" alt="DXFBase" style="height:80px;vertical-align:middle;"></a><div class="lang-selector"><div class="lang-button" onclick="toggleLangPanel()">Languages</div><div id="langPanel" class="lang-panel"><a href="#" onclick="setLang('tr');return false;">Turkish</a><a href="#" onclick="setLang('en');return false;">English</a><a href="#" onclick="setLang('de');return false;">German</a><a href="#" onclick="setLang('es');return false;">Spanish</a><a href="#" onclick="setLang('fr');return false;">French</a><a href="#" onclick="setLang('ru');return false;">Russian</a></div></div><div style="float:right"><a href="/">{{ get_text('ana_sayfa') }}</a>{% if current_user.is_authenticated %}<a href="/admin">{{ get_text('yonetim') }}</a><a href="/logout">{{ get_text('cikis') }}</a>{% else %}<a href="/login">{{ get_text('giris') }}</a><a href="/register">{{ get_text('kayit') }}</a>{% endif %}</div></div><div id="infoModal" class="modal"><div class="modal-content"><span class="modal-close" onclick="toggleModal()">&times;</span><h3 style="color:#0f0;border-bottom:2px solid #0f0;padding-bottom:10px;">{{ get_text('menu') }}</h3><div class="modal-tabs"><a href="#" class="modal-tab" onclick="showTab('hakkinda')">{{ get_text('hakkinda') }}</a><a href="#" class="modal-tab" onclick="showTab('iletisim')">{{ get_text('iletisim') }}</a><a href="#" class="modal-tab" onclick="showTab('vizyon')">{{ get_text('vizyon') }}</a></div><div id="hakkinda" class="tab-content" style="display:block;margin-top:20px;color:#0f0;border:1px solid #0f0;padding:10px;border-radius:5px;"><h4>{{ get_text('hakkinda') }}</h4><p>{{ get_text('hakkinda_text')|safe }}</p></div><div id="iletisim" class="tab-content" style="display:none;margin-top:20px;color:#0f0;border:1px solid #0f0;padding:10px;border-radius:5px;"><h4>{{ get_text('iletisim') }}</h4><p>{{ get_text('iletisim_text')|safe }}</p></div><div id="vizyon" class="tab-content" style="display:none;margin-top:20px;color:#0f0;border:1px solid #0f0;padding:10px;border-radius:5px;"><h4>{{ get_text('vizyon') }}</h4><p>{{ get_text('vizyon_text') }}</p></div></div></div><div class="container"><div class="sidebar"><h3>{{ get_text('kategoriler') }}</h3><a href="/?kat=Tum" class="kat-link">{{ get_text('tumu') }}</a><a href="/?kat=Vectors Animals" class="kat-link">{{ get_text('vectors_animals') }}</a><a href="/?kat=Vectors Furniture" class="kat-link">{{ get_text('vectors_furniture') }}</a><a href="/?kat=Vectors Toys/Games" class="kat-link">{{ get_text('vectors_toys_games') }}</a><a href="/?kat=Vectors Vehicles/Trains/Trucks/Airplanes/Ships/Boats" class="kat-link">{{ get_text('vectors_vehicles') }}</a><a href="/?kat=Vectors Decoration and Party" class="kat-link">{{ get_text('vectors_decoration_party') }}</a><a href="/?kat=Vectors Home and Utilities" class="kat-link">{{ get_text('vectors_home_utilities') }}</a><a href="/?kat=Vectors Houses/Construction/Architecture" class="kat-link">{{ get_text('vectors_construction') }}</a><a href="/?kat=Vectors Frames/Monograms" class="kat-link">{{ get_text('vectors_frames_monograms') }}</a><a href="/?kat=Vectors Boxes/Trays/Vases/Bags" class="kat-link">{{ get_text('vectors_boxes_trays_vases_bags') }}</a><a href="/?kat=Vectors Flowers and Plants" class="kat-link">{{ get_text('vectors_flowers_plants') }}</a><a href="/?kat=Vectors Religious" class="kat-link">{{ get_text('vectors_religious') }}</a><a href="/?kat=Vectors Signs of the Zodiac" class="kat-link">{{ get_text('vectors_zodiac') }}</a><a href="/?kat=Vectors Watches/Clock" class="kat-link">{{ get_text('vectors_watches_clock') }}</a></div><div class="content">{% with m = get_flashed_messages(with_categories=true) %}{% for c,msg in m %}<div class="flash flash-{{ c }}">{{ msg }}</div>{% endfor %}{% endwith %}<h2>> {{ kat_display }}</h2><div class="grid">{% for d in dosyalar %}<div class="card"><img src="/preview/{{ d.png_adi or 'noimg.png' }}" onerror="this.src='data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20100%20100%22%3E%3Crect%20width%3D%22100%22%20height%3D%22100%22%20fill%3D%22%23000%22%2F%3E%3Ctext%20x%3D%2250%22%20y%3D%2255%22%20fill%3D%22%230f0%22%20text-anchor%3D%22middle%22%20font-family%3D%22monospace%22%3E{{ d.orijinal_adi.split('.')[-1] }}%3C%2Ftext%3E%3C%2Fsvg%3E'"><b>{{ d.orijinal_adi[:15] }}</b><br>📥 {{ d.indirme }}<br><a href="/indir/{{ d.token }}"><button>{{ get_text('indir') }}</button></a></div>{% endfor %}</div></div></div><script>function toggleModal(){document.getElementById('infoModal').classList.toggle('active');}function showTab(tabName){const tabs=document.querySelectorAll('.tab-content');tabs.forEach(tab=>tab.style.display='none');document.getElementById(tabName).style.display='block';}function toggleLangPanel(){document.getElementById('langPanel').classList.toggle('active');}function setLang(lang){window.location.href='/set_lang/'+lang;}document.addEventListener('click',function(e){const panel=document.getElementById('langPanel');const button=document.querySelector('.lang-button');if(panel&&button&&!panel.contains(e.target)&&!button.contains(e.target)){panel.classList.remove('active');}});</script></body></html>"""
ADMIN = """<!DOCTYPE html><html><head><title>Admin</title><style>body{background:#000;color:#0f0;font-family:monospace;padding:20px}input,select{background:#1a1a1a;border:1px solid #0f0;color:#0f0;padding:8px}button{background:#1a1a1a;border:1px solid #0f0;color:#0f0;padding:8px 16px;cursor:pointer}</style></head><body><h1>{{ get_text('admin_panel') }}</h1><form method=post action="/yukle" enctype=multipart/form-data>{{ get_text('dosya') }}: <input type=file name=dosya accept=".dxf,.dwg,.svg" required><br>{{ get_text('png') }}: <input type=file name=png accept="image/png"><br>{{ get_text('kategori') }}: <select name=kat><option>Vectors Animals</option><option>Vectors Furniture</option><option>Vectors Toys/Games</option><option>Vectors Vehicles/Trains/Trucks/Airplanes/Ships/Boats</option><option>Vectors Decoration and Party</option><option>Vectors Home and Utilities</option><option>Vectors Houses/Construction/Architecture</option><option>Vectors Frames/Monograms</option><option>Vectors Boxes/Trays/Vases/Bags</option><option>Vectors Flowers and Plants</option><option>Vectors Religious</option><option>Vectors Signs of the Zodiac</option><option>Vectors Watches/Clock</option></select><br><button>{{ get_text('upload') }}</button></form><h2>{{ get_text('istatistikler') }}</h2><p>👥 {{ get_text('kullanici') }}: {{ k }}</p><p>📁 {{ get_text('dosyalar') }}: {{ d }}</p><h2>📋 {{ get_text('dosyalar') }}</h2>{% for dosya in dosyalar %}<div style="background:#0a0a0a;margin:10px 0;padding:10px">{{ dosya.orijinal_adi }} - 📥 {{ dosya.indirme }}<form method=post action="/sil/{{ dosya.id }}" style=display:inline><button onclick="return confirm('{{ get_text('sil') }}')">🗑️</button></form></div>{% endfor %}</body></html>"""
# ---------- DİL TERCİHLERİ ----------
DILLER = {
    'tr': {
        'menu': 'MENÜ',
        'hakkinda': 'Hakkında',
        'iletisim': 'İletişim',
        'vizyon': 'Vizyon',
        'ana_sayfa': 'ANA SAYFA',
        'yonetim': 'YÖNETİM',
        'cikis': 'ÇIKIŞ',
        'giris': 'GİRİŞ',
        'kayit': 'KAYIT',
        'ad': 'Ad',
        'soyad': 'Soyad',
        'ulke': 'Ülke',
        'sehir': 'Şehir',
        'kayit_buton': 'KAYDET',
        'kategoriler': 'KATEGORİLER',
        'tumu': 'Tümü',
        'vectors_animals': 'Vektör Hayvanlar',
        'vectors_furniture': 'Vektör Mobilya',
        'vectors_toys_games': 'Vektör Oyuncaklar',
        'vectors_vehicles': 'Vektör Araçlar',
        'vectors_decoration_party': 'Vektör Dekorasyon ve Parti',
        'vectors_home_utilities': 'Vektör Ev ve Yardımcı',
        'vectors_construction': 'Vektör İnşaat',
        'vectors_frames_monograms': 'Vektör Çerçeveler',
        'vectors_boxes_trays_vases_bags': 'Vektör Kutular',
        'vectors_flowers_plants': 'Vektör Çiçekler',
        'vectors_religious': 'Vektör Dini',
        'vectors_zodiac': 'Vektör Burçlar',
        'vectors_watches_clock': 'Vektör Saatler',
        'indir': 'İNDİR',
        'admin_panel': 'ADMIN PANEL',
        'dosya': 'Dosya',
        'png': 'PNG',
        'kategori': 'Kategori',
        'upload': 'YÜKLE',
        'istatistikler': 'İSTATİSTİKLER',
        'kullanici': 'Kullanıcı',
        'dosyalar': 'Dosyalar',
        'sil': 'Sil?',
        'geri': 'Geri',
        'google_devam': 'Google ile devam et',
        'email_giris': 'Veya e-posta ile giriş yapın',
        'email_placeholder': 'E-posta adresiniz',
        'sifre_placeholder': 'Şifreniz',
        'sifre_unuttum': 'Parolanızı mı unuttunuz?',
        'oturum_ac': 'Oturum aç',
        'hesap_yok': 'Hesabınız yok mu?',
        'kayit_ol': 'Kayıt ol',
        'hakkinda_text': 'DXFBase, tasarımcılar ve mühendisler için premium dosya paylaşım platformudur.',
        'iletisim_text': 'Email: info@dxfbase.com<br>Tel: +90 212 555 1234',
        'vizyon_text': 'Dünya çapında tasarım dosyası paylaşımında lider olmak.',
    },
    'en': {
        'menu': 'MENU',
        'hakkinda': 'About',
        'iletisim': 'Contact',
        'vizyon': 'Vision',
        'ana_sayfa': 'HOME',
        'yonetim': 'ADMIN',
        'cikis': 'LOGOUT',
        'giris': 'LOGIN',
        'kayit': 'REGISTER',
        'ad': 'First name',
        'soyad': 'Last name',
        'ulke': 'Country',
        'sehir': 'City',
        'kayit_buton': 'Register',
        'kategoriler': 'CATEGORIES',
        'tumu': 'All',
        'vectors_animals': 'Vectors Animals',
        'vectors_furniture': 'Vectors Furniture',
        'vectors_toys_games': 'Vectors Toys/Games',
        'vectors_vehicles': 'Vectors Vehicles/Trains/Trucks/Airplanes/Ships/Boats',
        'vectors_decoration_party': 'Vectors Decoration and Party',
        'vectors_home_utilities': 'Vectors Home and Utilities',
        'vectors_construction': 'Vectors Houses/Construction/Architecture',
        'vectors_frames_monograms': 'Vectors Frames/Monograms',
        'vectors_boxes_trays_vases_bags': 'Vectors Boxes/Trays/Vases/Bags',
        'vectors_flowers_plants': 'Vectors Flowers and Plants',
        'vectors_religious': 'Vectors Religious',
        'vectors_zodiac': 'Vectors Signs of the Zodiac',
        'vectors_watches_clock': 'Vectors Watches/Clock',
        'indir': 'DOWNLOAD',
        'geri': 'Back',
        'google_devam': 'Continue with Google',
        'email_giris': 'Or sign in with email',
        'email_placeholder': 'Your email address',
        'sifre_placeholder': 'Your password',
        'sifre_unuttum': 'Forgot your password?',
        'oturum_ac': 'Sign in',
        'hesap_yok': "Don't have an account?",
        'kayit_ol': 'Sign up',
        'hakkinda_text': 'DXFBase is a premium file sharing platform for designers and engineers.',
        'iletisim_text': 'Email: info@dxfbase.com<br>Phone: +90 212 555 1234',
        'vizyon_text': 'To be a leader in global design file sharing.',
    },
    'de': {
        'menu': 'MENÜ',
        'hakkinda': 'Über uns',
        'iletisim': 'Kontakt',
        'vizyon': 'Vision',
        'ana_sayfa': 'STARTSEITE',
        'yonetim': 'VERWALTUNG',
        'cikis': 'ABMELDEN',
        'giris': 'ANMELDEN',
        'kayit': 'REGISTRIEREN',
        'ad': 'Vorname',
        'soyad': 'Nachname',
        'ulke': 'Land',
        'sehir': 'Stadt',
        'kayit_buton': 'Registrieren',
        'kategoriler': 'KATEGORIEN',
        'tumu': 'Alle',
        'mimari': 'Architektur',
        'mekanik': 'Mechanik',
        'indir': 'HERUNTERLADEN',
        'geri': 'Zurück',
        'google_devam': 'Mit Google fortfahren',
        'email_giris': 'Oder mit E-Mail anmelden',
        'email_placeholder': 'Ihre E-Mail-Adresse',
        'sifre_placeholder': 'Ihr Passwort',
        'sifre_unuttum': 'Passwort vergessen?',
        'oturum_ac': 'Anmelden',
        'hesap_yok': 'Haben Sie kein Konto?',
        'kayit_ol': 'Jetzt registrieren',
        'hakkinda_text': 'DXFBase ist eine Premium-Dateifreigabeplattform für Designer und Ingenieure.',
        'iletisim_text': 'E-Mail: info@dxfbase.com<br>Telefon: +90 212 555 1234',
        'vizyon_text': 'Marktführer bei der globalen Freigabe von Designdateien sein.',
    },
    'es': {
        'menu': 'MENÚ',
        'hakkinda': 'Acerca de',
        'iletisim': 'Contacto',
        'vizyon': 'Visión',
        'ana_sayfa': 'INICIO',
        'yonetim': 'ADMINISTRACIÓN',
        'cikis': 'CERRAR SESIÓN',
        'giris': 'INICIAR SESIÓN',
        'kayit': 'REGISTRARSE',
        'ad': 'Nombre',
        'soyad': 'Apellido',
        'ulke': 'País',
        'sehir': 'Ciudad',
        'kayit_buton': 'Registrar',
        'kategoriler': 'CATEGORÍAS',
        'tumu': 'Todo',
        'mimari': 'Arquitectura',
        'mekanik': 'Mecánica',
        'indir': 'DESCARGAR',
        'geri': 'Atrás',
        'google_devam': 'Continuar con Google',
        'email_giris': 'O inicia sesión con correo electrónico',
        'email_placeholder': 'Tu dirección de correo electrónico',
        'sifre_placeholder': 'Tu contraseña',
        'sifre_unuttum': '¿Olvidaste tu contraseña?',
        'oturum_ac': 'Iniciar sesión',
        'hesap_yok': '¿No tienes cuenta?',
        'kayit_ol': 'Regístrate',
        'hakkinda_text': 'DXFBase es una plataforma premium de intercambio de archivos para diseñadores e ingenieros.',
        'iletisim_text': 'Correo electrónico: info@dxfbase.com<br>Teléfono: +90 212 555 1234',
        'vizyon_text': 'Ser líder mundial en el intercambio de archivos de diseño.',
    },
    'fr': {
        'menu': 'MENU',
        'hakkinda': 'À propos',
        'iletisim': 'Contact',
        'vizyon': 'Vision',
        'ana_sayfa': 'ACCUEIL',
        'yonetim': 'ADMINISTRATION',
        'cikis': 'DÉCONNEXION',
        'giris': 'CONNEXION',
        'kayit': 'S\'INSCRIRE',
        'ad': 'Prénom',
        'soyad': 'Nom',
        'ulke': 'Pays',
        'sehir': 'Ville',
        'kayit_buton': 'S\'inscrire',
        'kategoriler': 'CATÉGORIES',
        'tumu': 'Tous',
        'mimari': 'Architecture',
        'mekanik': 'Mécanique',
        'indir': 'TÉLÉCHARGER',
        'geri': 'Retour',
        'google_devam': 'Continuer avec Google',
        'email_giris': 'Ou connectez-vous avec un e-mail',
        'email_placeholder': 'Votre adresse e-mail',
        'sifre_placeholder': 'Votre mot de passe',
        'sifre_unuttum': 'Mot de passe oublié?',
        'oturum_ac': 'Connexion',
        'hesap_yok': 'Vous n\'avez pas de compte?',
        'kayit_ol': 'S\'inscrire',
        'hakkinda_text': 'DXFBase est une plateforme premium de partage de fichiers pour les designers et les ingénieurs.',
        'iletisim_text': 'E-mail: info@dxfbase.com<br>Téléphone: +90 212 555 1234',
        'vizyon_text': 'Être un leader mondial du partage de fichiers de conception.',
    },
    'ru': {
        'menu': 'МЕНЮ',
        'hakkinda': 'О нас',
        'iletisim': 'Контакты',
        'vizyon': 'Видение',
        'ana_sayfa': 'ГЛАВНАЯ',
        'yonetim': 'АДМИН',
        'cikis': 'ВЫХОД',
        'giris': 'ВХОД',
        'kayit': 'РЕГИСТРАЦИЯ',
        'ad': 'Имя',
        'soyad': 'Фамилия',
        'ulke': 'Страна',
        'sehir': 'Город',
        'kayit_buton': 'Зарегистрироваться',
        'kategoriler': 'КАТЕГОРИИ',
        'tumu': 'Все',
        'mimari': 'Архитектура',
        'mekanik': 'Механика',
        'indir': 'СКАЧАТЬ',
        'geri': 'Назад',
        'google_devam': 'Продолжить с Google',
        'email_giris': 'Или войдите по электронной почте',
        'email_placeholder': 'Ваш адрес электронной почты',
        'sifre_placeholder': 'Ваш пароль',
        'sifre_unuttum': 'Забыли пароль?',
        'oturum_ac': 'Вход',
        'hesap_yok': 'Нет аккаунта?',
        'kayit_ol': 'Зарегистрироваться',
        'hakkinda_text': 'DXFBase - премиум-платформа обмена файлами для дизайнеров и инженеров.',
        'iletisim_text': 'Email: info@dxfbase.com<br>Телефон: +90 212 555 1234',
        'vizyon_text': 'Быть лидером в глобальном обмене файлами дизайна.',
    }
}

def get_lang(): return session.get('lang', 'tr')

def get_text(key): lang = get_lang(); return DILLER.get(lang, DILLER['tr']).get(key, key)

def get_category_label(kat):
    if kat in ['Tum', 'Tüm']: return get_text('tumu')
    if kat in ['DXF', 'DWG', 'SVG']: return kat
    if kat == 'Mimari': return get_text('mimari')
    if kat == 'Mekanik': return get_text('mekanik')
    return kat

FORM = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>{{ baslik }}</title><style>body{background:#000;color:#0f0;font-family:Arial,sans-serif;margin:0;padding:0}.kutu{background:#0a0a0a;border:1px solid #0f0;border-radius:12px;padding:40px;width:380px;margin:60px auto}input{width:100%;background:#1a1a1a;border:1px solid #333;border-radius:8px;padding:12px;margin:8px 0;color:#fff;box-sizing:border-box}button{width:100%;background:#0f0;border:none;border-radius:8px;padding:12px;color:#000;font-weight:bold;cursor:pointer}a{color:#0f0;text-decoration:none}.link{margin-top:20px;text-align:center;color:#666}</style></head><body><div class="kutu"><h1>{{ baslik }}</h1><form method="post">{% if 'ad' in form %}{{ get_text('ad') }}: <input type="text" name="ad" required><br>{% endif %}{% if 'soyad' in form %}{{ get_text('soyad') }}: <input type="text" name="soyad" required><br>{% endif %}{% if 'email' in form %}{{ get_text('email_placeholder') }}: <input type="email" name="email" placeholder="{{ get_text('email_placeholder') }}" required><br>{% endif %}{% if 'sifre' in form %}{{ get_text('sifre_placeholder') }}: <input type="password" name="sifre" placeholder="{{ get_text('sifre_placeholder') }}" required><br>{% endif %}{% if 'ulke' in form %}{{ get_text('ulke') }}: <input type="text" name="ulke"><br>{% endif %}{% if 'sehir' in form %}{{ get_text('sehir') }}: <input type="text" name="sehir"><br>{% endif %}<button type="submit">{{ buton }}</button></form><div class="link"><a href="/{{ link }}">{{ link_yazi }}</a></div></div></body></html>"""

LOGIN = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>{{ get_text('giris') }}</title><style>body{background:#000;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;font-family:Arial}.kutu{background:#0a0a0a;border:1px solid #0f0;border-radius:12px;padding:40px;width:380px;position:relative}h1{color:#0f0;text-align:center;margin-bottom:30px}.google{background:#1a1a1a;border:1px solid #333;border-radius:8px;padding:12px;text-align:center;margin-bottom:20px;cursor:pointer;color:#fff}.ayrac{text-align:center;color:#666;margin:20px 0}input{width:100%;background:#1a1a1a;border:1px solid #333;border-radius:8px;padding:12px;margin:8px 0 20px;color:#fff;box-sizing:border-box}.sifre_unuttum{text-align:right;margin-bottom:25px}.sifre_unuttum a{color:#666;text-decoration:none}button{width:100%;background:#0f0;border:none;border-radius:8px;padding:12px;color:#000;font-weight:bold;cursor:pointer}.kayit{text-align:center;color:#666;margin-top:20px}.kayit a{color:#0f0;text-decoration:none}.geri{position:absolute;top:20px;left:20px;color:#0f0;text-decoration:none}</style></head><body><div class=kutu><a href="/" class="geri">&larr; {{ get_text('geri') }}</a><h1>{{ get_text('oturum_ac') }}</h1><div class=google onclick="alert('Yakında')"><span>{{ get_text('google_devam') }}</span></div><div class=ayrac>{{ get_text('email_giris') }}</div><form method=post><input type=email name=email placeholder="{{ get_text('email_placeholder') }}" required><input type=password name=sifre placeholder="{{ get_text('sifre_placeholder') }}" required><div class=sifre_unuttum><a href="#">{{ get_text('sifre_unuttum') }}</a></div><button type=submit>{{ get_text('oturum_ac') }}</button></form><div class=kayit>{{ get_text('hesap_yok') }} <a href="/register">{{ get_text('kayit_ol') }}</a></div></div></body></html>"""

# ---------- ROUTE'LAR ----------
@app.route('/set_lang/<lang>')
def set_lang(lang):
    if lang in DILLER: session['lang'] = lang
    return redirect(request.referrer or '/')

@app.route('/')
def index():
    kat = request.args.get('kat', 'Tum')
    if kat == 'Tüm': kat = 'Tum'
    dosyalar = Dosya.query.all() if kat == 'Tum' else Dosya.query.filter_by(kategori=kat).all()
    kat_display = get_category_label(kat)
    return render_template_string(TEMA, dosyalar=dosyalar, kat=kat, kat_display=kat_display, get_text=get_text, lang=get_lang())

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
    return render_template_string(FORM, baslik=get_text('kayit'), form=['ad','soyad','email','sifre','ulke','sehir'], buton=get_text('kayit_buton'), link='login', link_yazi=get_text('giris'), get_text=get_text)

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
    return render_template_string(LOGIN, get_text=get_text, lang=get_lang())

@app.route('/logout')
def logout(): logout_user(); session.clear(); return redirect('/')

@app.route('/indir/<token>')
def indir(token):
    dosya = Dosya.query.filter_by(token=token).first()
    if dosya:
        dosya.indirme += 1
        db.session.commit()
        return send_from_directory('uploads', dosya.dosya_adi, as_attachment=True)
    return 'Dosya yok', 404

@app.route('/preview/<png>')
def preview(png): return send_from_directory('previews', png)

@app.route('/admin')
def admin():
    if not current_user.is_authenticated or session.get('rol') != 'admin':
        flash('Admin yetkisi gerekli!', 'error')
        return redirect('/')
    return render_template_string(ADMIN, k=User.query.count(), d=Dosya.query.count(), dosyalar=Dosya.query.all(), get_text=get_text)

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
        yeni = Dosya(dosya_adi=yeni_adi, orijinal_adi=orijinal, png_adi=png_adi, kategori=request.form.get('kat', 'DXF'))
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='admin@dxfbase.com').first():
            admin_hash = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
            admin = User(ad='Admin', email='admin@dxfbase.com', sifre_hash=admin_hash, rol='admin')
            db.session.add(admin)
            db.session.commit()
        if Dosya.query.count() == 0:
            ornek_dosyalar = [
                Dosya(orijinal_adi='Lion Vector.dxf', dosya_adi='lion.dxf', png_adi='noimg.png', kategori='Vectors Animals'),
                Dosya(orijinal_adi='Chair Design.dxf', dosya_adi='chair.dxf', png_adi='noimg.png', kategori='Vectors Furniture'),
                Dosya(orijinal_adi='Toy Car.dxf', dosya_adi='toy_car.dxf', png_adi='noimg.png', kategori='Vectors Toys/Games'),
                Dosya(orijinal_adi='Truck Model.dxf', dosya_adi='truck.dxf', png_adi='noimg.png', kategori='Vectors Vehicles/Trains/Trucks/Airplanes/Ships/Boats'),
                Dosya(orijinal_adi='Party Balloon.dxf', dosya_adi='balloon.dxf', png_adi='noimg.png', kategori='Vectors Decoration and Party'),
                Dosya(orijinal_adi='House Plan.dxf', dosya_adi='house.dxf', png_adi='noimg.png', kategori='Vectors Houses/Construction/Architecture'),
                Dosya(orijinal_adi='Frame Pattern.dxf', dosya_adi='frame.dxf', png_adi='noimg.png', kategori='Vectors Frames/Monograms'),
                Dosya(orijinal_adi='Box Template.dxf', dosya_adi='box.dxf', png_adi='noimg.png', kategori='Vectors Boxes/Trays/Vases/Bags'),
                Dosya(orijinal_adi='Flower Vector.dxf', dosya_adi='flower.dxf', png_adi='noimg.png', kategori='Vectors Flowers and Plants'),
                Dosya(orijinal_adi='Cross Symbol.dxf', dosya_adi='cross.dxf', png_adi='noimg.png', kategori='Vectors Religious'),
                Dosya(orijinal_adi='Zodiac Sign.dxf', dosya_adi='zodiac.dxf', png_adi='noimg.png', kategori='Vectors Signs of the Zodiac'),
                Dosya(orijinal_adi='Watch Face.dxf', dosya_adi='watch.dxf', png_adi='noimg.png', kategori='Vectors Watches/Clock'),
            ]
            for dosya in ornek_dosyalar:
                db.session.add(dosya)
            db.session.commit()
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
