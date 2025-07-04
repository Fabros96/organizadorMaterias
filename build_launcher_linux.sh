#!/bin/bash

# Variables
ICON_PNG="./icos/logo.png"
ICON_ICO="./icos/logo.ico"
EXECUTABLE_NAME="OrganizadorLinux"
LAUNCHER_SCRIPT="launcher_linux.py"
VENV_NAME="venv_pyinst"
DESKTOP_FILE="$HOME/.local/share/applications/organizador.desktop"

# Crear entorno virtual para PyInstaller si no existe
if [ ! -d "$VENV_NAME" ]; then
    echo "🔧 Creando entorno virtual para PyInstaller..."
    python3 -m venv "$VENV_NAME" || { echo "❌ Error creando entorno virtual"; exit 1; }
fi

source "$VENV_NAME/bin/activate"

# Instalar pyinstaller si no está
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 Instalando PyInstaller..."
    pip install --upgrade pip
    pip install pyinstaller || { echo "❌ Error instalando PyInstaller"; deactivate; exit 1; }
fi

# Convertir PNG a ICO si es necesario
if [ ! -f "$ICON_ICO" ]; then
    echo "🖼️ Convirtiendo logo.png a logo.ico..."
    if ! command -v convert &> /dev/null; then
        echo "❌ ImageMagick no está instalado. Instalalo con:"
        echo "    sudo apt install imagemagick"
        deactivate
        exit 1
    fi
    convert "$ICON_PNG" "$ICON_ICO" || { echo "❌ Error al convertir ícono"; deactivate; exit 1; }
fi

# Buscar la librería libpython compartida
echo "🔍 Buscando libpython..."
LIBPY_PATH=$(find /usr/lib -name "libpython3*.so*" | grep -v "config" | head -n 1)

if [ -z "$LIBPY_PATH" ]; then
    echo "❌ No se encontró libpython3.x.so. Asegurate de tener instalado el paquete python3.x-dev."
    echo "Ejemplo para instalar: sudo apt install python3.11-dev"
    deactivate
    exit 1
fi

echo "✅ Encontrado: $LIBPY_PATH"

# Generar ejecutable con PyInstaller
echo "⚙️ Generando ejecutable con PyInstaller..."
pyinstaller --onefile --icon="$ICON_ICO" --add-binary "$LIBPY_PATH:." "$LAUNCHER_SCRIPT" || { echo "❌ Error generando ejecutable"; deactivate; exit 1; }

# Mover ejecutable final
if [ -f dist/launcher_linux ]; then
    mv dist/launcher_linux "$EXECUTABLE_NAME"
    chmod +x "$EXECUTABLE_NAME"
    echo "🎉 Ejecutable creado: $EXECUTABLE_NAME"
else
    echo "❌ No se encontró el ejecutable generado en dist/"
    deactivate
    exit 1
fi

deactivate

# Crear archivo .desktop
echo "📁 Creando archivo .desktop..."

mkdir -p "$(dirname "$DESKTOP_FILE")"

cat > "$DESKTOP_FILE" << EOL
[Desktop Entry]
Type=Application
Name=Organizador Horarios
Comment=Aplicación para gestión de horarios
Exec=$(pwd)/$EXECUTABLE_NAME
Icon=$(pwd)/$ICON_PNG
Terminal=false
Categories=Utility;Education;
StartupNotify=true
EOL

chmod +x "$DESKTOP_FILE"

echo "✅ Archivo .desktop creado en: $DESKTOP_FILE"
echo "🎯 Podés buscar 'Organizador Horarios' en tu menú de aplicaciones."

# Ejecutar la aplicación
echo "🚀 Ejecutando la aplicación..."
./"$EXECUTABLE_NAME"
