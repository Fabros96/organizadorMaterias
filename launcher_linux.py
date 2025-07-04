import subprocess
import sys
import os

PYTHON_MIN_VERSION = (3, 10)

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
    if not os.path.exists("venv"):
        print("📦 Creando entorno virtual...")
        try:
            subprocess.run(["python3", "-m", "venv", "venv"], check=True)
        except subprocess.CalledProcessError:
            print("❌ Error al crear el entorno virtual.")
            sys.exit(1)
    else:
        print("✅ Entorno virtual ya existe.")

def instalar_dependencias_y_ejecutar():
    pip_path = "./venv/bin/pip"
    python_path = "./venv/bin/python"

    if not os.path.exists(pip_path):
        print("❌ No se encontró pip en el entorno virtual. Abortando.")
        sys.exit(1)

    print("📥 Instalando dependencias...")
    try:
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
    except subprocess.CalledProcessError:
        print("❌ Falló la instalación de dependencias.")
        sys.exit(1)

    print("🚀 Ejecutando la aplicación...")
    try:
        subprocess.run([python_path, "app.py"], check=True)
    except subprocess.CalledProcessError:
        print("❌ Error al ejecutar la aplicación.")
        sys.exit(1)

if __name__ == "__main__":
    print("🔎 Verificando versión de Python...")
    if not verificar_python():
        print("⚠️ Python 3.10+ no está instalado. Se intentará instalar.")
        instalar_python()

    crear_entorno_virtual()
    instalar_dependencias_y_ejecutar()
