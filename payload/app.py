import json
import tkinter as tk
import webbrowser
import os
import glob
import darkdetect
import matplotlib
import matplotlib.patheffects as patheffects
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import ttkbootstrap as tb

from matplotlib import font_manager
from tkinter import messagebox, filedialog, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
from ttkbootstrap.constants import *

# ============================================================================
# VARIABLES GLOBALES
# ============================================================================
font_emoji = font_manager.FontProperties(fname="C:/Windows/Fonts/seguiemj.ttf")

_canvas_scroll_activo = None

materias = {}
colores_materias = {}
colores_base = ["PiYG", "summer", "winter", "vanimo", "hsv", "cool", "inferno_r", "Pastel2"]
indice_color = 0

dias_validos = {
    "lunes": "Lunes", "martes": "Martes", "miercoles": "Miércoles",
    "miércoles": "Miércoles", "jueves": "Jueves", "viernes": "Viernes",
    "sabado": "Sábado", "sábado": "Sábado", "domingo": "Domingo"
}

CODIGOS_CARRERA = {
    "Sistemas": "Sist",
    "Electromecánica": "Elmca",
    "Electrónica": "Elec",
    "Química": "Qui",
    "Civil": "Civ"
}

comisiones_visibles = []
datos_alumno = {}
planes_estudio = {}
archivo_alumno_actual = None

# Directorio para almacenar archivos de alumnos
DATA_DIR = "data"

# Orientación del gráfico (horizontal o vertical)
orientacion_grafico = "horizontal"

# Color de fondo del gráfico (None = automático según tema)
color_fondo_grafico = None
usar_mismo_color_por_materia = False
# NUEVO: Diccionario de colores personalizados para horarios propios
colores_extra_personalizados = {}

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================


def crear_tooltip(widget, texto):
    """Muestra un tooltip al hacer hover sobre un widget."""
    tooltip_win = [None]

    def mostrar(event):
        if tooltip_win[0] is not None:
            return
        x = widget.winfo_rootx() + widget.winfo_width() // 2
        y = widget.winfo_rooty() + 50
        
        win = tk.Toplevel(widget)
        win.wm_overrideredirect(True)
        win.attributes('-topmost', True)
        win.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(win, text=texto, background="#FFFFE0", fg="black",
                         relief="solid", borderwidth=1,
                         font=("Arial", 9), padx=6, pady=3)
        label.pack()
        tooltip_win[0] = win

    def ocultar(event):
        if tooltip_win[0] is not None:
            tooltip_win[0].destroy()
            tooltip_win[0] = None

    widget.bind("<Enter>", mostrar)
    widget.bind("<Leave>", ocultar)

    
def obtener_tema_sistema():
    return "darkly" if darkdetect.isDark() else "superhero"

# AGREGAR ESTAS DOS FUNCIONES:
def cargar_tema_guardado():
    """Carga el tema guardado del archivo de configuración"""
    archivo_config = os.path.join(DATA_DIR, ".config_tema.json")
    if os.path.exists(archivo_config):
        try:
            with open(archivo_config, "r") as f:
                config = json.load(f)
                return config.get("tema", obtener_tema_sistema())
        except:
            return obtener_tema_sistema()
    return obtener_tema_sistema()

def guardar_tema(tema):
    """Guarda el tema seleccionado en archivo de configuración"""
    asegurar_carpeta_data()
    archivo_config = os.path.join(DATA_DIR, ".config_tema.json")
    try:
        with open(archivo_config, "w") as f:
            json.dump({"tema": tema}, f)
    except Exception as e:
        print(f"Error al guardar tema: {e}")

def cerrar_con_esc(event):
    widget = event.widget
    if isinstance(widget.winfo_toplevel(), tk.Toplevel):
        widget.winfo_toplevel().destroy()

def abrir_github():
    webbrowser.open("https://github.com/Fabros96")
    webbrowser.open("https://github.com/Fabros96/organizadorMaterias")

def mostrar_tutorial(root, forzar=False):
    """Tutorial: fondo oscuro + caja info + ventana del menú principal completamente nítida."""

    es_primera_vez = not os.path.exists(os.path.join(DATA_DIR, ".tutorial_completado"))

    if not forzar and not es_primera_vez:
        if not messagebox.askyesno("Tutorial", "¿Desea ver el tutorial nuevamente?"):
            return

    root.focus_set()
    root.update_idletasks()

    # ══ VENTANA 1: fondo oscuro tamaño pantalla (sin tapar explorador) ══
    overlay = tk.Toplevel(root)
    overlay.overrideredirect(True)
    # NO usar -fullscreen ni -topmost para no tapar la barra de tareas
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    overlay.geometry(f"{sw}x{sh}+0+0")
    overlay.configure(bg='black')
    overlay.attributes('-alpha', 0.72)

    # ══ VENTANA 3: copia nítida del menú principal ═══════════════
    # Posicionada exactamente sobre el root, sin alpha, completamente opaca
    root.update_idletasks()
    rx  = root.winfo_rootx()
    ry  = root.winfo_rooty()
    rw  = root.winfo_width()
    rh  = root.winfo_height()

    menu_clone = tk.Toplevel(root)
    menu_clone.overrideredirect(True)
    menu_clone.attributes('-topmost', True)
    menu_clone.geometry(f"{rw}x{rh}+{rx}+{ry}")

    try:
        import PIL.ImageGrab as ImageGrab
        screenshot = ImageGrab.grab(bbox=(rx, ry, rx + rw, ry + rh))
        screenshot_tk = ImageTk.PhotoImage(screenshot)
        clone_canvas = tk.Canvas(menu_clone, highlightthickness=0, width=rw, height=rh)
        clone_canvas.pack(fill="both", expand=True)
        clone_canvas.create_image(0, 0, anchor="nw", image=screenshot_tk)
        clone_canvas._img_ref = screenshot_tk
    except Exception:
        clone_canvas = tk.Canvas(menu_clone, bg="#dddddd", highlightthickness=0)
        clone_canvas.pack(fill="both", expand=True)

    # ══ VENTANA 2: caja de información ══════════════════════════
    info_win = tk.Toplevel(root)
    info_win.attributes('-topmost', True)
    info_win.overrideredirect(True)
    info_win.configure(bg='white')

    texto_frame = tk.Frame(info_win, bg='white', relief='solid', borderwidth=3)
    texto_frame.pack(fill="both", expand=True)

    paso_actual = [0]

    pasos = [
        {"titulo": "¡Bienvenido al Planificador de Horarios! 🎓",
         "texto": "Este tutorial te guiará por las funcionalidades principales.\n\n"
                  "Presiona 'Siguiente' para continuar o 'Omitir' para salir.",
         "widget_objetivo": None, "posicion": "centro"},
        {"titulo": "Información del Alumno 👤",
         "texto": "Aquí se muestra tu nombre y carrera actual.\n\n"
                  "Puedes cambiar estos datos en 'Gestión de Alumno'.",
         "widget_objetivo": "info_frame", "posicion": "abajo"},
        {"titulo": "Barra de Progreso 📊",
         "texto": "Visualiza tu avance:\n• Verde: Materias obligatorias aprobadas\n"
                  "• Naranja: Horas electivas completadas\n\nSe actualiza automáticamente.",
         "widget_objetivo": "progreso_frame", "posicion": "abajo"},
        {"titulo": "Gestión de Alumno - Nuevo 📝",
         "texto": "Clic en 'Nuevo' para crear un alumno nuevo.\n\n"
                  "Deberás ingresar:\n• Nombre del alumno\n• Carrera que cursa",
         "widget_objetivo": "btn_nuevo_alumno", "posicion": "abajo", "extra_highlight": True},
        {"titulo": "Gestión de Alumno - Editar ✏️",
         "texto": "Clic en 'Editar' para modificar:\n• Nombre del alumno actual\n• Cambiar de carrera",
         "widget_objetivo": "btn_editar_alumno", "posicion": "abajo", "extra_highlight": True},
        {"titulo": "Gestión de Alumno - Cargar 📂",
         "texto": "Clic en 'Cargar' para abrir un alumno previamente guardado.\n\n"
                  "Útil cuando tienes múltiples alumnos creados.",
         "widget_objetivo": "btn_cargar_alumno", "posicion": "abajo", "extra_highlight": True},
        {"titulo": "Gestión de Alumno - Eliminar 🗑️",
         "texto": "Clic en 'Eliminar' para borrar el alumno actual.\n\n"
                  "⚠️ Esta acción NO se puede deshacer.",
         "widget_objetivo": "btn_eliminar_alumno", "posicion": "abajo", "extra_highlight": True},
        {"titulo": "Seleccionar Materias 📚",
         "texto": "Dos formas de seleccionar materias:\n\n"
                  "• Por Carrera: Organizadas por año\n• Por Materia: Búsqueda alfabética",
         "widget_objetivo": "frame_sel", "posicion": "abajo"},
        {"titulo": "Horarios Propios ⏰",
         "texto": "Agrega actividades personales:\n• Gimnasio, Talleres, Trabajo\n"
                  "• Cursos de idiomas\n\nAparecerán en tu horario con borde grueso.",
         "widget_objetivo": "frame_extra", "posicion": "abajo"},
        {"titulo": "Visualizar Horarios 📅",
         "texto": "Grafica tus materias seleccionadas:\n\n"
                  "• Ver horarios semanales\n• Detectar superposiciones\n"
                  "• Rotar vista\n• Exportar PNG/PDF/SVG\n"
                  "• Eliminar 🗑️ - Limpia los horarios de materias seleccionadas\n",
         "widget_objetivo": "frame_vis", "posicion": "abajo"},
        {"titulo": "Otras Opciones 🎨",
         "texto": "• Cambiar entre tema claro/oscuro 🌞/🌙\n"
                  "• Visitar el repositorio en GitHub\n• Volver a ver este tutorial",
         "widget_objetivo": "frame_otros", "posicion": "arriba"},
        {"titulo": "¡Todo Listo! 🚀",
         "texto": "Ya conoces las funcionalidades principales.\n\n"
                  "¡Comienza a organizar tu horario universitario!\n\n"
                  "Recuerda: Todo se guarda automáticamente.",
         "widget_objetivo": None, "posicion": "centro"},
    ]

    titulo_label = tk.Label(texto_frame, text="", font=("Arial", 10, "bold"),
                            bg='white', wraplength=400, justify="center")
    titulo_label.pack(pady=(15, 5), padx=20)

    contenido_label = tk.Label(texto_frame, text="", font=("Arial", 10),
                               bg='white', wraplength=400, justify="left")
    contenido_label.pack(pady=10, padx=20)

    progreso_label = tk.Label(texto_frame, text="", font=("Arial", 9), bg='white', fg='gray')
    progreso_label.pack(pady=5)

    botones_frame = tk.Frame(texto_frame, bg='white')
    botones_frame.pack(pady=15)

    def cerrar_todo():
        for w in (info_win, menu_clone, overlay):
            try:
                w.destroy()
            except:
                pass

    def buscar_widget(nombre):
        if hasattr(root, '_app_instance'):
            app = root._app_instance
            if hasattr(app, nombre):
                c = getattr(app, nombre)
                try:
                    if c.winfo_exists():
                        return c
                except:
                    pass
        return None

    def dibujar_recuadro(widget_nombre, extra_highlight=False):
        """Dibuja el recuadro verde/amarillo sobre clone_canvas."""
        clone_canvas.delete("spotlight")
        if not widget_nombre:
            return None
        widget = buscar_widget(widget_nombre)
        if not widget:
            return None
        try:
            widget.update_idletasks()
            wx = widget.winfo_rootx()
            wy = widget.winfo_rooty()
            ww = widget.winfo_width()
            wh = widget.winfo_height()
            # coordenadas relativas al menu_clone
            menu_clone.update_idletasks()
            mx = menu_clone.winfo_rootx()
            my = menu_clone.winfo_rooty()
            rel_x = wx - mx
            rel_y = wy - my
            pad = 10
            if extra_highlight:
                for off in [0, 3, 6, 9]:
                    clone_canvas.create_rectangle(
                        rel_x - pad - off, rel_y - pad - off,
                        rel_x + ww + pad + off, rel_y + wh + pad + off,
                        outline="#FFFF00", width=4, tags="spotlight")
            else:
                clone_canvas.create_rectangle(
                    rel_x - pad, rel_y - pad,
                    rel_x + ww + pad, rel_y + wh + pad,
                    outline="#00FF00", width=5, tags="spotlight")
            return rel_x, rel_y, ww, wh
        except:
            return None

    def posicionar_info(coords, posicion):
        fw, fh = 460, 330
        sw = overlay.winfo_screenwidth()
        sh = overlay.winfo_screenheight()
        if posicion == "centro" or coords is None:
            px = (sw - fw) // 2
            py = (sh - fh) // 2
        else:
            mx = menu_clone.winfo_rootx()
            my = menu_clone.winfo_rooty()
            ax = mx + coords[0]
            ay = my + coords[1]
            if posicion == "abajo":
                px, py = ax, ay + coords[3] + 30
            elif posicion == "arriba":
                px, py = ax, ay - fh - 30
            else:
                px, py = (sw - fw) // 2, (sh - fh) // 2
        px = max(10, min(px, sw - fw - 10))
        py = max(10, min(py, sh - fh - 10))
        info_win.geometry(f"{fw}x{fh}+{px}+{py}")

    def actualizar_paso():
        paso = pasos[paso_actual[0]]
        titulo_label.config(text=paso["titulo"])
        contenido_label.config(text=paso["texto"])
        progreso_label.config(text=f"Paso {paso_actual[0] + 1} de {len(pasos)}")
        btn_anterior.config(state="normal" if paso_actual[0] > 0 else "disabled")
        if paso_actual[0] == len(pasos) - 1:
            btn_siguiente.config(text="Finalizar", bg="#4CAF50")
        else:
            btn_siguiente.config(text="Siguiente →", bg="#2196F3")
        extra_hl = paso.get("extra_highlight", False)
        coords = dibujar_recuadro(paso["widget_objetivo"], extra_hl)
        posicionar_info(coords, paso["posicion"])
        btn_siguiente.focus_set()

    def siguiente():
        if paso_actual[0] < len(pasos) - 1:
            paso_actual[0] += 1
            actualizar_paso()
        else:
            finalizar_tutorial()

    def anterior():
        if paso_actual[0] > 0:
            paso_actual[0] -= 1
            actualizar_paso()

    def omitir():
        if es_primera_vez and not forzar:
            messagebox.showwarning("Tutorial Obligatorio",
                "Debes completar el tutorial en tu primera vez.\n"
                "Puedes avanzar rápidamente con 'Siguiente'.", parent=info_win)
        else:
            cerrar_todo()

    def finalizar_tutorial():
        asegurar_carpeta_data()
        with open(os.path.join(DATA_DIR, ".tutorial_completado"), "w") as f:
            f.write("1")
        cerrar_todo()

    btn_anterior = tk.Button(botones_frame, text="← Anterior", command=anterior,
                             padx=15, pady=8, font=("Arial", 10))
    btn_anterior.pack(side="left", padx=5)

    btn_siguiente = tk.Button(botones_frame, text="Siguiente →", command=siguiente,
                              bg="#2196F3", fg="white", padx=15, pady=8, font=("Arial", 10))
    btn_siguiente.pack(side="left", padx=5)

    if not es_primera_vez or forzar:
        btn_omitir = tk.Button(botones_frame, text="Omitir Tutorial", command=omitir,
                               padx=15, pady=8, font=("Arial", 10))
        btn_omitir.pack(side="left", padx=5)

    for win in (overlay, info_win, menu_clone):
        win.bind("<Left>",   lambda e: anterior())
        win.bind("<Right>",  lambda e: siguiente())
        win.bind("<Escape>", lambda e: omitir())
        win.bind("<Return>", lambda e: siguiente())

    actualizar_paso()

def mostrar_loader(parent, mensaje="Actualizando..."):
    parent.update_idletasks()

    px = parent.winfo_rootx()
    py = parent.winfo_rooty()
    pw = parent.winfo_width()
    ph = parent.winfo_height()

    # Capa oscura: usa overrideredirect=False para respetar z-order del SO
    fondo = tk.Toplevel(parent)
    fondo.overrideredirect(True)
    fondo.configure(bg='black')
    fondo.attributes('-alpha', 0.75)
    # NO usar -topmost para no tapar la barra de tareas de Windows
    fondo.geometry(f"{pw}x{ph}+{px}+{py}")
    try:
        fondo.wm_iconbitmap("")
    except Exception:
        pass

    cw, ch = 260, 60
    cx = px + (pw - cw) // 2
    cy = py + (ph - ch) // 2

    cartel = tk.Toplevel(parent)
    cartel.overrideredirect(True)
    # NO usar -topmost
    cartel.configure(bg='#1e1e1e')
    cartel.geometry(f"{cw}x{ch}+{cx}+{cy}")
    cartel.attributes('-alpha', 1.0)
    try:
        cartel.wm_iconbitmap("")
    except Exception:
        pass

    tk.Label(
        cartel, text=mensaje,
        font=("Arial", 11, "bold"),
        bg='#1e1e1e', fg='white',
        padx=20
    ).pack(pady=(14, 4))

    class LoaderHandle:
        def __init__(self, parent_win, f, c):
            self._parent    = parent_win
            self._fondo     = f
            self._cartel    = c
            self._destroyed = False
            self._cw = cw
            self._ch = ch
            # Bind Configure para seguir al padre al moverse
            self._bind_cfg  = self._parent.bind("<Configure>", self._sync, add="+")
            # Bind Map/Unmap para minimizado (más confiable que state())
            self._bind_unmap = self._parent.bind("<Unmap>", self._ocultar, add="+")
            self._bind_map   = self._parent.bind("<Map>",   self._sync,   add="+")

        def _ocultar(self, event=None):
            if self._destroyed:
                return
            try: self._fondo.withdraw()
            except Exception: pass
            try: self._cartel.withdraw()
            except Exception: pass

        def _sync(self, event=None):
            if self._destroyed:
                return
            # Solo reaccionar al evento del padre, no de sus hijos
            if event is not None and event.widget != self._parent:
                return
            try:
                state = self._parent.state()
            except Exception:
                return
            if state == 'iconic':
                self._ocultar()
                return
            try:
                ppx = self._parent.winfo_rootx()
                ppy = self._parent.winfo_rooty()
                ppw = self._parent.winfo_width()
                pph = self._parent.winfo_height()
                self._fondo.geometry(f"{ppw}x{pph}+{ppx}+{ppy}")
                self._fondo.deiconify()
                ncx = ppx + (ppw - self._cw) // 2
                ncy = ppy + (pph - self._ch) // 2
                self._cartel.geometry(f"{self._cw}x{self._ch}+{ncx}+{ncy}")
                self._cartel.deiconify()
                # Mantener el cartel sobre el fondo sin -topmost global
                self._cartel.lift(self._fondo)
            except Exception:
                pass

        def destroy(self):
            self._destroyed = True
            for bid, evt in [
                (self._bind_cfg,   "<Configure>"),
                (self._bind_unmap, "<Unmap>"),
                (self._bind_map,   "<Map>"),
            ]:
                try: self._parent.unbind(evt, bid)
                except Exception: pass
            for w in (self._cartel, self._fondo):
                try: w.destroy()
                except Exception: pass

        def update(self):
            for w in (self._fondo, self._cartel):
                try: w.update()
                except Exception: pass

    handle = LoaderHandle(parent, fondo, cartel)
    handle.update()
    return handle

def centrar_ventana(ventana):
    ventana.update_idletasks()
    pantalla_width = ventana.winfo_screenwidth()
    pantalla_height = ventana.winfo_screenheight()
    ventana_width = ventana.winfo_width()
    ventana_height = ventana.winfo_height()
    pos_x = (pantalla_width // 2) - (ventana_width // 2)
    pos_y = (pantalla_height // 2) - (ventana_height // 2)
    ventana.geometry(f"{ventana_width}x{ventana_height}+{pos_x}+{pos_y-100}")

def centrar_ventana_exacto(ventana):
    """Centra una ventana exactamente en el centro de la pantalla, luego de renderizarla."""
    def _centrar():
        ventana.update_idletasks()
        ancho = ventana.winfo_width()
        alto = ventana.winfo_height()
        pantalla_w = ventana.winfo_screenwidth()
        pantalla_h = ventana.winfo_screenheight()
        pos_x = (pantalla_w - ancho) // 2
        pos_y = (pantalla_h - alto) // 2
        ventana.geometry(f"{ancho}x{alto}+{pos_x}+{pos_y}")
    ventana.after(10, _centrar)

def configurar_ventana(ventana, titulo, ancho, alto, centrar=True, icono=None):
    ventana.title(titulo)
    ventana.geometry(f"{ancho}x{alto}")
    
    # Aplicar ícono si se proporciona
    if icono:
        try:
            ventana.iconphoto(True, icono)
        except:
            pass
    
    if centrar:
        ventana.update_idletasks()
        pantalla_width = ventana.winfo_screenwidth()
        pantalla_height = ventana.winfo_screenheight()
        pos_x = (pantalla_width - ancho) // 2
        pos_y = (pantalla_height - alto) // 2
        ventana.geometry(f"{ancho}x{alto}+{pos_x}+{pos_y-50}")

def traer_ventana_al_frente(ventana):
    ventana.lift()
    ventana.focus_force()
    ventana.attributes('-topmost', True)
    ventana.after(100, lambda: ventana.attributes('-topmost', False))

def quitar_foco_ventana(ventana):
    ventana.lower()

def habilitar_scroll_con_rueda(canvas, scrollable_frame):
    global _canvas_scroll_activo

    def _on_mousewheel(event):
        global _canvas_scroll_activo
        if _canvas_scroll_activo and _canvas_scroll_activo.winfo_exists():
            _canvas_scroll_activo.yview_scroll(
                int(-1 * (event.delta / 120)), "units"
            )

    def _on_enter(event):
        global _canvas_scroll_activo
        _canvas_scroll_activo = canvas
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _on_leave(event):
        global _canvas_scroll_activo
        if _canvas_scroll_activo == canvas:
            _canvas_scroll_activo = None
        canvas.unbind_all("<MouseWheel>")

    def _on_destroy(event):
        global _canvas_scroll_activo
        if _canvas_scroll_activo == canvas:
            _canvas_scroll_activo = None
        try:
            canvas.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass

    canvas.bind("<Enter>", _on_enter)
    canvas.bind("<Leave>", _on_leave)
    canvas.bind("<Destroy>", _on_destroy)

def obtener_periodo_cursado(data):
    for key, value in data.items():
        if key not in ["NumeroMat", "Año", "Regulares", "Arpobadas", "Hs"]:
            for item in value:
                if isinstance(item, list) and len(item) == 2 and item[0] == "Cursado":
                    periodo = item[1]
                    if periodo == "1":
                        return "1er Sem"
                    elif periodo == "2":
                        return "2do Sem"
                    elif periodo == "A":
                        return "Anual"
    return ""

def normalizar_texto(texto):
    import unicodedata
    texto_sin_tildes = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return texto_sin_tildes.lower()

def aplicar_color_widget(widget, color_bg, color_fg):
    try:
        widget.configure(bg=color_bg, fg=color_fg)
        if isinstance(widget, tk.Frame):
            for child in widget.winfo_children():
                if isinstance(child, (tk.Label, tk.Button)):
                    try:
                        child.configure(bg=color_bg, fg=color_fg)
                    except:
                        pass
    except:
        pass

def obtener_colores_segun_tema(estado, tema_oscuro):
    if estado == "aprobada":
        if tema_oscuro:
            return "#90EE90", "black"
        else:
            return "#006400", "white"
    elif estado == "regular":
        if tema_oscuro:
            return "#FFFFE0", "black"
        else:
            return "#DAA520", "black"
    elif estado == "libre":
        if tema_oscuro:
            return "#FFD700", "black"
        else:
            return "#FF8C00", "white"
    elif estado == "cursando":
        if tema_oscuro:
            return "#DDA0DD", "black"
        else:
            return "#8B008B", "white"
    elif estado == "por_cursar":
        if tema_oscuro:
            return "#808080", "white"
        else:
            return "#D3D3D3", "black"
    elif estado == "cursable":
        if tema_oscuro:
            return "#ADD8E6", "black"
        else:
            return "#00008B", "white"
    elif estado == "no_cursable":
        if tema_oscuro:
            return "#FFB6C1", "black"
        else:
            return "#8B0000", "white"
    else:
        if tema_oscuro:
            return "#2b2b2b", "white"
        else:
            return "#f0f0f0", "black"

# ============================================================================
# NUEVA FUNCIÓN: Calcular luminancia y colores contrastantes para leyenda
# ============================================================================

def calcular_colores_leyenda(bg_color):
    """
    Dado el color de fondo del gráfico, calcula el color de fondo y texto
    para la leyenda de materias con máximo contraste.
    
    Si el fondo es CLARO  → leyenda con fondo BLANCO y letras NEGRAS con borde negro
    Si el fondo es OSCURO → leyenda con fondo NEGRO y letras BLANCAS con borde blanco
    """
    try:
        hex_color = bg_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
    except:
        luminance = 1.0  # asumir claro si hay error

    if luminance >= 0.5:
        # Fondo claro → leyenda clara con borde oscuro
        legend_bg = 'white'
        legend_fg = 'black'
        legend_border = 'black'
    else:
        # Fondo oscuro → leyenda oscura con borde claro
        legend_bg = 'black'
        legend_fg = 'white'
        legend_border = 'white'

    return legend_bg, legend_fg, legend_border
# ============================================================================
# GESTIÓN DE DATOS
# ============================================================================

def asegurar_carpeta_data():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def generar_nombre_archivo(nombre, carrera):
    codigo = CODIGOS_CARRERA.get(carrera, "")
    nombre_limpio = nombre.replace(" ", "")
    return f"{nombre_limpio}-{codigo}.json"

def cargar_planes_estudio():
    global planes_estudio
    
    if not os.path.exists("ings"):
        messagebox.showerror("Error", "No se encuentra la carpeta 'ings/' con los planes de estudio")
        return False
    
    archivos = {
        "Sistemas": "Sistemas.json",
        "Civil": "Civil.json",
        "Electromecánica": "Electromecanica.json",
        "Electrónica": "Electronica.json",
        "Química": "Quimica.json"
    }
    
    for carrera, archivo in archivos.items():
        ruta = os.path.join("ings", archivo)
        if os.path.exists(ruta):
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    planes_estudio[carrera] = json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar {archivo}: {e}")
                return False
    
    if not planes_estudio:
        messagebox.showerror("Error", "No se pudo cargar ningún plan de estudio")
        return False
    
    return True

def listar_archivos_alumnos():
    asegurar_carpeta_data()
    patron = os.path.join(DATA_DIR, "*-*.json")
    archivos = glob.glob(patron)
    archivos_validos = []
    for archivo in archivos:
        nombre_archivo = os.path.basename(archivo)
        if any(codigo in nombre_archivo for codigo in CODIGOS_CARRERA.values()):
            archivos_validos.append(archivo)
    return archivos_validos

def cargar_archivo_alumno(ruta_archivo):
    global datos_alumno, archivo_alumno_actual, materias, comisiones_visibles, usar_mismo_color_por_materia, colores_extra_personalizados
    
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            datos_alumno = json.load(f)
        archivo_alumno_actual = ruta_archivo
        
        materias_guardadas = datos_alumno.get("materias_seleccionadas", {})
        materias = {}
        
        for materia, comisiones in materias_guardadas.items():
            materias[materia] = {}
            for comision, horarios in comisiones.items():
                materias[materia][comision] = [tuple(h) if isinstance(h, list) else h for h in horarios]
        
        comisiones_visibles_guardadas = datos_alumno.get("comisiones_visibles", [])
        comisiones_visibles = [tuple(cv) if isinstance(cv, list) else cv for cv in comisiones_visibles_guardadas]
        
        usar_mismo_color_por_materia = datos_alumno.get("usar_mismo_color_por_materia", False)
        
        # NUEVO: Cargar colores personalizados de horarios propio
        colores_extra_personalizados = datos_alumno.get("colores_extra_personalizados", {})
        
        return True
    except json.JSONDecodeError:
        nombre_archivo = os.path.basename(ruta_archivo)
        messagebox.showerror("Archivo Corrupto", 
                            f"Revise el archivo {nombre_archivo}\npuede que esté corrupto.")
        return False
    except Exception as e:
        messagebox.showerror("Error", f"Error al cargar archivo: {e}")
        return False

def guardar_datos_alumno():
    global archivo_alumno_actual
    
    asegurar_carpeta_data()
    
    if not archivo_alumno_actual:
        nombre_archivo = generar_nombre_archivo(
            datos_alumno.get("nombre", "Alumno"),
            datos_alumno.get("carrera", "Sistemas")
        )
        archivo_alumno_actual = os.path.join(DATA_DIR, nombre_archivo)
    
    try:
        with open(archivo_alumno_actual, "w", encoding="utf-8") as f:
            json.dump(datos_alumno, f, indent=2, ensure_ascii=False)
    except Exception as e:
        messagebox.showerror("Error", f"Error al guardar archivo: {e}")

def guardar_materias_seleccionadas():
    global materias, comisiones_visibles, usar_mismo_color_por_materia, colores_extra_personalizados
    
    materias_serializables = {}
    for materia, comisiones in materias.items():
        materias_serializables[materia] = {}
        for comision, horarios in comisiones.items():
            materias_serializables[materia][comision] = [list(h) if isinstance(h, tuple) else h for h in horarios]
    
    datos_alumno["materias_seleccionadas"] = materias_serializables
    
    comisiones_visibles_serializables = [list(cv) if isinstance(cv, tuple) else cv for cv in comisiones_visibles]
    datos_alumno["comisiones_visibles"] = comisiones_visibles_serializables
    
    datos_alumno["usar_mismo_color_por_materia"] = usar_mismo_color_por_materia
    
    # NUEVO: Guardar colores personalizados de horarios propio
    datos_alumno["colores_extra_personalizados"] = colores_extra_personalizados
    
    guardar_datos_alumno()

def crear_nuevo_alumno(root, icono_ventana=None):
    global datos_alumno, archivo_alumno_actual
    
    top = tk.Toplevel(root)
    configurar_ventana(top, "Nuevo Alumno", 450, 250, centrar=True, icono=icono_ventana)
    top.minsize(450, 250)
    try:
        if root.winfo_viewable():
            top.transient(root)
    except:
        pass
    top.grab_set()
    
    def cancelar_creacion():
        top.destroy()
    
    top.protocol("WM_DELETE_WINDOW", cancelar_creacion)
    traer_ventana_al_frente(top)
    
    tk.Label(top, text="Crear Nuevo Alumno", font=("Arial", 14, "bold")).pack(pady=15)
    
    frame = tk.Frame(top)
    frame.pack(pady=10)
    
    tk.Label(frame, text="Nombre:", font=("Arial", 10)).grid(row=0, column=0, sticky="e", padx=10, pady=10)
    entry_nombre = tk.Entry(frame, width=30, font=("Arial", 10))
    entry_nombre.grid(row=0, column=1, padx=10, pady=10)
    entry_nombre.focus()
    
    tk.Label(frame, text="Carrera:", font=("Arial", 10)).grid(row=1, column=0, sticky="e", padx=10, pady=10)
    combo_carrera = ttk.Combobox(frame, values=list(planes_estudio.keys()), width=28, state="readonly", font=("Arial", 10))
    combo_carrera.grid(row=1, column=1, padx=10, pady=10)
    
    def guardar_nuevo():
        global archivo_alumno_actual
        
        nombre = entry_nombre.get().strip()
        carrera = combo_carrera.get()
        
        if not nombre or not carrera:
            messagebox.showwarning("Datos incompletos", "Por favor complete todos los campos", parent=top)
            return
        
        asegurar_carpeta_data()
        
        datos_alumno["nombre"] = nombre
        datos_alumno["carrera"] = carrera
        datos_alumno["estado_materias"] = {}
        datos_alumno["horarios_extra"] = {}
        datos_alumno["materias_seleccionadas"] = {}
        datos_alumno["comisiones_visibles"] = []
        datos_alumno["colores_extra_personalizados"] = {}
        
        nombre_archivo = generar_nombre_archivo(nombre, carrera)
        archivo_alumno_actual = os.path.join(DATA_DIR, nombre_archivo)
        
        guardar_datos_alumno()
        
        messagebox.showinfo("Éxito", f"Archivo creado: {nombre_archivo}", parent=top)
        top.destroy()
    
    btn_frame = tk.Frame(top)
    btn_frame.pack(pady=15)
    
    btn_guardar = tk.Button(btn_frame, text="Crear", command=guardar_nuevo, bg="#4CAF50", fg="white", padx=25, pady=8, font=("Arial", 10))
    btn_guardar.pack(side="left", padx=5)
    
    btn_cancelar = tk.Button(btn_frame, text="Cancelar", command=cancelar_creacion, padx=25, pady=8, font=("Arial", 10))
    btn_cancelar.pack(side="left", padx=5)

    top.bind("<Return>", lambda e: guardar_nuevo())
    top.bind("<Escape>", lambda e: cancelar_creacion())
    
    top.wait_window()

def editar_alumno(root, icono_ventana=None):
    global datos_alumno, archivo_alumno_actual
    
    if not datos_alumno:
        messagebox.showwarning("Sin alumno", "No hay alumno cargado para editar")
        return
    
    top = tk.Toplevel(root)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    ancho = int(screen_width * 0.9)
    alto = int(screen_height * 0.9)
    configurar_ventana(top, "Editar Alumno", 450, 250, centrar=True, icono=icono_ventana)
    top.transient(root)
    top.grab_set()
    traer_ventana_al_frente(top)
    
    # TAMAÑO MÍNIMO - Ventana Editar Alumno
    top.minsize(450, 250)
    
    tk.Label(top, text="Editar Datos del Alumno", font=("Arial", 14, "bold")).pack(pady=15)
    
    frame = tk.Frame(top)
    frame.pack(pady=10)
    
    tk.Label(frame, text="Nombre:", font=("Arial", 10)).grid(row=0, column=0, sticky="e", padx=10, pady=10)
    entry_nombre = tk.Entry(frame, width=30, font=("Arial", 10))
    entry_nombre.insert(0, datos_alumno.get("nombre", ""))
    entry_nombre.grid(row=0, column=1, padx=10, pady=10)
    entry_nombre.focus()
    
    tk.Label(frame, text="Carrera:", font=("Arial", 10)).grid(row=1, column=0, sticky="e", padx=10, pady=10)
    combo_carrera = ttk.Combobox(frame, values=list(planes_estudio.keys()), width=28, state="readonly", font=("Arial", 10))
    combo_carrera.set(datos_alumno.get("carrera", ""))
    combo_carrera.grid(row=1, column=1, padx=10, pady=10)
    
    def guardar_cambios():
        global archivo_alumno_actual
        
        nombre = entry_nombre.get().strip()
        carrera = combo_carrera.get()
        
        if not nombre or not carrera:
            messagebox.showwarning("Datos incompletos", "Por favor complete todos los campos", parent=top)
            return
        
        nombre_antiguo = generar_nombre_archivo(datos_alumno.get("nombre", ""), datos_alumno.get("carrera", ""))
        nombre_nuevo = generar_nombre_archivo(nombre, carrera)
        
        if nombre_antiguo != nombre_nuevo:
            archivo_antiguo = os.path.join(DATA_DIR, nombre_antiguo)
            if os.path.exists(archivo_antiguo):
                os.remove(archivo_antiguo)
        
        datos_alumno["nombre"] = nombre
        datos_alumno["carrera"] = carrera
        
        archivo_alumno_actual = os.path.join(DATA_DIR, nombre_nuevo)
        guardar_datos_alumno()
        
        messagebox.showinfo("Éxito", "Datos actualizados correctamente", parent=top)
        top.destroy()
    
    btn_frame = tk.Frame(top)
    btn_frame.pack(pady=15)
    
    btn_guardar = tk.Button(btn_frame, text="Guardar", command=guardar_cambios, bg="#4CAF50", fg="white", padx=25, pady=8, font=("Arial", 10))
    btn_guardar.pack(side="left", padx=5)
    
    btn_volver = tk.Button(btn_frame, text="Volver", command=top.destroy, padx=25, pady=8, font=("Arial", 10))
    btn_volver.pack(side="left", padx=5)
    
    top.bind("<Return>", lambda e: guardar_cambios())
    top.bind("<Escape>", lambda e: top.destroy())

    top.wait_window()

def seleccionar_alumno_de_lista(archivos, root, icono_ventana=None):
    global datos_alumno, archivo_alumno_actual
    
    top = tk.Toplevel(root)
    configurar_ventana(top, "Seleccionar Alumno", 450, 350, centrar=True, icono=icono_ventana)
    top.minsize(450, 350)
    try:
        if root.winfo_viewable():
            top.transient(root)
    except:
        pass
    
    top.grab_set()
    traer_ventana_al_frente(top)
    
    seleccionado = [False]
    
    def cancelar_seleccion():
        top.destroy()
    
    top.protocol("WM_DELETE_WINDOW", cancelar_seleccion)
    
    tk.Label(top, text="Seleccione un alumno:", font=("Arial", 12, "bold")).pack(pady=10)
    
    frame = tk.Frame(top)
    frame.pack(fill="both", expand=True, padx=15, pady=10)
    
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")
    
    listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
    listbox.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=listbox.yview)
    
    for archivo in archivos:
        nombre_mostrar = os.path.basename(archivo)
        listbox.insert(tk.END, nombre_mostrar)
    
    def cargar_seleccionado():
        seleccion = listbox.curselection()
        if not seleccion:
            messagebox.showwarning("Sin selección", "Por favor seleccione un archivo", parent=top)
            return
        
        archivo = archivos[seleccion[0]]
        if cargar_archivo_alumno(archivo):
            if "horarios_extra" not in datos_alumno:
                datos_alumno["horarios_extra"] = {}
            if "materias_seleccionadas" not in datos_alumno:
                datos_alumno["materias_seleccionadas"] = {}
            if "comisiones_visibles" not in datos_alumno:
                datos_alumno["comisiones_visibles"] = []
            guardar_datos_alumno()
            seleccionado[0] = True
            top.destroy()
    
    def crear_nuevo_desde_lista():
        top.destroy()
        crear_nuevo_alumno(root)
        if datos_alumno and "nombre" in datos_alumno:
            seleccionado[0] = True
    
    btn_frame = tk.Frame(top)
    btn_frame.pack(pady=10)
    
    btn_cargar = tk.Button(btn_frame, text="Seleccionar", command=cargar_seleccionado, 
                          bg="#4CAF50", fg="white", padx=25, pady=8, font=("Arial", 10))
    btn_cargar.pack(side="left", padx=5)
    
    btn_nuevo = tk.Button(btn_frame, text="Crear Nuevo", command=crear_nuevo_desde_lista, 
                     padx=25, pady=8, font=("Arial", 10))
    btn_nuevo.pack(side="left", padx=5)

    btn_volver = tk.Button(btn_frame, text="Volver", command=cancelar_seleccion, 
                        padx=25, pady=8, font=("Arial", 10))
    btn_volver.pack(side="left", padx=5)

    listbox.bind("<Double-Button-1>", lambda e: cargar_seleccionado())
    top.bind("<Return>", lambda e: cargar_seleccionado())
    top.bind("<Escape>", lambda e: cancelar_seleccion())
    
    top.wait_window()

def cargar_alumno_existente(root, icono_ventana=None):
    archivos = listar_archivos_alumnos()
    
    if not archivos:
        messagebox.showinfo("Sin archivos", "No hay archivos de alumnos disponibles.\nCree uno nuevo.")
        return False
    
    seleccionar_alumno_de_lista(archivos, root)
    return bool(datos_alumno)

def inicializar_alumno(root, icono_ventana=None):
    archivos = listar_archivos_alumnos()
    
    if len(archivos) == 0:
        crear_nuevo_alumno(root)
        if not datos_alumno or "nombre" not in datos_alumno:
            return False
        return True
        
    elif len(archivos) == 1:
        cargar_archivo_alumno(archivos[0])
        if "horarios_extra" not in datos_alumno:
            datos_alumno["horarios_extra"] = {}
        if "materias_seleccionadas" not in datos_alumno:
            datos_alumno["materias_seleccionadas"] = {}
        if "comisiones_visibles" not in datos_alumno:
            datos_alumno["comisiones_visibles"] = []
        guardar_datos_alumno()
        nombre_archivo = os.path.basename(archivos[0])
        root.after(750, lambda: messagebox.showinfo("Alumno cargado", f"Se cargó automáticamente:\n{nombre_archivo}"))
        return True
        
    else:
        seleccionar_alumno_de_lista(archivos, root)
        if not datos_alumno or "nombre" not in datos_alumno:
            return False
        return True

def obtener_estado_materia(nombre_materia):
    # Si no está en el diccionario, devolver "por_cursar" en lugar de None
    return datos_alumno.get("estado_materias", {}).get(nombre_materia, "por_cursar")

def establecer_estado_materia(nombre_materia, estado):
    if "estado_materias" not in datos_alumno:
        datos_alumno["estado_materias"] = {}
    datos_alumno["estado_materias"][nombre_materia] = estado
    guardar_datos_alumno()

def verificar_correlativas(materia_data, carrera_plan=None):
    nombre_materia = None
    for nombre, data in (carrera_plan or planes_estudio.get(datos_alumno["carrera"], {})).items():
        if data == materia_data:
            nombre_materia = nombre
            break
    
    if nombre_materia:
        estado_actual = obtener_estado_materia(nombre_materia)
        if estado_actual == "aprobada":
            return "aprobada"
        elif estado_actual == "regular":
            return "regular"
        elif estado_actual == "libre":
            return "libre"
        elif estado_actual == "cursando":
            return "cursando"
        # NO devolver "por_cursar" aquí, dejar que se evalúe con correlativas
    
    aprobadas_necesarias = materia_data.get("Arpobadas", [])
    regulares_necesarias = materia_data.get("Regulares", [])
    
    plan = carrera_plan or planes_estudio.get(datos_alumno["carrera"], {})
    
    for num_mat in aprobadas_necesarias:
        materia_correlativa = encontrar_materia_por_numero(plan, num_mat)
        if materia_correlativa:
            estado = obtener_estado_materia(materia_correlativa)
            if estado not in ["aprobada"]:
                return "no_cursable"
    
    for num_mat in regulares_necesarias:
        materia_correlativa = encontrar_materia_por_numero(plan, num_mat)
        if materia_correlativa:
            estado = obtener_estado_materia(materia_correlativa)
            if estado not in ["regular", "aprobada"]:
                return "no_cursable"
    
    # Si llegamos aquí y el estado es "por_cursar", devolver cursable
    return "cursable"

def mostrar_correlativas_grafico(materia_nombre, root, icono_ventana=None):
    plan = planes_estudio.get(datos_alumno.get("carrera", ""), {})
    
    if materia_nombre not in plan:
        messagebox.showwarning("Materia no encontrada", f"No se encontró la materia '{materia_nombre}'")
        return
    
    materia_data = plan[materia_nombre]
    
    top = tk.Toplevel(root)
    configurar_ventana(top, f"Correlatividades: {materia_nombre}", 600, 400, centrar=True, icono=icono_ventana)
    top.transient(root)
    traer_ventana_al_frente(top)
    
    frame = tk.Frame(top)
    frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    canvas = tk.Canvas(frame, bg="white")
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollable = tk.Frame(canvas, bg="white")
    
    scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    habilitar_scroll_con_rueda(canvas, scrollable)
    
    tk.Label(scrollable, text=f"Materia: {materia_nombre}", font=("Arial", 12, "bold"), bg="white").pack(pady=10)
    
    aprobadas_necesarias = materia_data.get("Arpobadas", [])
    if aprobadas_necesarias:
        tk.Label(scrollable, text="Para RENDIR necesita APROBADAS:", font=("Arial", 10, "bold"), bg="white", fg="darkred").pack(anchor="w", padx=20, pady=(10, 5))
        for num in aprobadas_necesarias:
            nombre_correlativa = encontrar_materia_por_numero(plan, num)
            if nombre_correlativa:
                estado = obtener_estado_materia(nombre_correlativa)
                color = "#90EE90" if estado == "aprobada" else "#FFB6C1"
                item = tk.Label(scrollable, text=f"  • {num}. {nombre_correlativa} [{estado.upper()}]", 
                               bg=color, font=("Arial", 9), anchor="w", padx=10, pady=2)
                item.pack(fill="x", padx=40, pady=1)
    
    regulares_necesarias = materia_data.get("Regulares", [])
    if regulares_necesarias:
        tk.Label(scrollable, text="Para CURSAR necesita REGULARES:", font=("Arial", 10, "bold"), bg="white", fg="darkblue").pack(anchor="w", padx=20, pady=(10, 5))
        for num in regulares_necesarias:
            nombre_correlativa = encontrar_materia_por_numero(plan, num)
            if nombre_correlativa:
                estado = obtener_estado_materia(nombre_correlativa)
                if estado in ["regular", "aprobada"]:
                    color = "#FFFFE0" if estado == "regular" else "#90EE90"
                else:
                    color = "#FFB6C1"
                item = tk.Label(scrollable, text=f"  • {num}. {nombre_correlativa} [{estado.upper()}]", 
                               bg=color, font=("Arial", 9), anchor="w", padx=10, pady=2)
                item.pack(fill="x", padx=40, pady=1)
    
    if not aprobadas_necesarias and not regulares_necesarias:
        tk.Label(scrollable, text="Esta materia no tiene correlatividades", font=("Arial", 10), bg="white", fg="gray").pack(pady=20)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    btn_cerrar = tk.Button(top, text="Volcer", command=top.destroy)
    btn_cerrar.pack(pady=10)

def crear_tooltip_correlativas(widget, materia_nombre, parent_window):
    plan = planes_estudio.get(datos_alumno.get("carrera", ""), {})
    
    if materia_nombre not in plan:
        return
    
    materia_data = plan[materia_nombre]
    tooltip = None
    
    def mostrar_tooltip(event):
        nonlocal tooltip
        if tooltip is not None:
            return
        
        tooltip = tk.Toplevel(parent_window)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root+15}+{event.y_root+15}")
        tooltip.attributes('-topmost', True)
        
        main_frame = tk.Frame(tooltip, relief="solid", borderwidth=2, bg="lightyellow", padx=10, pady=10)
        main_frame.pack()
        
        tk.Label(main_frame, text=f"Correlatividades: {materia_nombre}", 
                font=("Arial", 10, "bold"), bg="lightyellow").pack(anchor="w", pady=(0, 5))
        
        aprobadas_necesarias = materia_data.get("Arpobadas", [])
        if aprobadas_necesarias:
            tk.Label(main_frame, text="Para RENDIR necesita APROBADAS:", 
                    font=("Arial", 9, "bold"), bg="lightyellow", fg="darkred").pack(anchor="w", pady=(5, 2))
            for num in aprobadas_necesarias:
                nombre_correlativa = encontrar_materia_por_numero(plan, num)
                if nombre_correlativa:
                    estado = obtener_estado_materia(nombre_correlativa)
                    color = "#90EE90" if estado == "aprobada" else "#FFB6C1"
                    item = tk.Label(main_frame, text=f"  • {num}. {nombre_correlativa} [{estado.upper()}]", 
                                   bg=color, font=("Arial", 8), anchor="w", padx=5, pady=1)
                    item.pack(fill="x", padx=10, pady=1)
        
        regulares_necesarias = materia_data.get("Regulares", [])
        if regulares_necesarias:
            tk.Label(main_frame, text="Para CURSAR necesita REGULARES:", 
                    font=("Arial", 9, "bold"), bg="lightyellow", fg="darkblue").pack(anchor="w", pady=(5, 2))
            for num in regulares_necesarias:
                nombre_correlativa = encontrar_materia_por_numero(plan, num)
                if nombre_correlativa:
                    estado = obtener_estado_materia(nombre_correlativa)
                    if estado in ["regular", "aprobada"]:
                        color = "#FFFFE0" if estado == "regular" else "#90EE90"
                    else:
                        color = "#FFB6C1"
                    item = tk.Label(main_frame, text=f"  • {num}. {nombre_correlativa} [{estado.upper()}]", 
                                   bg=color, font=("Arial", 8), anchor="w", padx=5, pady=1)
                    item.pack(fill="x", padx=10, pady=1)
        
        if not aprobadas_necesarias and not regulares_necesarias:
            tk.Label(main_frame, text="Sin correlatividades", 
                    font=("Arial", 9), bg="lightyellow", fg="gray").pack(pady=5)
    
    def ocultar_tooltip(event):
        nonlocal tooltip
        if tooltip is not None:
            tooltip.destroy()
            tooltip = None
    
    widget.bind("<Enter>", mostrar_tooltip)
    widget.bind("<Leave>", ocultar_tooltip)

def encontrar_materia_por_numero(plan, num_mat):
    for nombre, data in plan.items():
        if data.get("NumeroMat") == num_mat:
            return nombre
    return None

# ============================================================================
# GESTIÓN DE HORARIOS PROPIO
# ============================================================================

def agregar_horario_extra(root, icono_ventana=None):
    top = tk.Toplevel(root)
    configurar_ventana(top, "Agregar Horario Propio", 500, 450, centrar=True, icono=icono_ventana)
    top.transient(root)
    top.grab_set()
    traer_ventana_al_frente(top)
    top.minsize(500, 450)
    
    tk.Label(top, text="Agregar Taller/Curso Externo", font=("Arial", 14, "bold")).pack(pady=15)
    
    frame = tk.Frame(top)
    frame.pack(pady=10, padx=20, fill="both", expand=True)
    
    tk.Label(frame, text="Nombre:", font=("Arial", 10)).grid(row=0, column=0, sticky="e", padx=10, pady=10)
    entry_nombre = tk.Entry(frame, width=30, font=("Arial", 10))
    entry_nombre.grid(row=0, column=1, padx=10, pady=10, columnspan=2)
    entry_nombre.focus()
    
    # Checkboxes para días
    tk.Label(frame, text="Días:", font=("Arial", 10)).grid(row=1, column=0, sticky="ne", padx=10, pady=10)
    
    dias_frame = tk.Frame(frame)
    dias_frame.grid(row=1, column=1, padx=10, pady=10, sticky="w", columnspan=2)
    
    dias_vars = {}
    dias_lista = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    for i, dia in enumerate(dias_lista):
        var = tk.BooleanVar()
        dias_vars[dia] = var
        chk = tk.Checkbutton(dias_frame, text=dia, variable=var, font=("Arial", 9))
        chk.grid(row=i//2, column=i%2, sticky="w", padx=5, pady=2)
    
    tk.Label(frame, text="Hora inicio (HH:MM):", font=("Arial", 10)).grid(row=2, column=0, sticky="e", padx=10, pady=10)
    entry_hora_inicio = tk.Entry(frame, width=10, font=("Arial", 10))
    entry_hora_inicio.grid(row=2, column=1, padx=10, pady=10, sticky="w")
    entry_hora_inicio.insert(0, "08:00")
    
    tk.Label(frame, text="Hora fin (HH:MM):", font=("Arial", 10)).grid(row=3, column=0, sticky="e", padx=10, pady=10)
    entry_hora_fin = tk.Entry(frame, width=10, font=("Arial", 10))
    entry_hora_fin.grid(row=3, column=1, padx=10, pady=10, sticky="w")
    entry_hora_fin.insert(0, "10:00")
    
    tk.Label(frame, text="(Formato 24 horas: 14:30, 18:45, etc.)", font=("Arial", 8), fg="gray").grid(row=4, column=1, sticky="w", padx=10)
    
    def guardar_horario():
        nombre = entry_nombre.get().strip()
        hora_inicio_str = entry_hora_inicio.get().strip()
        hora_fin_str = entry_hora_fin.get().strip()
        
        # Obtener días seleccionados
        dias_seleccionados = [dia for dia, var in dias_vars.items() if var.get()]
        
        if not nombre:
            messagebox.showwarning("Datos incompletos", "Por favor ingrese un nombre", parent=top)
            return
        
        if not dias_seleccionados:
            messagebox.showwarning("Sin días seleccionados", "Debe seleccionar al menos un día", parent=top)
            return
        
        if not hora_inicio_str or not hora_fin_str:
            messagebox.showwarning("Datos incompletos", "Por favor complete los horarios", parent=top)
            return
        
        try:
            h_i, m_i = map(int, hora_inicio_str.split(":"))
            h_f, m_f = map(int, hora_fin_str.split(":"))
            
            if not (0 <= h_i <= 23 and 0 <= m_i <= 59):
                messagebox.showerror("Error", "Hora de inicio inválida. Use formato 00:00 - 23:59", parent=top)
                return
            
            if not (0 <= h_f <= 23 and 0 <= m_f <= 59):
                messagebox.showerror("Error", "Hora de fin inválida. Use formato 00:00 - 23:59", parent=top)
                return
            
            inicio = h_i + m_i / 60.0
            fin = h_f + m_f / 60.0
            
            if inicio >= fin:
                messagebox.showerror("Error", "La hora de inicio debe ser menor que la hora de fin", parent=top)
                return
            
            if "horarios_extra" not in datos_alumno:
                datos_alumno["horarios_extra"] = {}
            
            if nombre not in datos_alumno["horarios_extra"]:
                datos_alumno["horarios_extra"][nombre] = []
            
            # Agregar horario para cada día seleccionado
            for dia in dias_seleccionados:
                datos_alumno["horarios_extra"][nombre].append([dia, inicio, fin])
            
            guardar_datos_alumno()
            
            dias_str = ", ".join(dias_seleccionados)
            messagebox.showinfo("Éxito", f"Horario '{nombre}' agregado para:\n{dias_str}", parent=top)
            top.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Formato de hora inválido. Use HH:MM (ej: 14:30)", parent=top)
    
    btn_frame = tk.Frame(top)
    btn_frame.pack(pady=15)
    
    btn_guardar = tk.Button(btn_frame, text="Agregar", command=guardar_horario, bg="#4CAF50", fg="white", padx=25, pady=8, font=("Arial", 10))
    btn_guardar.pack(side="left", padx=5)
    
    btn_volver = tk.Button(btn_frame, text="Volver", command=top.destroy, padx=25, pady=8, font=("Arial", 10))
    btn_volver.pack(side="left", padx=5)
    
    top.bind("<Return>", lambda e: guardar_horario())
    top.bind("<Escape>", lambda e: top.destroy())

def gestionar_horarios_extra(root, icono_ventana=None):
    """Ventana para gestionar (ver, eliminar y cambiar color de) horarios propios"""
    top = tk.Toplevel(root)
    configurar_ventana(top, "Gestionar Horarios Propios", 600, 400, centrar=True, icono=icono_ventana)
    top.transient(root)
    traer_ventana_al_frente(top)
    
    tk.Label(top, text="Horarios Propios", font=("Arial", 14, "bold")).pack(pady=15)
    top.minsize(600, 400)

    frame = tk.Frame(top)
    frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")
    
    listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Arial", 10), height=12)
    listbox.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=listbox.yview)
    
    # Lista de tuplas: (nombre, dia, inicio, fin, índice_en_lista_horarios)
    items_data = []
    
    def actualizar_lista():
        listbox.delete(0, tk.END)
        items_data.clear()
        horarios_extra = datos_alumno.get("horarios_extra", {})
        
        if not horarios_extra:
            listbox.insert(tk.END, "-- No hay horarios propios agregados --")
            return
        
        for nombre, horarios in horarios_extra.items():
            for idx, (dia, inicio, fin) in enumerate(horarios):
                h_i = int(inicio)
                m_i = int((inicio % 1) * 60)
                h_f = int(fin)
                m_f = int((fin % 1) * 60)
                color_info = " 🎨" if nombre in colores_extra_personalizados else ""
                texto = f"{nombre}{color_info} - {dia} {h_i:02d}:{m_i:02d} a {h_f:02d}:{m_f:02d}"
                listbox.insert(tk.END, texto)
                items_data.append((nombre, dia, inicio, fin, idx))
    
    # Agregar bind para tecla SUPR
    def eliminar_con_supr(event):
        eliminar_seleccionado()

    listbox.bind("<Delete>", eliminar_con_supr)

    btn_frame = tk.Frame(top)

    def eliminar_seleccionado():
        seleccion = listbox.curselection()
        if not seleccion:
            messagebox.showwarning("Sin selección", "Por favor seleccione un horario para eliminar", parent=top)
            return
        
        idx_seleccion = seleccion[0]
        if idx_seleccion >= len(items_data):
            return
        
        nombre, dia, inicio, fin, idx_horario = items_data[idx_seleccion]
        
        h_i = int(inicio)
        m_i = int((inicio % 1) * 60)
        h_f = int(fin)
        m_f = int((fin % 1) * 60)
        
        if messagebox.askyesno("Confirmar", 
                              f"¿Eliminar el horario '{nombre}' del {dia} {h_i:02d}:{m_i:02d}-{h_f:02d}:{m_f:02d}?", 
                              parent=top):
            if "horarios_extra" in datos_alumno and nombre in datos_alumno["horarios_extra"]:
                # Eliminar solo el horario específico del día
                horarios_nombre = datos_alumno["horarios_extra"][nombre]
                
                # Buscar y eliminar el horario específico
                for i, (d, ini, fi) in enumerate(horarios_nombre):
                    if d == dia and ini == inicio and fi == fin:
                        del horarios_nombre[i]
                        break
                
                # Si no quedan más horarios para este nombre, eliminar la entrada completa
                if not horarios_nombre:
                    del datos_alumno["horarios_extra"][nombre]
                    # Limpiar color personalizado si existía
                    if nombre in colores_extra_personalizados:
                        del colores_extra_personalizados[nombre]
                
                guardar_materias_seleccionadas()
                actualizar_lista()
                messagebox.showinfo("Éxito", "Horario eliminado", parent=top)
    
    def cambiar_color_seleccionado():
        seleccion = listbox.curselection()
        if not seleccion:
            messagebox.showwarning("Sin selección", "Por favor seleccione un horario para cambiar su color", parent=top)
            return
        
        idx_seleccion = seleccion[0]
        if idx_seleccion >= len(items_data):
            return
        
        nombre = items_data[idx_seleccion][0]
        
        from tkinter import colorchooser
        color_actual = colores_extra_personalizados.get(nombre, None)
        color_inicial = color_actual if color_actual else "#4CAF50"
        
        color = colorchooser.askcolor(
            title=f"Elegir color para '{nombre}'",
            color=color_inicial,
            parent=top
        )
        if color[1]:
            colores_extra_personalizados[nombre] = color[1]
            guardar_materias_seleccionadas()
            actualizar_lista()
            messagebox.showinfo("Color actualizado", f"Color de '{nombre}' cambiado.\nSe aplicará al graficar.", parent=top)
    actualizar_lista()
    
    btn_frame = tk.Frame(top)
    btn_frame.pack(pady=10)
    
    btn_eliminar = tk.Button(btn_frame, text="🗑 Eliminar", command=eliminar_seleccionado, 
                             bg="#dc3545", fg="white", padx=20, pady=8, font=("Arial", 10))
    btn_eliminar.pack(side="left", padx=5)
    
    btn_color = tk.Button(btn_frame, text="🎨 Cambiar Color", command=cambiar_color_seleccionado, 
                          bg="#2196F3", fg="white", padx=20, pady=8, font=("Arial", 10))
    btn_color.pack(side="left", padx=5)
    
    btn_cerrar = tk.Button(btn_frame, text="Volver", command=top.destroy, padx=20, pady=8, font=("Arial", 10))
    btn_cerrar.pack(side="left", padx=5)
    
    tk.Label(top, text="💡 Los horarios con 🎨 tienen color personalizado", 
             font=("Arial", 8), fg="gray").pack(pady=2)
    
    top.bind("<Escape>", lambda e: top.destroy())

def regenerar_colores_materias():
    global colores_materias, indice_color, usar_mismo_color_por_materia
    
    temp_indice = indice_color
    
    for materia in materias.keys():
        if materia not in colores_materias:
            base_color = colores_base[temp_indice % len(colores_base)]
            temp_indice += 1
            
            if usar_mismo_color_por_materia:
                colores_materias[materia] = [matplotlib.colormaps.get_cmap(base_color)(0.5)] * 10
            else:
                colores_materias[materia] = [
                    matplotlib.colormaps.get_cmap(base_color)(0.2 + 0.6 * i / 10) for i in range(10)
                ]
    
    indice_color = temp_indice

# ============================================================================
# FUNCIÓN DE EXPORTACIÓN
# ============================================================================

def exportar_grafico():
    """Exporta el gráfico de horarios en múltiples formatos con layout mejorado"""
    guardar_materias_seleccionadas()
    
    global orientacion_grafico
    es_vertical = orientacion_grafico == "vertical"

    file_path = filedialog.asksaveasfilename(
        defaultextension=".png", 
        filetypes=[
            ("PNG files", "*.png"),
            ("PDF files", "*.pdf"),
            ("SVG files", "*.svg"),
            ("All files", "*.*")
        ]
    )
    if not file_path:
        return
    
    # ═══════════════════════════════════════════════════════════════
    # CALCULAR HORARIOS Y SUPERPOSICIONES
    # ═══════════════════════════════════════════════════════════════
    horario_termino_antes = float('inf')
    
    for materia, comisiones in materias.items():
        for comision, horarios in comisiones.items():
            if (materia, comision) in comisiones_visibles:
                for dia, inicio, fin in horarios:
                    if inicio < horario_termino_antes:
                        horario_termino_antes = inicio
    
    horarios_extra = datos_alumno.get("horarios_extra", {})
    for nombre, horarios in horarios_extra.items():
        for dia, inicio, fin in horarios:
            if inicio < horario_termino_antes:
                horario_termino_antes = inicio
    
    if horario_termino_antes == float('inf'):
        horario_termino_antes = 8
    
    # Configuración de colores
    global color_fondo_grafico
    tema_actual = obtener_tema_sistema()
    
    if color_fondo_grafico is None:
        if tema_actual == "darkly":
            bg_color = '#1e1e1e'
            text_color = 'white'
            grid_color = '#555555'
        else:
            bg_color = 'white'
            text_color = 'black'
            grid_color = '#cccccc'
    else:
        bg_color = color_fondo_grafico
        rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16)/255.0 for i in (0, 2, 4))
        luminance = 0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2]
        text_color = 'white' if luminance < 0.5 else 'black'
        grid_color = '#555555' if luminance < 0.5 else '#cccccc'

    legend_bg, legend_fg, legend_border = calcular_colores_leyenda(bg_color)
    
    # ═══════════════════════════════════════════════════════════════
    # DETECTAR SUPERPOSICIONES
    # ═══════════════════════════════════════════════════════════════
    barras_info_temp = []
    dias_map = {"Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4, "Sábado": 5, "Domingo": 6}
    
    for materia_clave, comisiones in materias.items():
        for idx, (comision, horarios) in enumerate(comisiones.items()):
            if (materia_clave, comision) in comisiones_visibles:
                for dia, inicio, fin in horarios:
                    dia_num = dias_map.get(dia, -1)
                    if dia_num >= 0:
                        barras_info_temp.append({
                            'materia': materia_clave, 'comision': comision,
                            'inicio': inicio, 'fin': fin, 'dia_num': dia_num, 'es_extra': False
                        })
    
    horarios_extra_visibles_exp = set(
        datos_alumno.get("horarios_extra_visibles", list(horarios_extra.keys()))
    )
    for nombre, horarios in horarios_extra.items():
        if nombre not in horarios_extra_visibles_exp:
            continue   # ← no exportar ni calcular superposiciones
        for dia, inicio, fin in horarios:
            dia_num = dias_map.get(dia, -1)
            if dia_num >= 0:
                barras_info_temp.append({
                    'materia': nombre, 'comision': "Extra",
                    'inicio': inicio, 'fin': fin, 'dia_num': dia_num, 'es_extra': True
                })
    
    solapamientos_totales = []
    solapamientos_parciales = []
    pares_vistos_temp = set()

    for i, barra1 in enumerate(barras_info_temp):
        for j, barra2 in enumerate(barras_info_temp):
            if i < j and barra1['dia_num'] == barra2['dia_num']:
                x1_1, x2_1 = barra1['inicio'], barra1['fin']
                x1_2, x2_2 = barra2['inicio'], barra2['fin']
                if x1_1 < x2_2 and x2_1 > x1_2:
                    solap_inicio = round(max(x1_1, x1_2), 4)
                    solap_fin    = round(min(x2_1, x2_2), 4)
                    dia          = barra1['dia_num']
                    id1 = f"{barra1['materia']}|{barra1['comision']}"
                    id2 = f"{barra2['materia']}|{barra2['comision']}"
                    par_id = (tuple(sorted([id1, id2])), dia, solap_inicio, solap_fin)
                    if par_id not in pares_vistos_temp:
                        pares_vistos_temp.add(par_id)
                        solap_info = {
                            'barra1': barra1, 'barra2': barra2,
                            'inicio': solap_inicio, 'fin': solap_fin,
                            'dia_num': dia
                        }
                        if x1_1 == x1_2 and x2_1 == x2_2:
                            solapamientos_totales.append(solap_info)
                        else:
                            solapamientos_parciales.append(solap_info)

    def obtener_nombre_completo(materia_clave):
        if "[" in materia_clave:
            nombre_materia = materia_clave.split("[")[0].strip()
            carrera = materia_clave.split("[")[1].rstrip("]").strip()
            return f"{nombre_materia} ({carrera})"
        return materia_clave


    # ── AGRUPAR solapamientos por zona idéntica (dia+inicio+fin) ──
    # Si 3 barras se solapan en el mismo lugar, se genera 1 sola referencia con N participantes
    def agrupar_solapamientos(lista_solap):
        grupos = {}  # clave (dia, inicio, fin) → set de participantes
        for solap in lista_solap:
            zona = (solap['dia_num'], solap['inicio'], solap['fin'])
            if zona not in grupos:
                grupos[zona] = {'participantes': set(), 'dia_num': solap['dia_num'],
                                'inicio': solap['inicio'], 'fin': solap['fin']}
            for key in ('barra1', 'barra2'):
                b = solap[key]
                grupos[zona]['participantes'].add(
                    (obtener_nombre_completo(b['materia']), b['comision'])
                )
        return list(grupos.values())

    grupos_totales   = agrupar_solapamientos(solapamientos_totales)
    grupos_parciales = agrupar_solapamientos(solapamientos_parciales)
    
    # ═══════════════════════════════════════════════════════════════
    # CREAR FIGURA CON GRIDSPEC (LAYOUT DE DOS COLUMNAS)
    # ═══════════════════════════════════════════════════════════════
    import matplotlib.gridspec as gridspec
    
    # Dimensiones adaptativas
    num_materias = len(set(mat for mat, _ in comisiones_visibles))
    num_extras = len(horarios_extra)
    num_superpos = len(solapamientos_totales) + len(solapamientos_parciales)
    
    # Calcular altura necesaria para las leyendas
    altura_minima = 10
    altura_por_item = 0.3
    altura_calculada = max(altura_minima, (num_materias + num_extras + num_superpos * 2) * altura_por_item + 4)
    
    fig_width = 20  # Ancho fijo generoso
    fig_height = max(12, altura_calculada)  # Altura adaptativa
    
    fig = plt.figure(figsize=(fig_width, fig_height), facecolor=bg_color)
    
    # GridSpec: 70% gráfico | 30% leyendas
    gs = gridspec.GridSpec(1, 2, figure=fig, width_ratios=[7, 3], 
                           left=0.05, right=0.98, top=0.95, bottom=0.08, wspace=0.15)
    
    # ═══════════════════════════════════════════════════════════════
    # SUBPLOT IZQUIERDO: GRÁFICO DE HORARIOS
    # ═══════════════════════════════════════════════════════════════
    ax = fig.add_subplot(gs[0])
    ax.set_facecolor(bg_color)
    
    # Configurar ejes
    if es_vertical:
        ax.set_ylim(horario_termino_antes, 24)
        ax.set_yticks(np.arange(horario_termino_antes, 24, 0.5))
        ax.set_yticklabels([f"{int(h)}:{int((h % 1) * 60):02d}" 
                           for h in np.arange(horario_termino_antes, 24, 0.5)])
        ax.set_xlim(-0.5, 6.5)
        ax.set_xticks(range(7))
        ax.set_xticklabels(["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"], rotation=45)
        ax.set_ylabel("Hora", color=text_color, fontsize=14, fontweight='bold')
        ax.set_xlabel("Día", color=text_color, fontsize=14, fontweight='bold')
        
        for y in np.arange(horario_termino_antes, 24, 0.25):
            ax.axhline(y, color=grid_color, linestyle='--', linewidth=0.8, alpha=0.6)
    else:
        ax.set_xlim(horario_termino_antes, 24)
        ax.set_xticks(np.arange(horario_termino_antes, 24, 0.5))
        ax.set_xticklabels([f"{int(h)}:{int((h % 1) * 60):02d}" 
                           for h in np.arange(horario_termino_antes, 24, 0.5)], rotation=45)
        ax.set_ylim(-0.5, 6.5)
        ax.set_yticks(range(7))
        ax.set_yticklabels(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
        ax.set_xlabel("Hora", color=text_color, fontsize=14, fontweight='bold')
        ax.set_ylabel("Día", color=text_color, fontsize=14, fontweight='bold')
        
        for x in np.arange(horario_termino_antes, 24, 0.25):
            ax.axvline(x, color=grid_color, linestyle='--', linewidth=0.8, alpha=0.6)
    
    ax.set_title("Horarios de Clases", color=text_color, fontsize=18, fontweight='bold', pad=15)
    ax.tick_params(axis='both', colors=text_color, labelsize=11)
    
    # ═══════════════════════════════════════════════════════════════
    # DIBUJAR BARRAS DE MATERIAS Y HORARIOS PROPIOS
    # ═══════════════════════════════════════════════════════════════
    dias = {"Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4, "Sábado": 5, "Domingo": 6}
    barras_info = []
    
    global indice_color, usar_mismo_color_por_materia
    for materia in materias.keys():
        if materia not in colores_materias:
            base_color = colores_base[indice_color % len(colores_base)]
            indice_color += 1
            if usar_mismo_color_por_materia:
                colores_materias[materia] = [matplotlib.colormaps.get_cmap(base_color)(0.5)] * 10
            else:
                colores_materias[materia] = [
                    matplotlib.colormaps.get_cmap(base_color)(0.2 + 0.6 * i / 10) for i in range(10)
                ]
    
    for nombre in horarios_extra.keys():
        if nombre not in colores_materias:
            base_color = colores_base[indice_color % len(colores_base)]
            indice_color += 1
            colores_materias[nombre] = [matplotlib.colormaps.get_cmap(base_color)(0.5)]
    
    # Aplicar colores personalizados
    for nombre in horarios_extra.keys():
        if nombre in colores_extra_personalizados:
            colores_materias[nombre] = [colores_extra_personalizados[nombre]]
    
    # Dibujar materias
    for materia_clave, comisiones in materias.items():
        for idx, (comision, horarios) in enumerate(comisiones.items()):
            if (materia_clave, comision) in comisiones_visibles:
                if usar_mismo_color_por_materia:
                    color = colores_materias[materia_clave][0]
                else:
                    color = colores_materias[materia_clave][idx % len(colores_materias[materia_clave])]
                
                for dia, inicio, fin in horarios:
                    dia_num = dias.get(dia, -1)
                    if dia_num >= 0:
                        if es_vertical:
                            rect = ax.bar(dia_num, fin - inicio, bottom=inicio, 
                                        color=color, edgecolor="black", linewidth=1.5)[0]
                        else:
                            rect = ax.barh(dia_num, fin - inicio, left=inicio, 
                                        color=color, edgecolor="black", linewidth=1.5)[0]
                        barras_info.append({
                            'rect': rect, 'materia': materia_clave, 'comision': comision,
                            'inicio': inicio, 'fin': fin, 'dia_num': dia_num, 'es_extra': False
                        })
    
    # Dibujar horarios propios (solo los visibles)
    # NUEVO: Obtener lista de horarios propios visibles desde datos_alumno
    horarios_extra_visibles = datos_alumno.get("horarios_extra_visibles", list(horarios_extra.keys()))

    for nombre, hrs in horarios_extra.items():
        # CRÍTICO: Solo dibujar si está en la lista de visibles
        if nombre not in horarios_extra_visibles:
            continue
            
        color = colores_materias[nombre][0]
        for dia, inicio, fin in hrs:
            dia_num = dias.get(dia, -1)
            if dia_num >= 0:
                if es_vertical:
                    rect = ax.bar(dia_num, fin - inicio, bottom=inicio, 
                                color=color, edgecolor="black", linewidth=3)[0]
                else:
                    rect = ax.barh(dia_num, fin - inicio, left=inicio, 
                                color=color, edgecolor="black", linewidth=3)[0]
                barras_info.append({
                    'rect': rect, 'materia': nombre, 'comision': "Extra",
                    'inicio': inicio, 'fin': fin, 'dia_num': dia_num, 'es_extra': True
                })
    
    # ═══════════════════════════════════════════════════════════════
    # MARCAR SUPERPOSICIONES CON REFERENCIAS
    # ═══════════════════════════════════════════════════════════════
    referencias_totales = {}
    referencias_parciales = {}
    barras_con_superposicion = set()

    referencias = [f"{chr(65 + i)}*" for i in range(26)]
    for i in range(26):
        for j in range(26):
            referencias.append(f"{chr(65 + i)}{chr(65 + j)}*")


    def acortar_nombre(nombre, max_chars=20):
        return nombre if len(nombre) <= max_chars else nombre[:max_chars-3] + "..."

    # Dibujar parche rojo + texto de referencia para cada grupo
    claves_con_superposicion = set()

    todos_grupos = (
        [(g, referencias[i], 'total')   for i, g in enumerate(grupos_totales)] +
        [(g, referencias[len(grupos_totales) + i], 'parcial') for i, g in enumerate(grupos_parciales)]
    )

    referencias_totales_agrupadas   = {}  # ref → grupo  (para leyenda)
    referencias_parciales_agrupadas = {}

    for grupo, ref, tipo in todos_grupos:
        dia_num = grupo['dia_num']
        inicio  = grupo['inicio']
        fin     = grupo['fin']

        if es_vertical:
            rect = mpatches.Rectangle((dia_num - 0.4, inicio), 0.8, fin - inicio,
                                      facecolor='red', hatch='//', edgecolor='black', linewidth=2, zorder=5)
            cx, cy = dia_num, (inicio + fin) / 2
        else:
            rect = mpatches.Rectangle((inicio, dia_num - 0.4), fin - inicio, 0.8,
                                      facecolor='red', hatch='//', edgecolor='black', linewidth=2, zorder=5)
            cx, cy = (inicio + fin) / 2, dia_num
        ax.add_patch(rect)

        text = ax.text(cx, cy, ref, ha='center', va='center',
                       fontsize=11, color='yellow', fontweight='bold', zorder=8)
        text.set_path_effects([patheffects.withStroke(linewidth=2.5, foreground='black')])

        # Marcar todas las barras participantes para no mostrar nombre encima
        for b in barras_info:
            clave = (b['dia_num'], round(b['inicio'], 4), round(b['fin'], 4),
                     b['materia'], b['comision'])
            nombre_b = obtener_nombre_completo(b['materia'])
            com_b    = b['comision']
            if (nombre_b, com_b) in grupo['participantes'] and b['dia_num'] == dia_num:
                claves_con_superposicion.add(clave)

        if tipo == 'total':
            referencias_totales_agrupadas[ref] = grupo
        else:
            referencias_parciales_agrupadas[ref] = grupo

    # Barras sin superposición: mostrar nombre/comisión
    for barra in barras_info:
        clave = (barra['dia_num'], round(barra['inicio'], 4), round(barra['fin'], 4),
                 barra['materia'], barra['comision'])
        if clave in claves_con_superposicion:
            continue
        if es_vertical:
            cx, cy = barra['dia_num'], (barra['inicio'] + barra['fin']) / 2
        else:
            cx, cy = (barra['inicio'] + barra['fin']) / 2, barra['dia_num']
        ancho_barra = barra['fin'] - barra['inicio']
        fontsize = 10 if ancho_barra > 2 else 8
        if barra['es_extra']:
            texto = acortar_nombre(barra['materia'], max_chars=25)
        else:
            texto = barra['comision'][:5] if ancho_barra < 1.5 else barra['comision']
        text = ax.text(cx, cy, texto, ha='center', va='center',
                       fontsize=fontsize, color='white', fontweight='bold', zorder=6)
        text.set_path_effects([patheffects.withStroke(linewidth=2.5, foreground='black')])
    
    # ═══════════════════════════════════════════════════════════════
    # SUBPLOT DERECHO: LEYENDAS (TEXTO PURO, SIN EJES)
    # ═══════════════════════════════════════════════════════════════
    ax_leyenda = fig.add_subplot(gs[1])
    ax_leyenda.axis('off')  # Ocultar ejes
    ax_leyenda.set_xlim(0, 1)
    ax_leyenda.set_ylim(0, 1)
    
    y_pos = 0.98  # Empezar desde arriba
    line_height = 0.025  # Espaciado entre líneas
    
    # ── SECCIÓN 1: MATERIAS ──
    if comisiones_visibles or horarios_extra:
        # Título (sin emoji para evitar warnings)
        ax_leyenda.text(0.05, y_pos, "MATERIAS", fontsize=13, fontweight='bold', 
                    color=text_color, ha='left', va='top',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor=legend_bg, 
                                edgecolor=legend_border, linewidth=2))
        y_pos -= line_height * 1.8
        
        # Dibujar recuadro de fondo
        materias_unicas = set()
        for (mat, _) in comisiones_visibles:
            nombre_completo = obtener_nombre_completo(mat)
            materias_unicas.add((acortar_nombre(nombre_completo, 35), mat))
        
        for nombre_extra in horarios_extra.keys():
            materias_unicas.add((acortar_nombre(nombre_extra, 35), nombre_extra))
        
        for nombre_corto, clave_original in sorted(materias_unicas):
            # Obtener color
            if clave_original in colores_materias:
                try:
                    color_hex = matplotlib.colors.to_hex(colores_materias[clave_original][0])
                except:
                    color_hex = "#808080"
            else:
                color_hex = "#808080"
            
            # Dibujar cuadrado de color
            from matplotlib.patches import Rectangle
            rect = Rectangle((0.02, y_pos - 0.012), 0.035, 0.018, 
                           facecolor=color_hex, edgecolor=legend_border, linewidth=1)
            ax_leyenda.add_patch(rect)
            
            # Texto
            ax_leyenda.text(0.07, y_pos, nombre_corto, fontsize=9, color=text_color, 
                           ha='left', va='top')
            y_pos -= line_height * 1.2
        
        y_pos -= line_height * 1.5  # Espacio antes de siguiente sección
    
    # ── SECCIÓN 2: SUPERPOSICIONES TOTALES ──
    if referencias_totales_agrupadas:
        ax_leyenda.text(0.02, y_pos, "SUPERPOSICIONES TOTALES", fontsize=10,
               fontweight='bold', color='red', ha='left', va='top',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.5))
        y_pos -= line_height * 1.6

        items_total = list(referencias_totales_agrupadas.items())
        mid = (len(items_total) + 1) // 2  # dividir en 2 columnas
        col_izq = items_total[:mid]
        col_der = items_total[mid:]

        for fila_idx in range(max(len(col_izq), len(col_der))):
            y_fila = y_pos

            # Columna izquierda
            if fila_idx < len(col_izq):
                ref, grupo = col_izq[fila_idx]
                participantes = sorted(grupo['participantes'])
                ax_leyenda.text(0.02, y_fila, f"{ref}:", fontsize=8, fontweight='bold',
                               color=text_color, ha='left', va='top')
                y_fila -= line_height * 0.9
                for nombre, com in participantes:
                    n_corto = acortar_nombre(nombre, 22)
                    ax_leyenda.text(0.04, y_fila, f"• {n_corto} ({com})",
                                   fontsize=7, color=text_color, ha='left', va='top')
                    y_fila -= line_height * 0.85

            # Columna derecha
            y_fila_der = y_pos
            if fila_idx < len(col_der):
                ref, grupo = col_der[fila_idx]
                participantes = sorted(grupo['participantes'])
                ax_leyenda.text(0.52, y_fila_der, f"{ref}:", fontsize=8, fontweight='bold',
                               color=text_color, ha='left', va='top')
                y_fila_der -= line_height * 0.9
                for nombre, com in participantes:
                    n_corto = acortar_nombre(nombre, 22)
                    ax_leyenda.text(0.54, y_fila_der, f"• {n_corto} ({com})",
                                   fontsize=7, color=text_color, ha='left', va='top')
                    y_fila_der -= line_height * 0.85

            # Avanzar y_pos por la columna más larga de esta fila
            altura_izq = (1 + len(col_izq[fila_idx][1]['participantes'])) * line_height * 0.9 if fila_idx < len(col_izq) else 0
            altura_der = (1 + len(col_der[fila_idx][1]['participantes'])) * line_height * 0.9 if fila_idx < len(col_der) else 0
            y_pos -= max(altura_izq, altura_der) + line_height * 0.3

        y_pos -= line_height * 0.8

    # ── SECCIÓN 3: SUPERPOSICIONES PARCIALES ──
    if referencias_parciales_agrupadas:
        ax_leyenda.text(0.02, y_pos, "SUPERPOSICIONES PARCIALES", fontsize=10,
               fontweight='bold', color='orange', ha='left', va='top',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.5))
        y_pos -= line_height * 1.6

        items_parcial = list(referencias_parciales_agrupadas.items())
        mid = (len(items_parcial) + 1) // 2
        col_izq = items_parcial[:mid]
        col_der = items_parcial[mid:]

        for fila_idx in range(max(len(col_izq), len(col_der))):
            y_fila = y_pos

            if fila_idx < len(col_izq):
                ref, grupo = col_izq[fila_idx]
                participantes = sorted(grupo['participantes'])
                ax_leyenda.text(0.02, y_fila, f"{ref}:", fontsize=8, fontweight='bold',
                               color=text_color, ha='left', va='top')
                y_fila -= line_height * 0.9
                for nombre, com in participantes:
                    n_corto = acortar_nombre(nombre, 22)
                    ax_leyenda.text(0.04, y_fila, f"• {n_corto} ({com})",
                                   fontsize=7, color=text_color, ha='left', va='top')
                    y_fila -= line_height * 0.85

            y_fila_der = y_pos
            if fila_idx < len(col_der):
                ref, grupo = col_der[fila_idx]
                participantes = sorted(grupo['participantes'])
                ax_leyenda.text(0.52, y_fila_der, f"{ref}:", fontsize=8, fontweight='bold',
                               color=text_color, ha='left', va='top')
                y_fila_der -= line_height * 0.9
                for nombre, com in participantes:
                    n_corto = acortar_nombre(nombre, 22)
                    ax_leyenda.text(0.54, y_fila_der, f"• {n_corto} ({com})",
                                   fontsize=7, color=text_color, ha='left', va='top')
                    y_fila_der -= line_height * 0.85

            altura_izq = (1 + len(col_izq[fila_idx][1]['participantes'])) * line_height * 0.9 if fila_idx < len(col_izq) else 0
            altura_der = (1 + len(col_der[fila_idx][1]['participantes'])) * line_height * 0.9 if fila_idx < len(col_der) else 0
            y_pos -= max(altura_izq, altura_der) + line_height * 0.3
    
    # ═══════════════════════════════════════════════════════════════
    # GUARDAR ARCHIVO
    # ═══════════════════════════════════════════════════════════════
    extension = os.path.splitext(file_path)[1].lower()
    
    if extension == '.pdf':
        fig.savefig(file_path, format='pdf', dpi=300, facecolor=bg_color)
    elif extension == '.svg':
        fig.savefig(file_path, format='svg', facecolor=bg_color)
    else:
        fig.savefig(file_path, format='png', dpi=300, facecolor=bg_color)
    
    plt.close(fig)
    messagebox.showinfo("Éxito", f"Gráfico exportado correctamente como {extension.upper()}")

# ============================================================================
# CLASE PRINCIPAL
# ============================================================================

class HorarioGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Planificador de Horarios - FRM UTN")

        # Control de ventanas únicas
        self.ventanas_activas = {}

        # Referencias para actualización dinámica
        self.canvas_progreso = None
        self.label_info_alumno = None
        
        # ⭐ IMPORTANTE: Lista para mantener referencias a TODAS las imágenes
        self.imagenes_referencias = []

        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_relative_path = os.path.join("icos", "logo.png")
        icon_paths = [
            os.path.join(os.getcwd(), icon_relative_path),
            os.path.join(base_dir, icon_relative_path),
        ]
        
        logo_cargado = False
        self.icon = None  # ⭐ Inicializar antes del bucle
        
        for path in icon_paths:
            if os.path.exists(path):
                try:
                    logo_image = Image.open(path).convert("RGBA")
                    self.icon = ImageTk.PhotoImage(logo_image)
                    
                    # ⭐ CRÍTICO: Guardar en lista de referencias
                    self.imagenes_referencias.append(self.icon)
                    
                    # Aplicar ícono a la ventana root
                    self.root.iconphoto(True, self.icon)
                    logo_cargado = True
                    break
                except Exception as e:
                    print(f"⚠️ No se pudo cargar el ícono desde {path}: {e}")
        
        if not logo_cargado:
            print("❌ No se encontró ningún ícono válido para la ventana.")
            self.icon = None
        
        # Guardar referencia al ícono para todas las ventanas
        self.icono_ventana = self.icon

        root.minsize(450, 515)
        centrar_ventana(root)
        self.tema_actual = cargar_tema_guardado()
        self.style = tb.Style(theme=self.tema_actual)
        
        self.style.configure("PpalGrande.TButton", font=("Arial", 18, "bold"))
        self.style.configure("Tema.TButton", font=("Arial", 20))
        self.style.configure("Github.TButton", font=("Arial", 20))
        
        github_icon_path = os.path.join("icos", "gh.png")
        github_paths = [
            os.path.join(os.getcwd(), github_icon_path),
            os.path.join(base_dir, github_icon_path),
        ]
        self.github_icon = None
        
        for path in github_paths:
            if os.path.exists(path):
                try:
                    github_icon = Image.open(path).convert("RGBA")
                    github_icon = github_icon.resize((30, 30), Image.LANCZOS)
                    self.github_icon = ImageTk.PhotoImage(github_icon)
                    
                    # ⭐ También guardar referencia del ícono de GitHub
                    self.imagenes_referencias.append(self.github_icon)
                    break
                except Exception as e:
                    print(f"⚠️ No se pudo cargar el ícono de GitHub desde {path}: {e}")
        
        self.crear_menu_principal()

        # Registrar instancia para que el tutorial pueda encontrar los widgets
        self.root._app_instance = self 

        # Verificar si es primera vez y mostrar tutorial
        archivos = listar_archivos_alumnos()
        if len(archivos) == 0:
            self.root.after(500, lambda: mostrar_tutorial(self.root, forzar=True))
                
    def menu_seleccionar_por_carrera(self):
        """Menú de selección de materias organizado por carrera y año"""
        
        # Verificar si ya existe la ventana
        if 'seleccionar_carrera' in self.ventanas_activas:
            try:
                ventana_existente = self.ventanas_activas['seleccionar_carrera']
                if ventana_existente.winfo_exists():
                    ventana_existente.lift()
                    ventana_existente.focus_force()
                    return
            except:
                pass
        
        top = tk.Toplevel(self.root)
        self.ventanas_activas['seleccionar_carrera'] = top
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        ancho = int(screen_width * 0.65)
        alto = int(screen_height * 0.65)
        configurar_ventana(top, "Seleccionar por Carrera", ancho, alto, centrar=False, icono=self.icono_ventana)
        top.update_idletasks()
        pos_x = (screen_width - ancho) // 2
        pos_y = (screen_height - alto) // 2
        top.geometry(f"{ancho}x{alto}+{pos_x}+{pos_y}")

        top.minsize(1024,600)
        top.bind("<Escape>", cerrar_con_esc)
        traer_ventana_al_frente(top)
        centrar_ventana_exacto(top)
        
        cambios_estado_temp = {}
        
        # Definir función de cierre PRIMERO
        def al_cerrar_ventana():
            if 'seleccionar_carrera' in self.ventanas_activas:
                del self.ventanas_activas['seleccionar_carrera']
            if cambios_estado_temp:
                for nombre_materia, nuevo_estado in cambios_estado_temp.items():
                    establecer_estado_materia(nombre_materia, nuevo_estado)
                # Actualizar barra de progreso
                self.actualizar_barra_progreso()
            top.destroy()
        
        top.protocol("WM_DELETE_WINDOW", al_cerrar_ventana)
        
        carrera_seleccionada = tk.StringVar(value=datos_alumno["carrera"])
        
        control_frame = tk.Frame(top)
        
        control_frame.pack(fill="x", padx=10, pady=5)
        
        btn_volver = tk.Button(control_frame, text="←", command=al_cerrar_ventana, 
                            bg="#0088ff", fg="white", padx=10, pady=5, font=("Arial", 12, "bold"))
        btn_volver.pack(side="left", padx=5)
        crear_tooltip(btn_volver, "Volver")
        
        tk.Label(control_frame, text="Ver otra carrera:").pack(side="left", padx=5)
        combo_carrera = ttk.Combobox(control_frame, textvariable=carrera_seleccionada, 
                                    values=list(planes_estudio.keys()), state="readonly", width=20)
        combo_carrera.pack(side="left", padx=5)
        
        tk.Label(control_frame, text="Buscar:").pack(side="left", padx=(20, 5))
        search_var = tk.StringVar()
        search_entry = tk.Entry(control_frame, textvariable=search_var, width=30)
        search_entry.pack(side="left", padx=5)
        
        mostrar_aprobadas_var = tk.BooleanVar(value=False)

        # Filtro de periodo
        tk.Label(control_frame, text="Periodo:").pack(side="left", padx=(20, 5))
        filtro_periodo_var = tk.StringVar(value="TODAS")
        combo_periodo = ttk.Combobox(control_frame, textvariable=filtro_periodo_var,
                                    values=["TODAS", "Solo 1er Sem", "Solo 2do Sem", "1er Sem Completo", "2do Sem Completo", "Solo Anual"],
                                    state="readonly", width=18, font=("Arial", 9))
        combo_periodo.pack(side="left", padx=5)

        btn_aprobadas = tk.Checkbutton(control_frame, text="Ver aprobadas", variable=mostrar_aprobadas_var)
        btn_aprobadas.pack(side="right", padx=5)
        
        def aplicar_cambios_vista():
            actualizar_vista()
        
        btn_actualizar = tk.Button(control_frame, text="🔄", 
                                command=aplicar_cambios_vista,
                                bg="#28a745", fg="white", padx=10, pady=5, font=("Arial", 13))
        btn_actualizar.pack(side="right", padx=5)
        crear_tooltip(btn_actualizar, "Actualizar Vista")
        
        main_frame = tk.Frame(top)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(main_frame)
        tema_oscuro = self.tema_actual == "darkly"
        bg_color_canvas = "#2b2b2b" if tema_oscuro else "white"
        canvas.configure(bg=bg_color_canvas)
        
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        tema_oscuro = self.tema_actual == "darkly"
        bg_color_scroll = "#2b2b2b" if tema_oscuro else "white"
        scrollable_frame.configure(bg=bg_color_scroll)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        habilitar_scroll_con_rueda(canvas, scrollable_frame)
        
        materias_expandidas = {}
        
        def obtener_estado_efectivo(nombre_materia):
            if nombre_materia in cambios_estado_temp:
                return cambios_estado_temp[nombre_materia]
            return obtener_estado_materia(nombre_materia)
        
        def actualizar_vista():
            filtro_texto = search_var.get()
            if len(filtro_texto) > 0 and len(filtro_texto) < 3:
                return
            if hasattr(actualizar_vista, 'pending_update'):
                scrollable_frame.after_cancel(actualizar_vista.pending_update)

            def _con_loader():
                ldr = mostrar_loader(top, "Actualizando...")
                top.update()
                _actualizar_vista_real()
                ldr.destroy()

            actualizar_vista.pending_update = scrollable_frame.after(300, _con_loader)

        def _actualizar_vista_real():
            # Cache del plan de estudios
            carrera = carrera_seleccionada.get()
            if not hasattr(_actualizar_vista_real, 'cache_plan') or \
            _actualizar_vista_real.cache_carrera != carrera:
                _actualizar_vista_real.cache_plan = planes_estudio.get(carrera, {})
                _actualizar_vista_real.cache_carrera = carrera

            plan = _actualizar_vista_real.cache_plan
            # Destruir widgets de forma más eficiente
            widgets_a_destruir = scrollable_frame.winfo_children()
            for widget in widgets_a_destruir:
                widget.destroy()
            del widgets_a_destruir
            
            materias_expandidas.clear()
            
            tema_oscuro = self.tema_actual == "darkly"
            bg_color_scroll = "#2b2b2b" if tema_oscuro else "white"
            text_color = "white" if tema_oscuro else "black"
            
            leyenda_frame = tk.Frame(scrollable_frame, relief="solid", borderwidth=2, bg=bg_color_scroll, padx=10, pady=10)
            leyenda_frame.pack(fill="x", padx=5, pady=10)
            
            tk.Label(leyenda_frame, text="LEYENDA DE ESTADOS:", font=("Arial", 10, "bold"), bg=bg_color_scroll, fg=text_color).pack(anchor="w", pady=(0, 5))
            
            estados_leyenda = [
                ("Aprobada", "aprobada"),
                ("Regular", "regular"),
                ("Libre", "libre"),
                ("Cursando", "cursando"),
                ("Podes Cursar", "cursable"),
                ("No Podes Cursar", "no_cursable")
            ]
            
            # UNA SOLA FILA para todas las referencias
            fila_unica = tk.Frame(leyenda_frame, bg=bg_color_scroll)
            fila_unica.pack(fill="x", pady=5)

            for idx, (texto, estado) in enumerate(estados_leyenda):
                color_bg, color_fg = obtener_colores_segun_tema(estado, tema_oscuro)
                item_frame = tk.Frame(fila_unica, bg=bg_color_scroll)
                item_frame.pack(side="left", padx=3)
                
                color_box = tk.Label(item_frame, text="  ", bg=color_bg, fg=color_fg, 
                                    width=2, relief="solid", borderwidth=1, highlightthickness=0)
                color_box.pack(side="left", padx=(0, 2))
                color_box.configure(bg=color_bg, fg=color_fg)
                
                tk.Label(item_frame, text=texto, bg=bg_color_scroll, fg=text_color, 
                        font=("Arial", 7)).pack(side="left")
            
            carrera = carrera_seleccionada.get()
            plan = planes_estudio.get(carrera, {})
            filtro = normalizar_texto(search_var.get())
            
            materias_por_año = {}
            for nombre, data in plan.items():
                año = data.get("Año", "E")
                if año not in materias_por_año:
                    materias_por_año[año] = []
                materias_por_año[año].append((nombre, data))
            
            años_ordenados = sorted([a for a in materias_por_año.keys() if a != "E"])
            if "E" in materias_por_año:
                años_ordenados.append("E")
            
            for año in años_ordenados:
                materias_filtradas = [(n, d) for n, d in materias_por_año[año] 
                                    if filtro in normalizar_texto(n)]
                
                if not materias_filtradas:
                    continue
                
                año_label = f"Año {año}" if año != "E" else "Electivas"

                # ──────────────────────────────────────────────────────────
                # WRAPPER FRAME: Agrupa header + materias para evitar reordenamiento
                # ──────────────────────────────────────────────────────────
                año_wrapper_frame = tk.Frame(scrollable_frame, bg=bg_color_scroll)
                año_wrapper_frame.pack(fill="x", pady=(10, 2), padx=5)

                # Frame para el header del año (clickeable)
                año_header_frame = tk.Frame(año_wrapper_frame, bg=bg_color_scroll, cursor="hand2")
                año_header_frame.pack(fill="x", pady=(0, 2))

                # Indicador de colapso
                indicador_año = tk.Label(año_header_frame, text="▼", font=("Arial", 10), 
                                        bg=bg_color_scroll, fg=text_color)
                indicador_año.pack(side="left", padx=5)

                # Label del año
                label_año = tk.Label(año_header_frame, text=f"━━━ {año_label} ━━━", 
                                    font=("Arial", 11, "bold"), fg="#1E3A8A", bg=bg_color_scroll)
                label_año.pack(side="left")

                # Frame contenedor para las materias del año
                año_materias_frame = tk.Frame(año_wrapper_frame, bg=bg_color_scroll)
                año_materias_frame.pack(fill="x")

                # Variable para controlar si está colapsado
                año_colapsado = [False]

                def toggle_año(e=None, frame=año_materias_frame, 
                            indicador=indicador_año, colapsado=año_colapsado):
                    if colapsado[0]:
                        # Expandir
                        frame.pack(fill="x")
                        indicador.config(text="▼")
                        colapsado[0] = False
                    else:
                        # Colapsar
                        frame.pack_forget()
                        indicador.config(text="▶")
                        colapsado[0] = True

                año_header_frame.bind("<Button-1>", toggle_año)
                indicador_año.bind("<Button-1>", toggle_año)
                label_año.bind("<Button-1>", toggle_año)
                
                # IMPORTANTE: Ahora las materias se crean DENTRO de año_materias_frame
                for nombre, data in materias_filtradas:
                    # CAMBIAR el parent a año_materias_frame
                    materia_frame = tk.Frame(año_materias_frame, relief="solid", borderwidth=1, bg=color_bg)
                    materia_frame.pack(fill="x", padx=5, pady=2)

                    materia_frame.configure(bg=color_bg)
                    materia_frame.update_idletasks()

                # Cambiar el parent a año_materias_frame en lugar de scrollable_frame
                    # Filtrar por periodo
                    periodo = obtener_periodo_cursado(data)
                    filtro_periodo = filtro_periodo_var.get()
                    
                    if filtro_periodo != "TODAS":
                        if filtro_periodo == "Solo 1er Sem" and periodo != "1er Sem":
                            continue
                        elif filtro_periodo == "Solo 2do Sem" and periodo != "2do Sem":
                            continue
                        elif filtro_periodo == "Solo Anual" and periodo != "Anual":
                            continue
                        elif filtro_periodo == "1er Sem Completo" and periodo not in ["1er Sem", "Anual"]:
                            continue
                        elif filtro_periodo == "2do Sem Completo" and periodo not in ["2do Sem", "Anual"]:
                            continue
                    
                    
                    estado_usuario = obtener_estado_efectivo(nombre)
                    
                    if estado_usuario == "aprobada" and not mostrar_aprobadas_var.get():
                        continue
                    
                    if estado_usuario in ["aprobada", "regular", "libre", "cursando"]:
                        estado = estado_usuario
                    else:
                        estado = verificar_correlativas(data, plan)
                    
                    color_bg, color_fg = obtener_colores_segun_tema(estado, tema_oscuro)

                    periodo = obtener_periodo_cursado(data)
                    periodo_texto = f" [{periodo}]" if periodo else ""

                    num_materia = data.get("NumeroMat", "")
                    num_texto = f"{num_materia}. " if num_materia else ""

                    header_frame = tk.Frame(materia_frame, bg=color_bg, cursor="hand2", 
                                    highlightthickness=0, borderwidth=0)
                    header_frame.pack(fill="x")
                    header_frame.configure(bg=color_bg)

                    indicador_label = tk.Label(header_frame, text="▶", bg=color_bg, fg=color_fg, 
                                        font=("Arial", 10), highlightthickness=0, borderwidth=0)
                    indicador_label.pack(side="left", padx=5)
                    indicador_label.configure(bg=color_bg, fg=color_fg)

                    texto_completo = f"{num_texto}{nombre}{periodo_texto}"
                    max_chars = 50
                    texto_display = texto_completo if len(texto_completo) <= max_chars else texto_completo[:max_chars-3] + "..."

                    nombre_label = tk.Label(header_frame, text=texto_display, 
                                    bg=color_bg, fg=color_fg, font=("Arial", 10, "bold"),
                                    highlightthickness=0, borderwidth=0)
                    nombre_label.pack(side="left", padx=5, fill="x", expand=False)
                    nombre_label.configure(bg=color_bg, fg=color_fg)

                    btn_corr = tk.Label(header_frame, text="🔍", bg=color_bg, fg=color_fg, 
                                    font=("Arial", 12), cursor="hand2",
                                    highlightthickness=0, borderwidth=0)
                    btn_corr.pack(side="left", padx=2)
                    btn_corr.configure(bg=color_bg, fg=color_fg)
                    
                    crear_tooltip_correlativas(btn_corr, nombre, top)

                    if len(texto_completo) > max_chars:
                        def crear_tooltip_nombre(widget, texto):
                            def mostrar(event):
                                tooltip = tk.Toplevel()
                                tooltip.wm_overrideredirect(True)
                                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                                label = tk.Label(tooltip, text=texto, background="yellow", 
                                            relief="solid", borderwidth=1, font=("Arial", 9))
                                label.pack()
                                widget.tooltip = tooltip
                            def ocultar(event):
                                if hasattr(widget, 'tooltip'):
                                    widget.tooltip.destroy()
                                    del widget.tooltip
                            widget.bind("<Enter>", mostrar)
                            widget.bind("<Leave>", ocultar)
                        crear_tooltip_nombre(nombre_label, texto_completo)
                    
                    controles_frame = tk.Frame(header_frame, bg=color_bg, highlightthickness=0, borderwidth=0)
                    controles_frame.pack(side="right", padx=5)

                    estado_var = tk.StringVar(value=estado_usuario)

                    def cambiar_estado(n=nombre, v=estado_var):
                        nuevo_estado = v.get()
                        cambios_estado_temp[n] = nuevo_estado

                    # ⭐ INICIALIZAR rb_frame como None SIEMPRE
                    rb_frame = None

                    # Solo crear radiobuttons si NO está aprobada
                    if estado_usuario != "aprobada":
                        rb_frame = tk.Frame(controles_frame, bg=color_bg, highlightthickness=0, borderwidth=0)

                        estados = [
                            ("Aprobada", "aprobada"), 
                            ("Regular", "regular"), 
                            ("Libre", "libre"), 
                            ("Cursando", "cursando"),
                            ("Por Cursar", "por_cursar")
                        ]

                        for texto_rb, valor in estados:
                            rb = tk.Radiobutton(rb_frame, text=texto_rb, variable=estado_var, value=valor,
                                            command=cambiar_estado, bg=color_bg, fg=color_fg,
                                            selectcolor=color_bg, activebackground=color_bg, 
                                            activeforeground=color_fg, highlightthickness=0,
                                            borderwidth=0, relief="flat", font=("Arial", 8))
                            rb.pack(side="left", padx=2)

                    btn_container = tk.Frame(controles_frame, bg=color_bg, highlightthickness=0, borderwidth=0)
                    btn_container.pack(side="left", padx=5)

                    # Condición para mostrar radiobuttons (solo si existen)
                    if estado_usuario != "aprobada":
                        clave_materia = f"{nombre}[{carrera}]"
                        materia_seleccionada = clave_materia in materias
                        
                        if not materia_seleccionada:
                            rb_frame.pack(side="left")
                        else:
                            rb_frame.pack_forget()
                    
                    def seleccionar_materia(n=nombre, d=data, carr=carrera):
                        clave_materia = f"{n}[{carr}]"
                        
                        if clave_materia not in materias:
                            materias[clave_materia] = {}
                        
                        for key, value in d.items():
                            if key in ["NumeroMat", "Año", "Regulares", "Arpobadas", "Hs"]:
                                continue
                            horarios = []
                            for item in value:
                                if isinstance(item, list) and len(item) == 3 and isinstance(item[1], (int, float)):
                                    horarios.append((item[0], item[1], item[2]))
                            if horarios:
                                materias[clave_materia][key] = horarios
                        
                        guardar_materias_seleccionadas()
                        actualizar_vista()
                    
                    def deseleccionar_materia(n=nombre, carr=carrera):
                        clave_materia = f"{n}[{carr}]"
                        if clave_materia in materias:
                            del materias[clave_materia]
                        guardar_materias_seleccionadas()
                        actualizar_vista()
                    
                    if estado_usuario != "aprobada":
                        if not materia_seleccionada:
                            btn_seleccionar = tk.Button(btn_container, text="Seleccionar", 
                                                    command=seleccionar_materia, bg="#04D40B", fg="white", 
                                                    padx=10, pady=3, highlightthickness=0, borderwidth=1,
                                                    activebackground="#03A009", activeforeground="white")
                            btn_seleccionar.pack()
                            
                            # Tooltip para materias no cursables
                            if estado == "no_cursable":
                                def crear_tooltip_no_cursable(widget):
                                    tooltip = None
                                    def mostrar(event):
                                        nonlocal tooltip
                                        if tooltip is not None:
                                            return
                                        tooltip = tk.Toplevel()
                                        tooltip.wm_overrideredirect(True)
                                        tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root-30}")
                                        tooltip.attributes('-topmost', True)
                                        label = tk.Label(tooltip, text="No cumple por el momento con las correlatividades", 
                                                    bg="#FFE4E1", fg="#8B0000", relief="solid", borderwidth=1, 
                                                    font=("Arial", 9), padx=8, pady=4)
                                        label.pack()
                                        widget.tooltip_win = tooltip
                                    
                                    def ocultar(event):
                                        nonlocal tooltip
                                        if tooltip is not None:
                                            tooltip.destroy()
                                            tooltip = None
                                    
                                    widget.bind("<Enter>", mostrar)
                                    widget.bind("<Leave>", ocultar)
                                
                                crear_tooltip_no_cursable(btn_seleccionar)
                        else:
                            check_label = tk.Label(btn_container, text="✓Seleccionada",
                                                bg=color_bg, fg="#00AA00",
                                                font=("Arial", 9),
                                                highlightthickness=3,
                                                highlightbackground="#00AA00",
                                                borderwidth=5, padx=2, pady=1, cursor="arrow")
                            check_label.pack(side="left", padx=2)
                            cross_label = tk.Label(btn_container, text="✗Eliminar",
                                                bg=color_bg, fg="#CC0000",
                                                font=("Arial", 9),
                                                highlightthickness=3,
                                                highlightbackground="#CC0000",
                                                borderwidth=5, padx=2, pady=1,
                                                cursor="hand2")
                            cross_label.pack(side="left", padx=2)
                            cross_label.bind("<Button-1>", lambda e, n=nombre, c=carrera: deseleccionar_materia(n, c))
                    else:
                        tk.Label(btn_container, text="Aprobada", bg=color_bg, fg=color_fg, 
                                font=("Arial", 9, "italic"), highlightthickness=0, borderwidth=0).pack(padx=5)
                    
                    comisiones_frame = tk.Frame(materia_frame, bg="white")
                    materias_expandidas[nombre] = {"frame": comisiones_frame, "expandida": False, "indicador": indicador_label}
                    
                    for key, value in data.items():
                        if key in ["NumeroMat", "Año", "Regulares", "Arpobadas", "Hs"]:
                            continue
                        comision = key
                        horarios_texto = []
                        for item in value:
                            if isinstance(item, list) and len(item) == 3 and isinstance(item[1], (int, float)):
                                dia, inicio, fin = item[0], item[1], item[2]
                                hora_ini = f"{int(inicio):02d}:{int((inicio % 1) * 60):02d}"
                                hora_fin = f"{int(fin):02d}:{int((fin % 1) * 60):02d}"
                                horarios_texto.append(f"{dia} {hora_ini}-{hora_fin}")
                        if horarios_texto:
                            horarios_str = " | ".join(horarios_texto)
                            comision_label = tk.Label(comisiones_frame, 
                                                    text=f"  • {comision}: {horarios_str}",
                                                    bg="white", anchor="w", justify="left", font=("Arial", 9))
                            comision_label.pack(fill="x", padx=5, pady=1)
                    
                    def toggle_comisiones(e=None, n=nombre):
                        info = materias_expandidas[n]
                        if info["expandida"]:
                            info["frame"].pack_forget()
                            info["indicador"].config(text="▶")
                            info["expandida"] = False
                        else:
                            info["frame"].pack(fill="x", padx=20, pady=5)
                            info["indicador"].config(text="▼")
                            info["expandida"] = True
                    
                    header_frame.bind("<Button-1>", toggle_comisiones)
                    indicador_label.bind("<Button-1>", toggle_comisiones)
                    nombre_label.bind("<Button-1>", toggle_comisiones)
        
        search_var.trace("w", lambda *args: actualizar_vista())
        mostrar_aprobadas_var.trace("w", lambda *args: actualizar_vista())
        carrera_seleccionada.trace("w", lambda *args: actualizar_vista())
        
        filtro_periodo_var.trace("w", lambda *args: actualizar_vista())

        # NUEVO: Llamar actualizar_vista en el próximo ciclo del event loop
        # para que el loader se muestre primero
        top.after(100, actualizar_vista)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def menu_seleccionar_por_materia(self):
        """Menú de selección de materias organizado alfabéticamente"""
        
        # Verificar si ya existe la ventana
        if 'seleccionar_materia' in self.ventanas_activas:
            try:
                ventana_existente = self.ventanas_activas['seleccionar_materia']
                if ventana_existente.winfo_exists():
                    ventana_existente.lift()
                    ventana_existente.focus_force()
                    return
            except:
                pass
        
        top = tk.Toplevel(self.root)
        self.ventanas_activas['seleccionar_materia'] = top
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        ancho = int(screen_width * 0.65)
        alto = int(screen_height * 0.65)
        configurar_ventana(top, "Seleccionar por Materia", ancho, alto, centrar=False, icono=self.icono_ventana)
        top.update_idletasks()
        pos_x = (screen_width - ancho) // 2
        pos_y = (screen_height - alto) // 2
        top.geometry(f"{ancho}x{alto}+{pos_x}+{pos_y}")
        
        top.minsize(1024,600)
        top.bind("<Escape>", cerrar_con_esc)
        traer_ventana_al_frente(top)
        centrar_ventana_exacto(top)
        
        cambios_estado_temp = {}
        
        # Definir función de cierre PRIMERO
        def al_cerrar_ventana():
            if cambios_estado_temp:
                for nombre_materia, nuevo_estado in cambios_estado_temp.items():
                    establecer_estado_materia(nombre_materia, nuevo_estado)
                # Actualizar barra de progreso
                self.actualizar_barra_progreso()
            top.destroy()
        
        top.protocol("WM_DELETE_WINDOW", al_cerrar_ventana)
        
        control_frame = tk.Frame(top)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        btn_volver = tk.Button(control_frame, text="←", command=al_cerrar_ventana,
                            bg="#0088ff", fg="white", padx=10, pady=5, font=("Arial", 12, "bold"))
        btn_volver.pack(side="left", padx=5)
        crear_tooltip(btn_volver, "Volver")
        
        tk.Label(control_frame, text="Buscar:").pack(side="left", padx=5)
        search_var = tk.StringVar()
        search_entry = tk.Entry(control_frame, textvariable=search_var, width=40)
        search_entry.pack(side="left", padx=5)
        
        mostrar_aprobadas_var = tk.BooleanVar(value=False)
        btn_aprobadas = tk.Checkbutton(control_frame, text="Ver aprobadas", variable=mostrar_aprobadas_var)
        btn_aprobadas.pack(side="right", padx=5)
        
        # Filtro de periodo
        tk.Label(control_frame, text="Periodo:").pack(side="right", padx=(20, 5))
        filtro_periodo_var = tk.StringVar(value="TODAS")
        combo_periodo = ttk.Combobox(control_frame, textvariable=filtro_periodo_var,
                                    values=["TODAS", "Solo 1er Sem", "Solo 2do Sem", "1er Sem Completo", "2do Sem Completo", "Solo Anual"],
                                    state="readonly", width=18, font=("Arial", 9))
        combo_periodo.pack(side="left", padx=5)

        def aplicar_cambios_vista():
            actualizar_vista()
        
        btn_actualizar = tk.Button(control_frame, text="🔄", 
                                command=aplicar_cambios_vista,
                                bg="#28a745", fg="white", padx=10, pady=5, font=("Arial", 13))
        btn_actualizar.pack(side="right", padx=5)
        crear_tooltip(btn_actualizar, "Actualizar Vista")
        
        main_frame = tk.Frame(top)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        tema_oscuro = self.tema_actual == "darkly"
        bg_scroll = "#2b2b2b" if tema_oscuro else "#f0f0f0"

        canvas = tk.Canvas(main_frame, bg=bg_scroll, highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=bg_scroll)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        habilitar_scroll_con_rueda(canvas, scrollable_frame)
        
        todas_materias = {}
        for carrera, plan in planes_estudio.items():
            for nombre, data in plan.items():
                if nombre not in todas_materias:
                    todas_materias[nombre] = {"carreras": {}}
                
                comisiones_carrera = {}
                for key, value in data.items():
                    if key not in ["NumeroMat", "Año", "Regulares", "Arpobadas", "Hs"]:
                        horarios = []
                        for item in value:
                            if isinstance(item, list) and len(item) == 3 and isinstance(item[1], (int, float)):
                                horarios.append((item[0], item[1], item[2]))
                        if horarios:
                            comisiones_carrera[key] = horarios
                
                if comisiones_carrera:
                    todas_materias[nombre]["carreras"][carrera] = {
                        "comisiones": comisiones_carrera,
                        "data": data
                    }
        
        materias_ordenadas = sorted(todas_materias.items())
        
        materias_regulares = []
        materias_electivas = []
        
        for nombre, info in materias_ordenadas:
            if not info["carreras"]:
                continue
            es_electiva = False
            for carrera_info in info["carreras"].values():
                data = carrera_info["data"]
                if data.get("NumeroMat") == 0 or data.get("Año") == "E":
                    es_electiva = True
                    break
            if es_electiva:
                materias_electivas.append((nombre, info))
            else:
                materias_regulares.append((nombre, info))
        
        materias_expandidas = {}
        
        def obtener_estado_efectivo(nombre_materia):
            if nombre_materia in cambios_estado_temp:
                return cambios_estado_temp[nombre_materia]
            return obtener_estado_materia(nombre_materia)
        
        def crear_frame_materia(parent, nombre, info, estado):
            primera_carrera = list(info["carreras"].keys())[0]
            data = info["carreras"][primera_carrera]["data"]
            
            tema_oscuro = self.tema_actual == "darkly"
            color_bg, color_fg = obtener_colores_segun_tema(estado, tema_oscuro)
            
            estado_usuario = obtener_estado_efectivo(nombre)

            # Verificar si la materia está seleccionada (buscar en cualquier carrera)
            materia_seleccionada = nombre in materias

            periodo = obtener_periodo_cursado(data)
            periodo_texto = f" [{periodo}]" if periodo else ""
            
            materia_frame = tk.Frame(parent, relief="solid", borderwidth=1, bg=color_bg)
            materia_frame.pack(fill="x", padx=5, pady=2)
                                
            header_frame = tk.Frame(materia_frame, bg=color_bg, cursor="hand2",
                                highlightthickness=0, borderwidth=0)
            header_frame.pack(fill="x")
            header_frame.configure(bg=color_bg)
            header_frame.update_idletasks()
            
            indicador_label = tk.Label(header_frame, text="▶", bg=color_bg, fg=color_fg, font=("Arial", 10),
                                    highlightthickness=0, borderwidth=0)
            indicador_label.pack(side="left", padx=5)
            indicador_label.configure(bg=color_bg, fg=color_fg)
            
            nombre_label = tk.Label(header_frame, text=f"{nombre}", 
                                bg=color_bg, fg=color_fg, font=("Arial", 10, "bold"),
                                highlightthickness=0, borderwidth=0)
            nombre_label.pack(side="left", padx=5)
            nombre_label.configure(bg=color_bg, fg=color_fg)
            
            btn_corr = tk.Label(header_frame, text="🔍", bg=color_bg, fg=color_fg, 
                            font=("Arial", 12), cursor="hand2",
                            highlightthickness=0, borderwidth=0)
            btn_corr.pack(side="left", padx=2)
            btn_corr.configure(bg=color_bg, fg=color_fg)
            
            crear_tooltip_correlativas(btn_corr, nombre, top)
            
            controles_frame = tk.Frame(header_frame, bg=color_bg, highlightthickness=0, borderwidth=0)
            controles_frame.pack(side="right", padx=5)
            
            estado_var = tk.StringVar(value=obtener_estado_efectivo(nombre))
            
            def cambiar_estado(n=nombre, v=estado_var):
                nuevo_estado = v.get()
                cambios_estado_temp[n] = nuevo_estado
            
            # Solo crear radiobuttons si NO está aprobada
            if estado_usuario != "aprobada":
                rb_frame = tk.Frame(controles_frame, bg=color_bg, highlightthickness=0, borderwidth=0)

                estados = [
                    ("Aprobada", "aprobada"), 
                    ("Regular", "regular"), 
                    ("Libre", "libre"), 
                    ("Cursando", "cursando"),
                    ("Por Cursar", "por_cursar")
                ]

                for texto_rb, valor in estados:
                    rb = tk.Radiobutton(rb_frame, text=texto_rb, variable=estado_var, value=valor,
                                    command=cambiar_estado, bg=color_bg, fg=color_fg,
                                    selectcolor=color_bg, activebackground=color_bg, 
                                    activeforeground=color_fg, highlightthickness=0,
                                    borderwidth=0, relief="flat", font=("Arial", 8))
                    rb.pack(side="left", padx=2)

            # ... código de botones (SIN cambios) ...

            btn_container = tk.Frame(controles_frame, bg=color_bg, highlightthickness=0, borderwidth=0)
            btn_container.pack(side="left", padx=5)

            # Mostrar/ocultar radiobuttons según estado de selección
            if estado_usuario != "aprobada":
                if rb_frame is not None: 
                    if not materia_seleccionada:
                        rb_frame.pack(side="left")
                    else:
                        rb_frame.pack_forget()
            
            # Contar número total de comisiones de todas las carreras
            num_comisiones_total = 0
            for carrera, carrera_info in info["carreras"].items():
                num_comisiones_total += len(carrera_info["comisiones"])
            
            def seleccionar_materia_completa(n=nombre, inf=info):
                if n not in materias:
                    materias[n] = {}
                for carrera, carrera_info in inf["carreras"].items():
                    for comision, horarios in carrera_info["comisiones"].items():
                        # Crear clave única: "Carrera - Comisión"
                        comision_key = f"{carrera} - {comision}"
                        materias[n][comision_key] = horarios
                guardar_materias_seleccionadas()
                actualizar_vista()
            
            def deseleccionar_materia_completa(n=nombre):
                if n in materias:
                    del materias[n]
                guardar_materias_seleccionadas()
                actualizar_vista()
            
            # Usar la variable ya definida:
            if estado_usuario != "aprobada":
                if not materia_seleccionada:
                    # Texto del botón según número de comisiones
                    texto_btn = "Seleccionar Todo" if num_comisiones_total > 1 else "Seleccionar"
                    
                    btn_seleccionar = tk.Button(btn_container, text=texto_btn, 
                                            command=seleccionar_materia_completa, bg="#04D40B", fg="white", 
                                            padx=10, pady=3, highlightthickness=0, borderwidth=1,
                                            activebackground="#03A009", activeforeground="white")
                    btn_seleccionar.pack()
                    
                    # Tooltip para materias no cursables
                    if estado == "no_cursable":
                        def crear_tooltip_no_cursable(widget):
                            tooltip = None
                            def mostrar(event):
                                nonlocal tooltip
                                if tooltip is not None:
                                    return
                                tooltip = tk.Toplevel()
                                tooltip.wm_overrideredirect(True)
                                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root-30}")
                                tooltip.attributes('-topmost', True)
                                label = tk.Label(tooltip, text="No cumple por el momento con las correlatividades", 
                                            bg="#FFE4E1", fg="#8B0000", relief="solid", borderwidth=1, 
                                            font=("Arial", 9), padx=8, pady=4)
                                label.pack()
                                widget.tooltip_win = tooltip
                            
                            def ocultar(event):
                                nonlocal tooltip
                                if tooltip is not None:
                                    tooltip.destroy()
                                    tooltip = None
                            
                            widget.bind("<Enter>", mostrar)
                            widget.bind("<Leave>", ocultar)
                        
                        crear_tooltip_no_cursable(btn_seleccionar)

                else:
                    check_label = tk.Label(btn_container, text="✓Seleccionada",
                                        bg=color_bg, fg="#00AA00",
                                        font=("Arial", 9),
                                        highlightthickness=1,
                                        highlightbackground="#00AA00",
                                        borderwidth=0, padx=2, pady=1, cursor="arrow")
                    check_label.pack(side="left", padx=2)
                    cross_label = tk.Label(btn_container, text="✗Eliminar",
                                        bg=color_bg, fg="#CC0000",
                                        font=("Arial", 9),
                                        highlightthickness=1,
                                        highlightbackground="#CC0000",
                                        borderwidth=0, padx=2, pady=1,
                                        cursor="hand2")
                    cross_label.pack(side="left", padx=2)
                    cross_label.bind("<Button-1>", lambda e: deseleccionar_materia_completa())

            else:
                tk.Label(btn_container, text="Aprobada", bg=color_bg, fg=color_fg, 
                        font=("Arial", 9, "italic"), highlightthickness=0, borderwidth=0).pack(padx=5)
            
            # ═══════════════════════════════════════════════════════════════════
            # COMISIONES FRAME - CON BOTONES DE SELECCIÓN INDIVIDUAL
            # ═══════════════════════════════════════════════════════════════════
            comisiones_frame = tk.Frame(materia_frame, bg="white")
            materias_expandidas[nombre] = {"frame": comisiones_frame, "expandida": False, "indicador": indicador_label, "info": info}
            
            def toggle_comisiones(e=None, n=nombre):
                exp_info = materias_expandidas[n]
                if exp_info["expandida"]:
                    exp_info["frame"].pack_forget()
                    exp_info["indicador"].config(text="▶")
                    exp_info["expandida"] = False
                else:
                    # Limpiar y recrear contenido
                    for widget in exp_info["frame"].winfo_children():
                        widget.destroy()
                    
                    # Si hay más de 1 comisión en total, mostrar botones individuales
                    if num_comisiones_total > 1:
                        for carrera, carrera_info in exp_info["info"]["carreras"].items():
                            # Header de carrera
                            tk.Label(exp_info["frame"], text=f"--- {carrera} ---", bg="white", 
                                font=("Arial", 9, "bold")).pack(anchor="w", padx=5, pady=(5, 2))
                            
                            for comision, horarios in carrera_info["comisiones"].items():
                                horarios_texto = []
                                for dia, inicio, fin in horarios:
                                    hora_ini = f"{int(inicio):02d}:{int((inicio % 1) * 60):02d}"
                                    hora_fin = f"{int(fin):02d}:{int((fin % 1) * 60):02d}"
                                    horarios_texto.append(f"{dia} {hora_ini}-{hora_fin}")
                                horarios_str = " | ".join(horarios_texto)
                                
                                # Obtener periodo de cursado
                                periodo = obtener_periodo_cursado(carrera_info["data"])
                                periodo_str = f" [{periodo}]" if periodo else ""
                                
                                comision_row = tk.Frame(exp_info["frame"], bg="white")
                                comision_row.pack(fill="x", padx=5, pady=2)
                                
                                comision_label = tk.Label(comision_row, 
                                                        text=f"  • {comision}{periodo_str}: {horarios_str}",
                                                        bg="white", anchor="w", justify="left", font=("Arial", 9))
                                comision_label.pack(side="left", fill="x", expand=True)
                                
                                # Verificar si esta comisión específica está seleccionada
                                comision_key = f"{carrera} - {comision}"
                                comision_seleccionada = (n in materias and comision_key in materias.get(n, {}))
                                
                                btn_comision_container = tk.Frame(comision_row, bg="white")
                                btn_comision_container.pack(side="right", padx=5)
                                
                                def seleccionar_comision_individual(nom=n, carr=carrera, com=comision, hrs=horarios):
                                    if nom not in materias:
                                        materias[nom] = {}
                                    com_key = f"{carr} - {com}"
                                    materias[nom][com_key] = hrs
                                    guardar_materias_seleccionadas()
                                    actualizar_vista()

                                def deseleccionar_comision_individual(nom=n, carr=carrera, com=comision):
                                    com_key = f"{carr} - {com}"
                                    if nom in materias and com_key in materias[nom]:
                                        del materias[nom][com_key]
                                        if not materias[nom]:
                                            del materias[nom]
                                    guardar_materias_seleccionadas()
                                    actualizar_vista()

                                # Solo mostrar botones si NO está aprobada
                                if estado_usuario != "aprobada":
                                    if not comision_seleccionada:
                                        btn_sel_com = tk.Button(btn_comision_container, text="Seleccionar",
                                                            command=seleccionar_comision_individual,
                                                            bg="#04D40B", fg="white", font=("Arial", 8),
                                                            padx=8, pady=2)
                                        btn_sel_com.pack()
                                    else:
                                        # Check y cruz para comisión individual
                                        check_f = tk.Frame(btn_comision_container, bg="#00CC00", relief="raised", borderwidth=1)
                                        check_f.pack(side="left", padx=1)
                                        tk.Label(check_f, text="✓Seleccionada", bg="#00CC00", fg="white", 
                                                font=("Arial", 10, "bold"), padx=2).pack()

                                        cross_f = tk.Frame(btn_comision_container, bg="#DC143C", relief="raised",
                                                        borderwidth=1, cursor="hand2")
                                        cross_f.pack(side="left", padx=1, cursor="arrow")
                                        cross_l = tk.Label(cross_f, text="✗Eliminar", bg="#DC143C", fg="white",
                                        font=("Arial", 10, "bold"), padx=2)
                                        cross_l.pack()
                                        
                                        cross_f.bind("<Button-1>", lambda e: deseleccionar_comision_individual())
                                        cross_l.bind("<Button-1>", lambda e: deseleccionar_comision_individual())
                    else:
                        # Solo 1 comisión total, mostrar info simple sin botones adicionales
                        for carrera, carrera_info in exp_info["info"]["carreras"].items():
                            tk.Label(exp_info["frame"], text=f"--- {carrera} ---", bg="white", 
                                font=("Arial", 9, "bold")).pack(anchor="w", padx=5, pady=(5, 2))
                            for comision, horarios in carrera_info["comisiones"].items():
                                horarios_texto = []
                                for dia, inicio, fin in horarios:
                                    hora_ini = f"{int(inicio):02d}:{int((inicio % 1) * 60):02d}"
                                    hora_fin = f"{int(fin):02d}:{int((fin % 1) * 60):02d}"
                                    horarios_texto.append(f"{dia} {hora_ini}-{hora_fin}")
                                horarios_str = " | ".join(horarios_texto)
                                
                                # Obtener periodo de cursado
                                periodo = obtener_periodo_cursado(carrera_info["data"])
                                periodo_str = f" [{periodo}]" if periodo else ""
                                
                                comision_label = tk.Label(exp_info["frame"], 
                                                        text=f"  • {comision}{periodo_str}: {horarios_str}",
                                                        bg="white", anchor="w", justify="left", font=("Arial", 9))
                                comision_label.pack(fill="x", padx=15, pady=1)
                    
                    exp_info["frame"].pack(fill="x", padx=20, pady=5)
                    exp_info["indicador"].config(text="▼")
                    exp_info["expandida"] = True
            
            header_frame.bind("<Button-1>", toggle_comisiones)
            indicador_label.bind("<Button-1>", toggle_comisiones)
            nombre_label.bind("<Button-1>", toggle_comisiones)
        
        def actualizar_vista():
            filtro_texto = search_var.get()
            if len(filtro_texto) > 0 and len(filtro_texto) < 3:
                return

            ldr = mostrar_loader(top, "Actualizando...")
            top.update()

            for widget in scrollable_frame.winfo_children():
                widget.destroy()
            
            materias_expandidas.clear()

            tema_oscuro = self.tema_actual == "darkly"
            bg_color_scroll = "#2b2b2b" if tema_oscuro else "#f0f0f0"
            text_color = "white" if tema_oscuro else "black"

            leyenda_frame = tk.Frame(scrollable_frame, relief="solid", borderwidth=2, bg=bg_color_scroll, padx=10, pady=10)
            leyenda_frame.pack(fill="x", padx=5, pady=10)

            tk.Label(leyenda_frame, text="LEYENDA DE ESTADOS:", font=("Arial", 10, "bold"), bg=bg_color_scroll, fg=text_color).pack(anchor="w", pady=(0, 5))

            estados_leyenda = [
                ("Aprobada", "aprobada"),
                ("Regular", "regular"),
                ("Libre", "libre"),
                ("Cursando", "cursando"),
                ("Podes Cursar", "cursable"),
                ("No Podes Cursar", "no_cursable")
            ]

            # UNA SOLA FILA para todas las referencias
            fila_unica = tk.Frame(leyenda_frame, bg=bg_color_scroll)
            fila_unica.pack(fill="x", pady=5)

            for idx, (texto, estado) in enumerate(estados_leyenda):
                color_bg, color_fg = obtener_colores_segun_tema(estado, tema_oscuro)
                item_frame = tk.Frame(fila_unica, bg=bg_color_scroll)
                item_frame.pack(side="left", padx=3)
                
                color_box = tk.Label(item_frame, text="  ", bg=color_bg, fg=color_fg, 
                                    width=2, relief="solid", borderwidth=1, highlightthickness=0)
                color_box.pack(side="left", padx=(0, 2))
                color_box.configure(bg=color_bg, fg=color_fg)
                
                tk.Label(item_frame, text=texto, bg=bg_color_scroll, fg=text_color, 
                        font=("Arial", 7)).pack(side="left")
                
            filtro = normalizar_texto(search_var.get())
            filtro_periodo = filtro_periodo_var.get()

            def periodo_match(periodo_val):
                """Retorna True si el periodo de una comisión cumple el filtro."""
                if filtro_periodo == "TODAS": return True
                if filtro_periodo == "Solo 1er Sem": return periodo_val == "1er Sem"
                if filtro_periodo == "Solo 2do Sem": return periodo_val == "2do Sem"
                if filtro_periodo == "Solo Anual": return periodo_val == "Anual"
                if filtro_periodo == "1er Sem Completo": return periodo_val in ["1er Sem", "Anual"]
                if filtro_periodo == "2do Sem Completo": return periodo_val in ["2do Sem", "Anual"]
                return True

            for nombre, info in materias_regulares:
                if filtro and filtro not in normalizar_texto(nombre): continue

                # Filtrar carreras/comisiones por periodo
                if filtro_periodo != "TODAS":
                    info_filtrada = {"carreras": {}}
                    for carrera, carrera_info in info["carreras"].items():
                        periodo_carrera = obtener_periodo_cursado(carrera_info["data"])
                        if periodo_match(periodo_carrera):
                            info_filtrada["carreras"][carrera] = carrera_info
                    if not info_filtrada["carreras"]:
                        continue  # No hay comisiones que cumplan el filtro → ocultar materia
                    info_usar = info_filtrada
                else:
                    info_usar = info

                estado_usuario = obtener_estado_efectivo(nombre)
                if estado_usuario == "aprobada" and not mostrar_aprobadas_var.get(): continue
                primera_carrera = list(info_usar["carreras"].keys())[0]
                data = info_usar["carreras"][primera_carrera]["data"]
                if estado_usuario in ["aprobada", "regular", "libre", "cursando"]:
                    estado = estado_usuario
                else:
                    estado = verificar_correlativas(data, planes_estudio[primera_carrera])
                crear_frame_materia(scrollable_frame, nombre, info_usar, estado)
            
            ldr.destroy()

            # Mensaje para electivas
            if materias_electivas:
                mensaje_frame = tk.Frame(scrollable_frame, relief="solid", borderwidth=2, bg="#FFF8DC", padx=20, pady=15)
                mensaje_frame.pack(fill="x", padx=5, pady=(20, 5))
                
                tk.Label(mensaje_frame, text="ℹ️ MATERIAS ELECTIVAS", 
                        font=("Arial", 12, "bold"), bg="#FFF8DC", fg="#B8860B").pack(pady=(0, 5))
                
                tk.Label(mensaje_frame, 
                        text="Para ver y seleccionar materias electivas,\nvaya a 'Seleccionar por Carrera'", 
                        font=("Arial", 10), bg="#FFF8DC", fg="#333", justify="center").pack()
    
        filtro_periodo_var.trace("w", lambda *args: actualizar_vista())
        search_var.trace("w", lambda *args: actualizar_vista())
        mostrar_aprobadas_var.trace("w", lambda *args: actualizar_vista())
        
        top.after(100, actualizar_vista)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def menu_graficar(self):
        """Menú de visualización del gráfico de horarios"""
        
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        
        global comisiones_visibles, usar_mismo_color_por_materia, orientacion_grafico 
        
        orientacion_var = tk.StringVar(value=orientacion_grafico)
        
        regenerar_colores_materias()
        
        top = tk.Toplevel(self.root)

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        ancho = int(screen_width * 0.75)
        alto = int(screen_height * 0.75)
        configurar_ventana(top, "Gráfico de Horarios", ancho, alto, centrar=False, icono=self.icono_ventana)
        top.update_idletasks()
        pos_x = (screen_width - ancho) // 2
        pos_y = (screen_height - alto) // 2
        top.geometry(f"{ancho}x{alto}+{pos_x}+{pos_y}")
        
        top.minsize(1280,720)
        traer_ventana_al_frente(top)
        top.after(300, lambda: centrar_ventana_exacto(top))
        
        def al_cerrar():
            guardar_materias_seleccionadas()
            top.destroy()
        
        top.protocol("WM_DELETE_WINDOW", al_cerrar)
        top.bind("<Escape>", lambda e: al_cerrar())
        
        horarios = [
            inicio
            for comisiones in materias.values()
            for horarios in comisiones.values()
            for _, inicio, _ in horarios
        ]
        
        horarios_extra = datos_alumno.get("horarios_extra", {})
        for nombre, hrs in horarios_extra.items():
            for _, inicio, _ in hrs:
                horarios.append(inicio)
        
        earliest_start = min(horarios) if horarios else 8
        
        global color_fondo_grafico

        if color_fondo_grafico is None:
            if self.tema_actual == "darkly":
                bg_color = '#1e1e1e'
                text_color = 'white'
                grid_color = '#555555'
            else:
                bg_color = 'white'
                text_color = 'black'
                grid_color = '#cccccc'
        else:
            bg_color = color_fondo_grafico
            import colorsys
            rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16)/255.0 for i in (0, 2, 4))
            luminance = 0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2]
            text_color = 'white' if luminance < 0.5 else 'black'
            grid_color = '#555555' if luminance < 0.5 else '#cccccc'
        
        # Determinar orientación
        es_vertical = orientacion_var.get() == "vertical"

        if es_vertical:
            fig, ax = plt.subplots(figsize=(6, 10), facecolor=bg_color)
        else:
            fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg_color)

        ax.set_facecolor(bg_color)

        if es_vertical:
            # Vertical: días en X, horas en Y
            ax.set_ylim(earliest_start, 24)
            ax.set_yticks(np.arange(earliest_start, 24, 0.25))
            ax.set_yticklabels([f"{int(h)}:{int((h % 1) * 60):02d}" for h in np.arange(earliest_start, 24, 0.25)])
            ax.set_xlim(-0.5, 6.5)
            ax.set_xticks(range(7))
            ax.set_xticklabels(["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"], rotation=45)
            ax.set_ylabel("Hora", color=text_color)
            ax.set_xlabel("Día", color=text_color)
            ax.set_title("Horarios de Clases (Vista Vertical)", color=text_color)
        else:
            # Horizontal: horas en X, días en Y
            ax.set_xlim(earliest_start, 24)
            ax.set_xticks(np.arange(earliest_start, 24, 0.25))
            ax.set_xticklabels([f"{int(h)}:{int((h % 1) * 60):02d}" for h in np.arange(earliest_start, 24, 0.25)], rotation=80)
            ax.set_ylim(-0.5, 6.5)
            ax.set_yticks(range(7))
            ax.set_yticklabels(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
            ax.set_xlabel("Hora", color=text_color)
            ax.set_ylabel("Día", color=text_color)
            ax.set_title("Horarios de Clases", color=text_color)
        ax.tick_params(axis='x', colors=text_color)
        ax.tick_params(axis='y', colors=text_color)
        
        if es_vertical:
            for y in np.arange(earliest_start, 24, 0.25):
                ax.axhline(y, color=grid_color, linestyle='--', linewidth=1, alpha=0.80)
        else:
            for x in np.arange(earliest_start, 24, 0.25):
                ax.axvline(x, color=grid_color, linestyle='--', linewidth=1, alpha=0.80)

        dias = {"Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4, "Sábado": 5, "Domingo": 6}
        comisiones_rects = {}
        solapamiento_patches = []
        
        global indice_color
        for materia in materias.keys():
            if materia not in colores_materias:
                base_color = colores_base[indice_color % len(colores_base)]
                indice_color += 1
                colores_materias[materia] = [
                    matplotlib.colormaps.get_cmap(base_color)(0.2 + 0.6 * i / 8) for i in range(8)
                ]
        
        for nombre in horarios_extra.keys():
            if nombre not in colores_materias:
                base_color = colores_base[indice_color % len(colores_base)]
                indice_color += 1
                colores_materias[nombre] = [matplotlib.colormaps.get_cmap(base_color)(0.5)]
        
        # CAMBIO 2: Aplicar colores personalizados a horarios propios en la vista
        for nombre in horarios_extra.keys():
            if nombre in colores_extra_personalizados:
                colores_materias[nombre] = [colores_extra_personalizados[nombre]]
        
        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas_widget = canvas.get_tk_widget()
        
        toolbar_frame = tk.Frame(top)
        toolbar_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()
        
        canvas_widget.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        def on_scroll_zoom(event):
            ax_current = event.inaxes
            if ax_current is None:
                return
            scale_factor = 1.1
            if event.button == 'up':
                scale = 1 / scale_factor
            elif event.button == 'down':
                scale = scale_factor
            else:
                return
            xdata = event.xdata
            ydata = event.ydata
            xlim = ax_current.get_xlim()
            ylim = ax_current.get_ylim()
            new_xlim = [xdata - (xdata - xlim[0]) * scale, xdata + (xlim[1] - xdata) * scale]
            new_ylim = [ydata - (ydata - ylim[0]) * scale, ydata + (ylim[1] - ydata) * scale]
            ax_current.set_xlim(new_xlim)
            ax_current.set_ylim(new_ylim)
            canvas.draw_idle()
        
        canvas.mpl_connect('scroll_event', on_scroll_zoom)
        
        pan_data = {'active': False, 'x': None, 'y': None}

        def on_mouse_press(event):
            if event.button == 2:
                pan_data['active'] = True
                pan_data['x'] = event.xdata
                pan_data['y'] = event.ydata
                canvas_widget.config(cursor="fleur")

        def on_mouse_release(event):
            if event.button == 2:
                pan_data['active'] = False
                pan_data['x'] = None
                pan_data['y'] = None
                canvas_widget.config(cursor="")

        def on_mouse_move(event):
            if pan_data['active'] and event.xdata and event.ydata:
                dx = event.xdata - pan_data['x']
                dy = event.ydata - pan_data['y']
                xlim = ax.get_xlim()
                ylim = ax.get_ylim()
                ax.set_xlim(xlim[0] - dx, xlim[1] - dx)
                ax.set_ylim(ylim[0] - dy, ylim[1] - dy)
                pan_data['x'] = event.xdata - dx
                pan_data['y'] = event.ydata - dy
                canvas.draw_idle()

        canvas.mpl_connect('button_press_event', on_mouse_press)
        canvas.mpl_connect('button_release_event', on_mouse_release)
        canvas.mpl_connect('motion_notify_event', on_mouse_move)

        indices_comisiones = {}
        contador_indice = 1
        
        for materia_clave, comisiones in materias.items():
            for comision in comisiones.keys():
                if (materia_clave, comision) in comisiones_visibles:
                    indices_comisiones[(materia_clave, comision)] = contador_indice
                    contador_indice += 1
        
        
        def actualizar_solapamientos():
            nonlocal solapamiento_patches
            for patch in solapamiento_patches:
                patch.remove()
            solapamiento_patches.clear()
            
            # Crear lista de información de barras
            solapamientos = []
            
            # Agregar barras de materias (solo visibles)
            for (materia, comision), rects in comisiones_rects.items():
                for bar in rects:
                    if bar.get_visible():
                        if es_vertical:
                            x = bar.get_x()
                            y, height = bar.get_y(), bar.get_height()
                            solapamientos.append((bar, y, y + height, x, materia, comision))
                        else:
                            x, width, y = bar.get_x(), bar.get_width(), bar.get_y()
                            solapamientos.append((bar, x, x + width, y, materia, comision))
            
            # Solo agregar horarios propios cuyos rectángulos son visibles
            for nombre, rects_extra in horarios_extra_rects_global.items():
                hrs = horarios_extra[nombre]
                for i, (dia, inicio, fin) in enumerate(hrs):
                    dia_num = dias.get(dia, -1)
                    if dia_num >= 0 and i < len(rects_extra):
                        rect = rects_extra[i]
                        if rect.get_visible():
                            solapamientos.append((rect, inicio, fin, dia_num, nombre, "Extra"))
            pares_procesados = set()
            
            for i, (bar1, x1_1, x2_1, y1, mat1, com1) in enumerate(solapamientos):
                for j, (bar2, x1_2, x2_2, y2, mat2, com2) in enumerate(solapamientos):
                    coord_match = (es_vertical and x1_1 == x1_2) or (not es_vertical and y1 == y2)
                    if i < j and coord_match and x1_1 < x2_2 and x2_1 > x1_2:
                        if bar1.get_visible() and bar2.get_visible():
                            id1 = f"{mat1}_{com1}"
                            id2 = f"{mat2}_{com2}"
                            par_id = tuple(sorted([id1, id2]))
                            
                            if par_id not in pares_procesados:
                                pares_procesados.add(par_id)
                                solapado_inicio = max(x1_1, x1_2)
                                solapado_fin = min(x2_1, x2_2)
                                ancho = solapado_fin - solapado_inicio
                                if ancho > 0:
                                    if es_vertical:
                                        rect = mpatches.Rectangle((y1 - 0.4, solapado_inicio), 0.8, ancho,
                                                                facecolor='red', hatch='//', edgecolor='black', zorder=5)
                                    else:
                                        rect = mpatches.Rectangle((solapado_inicio, y1 - 0.4), ancho, 0.8,
                                                                facecolor='red', hatch='//', edgecolor='black', zorder=5)
                                    ax.add_patch(rect)
                                    solapamiento_patches.append(rect)
            
            canvas.draw()
        
        # Dibujar barras de materias
        for materia_clave, comisiones in materias.items():
            for idx_comision, (comision, horarios) in enumerate(comisiones.items()):
                if usar_mismo_color_por_materia:
                    color_comision = colores_materias[materia_clave][0]
                else:
                    color_comision = colores_materias[materia_clave][idx_comision % len(colores_materias[materia_clave])]
                
                comisiones_rects[(materia_clave, comision)] = []
                for dia, inicio, fin in horarios:
                    dia_num = dias.get(dia, -1)
                    if dia_num >= 0:
                        # CORRECCIÓN: Dibujar según orientación
                        if es_vertical:
                            rect = ax.bar(dia_num, fin - inicio, bottom=inicio, 
                                        color=color_comision, edgecolor="black", linewidth=1.5)[0]
                        else:
                            rect = ax.barh(dia_num, fin - inicio, left=inicio, 
                                        color=color_comision, edgecolor="black", linewidth=1.5)[0]
                        comisiones_rects[(materia_clave, comision)].append(rect)

        # Dibujar horarios propios — guardar rectángulos y aplicar visibilidad guardada
        horarios_extra_visibles_set = set(
            datos_alumno.get("horarios_extra_visibles", list(horarios_extra.keys()))
        )
        horarios_extra_rects_global = {}   # nombre -> [rect, ...]

        for nombre, hrs in horarios_extra.items():
            color = colores_materias[nombre][0]
            horarios_extra_rects_global[nombre] = []
            visible_inicial = nombre in horarios_extra_visibles_set
            for dia, inicio, fin in hrs:
                dia_num = dias.get(dia, -1)
                if dia_num >= 0:
                    if es_vertical:
                        rect = ax.bar(dia_num, fin - inicio, bottom=inicio,
                                    color=color, edgecolor="black", linewidth=2)[0]
                    else:
                        rect = ax.barh(dia_num, fin - inicio, left=inicio,
                                    color=color, edgecolor="black", linewidth=2)[0]
                    rect.set_visible(visible_inicial)   # ← aplicar estado guardado
                    horarios_extra_rects_global[nombre].append(rect)
        def toggle_comision(materia, comision, var):
            visible = var.get()
            
            for bar in comisiones_rects.get((materia, comision), []):
                bar.set_visible(visible)
            
            if visible:
                if (materia, comision) not in comisiones_visibles:
                    comisiones_visibles.append((materia, comision))
            else:
                if (materia, comision) in comisiones_visibles:
                    comisiones_visibles.remove((materia, comision))
            
            indices_comisiones.clear()
            contador = 1
            for mat_clave, coms in materias.items():
                for com in coms.keys():
                    if (mat_clave, com) in comisiones_visibles:
                        indices_comisiones[(mat_clave, com)] = contador
                        contador += 1
            
            guardar_materias_seleccionadas()
            
            for txt in ax.texts:
                txt.remove()
            
            actualizar_solapamientos()
            canvas.draw()
        
        # Frame principal de leyenda (NO scrolleable)
        legend_main_frame = tk.Frame(top, bg="white", padx=5, pady=5)
        legend_main_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=10, pady=10)

        # Botones de acción (siempre visibles)
        btn_exportar = tk.Button(legend_main_frame, text="Exportar Gráfico", command=exportar_grafico)
        btn_exportar.pack(pady=5)
        
        def abrir_menu_personalizacion():
            global usar_mismo_color_por_materia
            
            menu_top = tk.Toplevel(top)
            configurar_ventana(menu_top, "Personalizar Gráfico", 400, 600, centrar=True, icono=self.icono_ventana)
            menu_top.minsize(400, 600)
            menu_top.transient(top)
            traer_ventana_al_frente(menu_top)
            
            tk.Label(menu_top, text="Personalización del Gráfico", font=("Arial", 12, "bold")).pack(pady=10)
            
            fondo_frame = tk.Frame(menu_top)
            fondo_frame.pack(fill="x", padx=20, pady=10)
            
            tk.Label(fondo_frame, text="Color de Fondo:", font=("Arial", 10)).pack(side="left", padx=5)
            
            def elegir_color_fondo():
                global color_fondo_grafico
                from tkinter import colorchooser
                color = colorchooser.askcolor(title="Elegir color de fondo")
                if color[1]:
                    color_fondo_grafico = color[1]
                    top.destroy()
                    self.menu_graficar()
            
            def restaurar_fondo_auto():
                global color_fondo_grafico
                color_fondo_grafico = None
                top.destroy()
                self.menu_graficar()
            
            btn_color_fondo = tk.Button(fondo_frame, text="Elegir Color", command=elegir_color_fondo, bg="#4CAF50", fg="white")
            btn_color_fondo.pack(side="left", padx=5)
            
            btn_auto_fondo = tk.Button(fondo_frame, text="Por Defecto", command=restaurar_fondo_auto)
            btn_auto_fondo.pack(side="left", padx=5)
            
            tk.Label(menu_top, text="─" * 50).pack(pady=5)
            
            color_comisiones_frame = tk.Frame(menu_top, relief="solid", borderwidth=1, padx=10, pady=10)
            color_comisiones_frame.pack(fill="x", padx=20, pady=10)
            
            tk.Label(color_comisiones_frame, text="Colores de Comisiones:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
            
            var_mismo_color = tk.BooleanVar(value=usar_mismo_color_por_materia)
            
            def toggle_color_comisiones():
                global usar_mismo_color_por_materia, colores_materias, indice_color  # ← VERIFICAR QUE ESTÉ
                usar_mismo_color_por_materia = var_mismo_color.get()
                
                colores_materias.clear()
                indice_color = 0
                
                for materia in materias.keys():
                    base_color = colores_base[indice_color % len(colores_base)]
                    indice_color += 1
                    if usar_mismo_color_por_materia:
                        colores_materias[materia] = [matplotlib.colormaps.get_cmap(base_color)(0.5)] * 10
                    else:
                        colores_materias[materia] = [
                            matplotlib.colormaps.get_cmap(base_color)(0.2 + 0.6 * i / 10) for i in range(10)
                        ]
                
                guardar_materias_seleccionadas()
                menu_top.destroy()
                top.destroy()
                self.menu_graficar()
            
            chk_mismo_color = tk.Checkbutton(
                color_comisiones_frame, 
                text="Usar el mismo color para todas las comisiones de cada materia",
                variable=var_mismo_color,
                command=toggle_color_comisiones,
                wraplength=320,
                justify="left"
            )
            chk_mismo_color.pack(anchor="w", pady=5)
            
            tk.Label(color_comisiones_frame, 
                    text="• Activado: Todas las comisiones de una materia tendrán el mismo color\n"
                        "• Desactivado: Cada comisión tendrá un tono diferente del mismo color base",
                    font=("Arial", 8), fg="gray", justify="left", wraplength=320).pack(anchor="w", padx=15)
            
            tk.Label(menu_top, text="─" * 50).pack(pady=5)
            
            # CAMBIO 2: Sección para colores de horarios propios en personalización
            extras_frame = tk.Frame(menu_top, relief="solid", borderwidth=1, padx=10, pady=10)
            extras_frame.pack(fill="x", padx=20, pady=5)
            
            tk.Label(extras_frame, text="Colores de Horarios Propios:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
            
            horarios_extra_actual = datos_alumno.get("horarios_extra", {})
            
            if not horarios_extra_actual:
                tk.Label(extras_frame, text="No hay horarios propios agregados", 
                        font=("Arial", 9), fg="gray").pack(anchor="w", padx=5)
            else:
                for nombre_extra in horarios_extra_actual.keys():
                    extra_row = tk.Frame(extras_frame)
                    extra_row.pack(fill="x", pady=2)
                    
                    # Mostrar color actual
                    color_actual_extra = colores_extra_personalizados.get(nombre_extra, None)
                    if color_actual_extra:
                        try:
                            color_hex_display = color_actual_extra
                        except:
                            color_hex_display = "#cccccc"
                    else:
                        if nombre_extra in colores_materias:
                            try:
                                color_hex_display = matplotlib.colors.to_hex(colores_materias[nombre_extra][0])
                            except:
                                color_hex_display = "#cccccc"
                        else:
                            color_hex_display = "#cccccc"
                    
                    canvas_color_extra = tk.Canvas(extra_row, width=20, height=20,
                                                   highlightthickness=1, highlightbackground="black")
                    canvas_color_extra.configure(bg=color_hex_display)
                    canvas_color_extra.pack(side="left", padx=5)
                    
                    tk.Label(extra_row, text=nombre_extra, width=20, anchor="w", font=("Arial", 9)).pack(side="left", padx=5)
                    
                    def cambiar_color_extra(n=nombre_extra):
                        global colores_extra_personalizados
                        from tkinter import colorchooser
                        color_ini = colores_extra_personalizados.get(n, "#4CAF50")
                        color = colorchooser.askcolor(title=f"Color para '{n}'", color=color_ini)
                        if color[1]:
                            colores_extra_personalizados[n] = color[1]
                            guardar_materias_seleccionadas()
                            menu_top.destroy()
                            top.destroy()
                            self.menu_graficar()
                    
                    def restaurar_color_extra(n=nombre_extra):
                        global colores_extra_personalizados
                        if n in colores_extra_personalizados:
                            del colores_extra_personalizados[n]
                            guardar_materias_seleccionadas()
                            menu_top.destroy()
                            top.destroy()
                            self.menu_graficar()
                    
                    tk.Button(extra_row, text="🎨 Cambiar", command=cambiar_color_extra,
                             bg="#2196F3", fg="white", font=("Arial", 8)).pack(side="left", padx=3)
                    tk.Button(extra_row, text="↩ Defecto", command=restaurar_color_extra,
                             bg="#6c757d", fg="white", font=("Arial", 8)).pack(side="left", padx=3)
            
            tk.Label(menu_top, text="─" * 50).pack(pady=5)
            
            tk.Label(menu_top, text="Cambiar Colores de Materias:", font=("Arial", 10, "bold")).pack(pady=5)
            
            materias_frame = tk.Frame(menu_top)
            materias_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            canvas_mat = tk.Canvas(materias_frame)
            scrollbar_mat = tk.Scrollbar(materias_frame, orient="vertical", command=canvas_mat.yview)
            scrollable_mat = tk.Frame(canvas_mat)
            
            scrollable_mat.bind("<Configure>", lambda e: canvas_mat.configure(scrollregion=canvas_mat.bbox("all")))
            canvas_mat.create_window((0, 0), window=scrollable_mat, anchor="nw")
            canvas_mat.configure(yscrollcommand=scrollbar_mat.set)
            
            habilitar_scroll_con_rueda(canvas_mat, scrollable_mat)
            
            def cambiar_color_materia(mat_clave):
                from tkinter import colorchooser
                color = colorchooser.askcolor(title=f"Color para {mat_clave}")
                if color[1]:
                    if usar_mismo_color_por_materia:
                        colores_materias[mat_clave] = [color[1]] * 10
                    else:
                        import matplotlib.colors as mcolors
                        rgb = mcolors.to_rgb(color[1])
                        colores_materias[mat_clave] = []
                        for i in range(10):
                            factor = 0.3 + 0.7 * i / 10
                            nuevo_rgb = tuple(min(1.0, c * factor) for c in rgb)
                            colores_materias[mat_clave].append(nuevo_rgb)
                    
                    menu_top.destroy()
                    top.destroy()
                    self.menu_graficar()
            
            for materia_clave in materias.keys():
                mat_row = tk.Frame(scrollable_mat)
                mat_row.pack(fill="x", pady=2)
                
                if "[" in materia_clave:
                    nombre_display = materia_clave.split("[")[0]
                    carrera_materia = materia_clave.split("[")[1].rstrip("]")
                    label_text = f"{nombre_display} ({carrera_materia})"
                else:
                    label_text = materia_clave
                
                tk.Label(mat_row, text=label_text, width=25, anchor="w").pack(side="left", padx=5)
                tk.Button(mat_row, text="Cambiar Color", 
                        command=lambda m=materia_clave: cambiar_color_materia(m),
                        bg="#2196F3", fg="white").pack(side="left", padx=5)
            
            canvas_mat.pack(side="left", fill="both", expand=True)
            scrollbar_mat.pack(side="right", fill="y")
            
            btn_cerrar = tk.Button(menu_top, text="Volver", command=menu_top.destroy, padx=20, pady=5)
            btn_cerrar.pack(pady=10)
        
        btn_personalizar = tk.Button(legend_main_frame, text="⚙ Personalizar", command=abrir_menu_personalizacion, bg="#2196F3", fg="white")
        btn_personalizar.pack(pady=5)

        def cambiar_orientacion():
            global orientacion_grafico 
            nueva_orientacion = "vertical" if orientacion_grafico == "horizontal" else "horizontal"
            orientacion_grafico = nueva_orientacion
            top.destroy()
            self.menu_graficar()

        btn_orientacion = tk.Button(legend_main_frame, text="🔄 Rotar Gráfico", 
                                    command=cambiar_orientacion, bg="#FF9800", fg="white")
        btn_orientacion.pack(pady=5)

        # Separador
        tk.Frame(legend_main_frame, height=2, bg="gray").pack(fill="x", pady=5)

        # Título de materias (siempre visible)
        tk.Label(legend_main_frame, text="Materias y Comisiones", font=("Arial", 10, "bold"), bg="white").pack(pady=4)

        # Frame con scroll para el contenido de materias
        legend_scroll_frame = tk.Frame(legend_main_frame, bg="white")
        legend_scroll_frame.pack(fill="both", expand=True)

        legend_canvas = tk.Canvas(legend_scroll_frame, bg="white")
        legend_scrollbar = tk.Scrollbar(legend_scroll_frame, orient="vertical", command=legend_canvas.yview)
        legend_scrollable = tk.Frame(legend_canvas, bg="white")

        legend_scrollable.bind(
            "<Configure>",
            lambda e: legend_canvas.configure(scrollregion=legend_canvas.bbox("all"))
        )

        legend_canvas.create_window((0, 0), window=legend_scrollable, anchor="nw")
        legend_canvas.configure(yscrollcommand=legend_scrollbar.set)

        habilitar_scroll_con_rueda(legend_canvas, legend_scrollable)

        legend_canvas.pack(side="left", fill="both", expand=True)
        legend_scrollbar.pack(side="right", fill="y")
        
        top.rowconfigure(0, weight=0)
        top.rowconfigure(1, weight=1)
        top.columnconfigure(0, weight=3)
        top.columnconfigure(1, weight=1)
        
        for materia_clave, comisiones in materias.items():
            if "[" in materia_clave:
                nombre_display = materia_clave.split("[")[0]
                carrera_materia = materia_clave.split("[")[1].rstrip("]")
                label_text = f"{nombre_display} ({carrera_materia})"
            else:
                nombre_display = materia_clave
                label_text = materia_clave
            
            materia_container = tk.Frame(legend_scrollable, bg="lightgray", padx=2, pady=1)
            materia_container.pack(fill="x", padx=2, pady=2)
            
            tk.Label(materia_container, text=label_text, bg="white", font=("Arial", 9, "bold"), 
                    relief="ridge", padx=5, pady=2).pack(fill="x")
            
            comisiones_frame = tk.Frame(materia_container, bg="white", padx=5, pady=5)
            comisiones_frame.pack(fill="x")
            
            for idx_comision, comision in enumerate(comisiones.keys()):
                visible_inicialmente = (materia_clave, comision) in comisiones_visibles
                var = tk.BooleanVar(value=visible_inicialmente)
                
                for bar in comisiones_rects.get((materia_clave, comision), []):
                    bar.set_visible(visible_inicialmente)
                
                color_comision = colores_materias[materia_clave][idx_comision % len(colores_materias[materia_clave])]
                color_hex = matplotlib.colors.to_hex(color_comision)
                
                comision_row = tk.Frame(comisiones_frame, bg="white")
                comision_row.pack(fill="x", pady=1)
                
                color_canvas = tk.Canvas(comision_row, width=15, height=15, bg="white", highlightthickness=0)
                color_canvas.create_rectangle(0, 0, 15, 15, fill=color_hex, outline="black")
                color_canvas.pack(side="left", padx=(0, 5))
                
                chk = tk.Checkbutton(comision_row, text=comision, variable=var,
                                    command=lambda m=materia_clave, c=comision, v=var: toggle_comision(m, c, v),
                                    bg="white", anchor="w")
                chk.pack(side="left", fill="x", expand=True)
        
        # ═══════════════════════════════════════════════════════════════
        # HORARIOS PROPIOS CON CHECKBOXES PARA MOSTRAR/OCULTAR
        # ═══════════════════════════════════════════════════════════════
        if horarios_extra:
            tk.Label(legend_scrollable, text="━ Horarios Propios ━", font=("Arial", 9, "bold"),
                    bg="white", fg="#B8860B").pack(fill="x", pady=(10, 2))

            for nombre in horarios_extra.keys():
                color_val = colores_materias[nombre][0]
                try:
                    color = matplotlib.colors.to_hex(color_val)
                except:
                    color = str(color_val) if isinstance(color_val, str) else "#cccccc"

                frame_extra = tk.Frame(legend_scrollable, bg="white", relief="ridge", borderwidth=1, padx=5, pady=2)
                frame_extra.pack(fill="x", padx=2, pady=1)

                # Estado inicial desde datos guardados
                vis_set = set(datos_alumno.get("horarios_extra_visibles", list(horarios_extra.keys())))
                visible_inicialmente = nombre in vis_set
                var_extra = tk.BooleanVar(value=visible_inicialmente)

                def toggle_horario_extra(nombre_horario, var):
                    visible = var.get()
                    # Actualizar rectángulos en el gráfico
                    for rect in horarios_extra_rects_global.get(nombre_horario, []):
                        rect.set_visible(visible)
                    # Persistir estado
                    vis_actual = set(datos_alumno.get("horarios_extra_visibles",
                                                      list(horarios_extra.keys())))
                    if visible:
                        vis_actual.add(nombre_horario)
                    else:
                        vis_actual.discard(nombre_horario)
                    datos_alumno["horarios_extra_visibles"] = list(vis_actual)
                    guardar_datos_alumno()
                    actualizar_solapamientos()
                    canvas.draw()

                canvas_extra = tk.Canvas(frame_extra, width=15, height=15, bg="white", highlightthickness=0)
                canvas_extra.create_rectangle(0, 0, 15, 15, fill=color, outline="black")
                canvas_extra.pack(side="left", padx=(0, 5))

                chk_extra = tk.Checkbutton(
                    frame_extra,
                    text=nombre,
                    variable=var_extra,
                    command=lambda n=nombre, v=var_extra: toggle_horario_extra(n, v),
                    bg="white",
                    anchor="w"
                )
                chk_extra.pack(side="left", fill="x", expand=True)
        
        legend_canvas.pack(side="left", fill="both", expand=True)
        legend_scrollbar.pack(side="right", fill="y")
        
        superposicion_patch = mpatches.Patch(facecolor='red', hatch='//', edgecolor='black', label='Superposición de horarios')
        ax.legend(handles=[superposicion_patch], loc='upper right')
        
        comisiones_actuales = set()
        for materia, comisiones in materias.items():
            for comision in comisiones.keys():
                comisiones_actuales.add((materia, comision))

        comisiones_visibles = [cv for cv in comisiones_visibles if cv in comisiones_actuales]
        # Actualizar variable global de orientación
        orientacion_grafico = orientacion_var.get()
        actualizar_solapamientos()
        canvas.draw()
        
        def toggle_comision(materia, comision, var):
            visible = var.get()
            
            for bar in comisiones_rects.get((materia, comision), []):
                bar.set_visible(visible)
            
            if visible:
                if (materia, comision) not in comisiones_visibles:
                    comisiones_visibles.append((materia, comision))
            else:
                if (materia, comision) in comisiones_visibles:
                    comisiones_visibles.remove((materia, comision))
            
            guardar_materias_seleccionadas()
            actualizar_solapamientos()
            canvas.draw()
        
        comisiones_actuales = set()
        for materia, comisiones in materias.items():
            for comision in comisiones.keys():
                comisiones_actuales.add((materia, comision))

        comisiones_visibles = [cv for cv in comisiones_visibles if cv in comisiones_actuales]

        actualizar_solapamientos()
        canvas.draw()
    
    def limpiar_seleccion(self):
        global materias, comisiones_visibles
        materias.clear()
        comisiones_visibles.clear()
        guardar_materias_seleccionadas()
        messagebox.showinfo("Éxito", "Selección de materias y horarios limpiada")
    
    def toggle_tema(self):
        if self.tema_actual == "darkly":
            self.tema_actual = "lumen"
            new_text = "🌙"
        else:
            self.tema_actual = "darkly"
            new_text = "🌞"
        
        guardar_tema(self.tema_actual)
                
        self.style.theme_use(self.tema_actual)
        self.style.configure("Tema.TButton", font=("Arial", 20))
        self.style.configure("Github.TButton", font=("Arial", 20))
        self.btn_tema.config(text=new_text, style="Tema.TButton")
        self.btn_github.config(style="Github.TButton")     
        
        self.actualizar_barra_progreso()
    
    def actualizar_barra_progreso(self):
        """Actualiza la barra de progreso sin recrear todo el menú"""
        if self.canvas_progreso is None:
            return
        
        def calcular_progreso():
            carrera = datos_alumno.get("carrera", "")
            plan = planes_estudio.get(carrera, {})
            
            if not plan:
                return 0, 0, 0, 0
            
            total_obligatorias = 0
            aprobadas_obligatorias = 0
            total_horas_electivas = 44
            horas_electivas_cursadas = 0
            
            # Nombres de materias electivas de la carrera actual
            nombres_electivas_carrera = set()
            
            for nombre, data in plan.items():
                año = data.get("Año", "")
                
                if año == "E":
                    nombres_electivas_carrera.add(nombre)
                else:
                    total_obligatorias += 1
            
            # Revisar estados guardados (incluye electivas de todas las carreras)
            estados_materias = datos_alumno.get("estado_materias", {})
            
            for nombre_materia, estado in estados_materias.items():
                # Verificar si es obligatoria de mi carrera
                if nombre_materia in plan:
                    año = plan[nombre_materia].get("Año", "")
                    if año != "E" and estado == "aprobada":
                        aprobadas_obligatorias += 1
                
                # Verificar si es electiva (de cualquier carrera) y está aprobada
                if estado == "aprobada":
                    # Buscar en todas las carreras si es electiva
                    for carrera_nombre, plan_carrera in planes_estudio.items():
                        if nombre_materia in plan_carrera:
                            año_materia = plan_carrera[nombre_materia].get("Año", "")
                            if año_materia == "E":
                                horas = plan_carrera[nombre_materia].get("Hs", 0)
                                horas_electivas_cursadas += horas
                                break  # Ya la contamos, salir del loop
            
            horas_electivas_cursadas = min(horas_electivas_cursadas, total_horas_electivas)
            
            return aprobadas_obligatorias, total_obligatorias, horas_electivas_cursadas, total_horas_electivas
        
        aprobadas, total_oblig, hs_elec, total_hs_elec = calcular_progreso()       
        
        if hasattr(self, 'label_header_oblig'):
            self.label_header_oblig.config(text=f"Obligatorias {aprobadas}/{total_oblig}")
        if hasattr(self, 'label_header_elec'):
            self.label_header_elec.config(text=f"Electivas {hs_elec}hs/{total_hs_elec}hs")
        
        self.canvas_progreso.delete("all")
        
        proporcion_elec = 0.25
        proporcion_oblig = 0.7
        
        if not hasattr(self, '_cache_ancho_canvas') or self._cache_ancho_canvas == 1:
            self.canvas_progreso.update()
            self._cache_ancho_canvas = self.canvas_progreso.winfo_width()

        ancho_total = self._cache_ancho_canvas
        
        self.canvas_progreso.update()
        ancho_total = self.canvas_progreso.winfo_width()
        
        ancho_seccion_oblig = ancho_total * proporcion_oblig
        ancho_seccion_elec = ancho_total * proporcion_elec
        
        progreso_oblig = (aprobadas / total_oblig) if total_oblig > 0 else 0
        progreso_elec = (hs_elec / total_hs_elec) if total_hs_elec > 0 else 0
        
        peso_oblig = 0.70
        peso_elec = 0.30
        progreso_total = (progreso_oblig * peso_oblig) + (progreso_elec * peso_elec)
        porcentaje_total = progreso_total * 100
        
        # ⭐ DETERMINAR COLORES SEGÚN TEMA (antes de dibujar)
        tema_oscuro = self.tema_actual == "darkly"
        color_texto = "white" if tema_oscuro else "black"
        color_linea_divisoria = "white" if tema_oscuro else "black"
        
        # Dibujar barra de obligatorias (verde)
        ancho_barra_oblig = ancho_seccion_oblig * progreso_oblig
        if ancho_barra_oblig > 0:
            self.canvas_progreso.create_rectangle(0, 0, ancho_barra_oblig, 30, 
                                        fill="#4CAF50", outline="")
        
        # Dibujar barra de electivas (naranja)
        inicio_elec = ancho_seccion_oblig
        ancho_barra_elec = ancho_seccion_elec * progreso_elec
        if ancho_barra_elec > 0:
            self.canvas_progreso.create_rectangle(inicio_elec, 0, inicio_elec + ancho_barra_elec, 30,
                                        fill="#FF9800", outline="")
        
        # ⭐ LÍNEA DIVISORIA CON COLOR SEGÚN TEMA
        self.canvas_progreso.create_line(ancho_seccion_oblig, 0, ancho_seccion_oblig, 30,
                                fill=color_linea_divisoria, width=2)
        
        # Texto central con porcentaje total
        texto_porcentaje = f"{porcentaje_total:.1f}%"
        x_text_centro = ancho_total / 2
        self.canvas_progreso.create_text(x_text_centro, 15,
                                text=texto_porcentaje,
                                font=("Arial", 12, "bold"), fill=color_texto)
    def crear_menu_principal(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        frame = tb.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        info_frame = tb.Frame(frame, relief="solid", borderwidth=1)
        info_frame.pack(fill="x", padx=5, pady=5)
        self.info_frame = info_frame  # Guardar referencia
        
        info_text = f"👤 {datos_alumno.get('nombre', 'Sin nombre')} - {datos_alumno.get('carrera', 'Sin carrera')}"
        
        tb.Label(info_frame, text=info_text, font=("Arial", 10, "bold")).pack(pady=5)
        
        progreso_frame = tb.Frame(frame, relief="solid", borderwidth=1)
        progreso_frame.pack(fill="x", padx=5, pady=5)
        self.progreso_frame = progreso_frame
        
        # PRIMERO: Definir la función calcular_progreso
        def calcular_progreso():
            carrera = datos_alumno.get("carrera", "")
            plan = planes_estudio.get(carrera, {})
            
            if not plan:
                return 0, 0, 0, 0
            
            total_obligatorias = 0
            aprobadas_obligatorias = 0
            total_horas_electivas = 44
            horas_electivas_cursadas = 0
            
            # Nombres de materias electivas de la carrera actual
            nombres_electivas_carrera = set()
            
            for nombre, data in plan.items():
                año = data.get("Año", "")
                
                if año == "E":
                    nombres_electivas_carrera.add(nombre)
                else:
                    total_obligatorias += 1
            
            # Revisar estados guardados (incluye electivas de todas las carreras)
            estados_materias = datos_alumno.get("estado_materias", {})
            
            for nombre_materia, estado in estados_materias.items():
                # Verificar si es obligatoria de mi carrera
                if nombre_materia in plan:
                    año = plan[nombre_materia].get("Año", "")
                    if año != "E" and estado == "aprobada":
                        aprobadas_obligatorias += 1
                
                # Verificar si es electiva (de cualquier carrera) y está aprobada
                if estado == "aprobada":
                    # Buscar en todas las carreras si es electiva
                    for carrera_nombre, plan_carrera in planes_estudio.items():
                        if nombre_materia in plan_carrera:
                            año_materia = plan_carrera[nombre_materia].get("Año", "")
                            if año_materia == "E":
                                horas = plan_carrera[nombre_materia].get("Hs", 0)
                                horas_electivas_cursadas += horas
                                break  # Ya la contamos, salir del loop
            
            horas_electivas_cursadas = min(horas_electivas_cursadas, total_horas_electivas)
            
            return aprobadas_obligatorias, total_obligatorias, horas_electivas_cursadas, total_horas_electivas
        
        # SEGUNDO: Calcular los valores
        aprobadas, total_oblig, hs_elec, total_hs_elec = calcular_progreso()
        
        # TERCERO: Crear el header con los valores calculados
        header_progreso = tk.Frame(progreso_frame)
        header_progreso.pack(fill="x", padx=5, pady=(5, 2))
        
        tk.Label(header_progreso, text="Progreso:", font=("Arial", 10, "bold")).pack(side="left")
        
        # Rectángulo verde para Obligatorias
        canvas_legend_oblig = tk.Canvas(header_progreso, width=20, height=15, 
                                       highlightthickness=0, bg=header_progreso.cget('bg'))
        canvas_legend_oblig.pack(side="left", padx=(10, 2))
        canvas_legend_oblig.create_rectangle(2, 2, 18, 13, fill="#4CAF50", outline="black", width=1)
        
        # Label para obligatorias con contador
        self.label_header_oblig = tk.Label(header_progreso, text=f"Obligatorias {aprobadas}/{total_oblig}", 
                                           font=("Arial", 9))
        self.label_header_oblig.pack(side="left", padx=(0, 10))
        
        # Rectángulo naranja para Electivas
        canvas_legend_elec = tk.Canvas(header_progreso, width=20, height=15,
                                      highlightthickness=0, bg=header_progreso.cget('bg'))
        canvas_legend_elec.pack(side="left", padx=(0, 2))
        canvas_legend_elec.create_rectangle(2, 2, 18, 13, fill="#FF9800", outline="black", width=1)
        
        # Label para electivas con contador
        self.label_header_elec = tk.Label(header_progreso, text=f"Electivas {hs_elec}hs/{total_hs_elec}hs", 
                                          font=("Arial", 9))
        self.label_header_elec.pack(side="left")
        
        # Barra de progreso unificada
        barra_frame = tk.Frame(progreso_frame)
        barra_frame.pack(fill="x", padx=10, pady=(2, 5))
        
        self.canvas_progreso = tk.Canvas(barra_frame, height=30, bg="lightgray", 
                                   highlightthickness=1, highlightbackground="black")
        self.canvas_progreso.pack(fill="x", pady=2)
        
        aprobadas, total_oblig, hs_elec, total_hs_elec = calcular_progreso()
        
        # Actualizar texto del header si existe
        if hasattr(self, 'label_header_oblig'):
            self.label_header_oblig.config(text=f"Obligatorias {aprobadas}/{total_oblig}")
        if hasattr(self, 'label_header_elec'):
            self.label_header_elec.config(text=f"Electivas {hs_elec}hs/{total_hs_elec}hs")
        
        # Limpiar canvas
        self.canvas_progreso.delete("all")
        
        # Calcular proporciones - Electivas más grandes (30% del total)
        proporcion_elec = 0.30
        proporcion_oblig = 0.70
        
        self.canvas_progreso.update()
        ancho_total = self.canvas_progreso.winfo_width()
        
        # Calcular anchos de secciones
        ancho_seccion_oblig = ancho_total * proporcion_oblig
        ancho_seccion_elec = ancho_total * proporcion_elec
        
        # Calcular progreso real
        progreso_oblig = (aprobadas / total_oblig) if total_oblig > 0 else 0
        progreso_elec = (hs_elec / total_hs_elec) if total_hs_elec > 0 else 0
        
        # Calcular progreso total combinado
        peso_oblig = 0.70
        peso_elec = 0.30
        progreso_total = (progreso_oblig * peso_oblig) + (progreso_elec * peso_elec)
        porcentaje_total = progreso_total * 100
        
        # Dibujar barra de obligatorias (verde)
        ancho_barra_oblig = ancho_seccion_oblig * progreso_oblig
        if ancho_barra_oblig > 0:
            self.canvas_progreso.create_rectangle(0, 0, ancho_barra_oblig, 30, 
                                           fill="#4CAF50", outline="")
        
        # Dibujar barra de electivas (naranja)
        inicio_elec = ancho_seccion_oblig
        ancho_barra_elec = ancho_seccion_elec * progreso_elec
        if ancho_barra_elec > 0:
            self.canvas_progreso.create_rectangle(inicio_elec, 0, inicio_elec + ancho_barra_elec, 30,
                                           fill="#FF9800", outline="")
        
        # Línea divisoria entre secciones
        
        # Determinar color del texto según tema
        tema_oscuro = self.tema_actual == "darkly"
        color_texto = "white" if tema_oscuro else "black"
        color_linea_divisoria = "white" if tema_oscuro else "black"
        
        self.canvas_progreso.create_line(ancho_seccion_oblig, 0, ancho_seccion_oblig, 30,
                                   fill=color_linea_divisoria, width=2)
        # Texto central con porcentaje total
        texto_porcentaje = f"{porcentaje_total:.1f}%"
        x_text_centro = ancho_total / 2
        self.canvas_progreso.create_text(x_text_centro, 15,
                                   text=texto_porcentaje,
                                   font=("Arial", 12, "bold"), fill=color_texto)

        alumno_frame = tb.Frame(frame, relief="solid", borderwidth=1)
        alumno_frame.pack(fill="x", padx=5, pady=5)
        self.alumno_frame = alumno_frame
        tb.Label(alumno_frame, text="Gestión de Alumno", font=("Arial", 10, "bold")).pack(side="top", anchor="w", padx=5)
        
        botones_alumno = tb.Frame(alumno_frame)
        botones_alumno.pack(fill="x")
        
        def nuevo_alumno_menu():
            crear_nuevo_alumno(self.root)
            self.crear_menu_principal()
        
        def editar_alumno_menu():
            nombre_antes = datos_alumno.get("nombre", "")
            editar_alumno(self.root, self.icono_ventana)
            # Solo recrear el menú si realmente hubo cambios
            if datos_alumno.get("nombre", "") != nombre_antes or True:
                self.crear_menu_principal()
        
        def cargar_alumno_menu():
            if cargar_alumno_existente(self.root):
                self.crear_menu_principal()
        
        btn_nuevo = tb.Button(botones_alumno, text="Nuevo", command=nuevo_alumno_menu, bootstyle="success-outline")
        btn_nuevo.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        self.btn_nuevo_alumno = btn_nuevo
        
        btn_editar = tb.Button(botones_alumno, text="Editar", command=editar_alumno_menu, bootstyle="warning-outline")
        btn_editar.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        self.btn_editar_alumno = btn_editar

        btn_cargar = tb.Button(botones_alumno, text="Cargar", command=cargar_alumno_menu, bootstyle="success-outline")
        btn_cargar.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        self.btn_cargar_alumno = btn_cargar
        
        def eliminar_alumno_menu():
            global archivo_alumno_actual, datos_alumno 
            
            if not messagebox.askyesno("Confirmar", 
                                    f"¿Eliminar alumno '{datos_alumno.get('nombre', 'actual')}'?\n\n"
                                    "Deberás crear o seleccionar otro alumno inmediatamente.\n"
                                    "Si cancelas, la aplicación se cerrará."):
                return
            
            archivo_a_eliminar = archivo_alumno_actual
            
            # Limpiar datos actuales temporalmente
            archivo_alumno_actual = None
            datos_alumno_backup = datos_alumno.copy()
            datos_alumno.clear()
            
            # Intentar cargar otro alumno
            archivos = listar_archivos_alumnos()
            archivos_restantes = [a for a in archivos if a != archivo_a_eliminar]
            
            if len(archivos_restantes) == 0:
                # No hay otros alumnos, debe crear uno nuevo
                messagebox.showinfo("Crear Nuevo Alumno", 
                                "No hay otros alumnos disponibles.\n"
                                "Debes crear un nuevo alumno ahora.",
                                parent=self.root)
                crear_nuevo_alumno(self.root)
                
                if not datos_alumno or "nombre" not in datos_alumno:
                    # Usuario canceló la creación
                    messagebox.showwarning("Operación Cancelada", 
                                        "No se eliminó el alumno.\n"
                                        "La aplicación se cerrará.")
                    # Restaurar datos
                    datos_alumno.update(datos_alumno_backup)
                    archivo_alumno_actual = archivo_a_eliminar
                    self.root.quit()
                    return
            else:
                # Hay otros alumnos, debe seleccionar uno
                messagebox.showinfo("Seleccionar Alumno", 
                                "Selecciona otro alumno antes de eliminar el actual.",
                                parent=self.root)
                seleccionar_alumno_de_lista(archivos_restantes, self.root)
                
                if not datos_alumno or "nombre" not in datos_alumno:
                    # Usuario canceló la selección
                    messagebox.showwarning("Operación Cancelada", 
                                        "No se eliminó el alumno.\n"
                                        "La aplicación se cerrará.")
                    # Restaurar datos
                    datos_alumno.update(datos_alumno_backup)
                    archivo_alumno_actual = archivo_a_eliminar
                    self.root.quit()
                    return
            
            # Si llegamos aquí, hay un nuevo alumno cargado, proceder con eliminación
            if archivo_a_eliminar and os.path.exists(archivo_a_eliminar):
                os.remove(archivo_a_eliminar)
                messagebox.showinfo("Éxito", "Alumno eliminado correctamente")
            
            self.crear_menu_principal()

        btn_eliminar = tb.Button(botones_alumno, text="Eliminar", command=eliminar_alumno_menu, bootstyle="danger-outline")
        btn_eliminar.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        self.btn_eliminar_alumno = btn_eliminar

        frame_sel = tb.Frame(frame, relief="solid", borderwidth=1)
        frame_sel.pack(fill="x", padx=5, pady=5)
        self.frame_sel = frame_sel
        tb.Label(frame_sel, text="Seleccionar Materias", font=("Arial", 10, "bold")).pack(side="top", anchor="w", padx=5)
        
        botones_frame_sel = tb.Frame(frame_sel)
        botones_frame_sel.pack(fill="x")
        
        btn_sel_carrera = tb.Button(botones_frame_sel, text="Por Carrera", command=self.menu_seleccionar_por_carrera, bootstyle="primary-outline")
        btn_sel_carrera.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        
        btn_sel_materia = tb.Button(botones_frame_sel, text="Por Materia", command=self.menu_seleccionar_por_materia, bootstyle="primary-outline")
        btn_sel_materia.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        
        frame_extra = tb.Frame(frame, relief="solid", borderwidth=1)
        frame_extra.pack(fill="x", padx=5, pady=5)
        self.frame_extra = frame_extra
        tb.Label(frame_extra, text="Horarios Propios", font=("Arial", 10, "bold")).pack(side="top", anchor="w", padx=5)
        
        botones_frame_extra = tb.Frame(frame_extra)
        botones_frame_extra.pack(fill="x")
        
        btn_agregar_extra = tb.Button(botones_frame_extra, text="Agregar Horario Propio",
                                      command=lambda: agregar_horario_extra(self.root), bootstyle="warning-outline")
        btn_agregar_extra.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        btn_gestionar_extra = tb.Button(botones_frame_extra, text="Gestionar Horarios Propios",
                                        command=lambda: gestionar_horarios_extra(self.root), bootstyle="warning-outline")
        btn_gestionar_extra.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        frame_vis = tb.Frame(frame, relief="solid", borderwidth=1)
        frame_vis.pack(fill="x", padx=5, pady=5)
        self.frame_vis = frame_vis
        tb.Label(frame_vis, text="Visualizar", font=("Arial", 10, "bold")).pack(side="top", anchor="w", padx=5)

        botones_frame_vis = tb.Frame(frame_vis)
        botones_frame_vis.pack(fill="x")
        
        btn_graficar = tb.Button(botones_frame_vis, text="Graficar Horarios", command=self.menu_graficar, bootstyle="success")
        btn_graficar.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        
        btn_limpiar = tb.Button(botones_frame_vis, text="🗑", command=self.limpiar_seleccion, bootstyle="danger")
        btn_limpiar.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        crear_tooltip(btn_limpiar, "Limpiar seleccionados")
        
        frame_otros = tb.Frame(frame, relief="solid", borderwidth=1)
        frame_otros.pack(fill="x", padx=5, pady=5)
        self.frame_otros = frame_otros
        tb.Label(frame_otros, text="Otros", font=("Arial", 10, "bold")).pack(side="top", anchor="w", padx=5)
        
        botones_frame_otros = tb.Frame(frame_otros)
        botones_frame_otros.pack(fill="x")
        
        # MEJORADO: Botones con texto + símbolo para mayor claridad
        texto_tema = "🌞" if self.tema_actual == "darkly" else "🌙"
        self.btn_tema = tb.Button(botones_frame_otros, text=texto_tema, 
                                 command=self.toggle_tema, style="Tema.TButton", bootstyle="info")
        self.btn_tema.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        
        # GitHub con imagen + texto
        # texto_github = " " if self.github_icon else "GitHub"
        self.btn_github = tb.Button(botones_frame_otros, image=self.github_icon,
                                    compound="left" if self.github_icon else "none", 
                                    command=abrir_github, style="Tema.TButton", bootstyle="info")
        self.btn_github.pack(side="left", padx=5, pady=5, expand=True, fill="x")       
        
        # Tutorial con símbolo más descriptivo
        self.btn_tutorial = tb.Button(botones_frame_otros, text="❓", 
                                      command=lambda: mostrar_tutorial(self.root, forzar=False), 
                                      style="Tema.TButton", bootstyle="info")
        self.btn_tutorial.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        # ── TOOLTIPS ──────────────────────────────────────────────
        crear_tooltip(self.btn_tema, "Cambiar entre tema claro y oscuro")
        crear_tooltip(self.btn_github, "Abrir repositorio en GitHub")
        crear_tooltip(self.btn_tutorial, "Ver el tutorial de la aplicación")

        if self.icon:
            try:
                self.root.iconphoto(True, self.icon)
            except Exception as e:
                print(f"⚠️ No se pudo re-aplicar el ícono: {e}")

# # ============================================================================
# # CÓDIGO PRINCIPAL
# # ============================================================================
if __name__ == "__main__":
    if not cargar_planes_estudio():
        temp_root = tk.Tk()
        temp_root.withdraw()
        messagebox.showerror("Error", "No se pudieron cargar los planes de estudio")
        temp_root.destroy()
        exit()

    root = tb.Window(themename=obtener_tema_sistema())
    root.withdraw()

    if not inicializar_alumno(root):
        root.destroy()
        exit()

    root.deiconify()

    app = HorarioGUI(root)

    try:
        root.mainloop()
    except BaseException:
        print("Aplicación interrumpida por el usuario.")
        root.destroy()
