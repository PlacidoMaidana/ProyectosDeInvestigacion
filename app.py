import tkinter as tk
from tkinter import Menu, filedialog, ttk, Label, Entry, Toplevel, Button, messagebox, Frame, Scrollbar, Text
from list_manager import ListManager
from db_setup import init_db, connect_to_db  # Importar lógica de base de datos
from analisis import AnalysisForm  # Archivo que maneja la ficha de análisis
from proyecto import ProyectoManager  # Importar el gestor de proyectos
from bib_importer import BibImporter
import sqlite3 

# Crear una instancia global (o puedes pasarla como parámetro)
list_manager = ListManager()

# Ventana principal
class App:
   
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Documentos y Análisis")        
        self.analysis_windows = {}  # Control de ventanas abiertas
        
        # Usa solo la variable de instancia, no la global
        self.current_db_path = "default_project.db"
        self.bib_importer = BibImporter(self.current_db_path)  # Pasar la ruta aquí
          
        
        # Inicializar archivos CSV al inicio del programa
        list_manager.inicializar_archivos_csv()
        
        # Menú principal
        self.menu_bar = Menu(self.root)
        self.root.config(menu=self.menu_bar)
         


        # Menú Archivo
        self.file_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Archivo", menu=self.file_menu)
        self.file_menu.add_command(label="Crear Nueva Base de Datos", command=self.create_new_database)  # Nuevo botón
        self.file_menu.add_command(label="Abrir...", command=self.open_database)
        self.file_menu.add_command(label="Guardar", command=self.save_database)
        self.file_menu.add_command(label="Guardar como...", command=self.save_database_as)
        
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Salir", command=self.root.quit)

        # Menú Proyecto
        self.project_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Proyecto", menu=self.project_menu)
        self.project_menu.add_command(label="Gestión de Proyectos", command=self.open_project_manager)

        # Menú Importaciones
        import_menu = tk.Menu(self.menu_bar, tearoff=0)
        import_menu.add_command(
            label="Importar desde BibTeX",
            command=self.import_from_bib,
            state=tk.DISABLED  # Inicialmente deshabilitado hasta abrir DB
        )
        self.menu_bar.add_cascade(label="Importaciones", menu=import_menu)
        
        self.root.config(menu=self.menu_bar)
        self.import_menu = import_menu  # Guardar referencia para actualizar estado


       # En la configuración inicial del Treeview (__init__):
        self.tree = ttk.Treeview(root, columns=("Cid", "CiteKey", "Title", "Author", "Year", "Etiqueta", "Cumplimiento", "ReferenciaAPA", "Actions"), show="headings")
        self.tree.heading("Cid", text="ID")
        self.tree.heading("CiteKey", text="CiteKey")
        self.tree.heading("Title", text="Título")
        self.tree.heading("Author", text="Autor")
        self.tree.heading("Year", text="Año")
        self.tree.heading("Etiqueta", text="Etiqueta")
        self.tree.heading("Cumplimiento", text="Cumplimiento de Criterios")
        self.tree.heading("ReferenciaAPA", text="Referencia APA")
        self.tree.heading("Actions", text="Acciones")

        # Configuración de columnas (sin cambios)
        self.tree.column("Cid", width=50, anchor="center")
        self.tree.column("CiteKey", width=100, anchor="center")
        self.tree.column("Title", width=200, anchor="center")
        self.tree.column("Author", width=150, anchor="center")
        self.tree.column("Year", width=80, anchor="center")
        self.tree.column("Etiqueta", width=100, anchor="center")
        self.tree.column("Cumplimiento", width=150, anchor="center")
        self.tree.column("ReferenciaAPA", width=200, anchor="center")
        self.tree.column("Actions", width=120, anchor="center")

        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.pack(fill=tk.BOTH, expand=True)

        
        
        
        # **Botones CRUD para documentos**
        self.crud_frame = tk.Frame(self.root)
        self.crud_frame.pack(pady=10)

        Button(self.crud_frame, text="Crear Documento", command=self.create_document).pack(side=tk.LEFT, padx=5)
        Button(self.crud_frame, text="Modificar Documento", command=self.update_document).pack(side=tk.LEFT, padx=5)
        Button(self.crud_frame, text="Eliminar Documento", command=self.delete_document).pack(side=tk.LEFT, padx=5)

    
    def create_new_database(self):
        db_path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite Database", "*.db")])
        if db_path:
            try:
                self.current_db_path = db_path
                init_db(self.current_db_path)
                self.bib_importer = BibImporter(self.current_db_path)  # Actualizar el importer
                self.import_menu.entryconfig(0, state=tk.NORMAL)  # Habilitar el menú
                self.load_documents()
                messagebox.showinfo("Éxito", f"Se creó una nueva base de datos: {db_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Hubo un problema al crear la base de datos: {e}")
    
    # Añade este nuevo método para manejar clics en el Treeview
    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        column = self.tree.identify_column(event.x)

        if region == "cell" and column == "#9":  # Asegúrate que sea la columna correcta (Actions)
            self.on_action_click(event)
            
    # Configurar clic en la columna de "Acciones"
    def on_action_click(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor selecciona un documento.")
            return

        try:
            document_id = self.tree.item(selected_item[0])["values"][0]

            # Verificar si la ventana ya está abierta
            if document_id in self.analysis_windows:
                existing_window = self.analysis_windows[document_id]
                if existing_window.winfo_exists():
                    existing_window.lift()
                    return
                else:
                    del self.analysis_windows[document_id]

            # Abrir nueva ventana de análisis con todos los parámetros necesarios
            analysis_window = AnalysisForm(self.root, document_id, current_db_path)
            self.analysis_windows[document_id] = analysis_window.window

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el análisis: {str(e)}")
                        
    def open_project_manager(self):
        ProyectoManager(self.root)        
                
    # Modifica el método load_documents:
    def load_documents(self):
        # Cargar documentos desde la base de datos y actualizar la grilla
        conn = connect_to_db(current_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT Cid, cite_key, title, author, year, etiqueta, cumplimiento_de_criterios, referencia_apa FROM documentos")
        rows = cursor.fetchall()
        conn.close()
    
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert("", "end", values=(*row, "📝 Analizar"))  # Icono añadido aquí
                
    # Configurar clic en la columna de "Acciones"
    def on_action_click(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor selecciona un documento.")
            return

        document_id = self.tree.item(selected_item[0])["values"][0]

        # Verificar si la ventana ya está abierta
        if document_id in self.analysis_windows:
            existing_window = self.analysis_windows[document_id]
            if existing_window.winfo_exists():
                existing_window.lift()  # Llevar la ventana al frente
                return
            else:
                del self.analysis_windows[document_id]  # Remover referencia si no existe

        # Abrir una nueva ventana de análisis
        analysis_window = AnalysisForm(self.root, document_id,current_db_path)
        self.analysis_windows[document_id] = analysis_window.window

        # Vincular clic en la columna "Acciones"
        self.tree.bind("<Button-1>", self.on_action_click)



    def open_database(self):
        db_path = filedialog.askopenfilename(filetypes=[("SQLite Database", "*.db")])
        if db_path:
            self.current_db_path = db_path
            init_db(self.current_db_path)
            self.bib_importer = BibImporter(self.current_db_path)  # Actualizar el importer
            self.load_documents()
            self.import_menu.entryconfig(0, state=tk.NORMAL)  # Habilitar el menú
            messagebox.showinfo("Éxito", f"Base de datos abierta: {db_path}")
            
    def save_database(self):
        """Guarda los cambios pendientes en la base de datos actual"""
        if not hasattr(self, 'current_db_path') or not self.current_db_path:
            messagebox.showwarning("Advertencia", "No hay una base de datos abierta actualmente.")
            return

        try:
            # Forzar guardado de todos los cambios pendientes
            print(f"la ruta de la base de datos en app {self.current_db_path}")
            conn = sqlite3.connect(self.current_db_path)
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Todos los cambios fueron guardados exitosamente.")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudieron guardar los cambios: {str(e)}")

        
    def save_database_as(self):
        global current_db_path
        db_path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite Database", "*.db")])
        if db_path:
            with connect_to_db(current_db_path) as old_conn, sqlite3.connect(db_path) as new_conn:
                old_conn.backup(new_conn)  # Copiar datos al nuevo archivo
            current_db_path = db_path
            messagebox.showinfo("Éxito", f"Base de datos guardada como: {db_path}")
            
    def import_from_bib(self):
        """Manejador para la importación BibTeX"""
        if not self.current_db_path:
            messagebox.showerror("Error", "Primero abra una base de datos")
            return

        try:
            # Usar with para manejo automático de recursos
            with BibImporter(self.current_db_path) as importer:
                imported_count = importer.import_bib_file(self.root)

                if imported_count > 0:
                    self.refresh_documents_list()
                    messagebox.showinfo("Éxito", f"Se importaron {imported_count} documentos")
                else:
                    messagebox.showinfo("Información", "No se importaron nuevos documentos")

        except Exception as e:
            messagebox.showerror("Error", f"Error durante la importación: {str(e)}")

        
    def refresh_documents_list(self):
        """Actualiza la lista de documentos con los datos más recientes"""
        try:
            # Limpiar el Treeview
            self.tree.delete(*self.tree.get_children())

            # Obtener conexión y cargar datos con manejo seguro
            conn = sqlite3.connect(self.current_db_path)
            cursor = conn.cursor()

            # Verificar estructura de la tabla
            cursor.execute("PRAGMA table_info(documentos)")
            columns = [column[1] for column in cursor.fetchall()]
            print("Columnas en la tabla documentos:", columns)  # Debug

            # Consulta segura con nombres de columnas explícitos
            safe_query = """
                SELECT "Cid", "cite_key", "title", "author", "year", 
                       "etiqueta", "cumplimiento_de_criterios", "referencia_apa" 
                FROM "documentos"
                ORDER BY "Cid" DESC
            """
            cursor.execute(safe_query)

            # Insertar los datos en el Treeview
            for row in cursor.fetchall():
                # Asegurar que todos los valores sean strings
                safe_row = [str(item) if item is not None else "" for item in row]
                self.tree.insert("", "end", values=(*safe_row, "📝 Analizar"))

            conn.close()

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudieron cargar los documentos: {str(e)}")
            # Debug adicional
            print("Consulta fallida:", safe_query)
            print("Error completo:", str(e))

        
    def create_document(self):
        # Abrir el formulario para crear un documento
        DocumentForm(self.root, mode="create")
    def update_document(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor selecciona un documento.")
            return

        try:
            item_values = self.tree.item(selected_item[0])["values"]
            if not item_values:
                messagebox.showerror("Error", "El documento seleccionado no tiene datos válidos.")
                return

            document_id = item_values[0]
            print(f"Preparando para editar documento ID: {document_id}")  # Debug

            # Pasar la referencia de la app principal al formulario
            form = DocumentForm(self.root, mode="edit", document_id=document_id)
            form.parent_app = self  # Esto permite acceder a current_db_path

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir para edición: {str(e)}")
            print("Error completo:", traceback.format_exc())
        
        
    def delete_document(self):
        """Elimina un documento seleccionado"""
        selected_item = self.tree.selection()

        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor selecciona un documento.")
            return

        try:
            item_values = self.tree.item(selected_item[0])["values"]

            if not item_values or len(item_values) < 1:
                messagebox.showerror("Error", "El documento seleccionado no tiene datos válidos.")
                return

            document_id = item_values[0]  # Cid es la primera columna

            # Confirmar antes de eliminar
            confirm = messagebox.askyesno(
                "Confirmar eliminación",
                f"¿Estás seguro de querer eliminar el documento con ID {document_id}?"
            )

            if not confirm:
                return

            conn = connect_to_db(self.current_db_path)  # Usar la variable de instancia
            cursor = conn.cursor()

            # Usar el nombre correcto de la columna (Cid)
            cursor.execute("DELETE FROM documentos WHERE Cid = ?", (document_id,))
            conn.commit()
            conn.close()

            self.load_documents()
            messagebox.showinfo("Éxito", "Documento eliminado exitosamente.")

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error de base de datos: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")
        
        
    def open_analysis_form(self, event):
        # Abrir la ficha de análisis para un documento seleccionado
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor selecciona un documento.")
            return

        document_id = self.tree.item(selected_item[0])["values"][0]

        if document_id in self.analysis_windows:  # Verificar si ya está abierta
            existing_window = self.analysis_windows[document_id]
            if existing_window.winfo_exists():
                existing_window.lift()  # Traer ventana al frente
                return
            else:
                del self.analysis_windows[document_id]  # Limpiar si la ventana no existe

        # Crear una nueva ventana de análisis
        analysis_window = AnalysisForm(self.root, document_id, current_db_path)
        self.analysis_windows[document_id] = analysis_window.window  # Guardar referencia

# Formulario para manejar creación y edición de documentos
class DocumentForm:
    def __init__(self, parent, mode, document_id=None):
        self.window = Toplevel(parent)
        self.window.title("Formulario Documento")
        self.mode = mode
        self.document_id = document_id

        print(f"es el valor de document id {document_id}")
        # Configurar grid principal
        self.window.grid_columnconfigure(0, weight=1)

        # Frame principal usando grid
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(1, weight=1)  # Hacer que la segunda columna se expanda

        # Estilo general
        padx_default = 10
        pady_default = 5
        entry_width = 50

        # Sección 1: Información básica
        ttk.Label(main_frame, text="Información Básica", font=('Helvetica', 12, 'bold')).grid(
            row=0, column=0, columnspan=2, pady=(0, 15), sticky="w")

        # CiteKey
        ttk.Label(main_frame, text="CiteKey:").grid(row=1, column=0, sticky="e", padx=padx_default, pady=pady_default)
        self.cite_key_entry = ttk.Entry(main_frame, width=entry_width)
        self.cite_key_entry.grid(row=1, column=1, sticky="ew", pady=pady_default)

        # Título
        ttk.Label(main_frame, text="Título:").grid(row=2, column=0, sticky="e", padx=padx_default, pady=pady_default)
        self.title_entry = ttk.Entry(main_frame, width=entry_width)
        self.title_entry.grid(row=2, column=1, sticky="ew", pady=pady_default)

        # Autor
        ttk.Label(main_frame, text="Autor:").grid(row=3, column=0, sticky="e", padx=padx_default, pady=pady_default)
        self.author_entry = ttk.Entry(main_frame, width=entry_width)
        self.author_entry.grid(row=3, column=1, sticky="ew", pady=pady_default)

        # Año
        ttk.Label(main_frame, text="Año:").grid(row=4, column=0, sticky="e", padx=padx_default, pady=pady_default)
        self.year_entry = ttk.Entry(main_frame, width=entry_width)
        self.year_entry.grid(row=4, column=1, sticky="ew", pady=pady_default)

        # Sección 2: Resumen
        ttk.Label(main_frame, text="Resumen", font=('Helvetica', 12, 'bold')).grid(
            row=5, column=0, columnspan=2, pady=(15, 5), sticky="w")

        self.abstract_text = Text(main_frame, wrap=tk.WORD, height=10, width=60, 
                                font=('Arial', 10), padx=5, pady=5)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.abstract_text.yview)
        self.abstract_text.configure(yscrollcommand=scrollbar.set)

        self.abstract_text.grid(row=6, column=0, columnspan=2, sticky="nsew", padx=padx_default)
        scrollbar.grid(row=6, column=2, sticky="ns")

        # Sección 3: Metadatos adicionales
        ttk.Label(main_frame, text="Metadatos Adicionales", font=('Helvetica', 12, 'bold')).grid(
            row=7, column=0, columnspan=2, pady=(15, 5), sticky="w")

        # Etiquetas
        ttk.Label(main_frame, text="Etiquetas:").grid(row=8, column=0, sticky="e", padx=padx_default, pady=pady_default)
        self.scolr_tags_entry = ttk.Entry(main_frame, width=entry_width)
        self.scolr_tags_entry.grid(row=8, column=1, sticky="ew", pady=pady_default)

        # Etiqueta (Combobox)
        # Inicializar archivos CSV al inicio del programa
        list_manager.inicializar_archivos_csv()
        ttk.Label(main_frame, text="Etiqueta:").grid(row=9, column=0, sticky="e", padx=padx_default, pady=pady_default)
        self.combobox_etiquetas = ttk.Combobox(main_frame, width=entry_width-3)  # Ajustar ancho
        self.combobox_etiquetas.grid(row=9, column=1, sticky="ew", pady=pady_default)

        # Botón para editar lista de etiquetas
        ttk.Button(main_frame, text="Editar lista de etiquetas", 
                  command=lambda: list_manager.editar_lista_csv('etiquetas.csv', 'Etiquetas')).grid(
                      row=10, column=0, columnspan=2, pady=pady_default)

        # Cumplimiento de Criterios
        ttk.Label(main_frame, text="Cumplimiento:").grid(row=11, column=0, sticky="e", padx=padx_default, pady=pady_default)
        self.cumplimiento_entry = ttk.Entry(main_frame, width=entry_width)
        self.cumplimiento_entry.grid(row=11, column=1, sticky="ew", pady=pady_default)

        # Referencia APA
        ttk.Label(main_frame, text="Referencia APA:").grid(row=12, column=0, sticky="e", padx=padx_default, pady=pady_default)
        self.referencia_apa_entry = ttk.Entry(main_frame, width=entry_width)
        self.referencia_apa_entry.grid(row=12, column=1, sticky="ew", pady=pady_default)

        # Botón Guardar
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=13, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(button_frame, text="Guardar", command=self.save_document).pack(pady=10, ipadx=20)

        # Configuración de grid para expansión
        main_frame.rowconfigure(6, weight=1)  # Hacer que la fila del resumen se expanda

        if self.mode == "edit":
            self.load_document()

        # Cargar combobox después de inicializar
        list_manager.actualizar_combobox(self.combobox_etiquetas, 'etiquetas.csv')

    def load_document(self):
        if not self.document_id:
            print("Error: No hay document_id definido")
            return

        try:
            # Usar connect_to_db en lugar de sqlite3.connect directamente
            conn = connect_to_db(current_db_path)
            cursor = conn.cursor()

            print(f"Consultando documento con ID: {self.document_id}")

            cursor.execute("""
                SELECT cite_key, title, author, year, abstract, 
                       scolr_tags, etiqueta, cumplimiento_de_criterios, referencia_apa 
                FROM documentos 
                WHERE Cid = ?
            """, (self.document_id,))

            document = cursor.fetchone()
            conn.close()

            if not document:
                print("Error: No se encontró el documento con ID:", self.document_id)
                return

            print("Datos recuperados:", document)

            # Limpiar campos primero
            self.cite_key_entry.delete(0, tk.END)
            self.title_entry.delete(0, tk.END)
            self.author_entry.delete(0, tk.END)
            self.year_entry.delete(0, tk.END)
            self.abstract_text.delete("1.0", tk.END)
            self.scolr_tags_entry.delete(0, tk.END)
            self.combobox_etiquetas.set('')
            self.cumplimiento_entry.delete(0, tk.END)
            self.referencia_apa_entry.delete(0, tk.END)

            # Llenar campos (convertir None a string vacío)
            self.cite_key_entry.insert(0, document[0] or "")
            self.title_entry.insert(0, document[1] or "")
            self.author_entry.insert(0, document[2] or "")
            self.year_entry.insert(0, str(document[3]) if document[3] is not None else "")
            self.abstract_text.insert("1.0", document[4] or "")
            self.scolr_tags_entry.insert(0, document[5] or "")
            self.combobox_etiquetas.set(document[6] or "")
            self.cumplimiento_entry.insert(0, document[7] or "")
            self.referencia_apa_entry.insert(0, document[8] or "")

        except Exception as e:
            print(f"Error al cargar documento: {str(e)}")
            messagebox.showerror("Error", f"No se pudo cargar el documento: {str(e)}")

        
            
    def save_document(self):
        # Obtener todos los valores del formulario
        cite_key = self.cite_key_entry.get()
        title = self.title_entry.get()
        author = self.author_entry.get()
        year = self.year_entry.get()
        abstract = self.abstract_text.get("1.0", tk.END).strip()
        scolr_tags = self.scolr_tags_entry.get()
        etiqueta = self.combobox_etiquetas.get()
        cumplimiento = self.cumplimiento_entry.get()
        referencia_apa = self.referencia_apa_entry.get()

        # Validación básica de campos requeridos
        if not all([cite_key, title, author, year]):
            messagebox.showwarning("Advertencia", "Por favor complete los campos obligatorios: CiteKey, Título, Autor y Año")
            return

        conn = None
        try:
            conn = connect_to_db(current_db_path)
            cursor = conn.cursor()

            if self.mode == "create":
                cursor.execute("""
                    INSERT INTO documentos (cite_key, title, author, year, abstract, 
                                        scolr_tags, etiqueta, cumplimiento_de_criterios, referencia_apa)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (cite_key, title, author, year, abstract, scolr_tags, etiqueta, cumplimiento, referencia_apa))
                messagebox.showinfo("Éxito", "Documento creado exitosamente.")
            elif self.mode == "edit":
                cursor.execute("""
                    UPDATE documentos
                    SET cite_key = ?, title = ?, author = ?, year = ?, abstract = ?, 
                        scolr_tags = ?, etiqueta = ?, cumplimiento_de_criterios = ?, referencia_apa = ?
                    WHERE Cid = ?
                """, (cite_key, title, author, year, abstract, scolr_tags, etiqueta, cumplimiento, referencia_apa, self.document_id))
                messagebox.showinfo("Éxito", "Documento actualizado exitosamente.")

            conn.commit()

            # Actualizar la lista de documentos en la ventana principal
            app_instance = self.window.master._app_instance
            if app_instance:
                app_instance.load_documents()

            self.window.destroy()

        except sqlite3.Error as e:
            messagebox.showerror("Error de Base de Datos", f"No se pudo guardar el documento: {str(e)}")
            if conn:
                conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {str(e)}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
                
                
# Ejecutar la aplicación
# Modifica la creación de la aplicación principal para exponer la instancia
if __name__ == "__main__":
    current_db_path = "default_project.db"
    init_db(current_db_path)
    root = tk.Tk()
    app = App(root)
    root._app_instance = app  # Hacer accesible la instancia de App
    root.mainloop()