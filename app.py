from flask import Flask, render_template_string, request, redirect, url_for, session
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'clave-secreta'

# Usuarios múltiples
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

MAX_INTENTOS = 3
TIEMPO_EXPIRACION = timedelta(minutes=3)

estilos = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(to bottom right, #0f2027, #203a43, #2c5364); color: white; text-align: center; padding-top: 100px; margin: 0; }
    input, button { padding: 10px; margin: 10px; border-radius: 5px; border: none; font-size: 16px; }
    button { background-color: #4CAF50; color: white; cursor: pointer; }
    button:hover { background-color: #45a049; }
    .mensaje { position: fixed; top: 20px; right: 20px; padding: 12px 16px; border-radius: 8px; display: flex; align-items: center; gap: 10px; font-size: 16px; z-index: 9999; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .verde { background-color: #4CAF50; color: white; }
    .rojo { background-color: #f44336; color: white; }
    .azul { background-color: #2196F3; color: white; }
    .amarillo { background-color: #ff9800; color: white; }
    .rango { position: fixed; top: 20px; left: 20px; padding: 10px; background-color: #444; border-radius: 8px; font-size: 14px; opacity: 0.85; }
    form { margin: auto; max-width: 400px; }
</style>
<script>
    setTimeout(() => { const alerta = document.getElementById('alerta'); if (alerta) alerta.remove(); }, 3000);
</script>
"""

login_html = """
<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Intranet - Iniciar Sesión</title>""" + estilos + """</head>
<body>
    {% if mensaje %}
    <div class="mensaje {{color}}" id="alerta">{{icono}} {{mensaje}}</div>
    <audio autoplay><source src="{{ url_for('static', filename=audio) }}" type="audio/mpeg"></audio>
    {% endif %}
    <h2>Acceso a la Intranet</h2>
    <form method="post">
        <input name="usuario" placeholder="ID" required><br>
        <input name="password" type="password" placeholder="Contraseña" required><br>
        <button type="submit">Ingresar</button>
    </form>
</body></html>
"""

home_html = """
<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Bienvenido</title>""" + estilos + """
<script>setTimeout(() => { window.location.href = "{{ url_for('logout', msg='auto') }}"; }, 180000);</script></head>
<body onload="document.getElementById('audio').play()">
    {% if mensaje %}
    <div class="mensaje {{color}}" id="alerta">{{icono}} {{mensaje}}</div>
    <audio id="audio" autoplay><source src="{{ url_for('static', filename=audio) }}" type="audio/mpeg"></audio>
    {% endif %}
    <div class="rango">🔰 {{ rango|capitalize }}</div>
    <h2>{{ icono }} {{ mensaje }}</h2>
    <h3>Bienvenido al sistema, {{ usuario }}</h3>
    {% if rango == "admin" %}
        <br><button onclick="location.href='{{ url_for('gestionar') }}'">⚙️ Opciones de Administrador</button>
    {% endif %}
    <br><br><button onclick="location.href='{{ url_for('logout', msg='manual') }}'">Cerrar Sesión</button>
</body></html>
"""

gestionar_html = """
<!DOCTYPE html><html><head><meta charset="utf-8"><title>Gestión de Usuarios</title>""" + estilos + """</head><body>
<h2>⚙️ Gestión de Usuarios</h2>
<form method="post">
    <input name="nuevo_id" placeholder="Nuevo ID" required><br>
    <input name="nuevo_nombre" placeholder="Nombre" required><br>
    <input name="nuevo_password" placeholder="Contraseña" required><br>
    <select name="nuevo_rango" required>
        <option value="local">Local</option>
        <option value="admin">Admin</option>
    </select><br>
    <button type="submit" name="accion" value="agregar">➕ Agregar Usuario</button>
</form>

<hr>

<form method="post">
    <input name="reset_id" placeholder="ID a restablecer" required><br>
    <input name="nuevo_password_reset" placeholder="Nueva contraseña" required><br>
    <button type="submit" name="accion" value="resetear">🔄 Restablecer Contraseña</button>
</form>
<br>
<button onclick="location.href='{{ url_for('home') }}'">⬅️ Volver</button>
</body></html>
"""

@app.route("/", methods=["GET", "POST"])
def login():
    if "intentos" not in session:
        session["intentos"] = MAX_INTENTOS

    if request.method == "POST":
        user = request.form["usuario"]
        pwd = request.form["password"]
        datos = USUARIOS.get(user)

        if not datos:
            session["mensaje"] = "¡Revisa el ID!"
            session["color"] = "amarillo"
            session["icono"] = "⚠️"
            session["audio"] = "error_id.mp3"
            return redirect(url_for("login"))

        if pwd != datos["password"]:
            session["intentos"] -= 1
            intentos = session["intentos"]
            mensaje = f"Contraseña incorrecta. Quedan {intentos} intento(s)." if intentos > 0 else "Demasiados intentos. Ingrese más tarde."
            audio = f"error_{intentos}.mp3" if intentos >= 0 else "error_0.mp3"
            session["mensaje"], session["color"], session["icono"], session["audio"] = mensaje, "rojo", "❌", audio
            return redirect(url_for("login"))

        ahora = datetime.now()
        ultima = session.get("ultimo_login")
        session["usuario"] = datos["nombre"]
        session["rango"] = datos["rango"]
        session["ultimo_login"] = ahora.isoformat()
        session["intentos"] = MAX_INTENTOS
        if ultima:
            try:
                antes = datetime.fromisoformat(ultima)
                audio = datos["audio_bienvenido_de_nuevo"] if ahora - antes > timedelta(minutes=1) else datos["audio_bienvenido"]
            except:
                audio = datos["audio_bienvenido"]
        else:
            audio = datos["audio_bienvenido"]
        session["audio"] = audio
        return redirect(url_for("home"))

    return render_template_string(login_html,
        mensaje=session.pop("mensaje", None),
        color=session.pop("color", ""),
        icono=session.pop("icono", ""),
        audio=session.pop("audio", "")
    )

@app.route("/home")
def home():
    if "usuario" in session:
        usuario = session["usuario"]
        rango = session.get("rango", "")
        audio = session.get("audio", "bienvenido.mp3")
        mensaje = f"Bienvenido de nuevo, {usuario}" if "de_nuevo" in audio else f"Bienvenido {usuario}"
        return render_template_string(home_html,
            usuario=usuario, rango=rango, mensaje=mensaje,
            color="verde", icono="✅", audio=audio)
    return redirect(url_for("login"))

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    mensaje = "Cerrando sesión..."
    audio = "cerrar_sesion.mp3"
    color = "azul"
    icono = "🕓"
    html_logout = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Cerrando sesión</title>{estilos}
    <script>setTimeout(() => {{ window.location.href = "/"; }}, 3000);</script></head>
    <body><div class="mensaje {color}" id="alerta">{icono} {mensaje}</div>
    <audio autoplay><source src="{{{{ url_for('static', filename='{audio}') }}}}" type="audio/mpeg"></audio>
    <h2>{icono} {mensaje}</h2></body></html>"""
    return html_logout

@app.route("/gestionar", methods=["GET", "POST"])
def gestionar():
    if session.get("rango") != "admin":
        return redirect(url_for("home"))

    if request.method == "POST":
        accion = request.form["accion"]
        if accion == "agregar":
            nuevo_id = request.form["nuevo_id"]
            if nuevo_id in USUARIOS:
                session["mensaje"] = "❗ El usuario ya existe."
            else:
                USUARIOS[nuevo_id] = {
                    "nombre": request.form["nuevo_nombre"],
                    "password": request.form["nuevo_password"],
                    "rango": request.form["nuevo_rango"],
                    "audio_bienvenido": "bienvenido.mp3",
                    "audio_bienvenido_de_nuevo": "bienvenido_de_nuevo.mp3"
                }
                session["mensaje"] = "✅ Usuario agregado correctamente."
        elif accion == "resetear":
            reset_id = request.form["reset_id"]
            nuevo_pwd = request.form["nuevo_password_reset"]
            if reset_id in USUARIOS:
                USUARIOS[reset_id]["password"] = nuevo_pwd
                session["mensaje"] = "🔄 Contraseña restablecida."
            else:
                session["mensaje"] = "⚠️ El usuario no existe."

    return render_template_string(gestionar_html)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

