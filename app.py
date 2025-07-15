from flask import Flask, render_template_string, request, redirect, url_for, session
from datetime import datetime, timedelta

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
    body {
        margin: 0;
        font-family: 'Segoe UI', sans-serif;
        background: linear-gradient(to bottom right, #0f2027, #203a43, #2c5364);
        color: white;
        text-align: center;
        padding-top: 100px;
    }
    input, button {
        padding: 10px;
        margin: 10px;
        border-radius: 5px;
        border: none;
        font-size: 16px;
    }
    button {
        background-color: #4CAF50;
        color: white;
        cursor: pointer;
    }
    button:hover {
        background-color: #45a049;
    }
    .mensaje {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 16px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 16px;
        z-index: 9999;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .verde { background-color: #4CAF50; color: white; }
    .rojo { background-color: #f44336; color: white; }
    .azul { background-color: #2196F3; color: white; }
    .amarillo { background-color: #ff9800; color: white; }
    .rango {
        position: fixed;
        top: 20px;
        left: 20px;
        padding: 10px;
        background-color: #444;
        border-radius: 8px;
        font-size: 14px;
        opacity: 0.85;
    }
</style>
<script>
    setTimeout(function() {
        const alerta = document.getElementById('alerta');
        if (alerta) alerta.remove();
    }, 3000);
</script>
"""

login_html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Intranet - Iniciar Sesión</title>
    """ + estilos + """
</head>
<body>
    {% if mensaje %}
    <div class="mensaje {{color}}" id="alerta">
        {{icono}} {{mensaje}}
    </div>
    <audio autoplay><source src="{{ url_for('static', filename=audio) }}" type="audio/mpeg"></audio>
    {% endif %}

    <h2>Acceso a la Intranet</h2>
    <form method="post">
        <input name="usuario" placeholder="ID" required><br>
        <input name="password" type="password" placeholder="Contraseña" required><br>
        <button type="submit">Ingresar</button>
    </form>
</body>
</html>
"""

home_html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Bienvenido</title>
    """ + estilos + """
    <script>
        setTimeout(function() {
            window.location.href = "{{ url_for('logout', msg='auto') }}";
        }, 180000);
    </script>
</head>
<body onload="document.getElementById('audio').play()">
    {% if mensaje %}
    <div class="mensaje {{color}}" id="alerta">
        {{icono}} {{mensaje}}
    </div>
    <audio id="audio" autoplay>
        <source src="{{ url_for('static', filename=audio) }}" type="audio/mpeg">
    </audio>
    {% endif %}
    <div class="rango">🔰 {{ rango|capitalize }}</div>
    <h2>{{ icono }} {{ mensaje }}</h2>
    <h3>Bienvenido al sistema, {{ usuario }}</h3>

    <button onclick="location.href='{{ url_for('logout', msg='manual') }}'">Cerrar Sesión</button>
</body>
</html>
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
            if intentos == 2:
                mensaje = "Contraseña incorrecta. Quedan 2 intentos."
                audio = "error_2.mp3"
            elif intentos == 1:
                mensaje = "Contraseña incorrecta. Queda 1 intento."
                audio = "error_1.mp3"
            else:
                mensaje = "Demasiados intentos. Ingrese más tarde."
                audio = "error_0.mp3"

            session["mensaje"] = mensaje
            session["color"] = "rojo"
            session["icono"] = "❌"
            session["audio"] = audio
            return redirect(url_for("login"))

        ahora = datetime.now()
        ultima = session.get("ultimo_login")
        session["usuario"] = datos["nombre"]
        session["rango"] = datos["rango"]
        session["ultimo_login"] = ahora.isoformat()
        session["intentos"] = MAX_INTENTOS

        if ultima:
            antes = datetime.fromisoformat(ultima)
            audio = datos["audio_bienvenido_de_nuevo"] if ahora - antes > timedelta(minutes=1) else datos["audio_bienvenido"]
        else:
            audio = datos["audio_bienvenido"]

        session["audio"] = audio
        return redirect(url_for("home"))

    mensaje = session.pop("mensaje", None)
    color = session.pop("color", "")
    icono = session.pop("icono", "")
    audio = session.pop("audio", "")

    return render_template_string(login_html,
        mensaje=mensaje,
        color=color,
        icono=icono,
        audio=audio)

@app.route("/home")
def home():
    if "usuario" in session:
        audio = session.get("audio", "bienvenido.mp3")
        mensaje = "Bienvenido " + session["usuario"] if "de_nuevo" not in audio else "Bienvenido de nuevo, " + session["usuario"]
        return render_template_string(home_html,
            usuario=session["usuario"],
            rango=session.get("rango", ""),
            mensaje=mensaje,
            color="verde",
            icono="✅",
            audio=audio)
    return redirect(url_for("login"))

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()

    mensaje = "Cerrando sesión..."
    audio = "cerrar_sesion.mp3"
    color = "azul"
    icono = "🕓"

    html_logout = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Cerrando sesión</title>
        """ + estilos + """
        <script>
            setTimeout(function() {
                window.location.href = "/";
            }, 3000);
        </script>
    </head>
    <body>
        <div class="mensaje {{color}}" id="alerta">
            {{icono}} {{mensaje}}
        </div>
        <audio autoplay>
            <source src="{{ url_for('static', filename=audio) }}" type="audio/mpeg">
        </audio>
        <h2>{{ icono }} {{ mensaje }}</h2>
    </body>
    </html>
    """

    return render_template_string(html_logout,
        mensaje=mensaje,
        color=color,
        icono=icono,
        audio=audio)

if __name__ == "__main__":
    app.run(debug=True)


