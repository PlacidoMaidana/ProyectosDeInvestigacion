import tkinter as tk
from tkinter import Menu, filedialog, ttk, Label, Entry, Toplevel, Button, messagebox, Frame, Scrollbar, Text
from tkinter.font import Font
import sqlite3
from list_manager import ListManager
from IA_analisis import copiar_analisis_como_csv

class AnalysisGrid:
    def __init__(self, parent, db_path):
        self.parent = parent  # Clase App
        self.db_path = db_path
        
       
        
        self.create_window()
        self.create_widgets()
        self.load_dimensions()
        self.load_analysis()
        
    def create_window(self):
        """Configura la ventana principal"""
        self.window = tk.Toplevel(self.parent.master)
        self.window.title("Análisis de Documentos")
        self.window.geometry("1000x600")
        self.window.minsize(800, 400)
    
        # Configuración de expansión dinámica
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=1)  # La fila 1 será para el Treeview
     
        
    def create_widgets(self):
        """Crea todos los widgets de la interfaz"""
        # Frame de controles
        control_frame = ttk.Frame(self.window, padding=10)
        control_frame.grid(row=0, column=0, sticky="ew")
        control_frame.columnconfigure(1, weight=1)
        
        # Filtro por dimensión
        ttk.Label(control_frame, text="Filtrar por dimensión:").grid(row=0, column=0, padx=5, sticky="w")
        
        self.dimension_var = tk.StringVar()
        self.dimension_cb = ttk.Combobox(
            control_frame, 
            textvariable=self.dimension_var,
            state="readonly"
        )
        self.dimension_cb.grid(row=0, column=1, padx=5, sticky="ew")
        self.dimension_cb.bind("<<ComboboxSelected>>", lambda e: self.load_analysis())
        
        ttk.Button(
            control_frame,
            text="Mostrar todos",
            command=lambda: [self.dimension_var.set(""), self.load_analysis()]
        ).grid(row=0, column=2, padx=5)
        
        # Frame de la grilla
        grid_frame = ttk.Frame(self.window)
        grid_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.rowconfigure(0, weight=1)  # Permite que el Treeview se expanda 
        
        
        
        # Treeview con scrollbars
        self.tree = ttk.Treeview(
        grid_frame,
        columns=("id", "cite_key", "title", "dimension", "descripcion"),
        show="headings",
        selectmode="extended"  # Permite selección múltiple
        )
        
        # Configurar columnas
        self.tree.heading("id", text="ID", anchor="w")
        self.tree.heading("cite_key", text="Cite Key", anchor="w")
        self.tree.heading("title", text="Título", anchor="w")
        self.tree.heading("dimension", text="Dimensión", anchor="w")
        self.tree.heading("descripcion", text="Descripción", anchor="w")
        
        self.tree.column("id", width=50, stretch=False)
        self.tree.column("cite_key", width=100, stretch=False)
        self.tree.column("title", width=200)
        self.tree.column("dimension", width=150, stretch=False)
        self.tree.column("descripcion", width=400)
        
        # Scrollbars
        vsb = ttk.Scrollbar(grid_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(grid_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Menú contextual
        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.context_menu.add_command(
            label="Copiar selección como CSV",
            command=lambda: copiar_analisis_como_csv(self.tree, self.db_path, self.window)
        )
        
        self.tree.bind("<Button-3>", self.show_context_menu)
        
    def show_context_menu(self, event):
        """Muestra el menú contextual al hacer clic derecho"""
        # Identificar el registro bajo el cursor
        item = self.tree.identify_row(event.y)
        if item not in self.tree.selection():  # Evitar deseleccionar si ya está seleccionado
            self.tree.selection_set(item)
    
        # Mostrar el menú contextual
        self.context_menu.post(event.x_root, event.y_root)
        
    def load_dimensions(self):
        """Carga las dimensiones disponibles desde ListManager"""
        list_manager = ListManager()
        dimensions = list_manager.cargar_lista_desde_csv('dimensiones.csv')[1:]  # Excluye "Seleccionar"
        self.dimension_cb['values'] = [""] + sorted(dimensions)
        
    def load_analysis(self):
        """Carga los análisis según el filtro seleccionado"""
        dimension = self.dimension_var.get()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if dimension:
                query = """
                    SELECT a.id, d.cite_key, d.title, a.dimension, 
                           substr(a.descripcion, 1, 100) || '...' as desc_short
                    FROM analisis a
                    JOIN documentos d ON a.documento_id = d.Cid
                    WHERE a.dimension = ?
                    ORDER BY d.cite_key
                """
                cursor.execute(query, (dimension,))
            else:
                query = """
                    SELECT a.id, d.cite_key, d.title, a.dimension, 
                           substr(a.descripcion, 1, 100) || '...' as desc_short
                    FROM analisis a
                    JOIN documentos d ON a.documento_id = d.Cid
                    ORDER BY a.dimension, d.cite_key
                """
                cursor.execute(query)
            
            # Limpiar treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # Insertar nuevos datos
            for row in cursor.fetchall():
                self.tree.insert("", "end", values=row)
                
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al cargar análisis: {e}")
        finally:
            if conn:
                conn.close()