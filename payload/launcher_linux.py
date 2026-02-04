import subprocess
import sys
import os

PYTHON_MIN_VERSION = (3, 10)
APP_NAME = "Organizador"

# Detectar correctamente la ruta base según si está empaquetado o no
if getattr(sys, 'frozen', False):
    # Ejecutable empaquetado (PyInstaller u otro)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Script .py normal
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ICONO = os.path.join(BASE_DIR, "icos", "logo.png")
SCRIPT_PATH = os.path.join(BASE_DIR, "app.py")
VENV_PYTHON = os.path.join(BASE_DIR, "venv", "bin", "python")
VENV_PIP = os.path.join(BASE_DIR, "venv", "bin", "pip")
DESKTOP_ENTRY_PATH = os.path.expanduser(f"~/Escritorio/{APP_NAME}.desktop")

def verificar_python():
    try:
        version_output = subprocess.check_output(["python3", "--version"]).decode()
        version = tuple(map(int, version_output.strip().split()[1].split(".")))
        return version >= PYTHON_MIN_VERSION
    except Exception:
        return False

def instalar_python():
    print("⚙️ Intentando instalar Python (Ubuntu/Debian)...")
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "python3", "python3-venv", "python3-pip"], check=True)
    except subprocess.CalledProcessError:
        print("❌ Falló la instalación de Python. Por favor, instala Python manualmente.")
        sys.exit(1)

def crear_entorno_virtual():
    if not os.path.exists(os.path.join(BASE_DIR, "venv")):
        print("📦 Creando entorno virtual...")
        try:
            subprocess.run(["python3", "-m", "venv", "venv"], cwd=BASE_DIR, check=True)
        except subprocess.CalledProcessError:
            print("❌ Error al crear el entorno virtual.")
            sys.exit(1)
    else:
        print("✅ Entorno virtual ya existe.")

def instalar_dependencias():
    req_file = os.path.join(BASE_DIR, "requirements.txt")
    print("Intentando leer:", req_file)
    if not os.path.exists(req_file):
        print(f"⚠️ No se encontró '{req_file}'. Se saltará instalación de dependencias.")
        return

    if not os.path.exists(VENV_PIP):
        print("❌ No se encontró pip en el entorno virtual. Abortando.")
        sys.exit(1)

    print("📥 Instalando dependencias...")
    try:
        subprocess.run([VENV_PIP, "install", "--upgrade", "pip"], check=True)
        subprocess.run([VENV_PIP, "install", "-r", req_file], check=True)
    except subprocess.CalledProcessError:
        print("❌ Falló la instalación de dependencias.")
        sys.exit(1)

def crear_accesso_directo():
    if not os.path.exists(ICONO):
        print(f"⚠️ Atención: no se encontró el icono en {ICONO}. El acceso directo tendrá icono genérico.")
    desktop_entry = f"""[Desktop Entry]
Name={APP_NAME}
Comment=App del Fabri
Exec={VENV_PYTHON} {SCRIPT_PATH}
Icon={ICONO}
Terminal=false
Type=Application
Categories=Utility;
"""
    try:
        with open(DESKTOP_ENTRY_PATH, "w") as f:
            f.write(desktop_entry)
        os.chmod(DESKTOP_ENTRY_PATH, 0o755)
        print(f"✅ Acceso directo creado en: {DESKTOP_ENTRY_PATH}")
    except Exception as e:
        print(f"❌ Error al crear el acceso directo: {e}")
        sys.exit(1)


def ejecutar_aplicacion():
    print("🚀 Ejecutando la aplicación...")
    try:
        subprocess.run([VENV_PYTHON, SCRIPT_PATH], check=True)
    except subprocess.CalledProcessError:
        print("❌ Error al ejecutar la aplicación.")
        sys.exit(1)

if __name__ == "__main__":
    print("🔎 Verificando versión de Python...")
    if not verificar_python():
        print("⚠️ Python 3.10+ no está instalado. Se intentará instalar.")
        instalar_python()

    crear_entorno_virtual()
    instalar_dependencias()
    crear_accesso_directo()
    ejecutar_aplicacion()
