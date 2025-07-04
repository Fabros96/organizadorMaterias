#!/bin/bash

# Variables
ICON_PNG="./icos/logo.png"
ICON_ICO="./icos/logo.ico"
EXECUTABLE_NAME="Organizador"
LAUNCHER_SCRIPT="launcher_linux.py"
VENV_NAME="venv_pyinst"
DESKTOP_FILE="$HOME/.local/share/applications/organizador.desktop"
ICON_DEST_DIR="$HOME/.local/share/icons/hicolor/48x48/apps"
ICON_NAME="logo"  # Nombre para el icono sin extensión

# Obtener ruta absoluta del script launcher_linux.py
SCRIPT_DIR=$(dirname "$(realpath "$LAUNCHER_SCRIPT")")

# Verificar si el ícono PNG existe, si no, usar ruta desde el script
if [ ! -f "$ICON_PNG" ]; then
    ALT_ICON_PNG="$SCRIPT_DIR/icos/logo.png"
    if [ -f "$ALT_ICON_PNG" ]; then
        ICON_PNG="$ALT_ICON_PNG"
        echo "📂 Usando ícono alternativo desde: $ICON_PNG"
    else
        echo "❌ No se encontró el ícono PNG en ninguna de las rutas esperadas."
        exit 1
    fi
fi

# Verificar si el ícono ICO existe, si no usar ruta alternativa
if [ ! -f "$ICON_ICO" ]; then
    ALT_ICON_ICO="$SCRIPT_DIR/icos/logo.ico"
    if [ -f "$ALT_ICON_ICO" ]; then
        ICON_ICO="$ALT_ICON_ICO"
        echo "📂 Usando ícono .ico alternativo desde: $ICON_ICO"
    fi
fi

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

# Crear directorio para iconos estándar y copiar el icono PNG
echo "📁 Copiando ícono a directorio estándar..."
mkdir -p "$ICON_DEST_DIR"
cp "$ICON_PNG" "$ICON_DEST_DIR/$ICON_NAME.png"
chmod 644 "$ICON_DEST_DIR/$ICON_NAME.png"

# Crear archivo .desktop
echo "📁 Creando archivo .desktop..."

mkdir -p "$(dirname "$DESKTOP_FILE")"

cat > "$DESKTOP_FILE" << EOL
[Desktop Entry]
Type=Application
Name=Organizador
Comment=Aplicación para gestión de horarios UTN FRM
Exec=$(pwd)/$EXECUTABLE_NAME
Icon=$ICON_NAME
Terminal=false
Categories=Utility;Education;
StartupNotify=true
EOL

chmod +x "$DESKTOP_FILE"

# Actualizar caché de iconos
echo "♻️ Actualizando caché de iconos..."
gtk-update-icon-cache ~/.local/share/icons/hicolor

echo "✅ Archivo .desktop creado en: $DESKTOP_FILE"
echo "🎯 Podés buscar 'Organizador Horarios' en tu menú de aplicaciones."

# Ejecutar la aplicación
echo "🚀 Ejecutando la aplicación..."
./"$EXECUTABLE_NAME"
