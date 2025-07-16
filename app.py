from flask import Flask, request, redirect, url_for, session, render_template_string
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'clave-secreta'

# Base de datos de usuarios
USUARIOS = {
    "1016730173": {
        "password": "E2025*BOG",
        "nombre": "Emanuel",
        "rango": "admin",
        "audio_bienvenido": "bienvenido.mp3",
        "audio_bienvenido_de_nuevo": "bienvenido_de_nuevo.mp3"
    },
    "2025123456": {
        "password": "clave123",
        "nombre": "Andrés",
        "rango": "local",
        "audio_bienvenido": "bienvenido_andres.mp3",
        "audio_bienvenido_de_nuevo": "bienvenido_de_nuevo_andres.mp3"
    }
}

# === PÁGINAS HTML ===

LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Intranet Vandoel - Login</title>
    <style>
        body {
            font-family: Arial, sans-serif; background: #eef2f3;
            display: flex; justify-content: center; align-items: center;
            height: 100vh; margin: 0;
        }
        .login-box {
            background: white; padding: 30px; border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            width: 300px;
        }
        input[type="text"], input[type="password"] {
            width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #ccc;
        }
        button {
            width: 100%; padding: 10px; background: #0057b8; color: white;
            border: none; border-radius: 5px; cursor: pointer;
        }
        .error {
            color: red; text-align: center; margin-top: 10px;
        }
    </style>
</head>
<body>
    <form method="post" class="login-box">
        <h2>Iniciar Sesión</h2>
        <input type="text" name="usuario" placeholder="ID" required>
        <input type="password" name="clave" placeholder="Contraseña" required>
        <button type="submit">Ingresar</button>
        {% if error %}
        <p class="error">{{ error }}</p>
        {% endif %}
    </form>
</body>
</html>
'''

HOME_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Bienvenido {{ nombre }}</title>
    <style>
        body {
            font-family: sans-serif;
            background: #f9f9f9;
            margin: 0; padding: 0;
        }
        .top-bar {
            background: #004085;
            color: white;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .admin-button {
            background: #ffc107;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
        }
        .logout {
            color: white;
            text-decoration: none;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="top-bar">
        <div>Bienvenido al sistema, {{ nombre }} | Rango: {{ rango }}</div>
        <div>
            {% if rango == 'admin' %}
            <a href="{{ url_for('admin_panel') }}"><button class="admin-button">⚙️ Opciones de administrador</button></a>
            {% endif %}
            <a href="{{ url_for('logout') }}" class="logout">Cerrar sesión</a>
        </div>
    </div>

    {% if audio %}
    <audio autoplay>
        <source src="{{ url_for('static', filename=audio) }}" type="audio/mp3">
    </audio>
    {% endif %}
</body>
</html>
'''

ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Panel de administrador</title>
    <style>
        body {
            font-family: sans-serif;
            padding: 30px;
            background: #f4f4f4;
        }
        h2 { margin-top: 0; }
        form {
            background: white; padding: 20px;
            border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        input, select {
            padding: 10px; width: 100%;
            margin: 10px 0; border: 1px solid #ccc; border-radius: 5px;
        }
        button {
            background: #007bff; color: white; border: none;
            padding: 10px 20px; border-radius: 5px; cursor: pointer;
        }
    </style>
</head>
<body>
    <h2>⚙️ Panel de administrador</h2>

    <form method="post" action="{{ url_for('agregar_usuario') }}">
        <h3>Agregar nuevo usuario</h3>
        <input type="text" name="nuevo_id" placeholder="ID del nuevo usuario" required>
        <input type="text" name="nuevo_nombre" placeholder="Nombre completo" required>
        <input type="password" name="nuevo_password" placeholder="Contraseña" required>
        <select name="nuevo_rango">
            <option value="local">Local</option>
            <option value="admin">Administrador</option>
        </select>
        <button type="submit">Agregar</button>
    </form>

    <form method="post" action="{{ url_for('reset_password') }}">
        <h3>Restablecer contraseña</h3>
        <input type="text" name="usuario_id" placeholder="ID del usuario" required>
        <input type="password" name="nueva_contrasena" placeholder="Nueva contraseña" required>
        <button type="submit">Restablecer</button>
    </form>

    <a href="{{ url_for('home') }}">⬅️ Volver</a>
</body>
</html>
'''

# === RUTAS ===

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']
        now = datetime.now()

        if usuario in USUARIOS and USUARIOS[usuario]["password"] == clave:
            session['usuario'] = usuario
            session['nombre'] = USUARIOS[usuario]["nombre"]
            session['rango'] = USUARIOS[usuario]["rango"]

            ultimo = session.get('ultimo_login')
            session['ultimo_login'] = now.strftime('%Y-%m-%d %H:%M:%S')

            if ultimo:
                ultimo_dt = datetime.strptime(ultimo, '%Y-%m-%d %H:%M:%S')
                segundos = (now - ultimo_dt).total_seconds()
                audio = USUARIOS[usuario]["audio_bienvenido_de_nuevo"] if segundos > 60 else USUARIOS[usuario]["audio_bienvenido"]
            else:
                audio = USUARIOS[usuario]["audio_bienvenido"]

            return redirect(url_for('home', audio=audio))
        else:
            return render_template_string(LOGIN_HTML, error="ID o contraseña incorrectos")
    return render_template_string(LOGIN_HTML)

@app.route('/home')
def home():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    nombre = session.get('nombre')
    rango = session.get('rango')
    audio = request.args.get('audio')

    return render_template_string(HOME_HTML, nombre=nombre, rango=rango, audio=audio)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin/opciones')
def admin_panel():
    if 'usuario' not in session or session.get('rango') != 'admin':
        return redirect(url_for('home'))
    return render_template_string(ADMIN_HTML)

@app.route('/admin/agregar', methods=['POST'])
def agregar_usuario():
    if session.get('rango') != 'admin':
        return redirect(url_for('home'))

    nuevo_id = request.form['nuevo_id']
    nuevo_nombre = request.form['nuevo_nombre']
    nuevo_password = request.form['nuevo_password']
    nuevo_rango = request.form['nuevo_rango']

    if nuevo_id not in USUARIOS:
        USUARIOS[nuevo_id] = {
            "password": nuevo_password,
            "nombre": nuevo_nombre,
            "rango": nuevo_rango,
            "audio_bienvenido": "bienvenido.mp3",
            "audio_bienvenido_de_nuevo": "bienvenido_de_nuevo.mp3"
        }
    return redirect(url_for('admin_panel'))

@app.route('/admin/reset_password', methods=['POST'])
def reset_password():
    if session.get('rango') != 'admin':
        return redirect(url_for('home'))

    usuario_id = request.form['usuario_id']
    nueva = request.form['nueva_contrasena']

    if usuario_id in USUARIOS:
        USUARIOS[usuario_id]['password'] = nueva
    return redirect(url_for('admin_panel'))

# === MAIN ===
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')


