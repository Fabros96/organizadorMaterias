#FALTA TEMA OSCURO con Boton incluido y Ordenar mejor el menu principal

from tkinter import ttk
from tkinter import ttk, messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog, messagebox
import tkinter as tk 
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import json
import matplotlib
import matplotlib.colors

# Estructuras de datos
materias = {}
colores_materias = {}
colores_base = ["PiYG", "PuBu", "winter", "vanimo", "hsv", "cool", "inferno_r"]
indice_color = 0

def cerrar_con_esc(event):
    event.widget.destroy()

class HorarioGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Horarios")
        self.crear_menu_principal()

    def crear_menu_principal(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        opciones = [
            ("Graficar horarios", self.menu_graficar),
            ("Mostrar horarios", self.mostrar_ocultar_horarios),
            ("ABM Materia", self.menu_abm_materia),
            ("ABM Comisión", self.menu_abm_comision),
            ("ABM Horarios", self.menu_abm_horarios),
            ("Exportar Datos JSON", self.exportar_json),
            ("Importar Datos JSON", self.importar_json)
        ]

        for texto, comando in opciones:
            btn = tk.Button(frame, text=texto, command=comando)
            btn.pack(fill="x", padx=5, pady=5, expand=True)

    def menu_graficar(self):
        top = tk.Toplevel(self.root)
        top.title("Gráfico de Horarios")
        top.bind("<Escape>", cerrar_con_esc)

        # Configurar el layout para que se expanda correctamente
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=3)  # Más espacio para el gráfico
        top.columnconfigure(1, weight=1)  # Menos espacio para la leyenda

        # Crear el gráfico
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_xlim(12, 24)
        ax.set_xticks(np.arange(12, 24, 0.25))
        ax.set_xticklabels([f"{int(h)}:{int((h % 1) * 60):02d}" for h in np.arange(12, 24, 0.25)], rotation=80)
        ax.set_ylim(-0.5, 6.5)
        ax.set_yticks(range(7))
        ax.set_yticklabels(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
        ax.set_xlabel("Hora")
        ax.set_ylabel("Día")
        ax.set_title("Horarios de Clases")

        # Líneas de referencia verticales cada 15 minutos
        for x in np.arange(12, 24, 0.25):
            ax.axvline(x, color='gray', linestyle='--', linewidth=1, alpha=0.5)

        dias = {"Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4, "Sábado": 5, "Domingo": 6}
        ocupacion = {}
        comisiones_rects = {}
        solapamiento_patches = []

        global indice_color
        for materia in materias.keys():
            if materia not in colores_materias:
                base_color = colores_base[indice_color % len(colores_base)]
                indice_color += 1
                colores_materias[materia] = [
                    matplotlib.colormaps.get_cmap(base_color)(0.2 + 0.6 * i / 5) for i in range(5)
                ]

        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

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

        def toggle_comision(materia, comision, var):
            visible = var.get()
            for bar in comisiones_rects.get((materia, comision), []):
                bar.set_visible(visible)
            actualizar_solapamientos()
            canvas.draw()

        # Crear la leyenda en un Frame separado y que se expanda correctamente
        legend_frame = tk.Frame(top, bg="white", padx=5, pady=5)
        legend_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Configurar para que la leyenda se expanda correctamente
        top.rowconfigure(0, weight=1)
        top.columnconfigure(1, weight=1)

        tk.Label(legend_frame, text="Materias y Comisiones", font=("Arial", 10, "bold"), bg="white").pack(pady=5)

        for materia, comisiones in materias.items():
            color = matplotlib.colors.to_hex(colores_materias[materia][0])
            legend_patch = tk.Label(legend_frame, text=materia, bg=color, fg="white", width=20, relief="ridge")
            legend_patch.pack(pady=2, fill="x")

            for comision in comisiones.keys():
                var = tk.BooleanVar(value=True)
                chk = tk.Checkbutton(legend_frame, text=comision, variable=var,
                                    command=lambda m=materia, c=comision, v=var: toggle_comision(m, c, v),
                                    bg="white")
                chk.pack(anchor="w", padx=10)

        canvas.draw()



    def mostrar_ocultar_horarios(self):
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

        for materia, comisiones in materias.items():
            text_area.insert(tk.END, f"{materia}\n")
            for comision, horarios in comisiones.items():
                text_area.insert(tk.END, f"  {comision}\n")
                for dia, inicio, fin in horarios:
                    text_area.insert(tk.END, f"    {dia} -> {inicio} - {fin}\n")

    def exportar_json(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "w") as f:
                json.dump(materias, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Éxito", "Datos exportados correctamente")

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
        
    def menu_abm_materia(self):
        top = tk.Toplevel(self.root)
        top.title("ABM Materias")
        top.bind("<Escape>", cerrar_con_esc)

        tk.Label(top, text="Materias Existentes:").pack()
        listbox = tk.Listbox(top)
        listbox.pack()
        for materia in materias.keys():
            listbox.insert(tk.END, materia)

        frame = tk.Frame(top)
        frame.pack()
        tk.Label(frame, text="Nombre Materia:").grid(row=0, column=0)
        entry_materia = tk.Entry(frame)
        entry_materia.grid(row=0, column=1)

        def agregar_materia():
            nombre = entry_materia.get()
            if nombre and nombre not in materias:
                materias[nombre] = {}
                listbox.insert(tk.END, nombre)
                messagebox.showinfo("Éxito", "Materia agregada")
            else:
                messagebox.showerror("Error", "Nombre inválido o ya existente")
            top.lift()

        btn_agregar = tk.Button(frame, text="Agregar", command=agregar_materia)
        btn_agregar.grid(row=1, columnspan=2)

        def eliminar_materia():
            seleccion = listbox.curselection()
            if seleccion:
                materia = listbox.get(seleccion)
                del materias[materia]
                listbox.delete(seleccion)
                messagebox.showinfo("Éxito", "Materia eliminada")
                top.lift()

        btn_eliminar = tk.Button(frame, text="Eliminar", command=eliminar_materia)
        btn_eliminar.grid(row=2, columnspan=2)

        top.bind("<Return>", lambda e: agregar_materia())
        top.bind("<Delete>", lambda e: eliminar_materia())

    def menu_abm_comision(self):
        top = tk.Toplevel(self.root)
        top.title("ABM Comisiones")
        top.bind("<Escape>", cerrar_con_esc)

        tk.Label(top, text="Seleccione una Materia:").pack()
        combo_materia = ttk.Combobox(top, values=list(materias.keys()))
        combo_materia.pack()

        listbox = tk.Listbox(top)
        listbox.pack()

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
        entry_comision.grid(row=0, column=1)

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

        btn_agregar = tk.Button(frame, text="Agregar Comisión", command=agregar_comision)
        btn_agregar.grid(row=1, columnspan=2)

        def eliminar_comision():
            materia = combo_materia.get()
            seleccion = listbox.curselection()
            if seleccion:
                comision = listbox.get(seleccion)
                del materias[materia][comision]
                listbox.delete(seleccion)
                messagebox.showinfo("Éxito", "Comisión eliminada")
                top.lift()

        btn_eliminar = tk.Button(frame, text="Eliminar Comisión", command=eliminar_comision)
        btn_eliminar.grid(row=2, columnspan=2)

        top.bind("<Return>", lambda e: agregar_comision())
        top.bind("<Delete>", lambda e: eliminar_comision())

    def menu_abm_horarios(self):
        top = tk.Toplevel(self.root)
        top.title("ABM Horarios")
        top.bind("<Escape>", cerrar_con_esc)

        tk.Label(top, text="Seleccione Materia:").pack()
        combo_materia = ttk.Combobox(top, values=list(materias.keys()))
        combo_materia.pack()

        tk.Label(top, text="Seleccione Comisión:").pack()
        combo_comision = ttk.Combobox(top)
        combo_comision.pack()

        def actualizar_comisiones():
            materia = combo_materia.get()
            combo_comision['values'] = list(materias.get(materia, {}).keys())

        def actualizar_horarios():
            """Actualiza la lista de horarios en la listbox según la materia y comisión seleccionadas"""
            materia = combo_materia.get()
            comision = combo_comision.get()
            
            listbox.delete(0, tk.END)  # Borra la lista actual

            if materia and comision and materia in materias and comision in materias[materia]:
                for dia, inicio, fin in materias[materia][comision]:
                    listbox.insert(tk.END, f"{dia}: {inicio}-{fin}")  # Muestra solo los horarios de la combinación seleccionada

        combo_materia.bind("<<ComboboxSelected>>", lambda e: (actualizar_comisiones(), actualizar_horarios()))
        combo_comision.bind("<<ComboboxSelected>>", lambda e: actualizar_horarios())


        listbox = tk.Listbox(top)
        listbox.pack()

        frame = tk.Frame(top)
        frame.pack()
        tk.Label(frame, text="Día:").grid(row=0, column=0)
        tk.Label(frame, text="Desde (hora decimal, ej. 14.5 para 14:30):").grid(row=1, column=0)
        tk.Label(frame, text="Hasta:").grid(row=2, column=0)

        entry_dia = ttk.Combobox(frame, values=["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado"])
        entry_dia.grid(row=0, column=1)
        entry_inicio = tk.Entry(frame)
        entry_inicio.grid(row=1, column=1)
        entry_fin = tk.Entry(frame)
        entry_fin.grid(row=2, column=1)

        def agregar_horario():
            materia = combo_materia.get()
            comision = combo_comision.get()
            dia = entry_dia.get()
            inicio = entry_inicio.get()
            fin = entry_fin.get()

            if materia and comision and dia and inicio and fin:
                materias[materia][comision].append((dia, float(inicio), float(fin)))
                listbox.insert(tk.END, f"{dia}: {inicio}-{fin}")
                actualizar_horarios()
                messagebox.showinfo("Éxito", "Horario agregado")
            else:
                messagebox.showerror("Error", "Datos inválidos")
            top.lift()

        btn_agregar = tk.Button(frame, text="Agregar Horario", command=agregar_horario)
        btn_agregar.grid(row=3, columnspan=2)

        def eliminar_horario():
            materia = combo_materia.get()
            comision = combo_comision.get()
            seleccion = listbox.curselection()

            if materia and comision and seleccion:
                indice = seleccion[0]  # Obtener el índice seleccionado
                del materias[materia][comision][indice]  # Eliminar de la estructura de datos
                actualizar_horarios()  # Refrescar la lista de horarios en la interfaz
                messagebox.showinfo("Éxito", "Horario eliminado")
            else:
                messagebox.showerror("Error", "Seleccione un horario para eliminar")
            top.lift()


        btn_eliminar = tk.Button(frame, text="Eliminar Horario", command=eliminar_horario)
        btn_eliminar.grid(row=4, columnspan=2)

        top.bind("<Return>", lambda e: agregar_horario())
        top.bind("<Delete>", lambda e: eliminar_horario())
        
if __name__ == "__main__":
    root = tk.Tk()
    app = HorarioGUI(root)
    root.mainloop()
