#--------------------------------------------------------------------#
#Hecho por Fabrizio Azeglio (@Fabros96) para organizar los horarios de cursado de la FRM-UTN. 
#La idea es que sea una herramienta para que los estudiantes puedan organizar sus horarios de cursado
#de manera más eficiente y les facilite antes de tiempo planificar sus horarios.
#El código es libre de uso y modificación, si queres colaborar con el proyecto podes hacerlo sin problemas.
#Si tenes alguna sugerencia o mejora no dudes en comentarla.   
#Sin más que agregar sos libre de modificar el código a tu gusto y necesidad y si querés compartirlo también.

#El código también esta comentado para su mayor entendimiento. Esta programado en Python y usa la librería Tkinter para la interfaz gráfica.

#El ejecutable esta en la ruta 'organizadorMaterias\dist' y
#--------------------------------------------------------------------#

from tkinter import ttk, messagebox, filedialog
import darkdetect
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import matplotlib.patheffects as patheffects
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import ttkbootstrap as tb
import tkinter as tk
import numpy as np
import json
import matplotlib
import webbrowser

# Diccionario para almacenar las materias y sus comisiones
materias = {}
# Diccionario para almacenar los colores asignados a cada materia
colores_materias = {}
# Lista de colores base para asignar a las materias
colores_base = ["PiYG", "summer", "winter", "vanimo", "hsv", "cool", "inferno_r", "Pastel2"]
# Índice para recorrer la lista de colores base
indice_color = 0

comisiones_visibles = []

# Función para obtener el tema del sistema (oscuro o claro)
def obtener_tema_sistema():
    return "darkly" if darkdetect.isDark() else "superhero"

# Función para cerrar una ventana con la tecla Escape
def cerrar_con_esc(event):
    # Solo cierra la ventana si el foco está en la ventana Toplevel
    if isinstance(event.widget, tk.Toplevel):
        event.widget.destroy()
    else:
        # Verificar si el widget con el foco está dentro de un contenedor que usa 'pack'
        if event.widget.master and isinstance(event.widget.master, tk.Frame):
            # Verificar que el contenedor master tenga 'pack_info', indicando que es un contenedor pack
            if event.widget.master.pack_info():
                # El widget está dentro de un contenedor que usa 'pack'
                if event.widget.master.master:
                    event.widget.master.master.destroy()  # Cierra la ventana contenedora
                else:
                    # Si no hay master.master, cerramos la ventana raíz (root o top-level)
                    event.widget.master.destroy()
            else:
                # Si no está dentro de un 'pack', cerramos la ventana que tiene el foco
                if event.widget.master:
                    event.widget.master.destroy()
        else:
            # Si no está dentro de un 'Frame' o 'pack', simplemente cerramos el contenedor actual
            if event.widget.master:
                event.widget.master.destroy()

# Función para abrir el perfil de GitHub en el navegador
def abrir_github():
    webbrowser.open("https://github.com/Fabros96")
    webbrowser.open("https://github.com/Fabros96/organizadorMaterias")

def obtener_materias_visibles(comisiones_rects):
    visibles = []
    for (materia, comision), rects in comisiones_rects.items():
        if any(bar.get_visible() for bar in rects):
            visibles.append((materia, comision))
    return visibles

# Función para exportar el gráfico a un archivo PNG
def exportar_grafico():
    file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
    if file_path:
        
        # Buscar el horario de inicio más temprano solo de las materias visibles
        horario_termino_antes = float('inf')  # Establecemos un valor muy grande inicialmente
        
        for materia, comisiones in materias.items():
            for comision, horarios in comisiones.items():
                if (materia, comision) in comisiones_visibles:  # Solo procesamos las materias visibles
                    for dia, inicio, fin in horarios:
                        if inicio < horario_termino_antes:
                            horario_termino_antes = inicio

        # Crear una nueva figura y eje para el gráfico
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Usar el horario más temprano para establecer el límite del gráfico
        ax.set_xlim(horario_termino_antes, 24)  # Ajustar el límite de inicio en el horario más temprano encontrado
        
        # Establecer ticks y etiquetas para el eje x
        ax.set_xticks(np.arange(horario_termino_antes, 24, 0.25))
        ax.set_xticklabels([f"{int(h)}:{int((h % 1) * 60):02d}" for h in np.arange(horario_termino_antes, 24, 0.25)], rotation=80)

        ax.set_ylim(-0.5, 6.5)
        ax.set_yticks(range(7))
        ax.set_yticklabels(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
        ax.set_xlabel("Hora")
        ax.set_ylabel("Día")
        ax.set_title("Horarios de Clases")

        for x in np.arange(horario_termino_antes, 24, 0.25):
            ax.axvline(x, color='#27282b', linestyle='--', linewidth=1, alpha=0.80)

        dias = {"Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4, "Sábado": 5, "Domingo": 6}

        global indice_color
        for materia in materias.keys():
            if materia not in colores_materias:
                base_color = colores_base[indice_color % len(colores_base)]
                indice_color += 1
                colores_materias[materia] = [
                    matplotlib.colormaps.get_cmap(base_color)(0.2 + 0.6 * i / 10) for i in range(10)
                ]

        # Crear el diccionario de rectángulos
        comisiones_rects = {}
        barras_sin_superposicion = []  # Lista para las barras sin superposición inicialmente
        for materia, comisiones in materias.items():
            for idx, (comision, horarios) in enumerate(comisiones.items()):
                if (materia, comision) in comisiones_visibles:
                    color = colores_materias[materia][idx % len(colores_materias[materia])]
                    comisiones_rects[(materia, comision)] = []
                    for dia, inicio, fin in horarios:
                        dia_num = dias.get(dia, -1)
                        if dia_num >= 0:
                            rect = ax.barh(dia_num, fin - inicio, left=inicio, color=color, edgecolor="black")[0]
                            comisiones_rects[(materia, comision)].append(rect)
                            
                            # Agregar a las barras sin superposición inicialmente
                            barras_sin_superposicion.append((rect, materia, comision, inicio, fin, dia_num))

        # Añadir superposiciones rojas
        solapamientos = []
        for (materia, comision), rects in comisiones_rects.items():
            for bar in rects:
                x, width, y = bar.get_x(), bar.get_width(), bar.get_y()
                solapamientos.append((bar, x, x + width, y, materia, comision))

        for bar, x1, x2, y, materia, comision in solapamientos:
            bar.set_color(colores_materias[materia][0])

        # Detectar y manejar superposiciones
        superposiciones_parciales = {}  # Diccionario para guardar las superposiciones parciales con sus referencias
        superposiciones_totales = {}  # Diccionario para guardar las superposiciones totales con sus referencias
        referencias = [f"*{chr(65 + i)}" for i in range(26)]  # Asegúrate de que haya al menos 26 referencias

        for i, (bar1, x1_1, x2_1, y1, mat1, com1) in enumerate(solapamientos):
            for j, (bar2, x1_2, x2_2, y2, mat2, com2) in enumerate(solapamientos):
                if i < j and y1 == y2 and x1_1 < x2_2 and x2_1 > x1_2:
                    solapado_inicio = max(x1_1, x1_2)
                    solapado_fin = min(x2_1, x2_2)
                    ancho = solapado_fin - solapado_inicio

                    if ancho > 0:
                        # Marcar las barras como sin texto si hay superposición
                        bar1.no_text = True
                        bar2.no_text = True

                        if x1_1 == x1_2 and x2_1 == x2_2:
                            # Superposición total: mostrar una referencia y cubrir completamente el rectángulo original
                            referencia = referencias.pop(0)
                            superposiciones_totales[referencia] = f"{mat1}-{com1} y {mat2}-{com2}"
                            
                            # Marcar las barras como sin texto
                            bar1.no_text = True
                            bar2.no_text = True
                            
                            # Agregar un rectángulo rojo que cubra completamente el original
                            rect = mpatches.Rectangle((x1_1, y1), x2_1 - x1_1, 0.8,
                                                      facecolor='red', hatch='//', edgecolor='black', zorder=5)
                            ax.add_patch(rect)
                            
                            # Agregar texto con la referencia
                            text = ax.text((x1_1 + x2_1) / 2, y1 + 0.4, referencia,
                                           ha='center', va='center', fontsize=14, color='white',
                                           fontname='Arial', zorder=6)
                            text.set_path_effects([patheffects.withStroke(linewidth=3, foreground='black')])
                        else:
                            # Superposición parcial: mostrar solo la referencia
                            referencia = referencias.pop(0)
                            superposiciones_parciales[referencia] = f"{mat1}-{com1} y {mat2}-{com2}"
                            rect = mpatches.Rectangle((solapado_inicio, y1 - 0.4), ancho, 0.8,
                                                      facecolor='red', hatch='//', edgecolor='black', zorder=5)
                            ax.add_patch(rect)
                            text = ax.text(solapado_inicio + ancho / 2, y1, referencia,
                                           ha='center', va='center', fontsize=14, color='white',
                                           fontname='Arial', zorder=6)
                            text.set_path_effects([patheffects.withStroke(linewidth=3, foreground='black')])

        # Escribir el texto solo en las barras sin superposición
        for rect, materia, comision, inicio, fin, dia_num in barras_sin_superposicion:
            # Solo agregar texto si la barra no tiene superposición
            if not hasattr(rect, 'no_text') or not rect.no_text:
                # Añadir texto de la comisión dentro del rectángulo
                text = ax.text(
                    inicio + (fin - inicio) / 2, dia_num, f"{materia}-{comision}", ha='center', va='center',
                    fontsize=14, color='white', fontname='Arial', zorder=6)
                text.set_path_effects([patheffects.withStroke(linewidth=3, foreground='black')])

        # Crear leyenda a la derecha para superposiciones parciales y totales
        leyenda_x = 24.5  # Posición x para la leyenda
        leyenda_y = 3.5   # Posición y para la leyenda

        # Margen superior
        leyenda_y += 0.5

        # Título de la leyenda para superposiciones parciales
        ax.text(leyenda_x, leyenda_y, "Superposiciones Parciales", ha='left', va='center',
                fontsize=14, color='black', fontname='Arial', fontweight='bold')

        # Margen inferior
        leyenda_y -= 0.5

        for i, (referencia, detalle) in enumerate(superposiciones_parciales.items()):
            text = ax.text(leyenda_x, leyenda_y - i * 0.4, f"{referencia}: {detalle}", ha='left', va='center',
                           fontsize=12, color='white', fontname='Arial')
            text.set_path_effects([patheffects.withStroke(linewidth=3, foreground='black')])

        # Margen superior antes del título de superposiciones totales
        leyenda_y -= len(superposiciones_parciales) * 0.4 + 0.5

        # Título de la leyenda para superposiciones totales
        ax.text(leyenda_x, leyenda_y, "Superposiciones Totales", ha='left', va='center',
                fontsize=14, color='black', fontname='Arial', fontweight='bold')

        # Margen inferior
        leyenda_y -= 0.5

        for i, (referencia, detalle) in enumerate(superposiciones_totales.items()):
            text = ax.text(leyenda_x, leyenda_y - i * 0.4, f"{referencia}: {detalle}", ha='left', va='center',
                           fontsize=12, color='white', fontname='Arial')
            text.set_path_effects([patheffects.withStroke(linewidth=3, foreground='black')])

        # Crear leyenda para las materias y comisiones
        handles = []
        for materia, color in colores_materias.items():
            patch = mpatches.Patch(color=color[0], label=materia)
            handles.append(patch)
        ax.legend(handles=handles, loc='upper left', bbox_to_anchor=(1, 1))

    # Guardar la figura como un archivo PNG
    fig.savefig(file_path, bbox_inches='tight')
    plt.close(fig)
    messagebox.showinfo("Éxito", "Gráfico exportado correctamente")

def centrar_ventana(ventana):
    ventana.update_idletasks()
    # Obtener el tamaño de la pantalla
    pantalla_width = ventana.winfo_screenwidth()
    pantalla_height = ventana.winfo_screenheight()
    # Obtener el tamaño de la ventana
    ventana_width = ventana.winfo_width()
    ventana_height = ventana.winfo_height()
    # Calcular la posición de la ventana para centrarla
    pos_x = (pantalla_width // 2) - (ventana_width // 2)
    pos_y = (pantalla_height // 2) - (ventana_height // 2)
    # Establecer la nueva posición de la ventana
    ventana.geometry(f"{ventana_width}x{ventana_height}+{pos_x}+{pos_y-100}")

# Clase principal de la interfaz gráfica
class HorarioGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Horarios")
        self.root.iconbitmap('logo.ico')
        root.minsize(400, 400)
        centrar_ventana(root)
        self.tema_actual = obtener_tema_sistema()
        self.style = tb.Style(theme=self.tema_actual)

        # Configuración de estilos para los botones
        self.style.configure("Tema.TButton", font=("Arial", 20))
        self.style.configure("Github.TButton", font=("Arial", 20))

        # Cargar y redimensionar el icono de GitHub
        github_icon_path = 'gh.ico'
        try:
            github_icon = Image.open(github_icon_path)
            github_icon = github_icon.resize((30, 30), Image.LANCZOS)
            self.github_icon = ImageTk.PhotoImage(github_icon)
            github_button_text = "Fabros96"
        except Exception as e:
            self.github_icon = None
            github_button_text = "@Fabros96"

        # Crear el menú principal
        self.crear_menu_principal()

    # Método para crear el menú de ABM de materias
    def menu_abm_materia(self):
        top = tk.Toplevel(self.root)
        top.title("AB Materias")
        top.bind("<Escape>", cerrar_con_esc)
        top.focus_force()
        top.minsize(300, 275)
        top.geometry("300x275")
        top.maxsize(800, 600)

        # Obtener la posición de la ventana principal (self.root)
        pos_x = self.root.winfo_rootx()
        pos_y = self.root.winfo_rooty()

        # Establecer la posición de la ventana hija en la misma ubicación que la ventana principal
        top.geometry(f"300x275+{pos_x}+{pos_y}")

        tk.Label(top, text="Materias Existentes:").pack()
        listbox = tk.Listbox(top)
        listbox.pack()
        for materia in materias.keys():
            listbox.insert(tk.END, materia)

        frame = tk.Frame(top)
        frame.pack()
        tk.Label(frame, text="Nombre Materia:").grid(row=0, column=0)
        entry_materia = tk.Entry(frame)
        entry_materia.grid(row=0, column=1, pady=10)

        # Función para agregar una nueva materia
        def agregar_materia():
            nombre = entry_materia.get()
            if nombre and nombre not in materias:
                materias[nombre] = {}
                listbox.insert(tk.END, nombre)
                messagebox.showinfo("Éxito", "Materia agregada")
            else:
                messagebox.showerror("Error", "Nombre inválido o ya existente")
            top.lift()
            top.focus_force()

        # Función para eliminar una materia seleccionada
        def eliminar_materia():
            seleccion = listbox.curselection()
            if seleccion:
                materia = listbox.get(seleccion)
                del materias[materia]
                listbox.delete(seleccion)
                messagebox.showinfo("Éxito", "Materia eliminada")
                top.lift()
                top.focus_force()

        btn_frame_mat = tk.Frame(frame)
        btn_frame_mat.grid(row=5, column=0, columnspan=2, pady=15)
        tk.Button(btn_frame_mat, text="Agregar Materia", command=agregar_materia).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame_mat, text="Eliminar Materia", command=eliminar_materia).pack(side=tk.LEFT, padx=5)

        top.bind("<Return>", lambda e: agregar_materia())
        top.bind("<Delete>", lambda e: eliminar_materia())

    # Método para crear el menú de ABM de comisiones
    def menu_abm_comision(self):
        top = tk.Toplevel(self.root)
        top.title("AB Comisiones")
        top.bind("<Escape>", cerrar_con_esc)
        top.focus_force()
        top.minsize(310, 310)
        top.geometry("310x30")
        top.maxsize(800, 600)

        # Obtener la posición de la ventana principal (self.root)
        pos_x = self.root.winfo_rootx()
        pos_y = self.root.winfo_rooty()

        # Establecer la posición de la ventana hija en la misma ubicación que la ventana principal
        top.geometry(f"300x275+{pos_x}+{pos_y}")

        tk.Label(top, text="Seleccione una Materia:").pack()
        combo_materia = ttk.Combobox(top, values=list(materias.keys()))
        combo_materia.pack()

        listbox = tk.Listbox(top)
        listbox.pack()

        # Función para actualizar la lista de comisiones
        def actualizar_comisiones():
            materia = combo_materia.get()
            listbox.delete(0, tk.END)
            if materia in materias:
                for comision in materias[materia].keys():
                    listbox.insert(tk.END, comision)

        combo_materia.bind("<<ComboboxSelected>>", lambda e: actualizar_comisiones())

        frame = tk.Frame(top)
        frame.pack()
        tk.Label(frame, text="Nombre Comisión:").grid(row=0, column=0)
        entry_comision = tk.Entry(frame)
        entry_comision.grid(row=0, column=1, pady=10)

        # Función para agregar una nueva comisión
        def agregar_comision():
            materia = combo_materia.get()
            comision = entry_comision.get()
            if materia and comision and comision not in materias[materia]:
                materias[materia][comision] = []
                listbox.insert(tk.END, comision)
                messagebox.showinfo("Éxito", "Comisión agregada")
            else:
                messagebox.showerror("Error", "Datos inválidos")
            top.lift()
            top.focus_force()

        # Función para eliminar una comisión seleccionada
        def eliminar_comision():
            materia = combo_materia.get()
            seleccion = listbox.curselection()
            if seleccion:
                comision = listbox.get(seleccion)
                del materias[materia][comision]
                listbox.delete(seleccion)
                messagebox.showinfo("Éxito", "Comisión eliminada")
                top.lift()
                top.focus_force()

        btn_frame_com = tk.Frame(frame)
        btn_frame_com.grid(row=5, column=0, columnspan=2, pady=15)
        tk.Button(btn_frame_com, text="Agregar Comision", command=agregar_comision).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame_com, text="Eliminar Comision", command=eliminar_comision).pack(side=tk.LEFT, padx=5)

        top.bind("<Return>", lambda e: agregar_comision())
        top.bind("<Delete>", lambda e: eliminar_comision())

    def menu_abm_horarios(self):
        top = tk.Toplevel(self.root)
        top.title("AB Horarios")
        top.bind("<Escape>", cerrar_con_esc)
        top.focus_force()
        top.minsize(300, 475)
        top.geometry("300x475")
        top.maxsize(300, 475)

        # Obtener la posición de la ventana principal (self.root)
        pos_x = self.root.winfo_rootx()
        pos_y = self.root.winfo_rooty()

        # Establecer la posición de la ventana hija en la misma ubicación que la ventana principal
        top.geometry(f"300x275+{pos_x}+{pos_y}")

        tk.Label(top, text="Seleccione Materia:").pack(pady=5)
        combo_materia = ttk.Combobox(top, values=list(materias.keys()))
        combo_materia.pack(pady=5)

        tk.Label(top, text="Seleccione Comisión:").pack(pady=5)
        combo_comision = ttk.Combobox(top)
        combo_comision.pack(pady=5)

        def actualizar_comisiones():
            materia = combo_materia.get()
            combo_comision['values'] = list(materias.get(materia, {}).keys())

        def actualizar_horarios():
            materia = combo_materia.get()
            comision = combo_comision.get()
            
            listbox.delete(0, tk.END)

            if materia and comision and materia in materias and comision in materias[materia]:
                for dia, inicio, fin in materias[materia][comision]:
                    horas_desde = int(inicio)
                    minutos_desde = int((inicio - horas_desde) * 60)
                    horas_hasta = int(fin)
                    minutos_hasta = int((fin - horas_hasta) * 60)
                    listbox.insert(tk.END, f"{dia}: {horas_desde:02}:{minutos_desde:02}-{horas_hasta:02}:{minutos_hasta:02}")

        combo_materia.bind("<<ComboboxSelected>>", lambda e: (actualizar_comisiones(), actualizar_horarios()))
        combo_comision.bind("<<ComboboxSelected>>", lambda e: actualizar_horarios())

        listbox = tk.Listbox(top)
        listbox.pack(pady=5)

        # Fila 1: Día
        frame_dia = tk.Frame(top)
        frame_dia.pack(fill="x", pady=5)  # Empaquetar el frame para la fila "Día"

        tk.Label(frame_dia, text="Día:").pack(side="left", padx=(50, 0))
        entry_dia = ttk.Combobox(frame_dia, values=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
        entry_dia.pack(side="left")

        # Fila 2: Desde
        frame_desde = tk.Frame(top)
        frame_desde.pack(fill="x", pady=5)  # Empaquetar el frame para la fila "Desde"

        tk.Label(frame_desde, text="Desde:").pack(side="left", padx=(50, 0))

        entry_horas_desde = tk.Entry(frame_desde, width=7)
        entry_horas_desde.pack(side="left")  # Entrar las horas

        label_colon_1 = tk.Label(frame_desde, text=":", font=("Arial", 12))
        label_colon_1.pack(side="left")

        entry_minutos_desde = tk.Entry(frame_desde, width=7)
        entry_minutos_desde.pack(side="left")  # Entrar los minutos

        # Fila 3: Hasta
        frame_hasta = tk.Frame(top)
        frame_hasta.pack(fill="x", pady=5)  # Empaquetar el frame para la fila "Hasta"

        tk.Label(frame_hasta, text="Hasta:").pack(side="left", padx=(50, 0))

        entry_horas_hasta = tk.Entry(frame_hasta, width=7)
        entry_horas_hasta.pack(side="left")  # Entrar las horas

        label_colon_2 = tk.Label(frame_hasta, text=":", font=("Arial", 12))
        label_colon_2.pack(side="left")

        entry_minutos_hasta = tk.Entry(frame_hasta, width=7)
        entry_minutos_hasta.pack(side="left")  # Entrar los minutos


        # Funciones para agregar y eliminar horarios (definir antes de los botones)
        def agregar_horario():
            materia = combo_materia.get()
            comision = combo_comision.get()
            dia = entry_dia.get()
            horasDesde = entry_horas_desde.get().strip() or "00"  # Asignar "00" si está vacío
            minutosDesde = entry_minutos_desde.get().strip() or "00"  # Asignar "00" si está vacío
            horasHasta = entry_horas_hasta.get().strip() or "00"  # Asignar "00" si está vacío
            minutosHasta = entry_minutos_hasta.get().strip() or "00"  # Asignar "00" si está vacío
            
            # Validar que las horas y minutos estén entre 00 y 23
            if (not (0 <= int(horasDesde) <= 23)) or (not (0 <= int(horasHasta) <= 23)):
                messagebox.showerror("Error", "Las horas debe estar entre 00 y 23")
                return
            
            if (not (0 <= int(minutosDesde) <= 59)) or (not (0 <= int(minutosHasta) <= 59)):
                messagebox.showerror("Error", "Los minutos deben estar entre 00 y 59")
                return
            # Convertir hora y minutos a formato decimal
            hora_decimal_desde = float(horasDesde) + float(minutosDesde) / 60.0
            hora_decimal_hasta = float(horasHasta) + float(minutosHasta) / 60.0

            # Verificar que los campos no estén vacíos
            if materia and comision and dia and horasDesde and minutosDesde and horasHasta and minutosHasta:
                materias[materia][comision].append((dia, hora_decimal_desde, hora_decimal_hasta))
                listbox.insert(tk.END, f"{dia}: {horasDesde}:{minutosDesde}-{horasHasta}:{minutosHasta}")
                actualizar_horarios()
                messagebox.showinfo("Éxito", "Horario agregado")
            else:
                messagebox.showerror("Error", "Datos inválidos")
            top.lift()
            top.focus_force()

        def eliminar_horario():
            materia = combo_materia.get()
            comision = combo_comision.get()
            seleccion = listbox.curselection()

            if materia and comision and seleccion:
                indice = seleccion[0]
                del materias[materia][comision][indice]
                actualizar_horarios()
                messagebox.showinfo("Éxito", "Horario eliminado")
            else:
                messagebox.showerror("Error", "Seleccione un horario para eliminar")
            top.lift()
            top.focus_force()

        # Botón para agregar y eliminar horario
        btn_frame = tk.Frame(top)
        btn_frame.pack(pady=1)

        tk.Button(btn_frame, text="Agregar Horario", command=agregar_horario).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Eliminar Horario", command=eliminar_horario).pack(side="left", padx=5)

        tk.Label(top, text="Si hay algún campo vacío, tomará el valor de 00").pack(pady=1)

        top.bind("<Return>", lambda e: agregar_horario())
        top.bind("<Delete>", lambda e: eliminar_horario())

    # Método para exportar los datos a un archivo JSON
    def exportar_json(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "w") as f:
                json.dump(materias, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Éxito", "Datos exportados correctamente")

    # Método para importar los datos desde un archivo JSON
    def importar_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, "r") as f:
                    global materias
                    materias = json.load(f)
                messagebox.showinfo("Éxito", "Datos importados correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al importar datos: {e}")

    # Método para alternar entre temas oscuro y claro
    def toggle_tema(self):
        if self.tema_actual == "darkly":
            self.tema_actual = "lumen"
            new_icon = "🌙"
        else:
            self.tema_actual = "darkly"
            new_icon = "🌞"
        self.style.theme_use(self.tema_actual)
        self.style.configure("Tema.TButton", font=("Arial", 20))
        self.style.configure("Github.TButton", font=("Arial", 20))
        self.btn_tema.config(text=new_icon, style="Tema.TButton")
        self.btn_github.config(style="Github.TButton")

    # Método para crear el menú de graficar horarios
    def menu_graficar(self):
        top = tk.Toplevel(self.root)
        top.title("Gráfico de Horarios")
        top.bind("<Escape>", cerrar_con_esc)
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=3)
        top.columnconfigure(1, weight=1)

        # Encontrar el horario de inicio más temprano
        horarios = [
            inicio
            for comisiones in materias.values()
            for horarios in comisiones.values()
            for _, inicio, _ in horarios
        ]
        earliest_start = min(horarios) if horarios else 8

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_xlim(earliest_start, 24)
        ax.set_xticks(np.arange(earliest_start, 24, 0.25))
        ax.set_xticklabels([f"{int(h)}:{int((h % 1) * 60):02d}" for h in np.arange(earliest_start, 24, 0.25)], rotation=80)
        ax.set_ylim(-0.5, 6.5)
        ax.set_yticks(range(7))
        ax.set_yticklabels(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sabado", "Domingo"])
        ax.set_xlabel("Hora")
        ax.set_ylabel("Día")
        ax.set_title("Horarios de Clases")

        for x in np.arange(earliest_start, 24, 0.25):
            ax.axvline(x, color='#27282b', linestyle='--', linewidth=1, alpha=0.80)

        dias = {"Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4, "Sabado": 5, "Domingo": 6}
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

        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Función para actualizar los solapamientos de horarios
        def actualizar_solapamientos():
            nonlocal solapamiento_patches
            for patch in solapamiento_patches:
                patch.remove()
            solapamiento_patches.clear()

            solapamientos = []
            for (materia, comision), rects in comisiones_rects.items():
                for bar in rects:
                    if bar.get_visible():
                        x, width, y = bar.get_x(), bar.get_width(), bar.get_y()
                        solapamientos.append((bar, x, x + width, y, materia))

            for bar, x1, x2, y, materia in solapamientos:
                bar.set_color(colores_materias[materia][0])

            for i, (bar1, x1_1, x2_1, y1, mat1) in enumerate(solapamientos):
                for j, (bar2, x1_2, x2_2, y2, mat2) in enumerate(solapamientos):
                    if i < j and y1 == y2 and x1_1 < x2_2 and x2_1 > x1_2:
                        if bar1.get_visible() and bar2.get_visible():
                            solapado_inicio = max(x1_1, x1_2)
                            solapado_fin = min(x2_1, x2_2)
                            ancho = solapado_fin - solapado_inicio
                            if ancho > 0:
                                rect = mpatches.Rectangle((solapado_inicio, y1 - 0.4), ancho, 0.8,
                                                        facecolor='red', hatch='//', edgecolor='black', zorder=5)
                                ax.add_patch(rect)
                                solapamiento_patches.append(rect)
            canvas.draw()

        for materia, comisiones in materias.items():
            for idx, (comision, horarios) in enumerate(comisiones.items()):
                color = colores_materias[materia][idx % len(colores_materias[materia])]
                comisiones_rects[(materia, comision)] = []
                for dia, inicio, fin in horarios:
                    dia_num = dias.get(dia, -1)
                    if dia_num >= 0:
                        rect = ax.barh(dia_num, fin - inicio, left=inicio, color=color, edgecolor="black")[0]
                        comisiones_rects[(materia, comision)].append(rect)

        actualizar_solapamientos()

        # Inicializar todas las materias y sus comisiones como visibles
        def inicializar_comisiones_visibles():
            global comisiones_visibles
            comisiones_visibles = []
            
            # Iterar sobre todas las materias y comisiones
            for materia, comisiones in materias.items():
                for comision in comisiones.keys():
                    comisiones_visibles.append((materia, comision))

        def toggle_comision(materia, comision, var):
            # Obtener el estado de visibilidad de la comisión
            visible = var.get()

            # Alternar la visibilidad de las barras correspondientes a la comisión
            for bar in comisiones_rects.get((materia, comision), []):
                bar.set_visible(visible)  # Alterna visibilidad

            # Actualizar el arreglo de comisiones visibles
            if visible:
                # Si es visible, agregar a la lista si no está ya
                if (materia, comision) not in comisiones_visibles:
                    comisiones_visibles.append((materia, comision))
            else:
                # Si no es visible, eliminar de la lista si está presente
                if (materia, comision) in comisiones_visibles:
                    comisiones_visibles.remove((materia, comision))

            # Asegurarse de que se actualicen correctamente los solapamientos si es necesario
            actualizar_solapamientos()

            # Redibujar el canvas solo si se está actualizando el estado de las barras
            canvas.draw()

        # Crear un marco para la leyenda de materias y comisiones
        legend_frame = tk.Frame(top, bg="white", padx=5, pady=5)
        legend_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Botón para exportar el gráfico
        btn_exportar = tk.Button(legend_frame, text="Exportar Gráfico", command=exportar_grafico)
        btn_exportar.pack(pady=5)

        # Configurar la disposición de filas y columnas del marco superior
        top.rowconfigure(0, weight=1)
        top.columnconfigure(1, weight=1)

        # Etiqueta para el título de la leyenda
        tk.Label(legend_frame, text="Materias y Comisiones", font=("Arial", 10, "bold"), bg="white").pack(pady=4)

        # Crear la leyenda para cada materia y sus comisiones
        for materia, comisiones in materias.items():
            # Obtener el color asignado a la materia
            color = matplotlib.colors.to_hex(colores_materias[materia][0])

            # Crear un marco principal para cada materia
            frame_principal = tk.Frame(legend_frame, bg="lightgray", padx=2, pady=1)
            frame_principal.pack(fill="x", padx=2, pady=1)

            # Crear un sub-marco para la materia
            materia_frame = tk.Frame(frame_principal, bg="white")
            materia_frame.pack(fill="x")

            # Crear un canvas para mostrar el color de la materia
            canvas_legend = tk.Canvas(materia_frame, width=15, height=15)
            canvas_legend.create_rectangle(0, 0, 15, 15, fill=color)
            canvas_legend.pack(side="left", padx=5)

            # Etiqueta para el nombre de la materia
            legend_patch = tk.Label(materia_frame, text=materia, bg="white", width=20, relief="ridge")
            legend_patch.pack(side="left", fill="x")

            # Crear un sub-marco para las comisiones de la materia
            comisiones_frame = tk.Frame(frame_principal, bg="white")
            comisiones_frame.pack(fill="x")

            # Crear un checkbox para cada comisión
            for comision in comisiones.keys():
                var = tk.BooleanVar(value=True)
                chk = tk.Checkbutton(comisiones_frame, text=comision, variable=var,
                                    command=lambda m=materia, c=comision, v=var: toggle_comision(m, c, v),
                                    bg="white")
                chk.pack(anchor="w", padx=2, pady=0)

        # Crear un parche para indicar la superposición de horarios
        superposicion_patch = mpatches.Patch(facecolor='red', hatch='//', edgecolor='black', label='Superposición de horarios')
        ax.legend(handles=[superposicion_patch], loc='upper right')

        inicializar_comisiones_visibles()
        # Redibujar el canvas
        canvas.draw()

    # Método para mostrar los horarios actuales en una nueva ventana
    def mostrar_horarios(self):
        top = tk.Toplevel(self.root)
        top.title("Horarios Actuales")
        top.bind("<Escape>", cerrar_con_esc)

        frame = tk.Frame(top)
        frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        text_area = tk.Text(frame, width=50, height=20, yscrollcommand=scrollbar.set)
        text_area.pack(fill="both", expand=True)
        scrollbar.config(command=text_area.yview)

        # Insertar los horarios en el área de texto
        for materia, comisiones in materias.items():
            text_area.insert(tk.END, f"{materia}\n")
            for comision, horarios in comisiones.items():
                text_area.insert(tk.END, f"  {comision}\n")
                for dia, inicio, fin in horarios:
                    text_area.insert(tk.END, f"    {dia} -> {inicio} - {fin}\n")

    # Método para crear el menú principal de la aplicación
    def crear_menu_principal(self):
        # Eliminar todos los widgets existentes en la ventana principal
        for widget in self.root.winfo_children():
            widget.destroy()

        frame = tb.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Crear un marco para la sección gráfica
        frame_graf = tb.Frame(frame, relief="solid", borderwidth=1)
        frame_graf.pack(fill="x", padx=5, pady=5)
        tb.Label(frame_graf, text="Graficamente", font=("Arial", 10, "bold")).pack(side="top", anchor="w", padx=5)
        
        botones_frame_graf = tb.Frame(frame_graf)
        botones_frame_graf.pack(fill="x")

        # Botón para graficar horarios
        btn_graficar = tb.Button(botones_frame_graf, text="Graficar horarios", command=self.menu_graficar, bootstyle="primary")
        btn_graficar.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        # Crear un marco para la sección textual
        frame_txt = tb.Frame(frame, relief="solid", borderwidth=1)
        frame_txt.pack(fill="x", padx=5, pady=5)
        tb.Label(frame_txt, text="Textualmente", font=("Arial", 10, "bold")).pack(side="top", anchor="w", padx=5)
        
        botones_frame_txt = tb.Frame(frame_txt)
        botones_frame_txt.pack(fill="x")

        # Botón para mostrar horarios
        btn_mostrar = tb.Button(botones_frame_txt, text="Mostrar horarios", command=self.mostrar_horarios, bootstyle="primary")
        btn_mostrar.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        # Crear un marco para la sección de ABM (Alta, Baja, Modificación)
        frame_abm = tb.Frame(frame, relief="solid", borderwidth=1)
        frame_abm.pack(fill="x", padx=5, pady=5)

        tb.Label(frame_abm, text="AB", font=("Arial", 10, "bold")).pack(side="top", anchor="w", padx=5)

        botones_frame_abm = tb.Frame(frame_abm)
        botones_frame_abm.pack(fill="x")

        # Botones para ABM de Materia, Comisión y Horarios
        for texto, comando in [
            ("AB Materia", self.menu_abm_materia),
            ("AB Comisión", self.menu_abm_comision),
            ("AB Horarios", self.menu_abm_horarios),
        ]:
            btn = tb.Button(botones_frame_abm, text=texto, command=comando, bootstyle="primary")
            btn.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        # Crear un marco para la sección de JSON
        frame_json = tb.Frame(frame, relief="solid", borderwidth=1)
        frame_json.pack(fill="x", padx=5, pady=5)

        tb.Label(frame_json, text="JSON", font=("Arial", 10, "bold")).pack(side="top", anchor="w", padx=5)

        botones_frame_json = tb.Frame(frame_json)
        botones_frame_json.pack(fill="x")

        # Botones para exportar e importar datos JSON
        for texto, comando in [
            ("Exportar Datos JSON", self.exportar_json),
            ("Importar Datos JSON", self.importar_json),
        ]:
            btn = tb.Button(botones_frame_json, text=texto, command=comando, bootstyle="primary")
            btn.pack(side="right", padx=5, pady=5, expand=True, fill="x")

        # Crear un marco para la sección de otros botones
        frame_otros = tb.Frame(frame, relief="solid", borderwidth=1)
        frame_otros.pack(fill="x", padx=5, pady=5)

        tb.Label(frame_otros, text="Otros", font=("Arial", 10, "bold")).pack(side="top", anchor="w", padx=5)

        botones_frame_otros = tb.Frame(frame_otros)
        botones_frame_otros.pack(fill="x")

        # Botón para alternar el tema de la aplicación
        self.btn_tema = tb.Button(botones_frame_otros, text="🌞", command=self.toggle_tema, style="Tema.TButton", bootstyle="primary")
        self.btn_tema.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        # Definir el texto del botón de GitHub
        github_button_text = "Fabros96" if self.github_icon else "@Fabros96"

        # Botón para abrir el perfil de GitHub
        self.btn_github = tb.Button(botones_frame_otros, text=github_button_text, image=self.github_icon, compound="left" if self.github_icon else "none", command=abrir_github, style="Github.TButton", bootstyle="success-link")
        self.btn_github.pack(side="left", padx=3, pady=3, expand=True, fill="x")

# Código principal para iniciar la aplicación
if __name__ == "__main__":
    # Crear la ventana principal con el tema del sistema
    root = tb.Window(themename=obtener_tema_sistema())
    # Crear una instancia de la clase HorarioGUI
    app = HorarioGUI(root)
    # Iniciar el bucle principal de la aplicación
    root.mainloop()