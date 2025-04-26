import tkinter as tk
from tkinter import Menu, filedialog, ttk, Label, Entry, Toplevel, Button, messagebox, Frame, Scrollbar, Text

from db_setup import init_db, connect_to_db  # Importar lógica de base de datos
from analisis import AnalysisForm  # Archivo que maneja la ficha de análisis
from proyecto import ProyectoManager  # Importar el gestor de proyectos

# Ventana principal
class App:
   
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Documentos y Análisis")        
        self.analysis_windows = {}  # Control de ventanas abiertas
        
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

        # Configuración de la grilla con las columnas necesarias
        self.tree = ttk.Treeview(root, columns=("Cid", "CiteKey", "Title", "Author", "Year", "Etiqueta", "Cumplimiento", "Actions"), show="headings")
        self.tree.heading("Cid", text="ID")
        self.tree.heading("CiteKey", text="CiteKey")
        self.tree.heading("Title", text="Título")
        self.tree.heading("Author", text="Autor")
        self.tree.heading("Year", text="Año")
        self.tree.heading("Etiqueta", text="Etiqueta")  # Nueva columna
        self.tree.heading("Cumplimiento", text="Cumplimiento de Criterios")  # Nueva columna
        self.tree.heading("Actions", text="Acciones")

        # Ajustar el ancho de las columnas
        self.tree.column("Cid", width=50, anchor="center")
        self.tree.column("CiteKey", width=100, anchor="center")
        self.tree.column("Title", width=200, anchor="center")
        self.tree.column("Author", width=150, anchor="center")
        self.tree.column("Year", width=80, anchor="center")
        self.tree.column("Etiqueta", width=100, anchor="center")  # Ancho para la nueva columna
        self.tree.column("Cumplimiento", width=150, anchor="center")  # Ancho para la nueva columna
        self.tree.column("Actions", width=120, anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # **Botones CRUD para documentos**
        self.crud_frame = tk.Frame(self.root)
        self.crud_frame.pack(pady=10)

        Button(self.crud_frame, text="Crear Documento", command=self.create_document).pack(side=tk.LEFT, padx=5)
        Button(self.crud_frame, text="Modificar Documento", command=self.update_document).pack(side=tk.LEFT, padx=5)
        Button(self.crud_frame, text="Eliminar Documento", command=self.delete_document).pack(side=tk.LEFT, padx=5)

    
    def create_new_database(self):
        global current_db_path
        db_path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite Database", "*.db")])
        if db_path:
            try:
                # Inicializar una nueva base de datos
                current_db_path = db_path
                init_db(current_db_path)  # Crear tablas en la nueva base de datos
                messagebox.showinfo("Éxito", f"Se creó una nueva base de datos: {db_path}")
                self.load_documents()  # Actualizar la grilla para reflejar la nueva base de datos
            except Exception as e:
                messagebox.showerror("Error", f"Hubo un problema al crear la base de datos: {e}")
                        
    def open_project_manager(self):
        ProyectoManager(self.root)        
                
    def load_documents(self):
        # Cargar documentos desde la base de datos y actualizar la grilla
        conn = connect_to_db(current_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT Cid, cite_key, title, author, year FROM documentos")
        rows = cursor.fetchall()
        conn.close()

        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert("", "end", values=(*row, "Abrir Análisis"))  # Agregamos el texto "Abrir Análisis" en la columna Acciones

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
        global current_db_path
        db_path = filedialog.askopenfilename(filetypes=[("SQLite Database", "*.db")])
        if db_path:
            current_db_path = db_path
            init_db(current_db_path)  # Inicializar tablas si es necesario
            self.load_documents()
            messagebox.showinfo("Éxito", f"Base de datos abierta: {db_path}")
            

    def save_database(self):
        if current_db_path:
            # SQLite guarda automáticamente los cambios
            messagebox.showinfo("Éxito", "Cambios guardados exitosamente.")
        else:
            messagebox.showwarning("Advertencia", "No hay una base de datos abierta actualmente.")

    def save_database_as(self):
        global current_db_path
        db_path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite Database", "*.db")])
        if db_path:
            with connect_to_db(current_db_path) as old_conn, sqlite3.connect(db_path) as new_conn:
                old_conn.backup(new_conn)  # Copiar datos al nuevo archivo
            current_db_path = db_path
            messagebox.showinfo("Éxito", f"Base de datos guardada como: {db_path}")


    def create_document(self):
        # Abrir el formulario para crear un documento
        DocumentForm(self.root, mode="create")

    def update_document(self):
        # Abrir el formulario para modificar un documento
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor selecciona un documento.")
            return

        document_id = self.tree.item(selected_item[0])["values"][0]
        DocumentForm(self.root, mode="edit", document_id=document_id)

    def delete_document(self):
        # Eliminar un documento seleccionado
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor selecciona un documento.")
            return

        document_id = self.tree.item(selected_item[0])["values"][0]
        conn = connect_to_db(current_db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documentos WHERE id = ?", (document_id,))
        conn.commit()
        conn.close()
        self.load_documents()
        messagebox.showinfo("Éxito", "Documento eliminado exitosamente.")

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

        Label(self.window, text="CiteKey:").pack()
        self.cite_key_entry = Entry(self.window, width=40)
        self.cite_key_entry.pack(pady=5)

        Label(self.window, text="Título:").pack()
        self.title_entry = Entry(self.window, width=40)
        self.title_entry.pack(pady=5)

        Label(self.window, text="Autor:").pack()
        self.author_entry = Entry(self.window, width=40)
        self.author_entry.pack(pady=5)

        Label(self.window, text="Año:").pack()
        self.year_entry = Entry(self.window, width=20)
        self.year_entry.pack(pady=5)

        Label(self.window, text="Resumen:").pack()
        self.abstract_frame = tk.Frame(self.window)
        self.abstract_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(self.abstract_frame, orient=tk.VERTICAL)
        self.abstract_text = tk.Text(self.abstract_frame, wrap=tk.WORD, height=5, width=50, yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.abstract_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.abstract_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        Label(self.window, text="Etiquetas:").pack()
        self.scolr_tags_entry = Entry(self.window, width=40)
        self.scolr_tags_entry.pack(pady=5)

        # Nuevos campos para Etiqueta y Cumplimiento de Criterios
        Label(self.window, text="Etiqueta:").pack()
        self.etiqueta_entry = Entry(self.window, width=40)
        self.etiqueta_entry.pack(pady=5)

        Label(self.window, text="Cumplimiento de Criterios:").pack()
        self.cumplimiento_entry = Entry(self.window, width=40)
        self.cumplimiento_entry.pack(pady=5)

        if self.mode == "edit":
            self.load_document()

        Button(self.window, text="Guardar", command=self.save_document).pack(pady=10)

    def load_document(self):
        # Cargar información para edición
        if not self.document_id:
            return

        conn = connect_to_db(current_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT cite_key, title, author, year, abstract, scolr_tags, etiqueta, cumplimiento_de_criterios FROM documentos WHERE Cid = ?", (self.document_id,))
        document = cursor.fetchone()
        conn.close()

        if document:
            self.cite_key_entry.insert(0, document[0])
            self.title_entry.insert(0, document[1])
            self.author_entry.insert(0, document[2])
            self.year_entry.insert(0, document[3])
            self.abstract_text.insert("1.0", document[4])
            self.scolr_tags_entry.insert(0, document[5])
            self.etiqueta_entry.insert(0, document[6])
            self.cumplimiento_entry.insert(0, document[7])

    def save_document(self):
        # Guardar nuevo o actualizar documento
        cite_key = self.cite_key_entry.get()
        title = self.title_entry.get()
        author = self.author_entry.get()
        year = self.year_entry.get()
        abstract = self.abstract_text.get("1.0", tk.END).strip()
        scolr_tags = self.scolr_tags_entry.get()
        etiqueta = self.etiqueta_entry.get()
        cumplimiento = self.cumplimiento_entry.get()

        conn = connect_to_db(current_db_path)
        cursor = conn.cursor()

        if self.mode == "create":
            cursor.execute("""
                INSERT INTO documentos (cite_key, title, author, year, abstract, scolr_tags, etiqueta, cumplimiento_de_criterios)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (cite_key, title, author, year, abstract, scolr_tags, etiqueta, cumplimiento))
        elif self.mode == "edit":
            cursor.execute("""
                UPDATE documentos
                SET cite_key = ?, title = ?, author = ?, year = ?, abstract = ?, scolr_tags = ?, etiqueta = ?, cumplimiento_de_criterios = ?
                WHERE Cid = ?
            """, (cite_key, title, author, year, abstract, scolr_tags, etiqueta, cumplimiento, self.document_id))

        conn.commit()
        conn.close()
        self.window.destroy()
        messagebox.showinfo("Éxito", "Documento guardado exitosamente.")

        # Actualizar la grilla en la ventana principal
        parent = self.window.master
        for child in parent.winfo_children():
            if isinstance(child, App):
                child.load_documents()
                
                
# Ejecutar la aplicación
if __name__ == "__main__":
    # Inicializa la base de datos predeterminada
    current_db_path = "default_project.db"  # Ruta predeterminada de la base de datos
    init_db(current_db_path)  # Inicializar la base de datos
    root = tk.Tk()
    app = App(root)
    root.mainloop()