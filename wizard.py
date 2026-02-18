import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import sys
import os
import shutil
import threading
import platform

# ================= CONFIG =================

APP_NAME = "IngeniAz"
VERSION = "1.0.0"
SYSTEM = platform.system()

def get_appdata_dir():
    home = os.path.expanduser("~")
    if SYSTEM == "Windows":
        return os.path.join(os.environ["APPDATA"], APP_NAME)
    elif SYSTEM == "Linux":
        return os.path.join(home, ".local", "share", APP_NAME)
    elif SYSTEM == "Darwin":
        return os.path.join(home, "Library", "Application Support", APP_NAME)

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PAYLOAD_DIR = os.path.join(BASE_DIR, "payload")
APPDATA_DIR = get_appdata_dir()

APP_EXE = os.path.join(APPDATA_DIR, "IngeniAz.exe")

# ==========================================


class Wizard:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Instalador de {APP_NAME}")
        self.root.geometry("620x520")
        self.root.resizable(False, False)

        self.step = 0

        self.main = tk.Frame(root)
        self.main.pack(fill="both", expand=True, padx=20, pady=20)

        self.title = tk.Label(self.main, font=("Segoe UI", 15, "bold"))
        self.title.pack(pady=10)

        self.body = tk.Frame(self.main)
        self.body.pack(fill="both", expand=True)

        self.progress = ttk.Progressbar(self.main, length=560, maximum=100)
        self.progress.pack(pady=10)

        self.btn = tk.Button(
            self.main,
            text="Siguiente →",
            width=14,
            state=tk.DISABLED,
            command=self.next_step
        )
        self.btn.pack(pady=10)

        self.log = None
        self.welcome()

    # ---------- UI HELPERS ----------

    def clear(self):
        for w in self.body.winfo_children():
            w.destroy()
        self.log = None

    def create_log(self):
        self.log = scrolledtext.ScrolledText(
            self.body,
            font=("Consolas", 9),
            height=16
        )
        self.log.pack(fill="both", expand=True)

    def write(self, txt):
        if self.log:
            self.log.insert(tk.END, txt)
            self.log.see(tk.END)
            self.log.update()

    def lock_next(self):
        self.btn.config(state=tk.DISABLED)

    def unlock_next(self):
        self.btn.config(state=tk.NORMAL)

    def set_progress(self, value):
        self.progress["value"] = value

    # ---------- STEPS ----------

    def welcome(self):
        self.title.config(text=f"Bienvenido a {APP_NAME}")
        self.clear()
        self.set_progress(0)

        tk.Label(
            self.body,
            justify="left",
            text=(
                f"{APP_NAME} se instalará en:\n\n"
                f"{APPDATA_DIR}\n\n"
                "Este asistente:\n"
                "• Copiará los archivos\n"
                "• Creará accesos directos\n\n"
                "Presione Siguiente para comenzar."
            )
        ).pack(pady=30)

        self.unlock_next()

    def check_python(self):
        self.title.config(text="Verificando Python")
        self.clear()
        self.create_log()
        self.set_progress(0)
        self.lock_next()

        def run():
            # 1. Verificar si Python ya está instalado
            python_cmd = shutil.which("python") or shutil.which("python3")
            if python_cmd:
                try:
                    result = subprocess.run(
                        [python_cmd, "--version"],
                        capture_output=True, text=True
                    )
                    version = result.stdout.strip() or result.stderr.strip()
                    self.root.after(0, lambda: self.write(f"✅ Python ya instalado: {version}\n"))
                    self.root.after(0, lambda: self.set_progress(100))
                    self.root.after(0, self.unlock_next)
                    return
                except Exception:
                    pass

            # 2. Si no está, buscar la última versión disponible
            self.root.after(0, lambda: self.write("🔍 Python no encontrado. Buscando última versión...\n"))

            try:
                import urllib.request
                import json

                url = "https://www.python.org/api/v2/downloads/release/?is_published=true&pre_release=false&version=3"
                with urllib.request.urlopen(url) as response:
                    data = json.loads(response.read())

                # Ordenar por versión descendente y tomar la primera
                latest = sorted(data, key=lambda x: x["name"], reverse=True)[0]
                latest_name = latest["name"]  # ej: "Python 3.13.2"
                self.root.after(0, lambda: self.write(f"📦 Última versión encontrada: {latest_name}\n"))

                # 3. Buscar el instalador para Windows x64
                files_url = latest["resource_uri"] + "?format=json"
                # Buscar el archivo .exe directamente desde release_files
                release_files_url = "https://www.python.org/api/v2/downloads/release_file/?release=" + str(latest["pk"])
                with urllib.request.urlopen(release_files_url) as response:
                    files_data = json.loads(response.read())

                installer_url = None
                for f in files_data:
                    if "amd64" in f["url"] and f["url"].endswith(".exe"):
                        installer_url = f["url"]
                        break

                if not installer_url:
                    raise Exception("No se encontró instalador .exe para Windows x64.")

                self.root.after(0, lambda: self.write(f"⬇️ Descargando instalador...\n"))

                # 4. Descargar
                installer_path = os.path.join(os.environ["TEMP"], "python_installer.exe")

                def progress_hook(block_num, block_size, total_size):
                    if total_size > 0:
                        percent = min(int(block_num * block_size * 100 / total_size), 99)
                        self.root.after(0, lambda p=percent: self.set_progress(p))

                urllib.request.urlretrieve(installer_url, installer_path, reporthook=progress_hook)
                self.root.after(0, lambda: self.write("✅ Descarga completa. Instalando...\n"))

                # 5. Instalar silenciosamente
                result = subprocess.run(
                    [installer_path, "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_pip=1"],
                    capture_output=True, text=True
                )

                if result.returncode == 0:
                    self.root.after(0, lambda: self.write("✅ Python instalado correctamente.\n"))
                    self.root.after(0, lambda: self.set_progress(100))
                    self.root.after(0, self.unlock_next)
                else:
                    raise Exception(f"El instalador terminó con código {result.returncode}.\n{result.stderr}")

            except Exception as e:
                self.root.after(
                    0,
                    lambda err=str(e): messagebox.showerror(
                        "Error", f"No se pudo instalar Python:\n{err}"
                    )
                )

        threading.Thread(target=run, daemon=True).start()


    def register_uninstall(self):
        if SYSTEM != "Windows":
            return

        uninstall_exe = os.path.join(APPDATA_DIR, "uninstall.exe")

        cmds = [
            rf'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\IngeniAz" /v DisplayName /d "{APP_NAME}" /f',
            rf'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\IngeniAz" /v DisplayVersion /d "{VERSION}" /f',
            rf'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\IngeniAz" /v Publisher /d "Fabrizio Azeglio" /f',
            rf'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\IngeniAz" /v InstallLocation /d "{APPDATA_DIR}" /f',
            rf'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\IngeniAz" /v UninstallString /d "\"{uninstall_exe}\"" /f'
        ]

        for c in cmds:
            subprocess.run(c, shell=True)




    def copy_files(self):
        self.title.config(text="Copiando archivos")
        self.clear()
        self.create_log()
        self.set_progress(0)
        self.lock_next()

        def run():
            try:
                files = []
                for root, _, fs in os.walk(PAYLOAD_DIR):
                    for f in fs:
                        files.append(os.path.join(root, f))

                total = len(files)
                copied = 0

                for src in files:
                    rel = os.path.relpath(src, PAYLOAD_DIR)
                    dst = os.path.join(APPDATA_DIR, rel)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)

                    copied += 1
                    percent = int((copied / total) * 100)
                    self.root.after(0, lambda p=percent: self.set_progress(p))

                self.root.after(0, lambda: self.write("✅ Archivos copiados correctamente\n"))
                self.root.after(0, self.unlock_next)

            except Exception as e:
                self.root.after(
                    0,
                    lambda err=str(e): messagebox.showerror(
                        "Error", f"Error copiando archivos:\n{err}"
                    )
                )

        threading.Thread(target=run, daemon=True).start()

    def shortcuts(self):
        self.title.config(text="Acceso directo")
        self.clear()
        self.set_progress(100)

        if messagebox.askyesno(
            "Acceso directo",
            "¿Crear acceso directo en el Escritorio?"
        ):
            self.create_shortcut()

        self.unlock_next()

    def create_shortcut(self):
        if SYSTEM != "Windows":
            return

        ps_script = f'''
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "{APP_NAME}.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = "{APP_EXE}"
$Shortcut.WorkingDirectory = "{APPDATA_DIR}"
$Shortcut.IconLocation = "{APP_EXE},0"
$Shortcut.Save()
'''

        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            messagebox.showerror(
                "Error",
                f"No se pudo crear el acceso directo:\n\n{result.stderr}"
            )
        else:
            messagebox.showinfo(
                "Acceso directo",
                "Acceso directo creado correctamente en el Escritorio."
            )

    def finish(self):
        self.set_progress(100)

        if messagebox.askyesno(
            "Instalación finalizada",
            "¿Desea ejecutar la aplicación ahora?"
        ):
            subprocess.Popen([APP_EXE], cwd=APPDATA_DIR)
        self.register_uninstall()
        self.root.destroy()

    # ---------- FLOW ----------

    def next_step(self):
        self.step += 1
        steps = {
            1: self.check_python,
            2: self.copy_files,
            3: self.shortcuts,
            4: self.finish
        }
        steps[self.step]()


def main():
    root = tk.Tk()
    Wizard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
