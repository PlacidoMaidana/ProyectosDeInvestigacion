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

































import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.font import Font
import os
from db_setup import connect_to_db
from list_manager import ListManager

class AnalysisFormEditor:
    def __init__(self, parent, document_id, db_path, mode, analysis_id=None):
        self.parent = parent
        self.document_id = document_id
        self.db_path = db_path
        self.mode = mode
        self.analysis_id = analysis_id
        self.archivo_path = ""
        
        # Configurar iconos (asegúrate de tener estos iconos en tu proyecto)
        self.icons = {
            'save': '💾',
            'file': '📎',
            'open': '📂',
            'edit': '✏️',
            'dimension': '📊'
        }
        
        self.create_window()
        self.create_widgets()
        self.load_initial_data()
        
        if self.mode == "edit":
            self.load_analysis()
    
    def create_window(self):
        """Crea la ventana principal del formulario"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Editor de Análisis")
        self.window.geometry("800x600")
        self.window.minsize(600, 400)
        self.window.transient(self.parent)
        
        # Configurar el grid principal
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
    
    def create_widgets(self):
        """Crea y organiza todos los widgets del formulario"""
        # Frame principal con padding
        main_frame = ttk.Frame(self.window, padding=15)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Título del formulario
        title_font = Font(size=12, weight="bold")
        ttk.Label(
            main_frame, 
            text="EDITOR DE ANÁLISIS", 
            font=title_font,
            foreground="#2c3e50"
        ).grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        # Dimensión
        ttk.Label(main_frame, text="Dimensión:").grid(
            row=1, column=0, sticky="w", pady=5
        )
        
        dimension_frame = ttk.Frame(main_frame)
        dimension_frame.grid(row=1, column=1, sticky="ew", pady=5)
        dimension_frame.columnconfigure(0, weight=1)
        
        self.combobox_dimensiones = ttk.Combobox(
            dimension_frame, 
            font=('Arial', 10),
            width=40
        )
        self.combobox_dimensiones.grid(row=0, column=0, sticky="ew")
        
        ttk.Button(
            dimension_frame,
            text=f" {self.icons['edit']} Editar dimensiones",
            command=lambda: ListManager().editar_lista_csv('dimensiones.csv', 'Dimensiones de Análisis'),
            style='TButton'
        ).grid(row=0, column=1, padx=(10, 0))
        
        # Archivo adjunto
        ttk.Label(main_frame, text="Archivo adjunto:").grid(
            row=2, column=0, sticky="w", pady=5
        )
        
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=2, column=1, sticky="ew", pady=5)
        file_frame.columnconfigure(0, weight=1)
        
        self.file_entry = ttk.Entry(file_frame, font=('Arial', 10))
        self.file_entry.grid(row=0, column=0, sticky="ew")
        
        ttk.Button(
            file_frame,
            text=f" {self.icons['file']} Seleccionar",
            command=self.select_file,
            style='TButton'
        ).grid(row=0, column=1, padx=(10, 0))
        
        ttk.Button(
            file_frame,
            text=f" {self.icons['open']} Abrir",
            command=self.open_file,
            style='TButton'
        ).grid(row=0, column=2, padx=(10, 0))
        
        # Descripción
        ttk.Label(main_frame, text="Descripción:").grid(
            row=3, column=0, sticky="nw", pady=5
        )
        
        desc_frame = ttk.Frame(main_frame)
        desc_frame.grid(row=3, column=1, sticky="nsew", pady=5)
        desc_frame.rowconfigure(0, weight=1)
        desc_frame.columnconfigure(0, weight=1)
        
        # Text widget con scrollbars
        self.desc_text = tk.Text(
            desc_frame, 
            wrap="word", 
            font=('Arial', 10),
            padx=10,
            pady=10,
            insertbackground='black',
            selectbackground='#3498db'
        )
        
        scroll_y = ttk.Scrollbar(desc_frame, orient="vertical", command=self.desc_text.yview)
        scroll_x = ttk.Scrollbar(desc_frame, orient="horizontal", command=self.desc_text.xview)
        self.desc_text.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )
        
        # Grid para el texto y scrollbars
        self.desc_text.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        
        # Botones de acción
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))
        
        Button(
            btn_frame,
            text=f" {self.icons['save']} Guardar Análisis",
            command=self.save_analysis,
            bg='#4CAF50',  # Fondo verde
            fg='black',     # Texto negro
            padx=10,
            pady=5
        ).pack(side=tk.RIGHT, padx=5)
        
        
        
        
        # Configurar estilo para el botón de guardar
        style = ttk.Style()
        style.configure('Accent.TButton', 
                      foreground='white', 
                      background='#27ae60',
                      font=('Arial', 10, 'bold'),
                      padding=6)
        style.map('Accent.TButton',
                background=[('active', '#2ecc71'), ('pressed', '#16a085')])
    
    def load_initial_data(self):
        """Carga las dimensiones desde el ListManager"""
        list_manager = ListManager()
        list_manager.inicializar_archivos_csv()
        dimensiones = list_manager.cargar_lista_desde_csv('dimensiones.csv')
        self.combobox_dimensiones['values'] = dimensiones
        self.combobox_dimensiones.set("Seleccionar" if dimensiones else "")
    
    def select_file(self):
        """Abre el diálogo para seleccionar un archivo"""
        file_path = filedialog.askopenfilename()
        if file_path:
            self.archivo_path = file_path
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, os.path.basename(file_path))
    
    def open_file(self):
        """Abre el archivo adjunto con el programa predeterminado"""
        if self.archivo_path and os.path.exists(self.archivo_path):
            try:
                os.startfile(self.archivo_path)  # Para Windows
            except AttributeError:
                import subprocess
                subprocess.run(['open', self.archivo_path])  # Para macOS
                # Para Linux podrías usar 'xdg-open'
        else:
            messagebox.showwarning("Advertencia", "No hay archivo adjunto o el archivo no existe")
    
    def load_analysis(self):
        """Carga los datos del análisis para edición"""
        conn = None
        try:
            conn = connect_to_db(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT dimension, descripcion, archivo FROM analisis WHERE id = ?",
                (self.analysis_id,)
            )
            result = cursor.fetchone()
            
            if result:
                self.combobox_dimensiones.set(result[0])
                self.desc_text.insert("1.0", result[1])
                if result[2]:
                    self.archivo_path = result[2]
                    self.file_entry.insert(0, os.path.basename(result[2]))
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def save_analysis(self):
        """Guarda el análisis en la base de datos"""
        dimension = self.combobox_dimensiones.get().strip()
        descripcion = self.desc_text.get("1.0", "end-1c").strip()
        
        if not dimension or dimension == "Seleccionar":
            messagebox.showwarning("Advertencia", "Debe seleccionar una dimensión")
            return
            
        conn = None
        try:
            conn = connect_to_db(self.db_path)
            cursor = conn.cursor()
            
            if self.mode == "create":
                cursor.execute(
                    """INSERT INTO analisis 
                    (documento_id, dimension, descripcion, archivo) 
                    VALUES (?, ?, ?, ?)""",
                    (self.document_id, dimension, descripcion, self.archivo_path)
                )
            else:
                cursor.execute(
                    """UPDATE analisis 
                    SET dimension = ?, descripcion = ?, archivo = ? 
                    WHERE id = ?""",
                    (dimension, descripcion, self.archivo_path, self.analysis_id)
                )
            
            conn.commit()
            messagebox.showinfo("Éxito", "Análisis guardado correctamente")
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {str(e)}")
        finally:
            if conn:
                conn.close()