import os
import subprocess
import platform
import sys

APP_NAME = "OrganizadorByFabri"

if platform.system() != "Windows":
    raise SystemExit("Desinstalador solo soportado en Windows")

# Paths
APPDATA_DIR = os.path.join(os.environ["APPDATA"], APP_NAME)
DESKTOP = os.path.join(os.environ["USERPROFILE"], "Desktop")
SHORTCUT = os.path.join(DESKTOP, f"{APP_NAME}.lnk")
UNINSTALL_EXE = os.path.abspath(sys.argv[0])

def log(msg):
    print(msg)

# ---------- BORRAR SHORTCUT ----------
def delete_shortcut():
    if os.path.exists(SHORTCUT):
        try:
            os.remove(SHORTCUT)
            log("✔ Acceso directo eliminado")
        except Exception as e:
            log(f"⚠ No se pudo eliminar el acceso directo: {e}")
    else:
        log("ℹ No se encontró acceso directo")

# ---------- BORRAR REGISTRO ----------
def delete_registry():
    key = rf"HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}"
    subprocess.run(
        ["reg", "delete", key, "/f"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    log("✔ Registro eliminado")

# ---------- BORRADO DIFERIDO CON CMD ----------
def delayed_delete():
    """
    Esto crea un CMD temporal que:
    1. Espera 2 segundos
    2. Borra todo AppData
    3. Borra el uninstall.exe
    """
    cmd_content = f"""
@echo off
timeout /t 2 > nul
echo Eliminando {APPDATA_DIR}...
rmdir /s /q "{APPDATA_DIR}"
echo Eliminando {UNINSTALL_EXE}...
del "{UNINSTALL_EXE}"
"""
    # Guardar script temporal
    temp_cmd = os.path.join(os.environ["TEMP"], "del_uninstall.bat")
    with open(temp_cmd, "w") as f:
        f.write(cmd_content)

    # Ejecutar y salir
    subprocess.Popen(
        ["cmd", "/c", temp_cmd],
        creationflags=subprocess.CREATE_NO_WINDOW
    )

# ---------- MAIN ----------
if __name__ == "__main__":
    log(f"=== DESINSTALADOR {APP_NAME} ===")
    delete_shortcut()
    delete_registry()
    log("✔ Preparando borrado de AppData y auto-destrucción...")
    delayed_delete()
    log("✔ Desinstalación iniciada, cierre del desinstalador...")
