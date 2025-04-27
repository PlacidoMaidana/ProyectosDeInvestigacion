import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import Toplevel, Label, Entry, Button, Frame, Scrollbar, Text
from db_setup import connect_to_db
from list_manager import ListManager

# Crear una instancia global (o puedes pasarla como parámetro)
list_manager = ListManager()

class AnalysisForm:
    def __init__(self, parent, document_id, db_path):
        self.parent = parent
        self.document_id = document_id
        self.db_path = db_path
        self.window = Toplevel(parent)
        self.window.title(f"Análisis del Documento ID: {document_id}")
        
        # Configuración de tamaño y redimensionamiento
        self.window.geometry("800x600")
        self.window.minsize(600, 400)
        
        # Frame principal
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview con scrollbars
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Inicializar archivos CSV al inicio del programa
        list_manager.inicializar_archivos_csv()
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        x_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        # Configuración del Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Dimension", "Descripcion"),
            show="headings",
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set
        )
        
        # Configurar columnas
        self.tree.heading("ID", text="ID", anchor=tk.CENTER)
        self.tree.heading("Dimension", text="Dimensión", anchor=tk.CENTER)
        self.tree.heading("Descripcion", text="Descripción", anchor=tk.CENTER)
        
        self.tree.column("ID", width=50, anchor=tk.CENTER)
        self.tree.column("Dimension", width=150, anchor=tk.W)
        self.tree.column("Descripcion", width=500, anchor=tk.W)
        
        # Empacar scrollbars y treeview
        y_scroll.config(command=self.tree.yview)
        x_scroll.config(command=self.tree.xview)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Frame para botones CRUD
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            button_frame, 
            text="Crear Análisis", 
            command=self.create_analysis
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Modificar Análisis", 
            command=self.update_analysis
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Eliminar Análisis", 
            command=self.delete_analysis
        ).pack(side=tk.LEFT, padx=5)
        
        # Cargar datos iniciales
        self.load_analysis()
        
        # Manejar cierre de ventana
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.window.focus_set()  # Asegurar foco en esta ventana

    def load_analysis(self):
        """Cargar análisis desde la base de datos"""
        # Limpiar el treeview completamente
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        conn = None
        try:
            conn = connect_to_db(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, dimension, descripcion FROM analisis WHERE documento_id = ?",
                (self.document_id,)
            )
            
            # Insertar filas con formato adecuado
            for row in cursor.fetchall():
                self.tree.insert("", tk.END, values=row)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar análisis: {str(e)}")
        finally:
            if conn:
                conn.close()

    def create_analysis(self):
        """Abrir formulario para crear nuevo análisis"""
        editor = AnalysisFormEditor(
            self.window, 
            self.document_id, 
            self.db_path, 
            mode="create"
        )
        self.window.wait_window(editor.window)  # Esperar hasta que se cierre
        self.load_analysis()  # Refrescar datos
        self.window.focus_set()  # Recuperar foco

    def update_analysis(self):
        """Abrir formulario para editar análisis existente"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un análisis")
            return
            
        analysis_id = self.tree.item(selected[0])["values"][0]
        editor = AnalysisFormEditor(
            self.window,
            self.document_id,
            self.db_path,
            mode="edit",
            analysis_id=analysis_id
        )
        self.window.wait_window(editor.window)  # Esperar hasta que se cierre
        self.load_analysis()  # Refrescar datos
        self.window.focus_set()  # Recuperar foco

    def delete_analysis(self):
        """Eliminar análisis seleccionado"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un análisis")
            return
            
        if not messagebox.askyesno("Confirmar", "¿Eliminar este análisis?"):
            return
            
        analysis_id = self.tree.item(selected[0])["values"][0]
        conn = None
        try:
            conn = connect_to_db(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM analisis WHERE id = ?", (analysis_id,))
            conn.commit()
            self.load_analysis()  # Refrescar datos
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar: {str(e)}")
        finally:
            if conn:
                conn.close()

    def on_close(self):
        """Manejar cierre de ventana"""
        self.window.destroy()
        if hasattr(self.parent, 'focus_set'):
            self.parent.focus_set()


class AnalysisFormEditor:
    def __init__(self, parent, document_id, db_path, mode, analysis_id=None):
        self.parent = parent
        self.document_id = document_id
        self.db_path = db_path
        self.mode = mode
        self.analysis_id = analysis_id
        
        self.window = Toplevel(parent)
        self.window.title("Editor de Análisis")
        self.window.geometry("600x400")
        self.window.transient(parent)  # Establecer relación padre-hijo
        
        # Frame principal
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Inicializar archivos CSV al inicio del programa
        list_manager.inicializar_archivos_csv()
        
        # Por esto:
        ttk.Label(main_frame, text="Dimensión:").grid(row=0, column=0, sticky="w", pady=5)
        self.combobox_dimensiones = ttk.Combobox(main_frame, width=47)  # Ajustar ancho similar al Entry
        self.combobox_dimensiones.grid(row=0, column=1, sticky="ew", pady=5)

        # Botón para editar lista de dimensiones
        ttk.Button(main_frame, text="Editar lista de dimensiones",
                  command=lambda: list_manager.editar_lista_csv('dimensiones.csv', 'Dimensiones de Análisis')
                  ).grid(row=1, column=0, columnspan=2, pady=5)
        
        # Descripción
        ttk.Label(main_frame, text="Descripción:").grid(row=1, column=0, sticky="nw", pady=5)
        
        desc_frame = ttk.Frame(main_frame)
        desc_frame.grid(row=1, column=1, sticky="nsew")
        
        self.desc_text = Text(desc_frame, wrap="word", height=10)
        scrollbar = ttk.Scrollbar(desc_frame, orient="vertical", command=self.desc_text.yview)
        self.desc_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.desc_text.pack(side="left", fill="both", expand=True)
        
        # Botón Guardar
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Guardar", command=self.save_analysis).pack(padx=5)
        
        # Configurar grid
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Cargar datos si es edición
        if self.mode == "edit":
            self.load_analysis()
        
        self.window.focus_set()

    def load_analysis(self):
        """Cargar datos del análisis para edición"""
        conn = None
        try:
            conn = connect_to_db(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT dimension, descripcion FROM analisis WHERE id = ?",
                (self.analysis_id,)
            )
            result = cursor.fetchone()
            
            if result:
                self.combobox_dimensiones.set(result[0])
                self.desc_text.insert("1.0", result[1])
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos: {str(e)}")
        finally:
            if conn:
                conn.close()

    def save_analysis(self):
        """Guardar el análisis en la base de datos"""
        dimension = self.combobox_dimensiones.get().strip()
        descripcion = self.desc_text.get("1.0", "end-1c").strip()
        
        if not dimension:
            messagebox.showwarning("Advertencia", "La dimensión no puede estar vacía")
            return
            
        conn = None
        try:
            conn = connect_to_db(self.db_path)
            cursor = conn.cursor()
            
            if self.mode == "create":
                cursor.execute(
                    "INSERT INTO analisis (documento_id, dimension, descripcion) VALUES (?, ?, ?)",
                    (self.document_id, dimension, descripcion)
                )
            else:
                cursor.execute(
                    "UPDATE analisis SET dimension = ?, descripcion = ? WHERE id = ?",
                    (dimension, descripcion, self.analysis_id)
                )
            
            conn.commit()
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {str(e)}")
        finally:
            if conn:
                conn.close()