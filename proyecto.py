
from db_setup import connect_to_db
import tkinter as tk
import os
import subprocess
from tkinter import *
from tkinter import ttk, filedialog, messagebox, Toplevel, Button, messagebox, Frame, Scrollbar, Text
from tkinter.font import Font

class ProyectoForm:
    def __init__(self, parent, mode, project_id=None, current_db_path=None):
        self.window = Toplevel(parent)
        self.window.title("✏️ Formulario de Proyecto")
        self.window.geometry("700x550")
        self.style = ttk.Style()
        self.style.configure('TButton', padding=5, font=('Arial', 10))
        
        # Configurar iconos
        self.icons = {
            'save': '💾',
            'file': '📁',
            'project': '📋',
            'desc': '📝',
            'open': '🔍'
        }
        
        self.mode = mode
        self.project_id = project_id
        self.current_db_path = current_db_path
        self.file_path = StringVar()

        # Frame principal
        main_frame = ttk.Frame(self.window, padding="15 15 15 15")
        main_frame.pack(fill=BOTH, expand=True)

        # Título del formulario
        title_font = Font(size=12, weight='bold')
        ttk.Label(main_frame, 
                 text=f"{'Editar' if mode == 'edit' else 'Nuevo'} Proyecto", 
                 font=title_font,
                 foreground='#2c3e50').pack(pady=(0, 15))

        # Campo para el nombre del proyecto
        self.create_label_entry(main_frame, "Nombre del Proyecto:", 'project')
        
        # Área de texto para descripción con scrollbar
        self.create_desc_field(main_frame)
        
        # Campo para adjuntar archivo
        self.create_file_selector(main_frame)
        
        # Botones de acción
        self.create_action_buttons(main_frame)

        if self.mode == "edit":
            self.load_project()

              # Configurar estilo para el botón destacado
        self.style = ttk.Style()
        self.style.configure('Accent.TButton', 
                           foreground='white',          # Letras blancas
                           background='#27ae60',       # Verde esmeralda (color que enviaste)
                           font=('Arial', 10, 'bold'), # Fuente en negrita
                           padding=8)                  # Espaciado interno

        # Configurar estados del botón (hover y pressed)
        self.style.map('Accent.TButton',
                      background=[('active', '#2ecc71'),   # Verde más claro al pasar mouse
                                 ('pressed', '#16a085')]) # Verde más oscuro al presionar

    def create_label_entry(self, parent, label_text, icon_key):
        """Crea un campo de entrada con etiqueta e icono"""
        frame = ttk.Frame(parent)
        frame.pack(fill=X, pady=5)
        
        ttk.Label(frame, 
                 text=f" {self.icons.get(icon_key, '')}  {label_text}",
                 font=('Arial', 10, 'bold')).pack(anchor='w')
        
        self.nombre_entry = ttk.Entry(frame, width=50)
        self.nombre_entry.pack(fill=X, pady=2)

    def create_desc_field(self, parent):
        """Crea el área de descripción con scrollbar"""
        ttk.Label(parent, 
                 text=f" {self.icons['desc']}  Descripción:",
                 font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 0))
        
        desc_frame = Frame(parent)
        desc_frame.pack(fill=BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(desc_frame, orient=VERTICAL)
        self.descripcion_text = Text(desc_frame,
                                   height=10,
                                   wrap=WORD,
                                   font=('Arial', 10),
                                   padx=5,
                                   pady=5,
                                   yscrollcommand=scrollbar.set)
        
        scrollbar.config(command=self.descripcion_text.yview)
        
        self.descripcion_text.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

    def create_file_selector(self, parent):
        """Crea el selector de archivos con estilo mejorado"""
        file_frame = ttk.Frame(parent)
        file_frame.pack(fill=X, pady=10)
        
        ttk.Label(file_frame, 
                 text=f" {self.icons['file']}  Archivo Adjunto:",
                 font=('Arial', 10, 'bold')).pack(anchor='w')
        
        inner_frame = ttk.Frame(file_frame)
        inner_frame.pack(fill=X, pady=5)
        
        self.file_entry = ttk.Entry(inner_frame, 
                                  textvariable=self.file_path, 
                                  state='readonly')
        self.file_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
        
        ttk.Button(inner_frame,
                  text="Buscar...",
                  command=self.select_file).pack(side=LEFT, padx=2)
        
        # Botón para abrir archivo (solo visible cuando hay archivo)
        self.open_file_btn = ttk.Button(inner_frame,
                                      text=f" {self.icons['open']} Abrir",
                                      state=DISABLED,
                                      command=self.open_file)
        self.open_file_btn.pack(side=LEFT, padx=2)
        
        # Actualizar estado del botón cuando cambia el archivo
        self.file_path.trace_add('write', self.update_open_button)

    def create_action_buttons(self, parent):
        """Crea los botones de acción"""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=X, pady=15)
        
        
        Button(
            btn_frame,
            text=f" {self.icons['save']} Guardar Proyecto",
            command=self.save_project,
            bg='#4CAF50',  # Fondo verde
            fg='black',     # Texto negro
            padx=10,
            pady=5
        ).pack(side=tk.RIGHT, padx=5)
        
       
    def select_file(self):
        """Abre el diálogo para seleccionar archivo"""
        filetypes = [
            ('Todos los archivos', '*.*'),
            ('Documentos', '*.doc *.docx *.pdf'),
            ('Imágenes', '*.png *.jpg *.jpeg'),
            ('Archivos de texto', '*.txt')
        ]
        
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo adjunto",
            filetypes=filetypes
        )
        
        if filepath:
            self.file_path.set(filepath)

    def update_open_button(self, *args):
        """Actualiza el estado del botón de abrir archivo"""
        if self.file_path.get():
            self.open_file_btn.config(state=NORMAL)
        else:
            self.open_file_btn.config(state=DISABLED)

    def open_file(self):
        """Abre el archivo con el programa predeterminado"""
        filepath = self.file_path.get()
        if filepath and os.path.exists(filepath):
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(filepath)
                elif os.name == 'posix':  # macOS y Linux
                    subprocess.run(['xdg-open', filepath])
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}")
        else:
            messagebox.showwarning("Archivo no encontrado", "El archivo especificado no existe")

    def load_project(self):
        """Carga los datos del proyecto para edición"""
        if not self.project_id:
            return

        try:
            conn = connect_to_db(self.current_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT nombre, descripcion, archivo FROM proyecto WHERE id = ?", (self.project_id,))
            project = cursor.fetchone()
            conn.close()

            if project:
                self.nombre_entry.insert(0, project[0])
                self.descripcion_text.insert("1.0", project[1] or "")
                if project[2]:  # Si hay archivo adjunto
                    self.file_path.set(project[2])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los datos: {e}")

    def save_project(self):
        """Guarda los datos del proyecto con validación"""
        nombre = self.nombre_entry.get().strip()
        descripcion = self.descripcion_text.get("1.0", END).strip()
        archivo = self.file_path.get()

        if not nombre:
            messagebox.showwarning("Campo requerido", "El nombre del proyecto es obligatorio")
            return

        try:
            conn = connect_to_db(self.current_db_path)
            cursor = conn.cursor()

            if self.mode == "create":
                cursor.execute("INSERT INTO proyecto (nombre, descripcion, archivo) VALUES (?, ?, ?)", 
                             (nombre, descripcion, archivo))
            elif self.mode == "edit":
                cursor.execute("UPDATE proyecto SET nombre = ?, descripcion = ?, archivo = ? WHERE id = ?", 
                             (nombre, descripcion, archivo, self.project_id))

            conn.commit()
            conn.close()
            
            # Actualizar la lista de proyectos en la ventana principal
            if hasattr(self.window.master, 'load_projects'):
                self.window.master.load_projects()
                
            messagebox.showinfo("Éxito", "Proyecto guardado correctamente")
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el proyecto: {e}")

class ProyectoManager:
    def __init__(self, parent,current_db_path ):
        self.window = Toplevel(parent)
        self.window.title("Gestión de Proyectos")

         # Almacenar la ruta de la base de datos y crear la conexión
        self.current_db_path = current_db_path
        self.conn = connect_to_db(current_db_path)  # Guardar la conexión como atributo


        self.tree = ttk.Treeview(self.window, columns=("ID", "Nombre", "Descripción","Archivo"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre del Proyecto")
        self.tree.heading("Descripción", text="Descripción")
        self.tree.heading("Archivo", text="Archivo")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.load_projects()

        Button(self.window, text="Crear Proyecto", command=self.create_project).pack(side=tk.LEFT, padx=5)
        Button(self.window, text="Modificar Proyecto", command=self.update_project).pack(side=tk.LEFT, padx=5)
        Button(self.window, text="Eliminar Proyecto", command=self.delete_project).pack(side=tk.LEFT, padx=5)

    def load_projects(self):
        conn = connect_to_db(self.current_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, descripcion, archivo FROM proyecto")
        rows = cursor.fetchall()
        conn.close()

        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert("", "end", values=row)

    def create_project(self):
        ProyectoForm(self.window, mode="create",current_db_path=self.current_db_path)

    def update_project(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor selecciona un proyecto.")
            return

        project_id = self.tree.item(selected_item[0])["values"][0]
        ProyectoForm(self.window, mode="edit", project_id=project_id, current_db_path=self.current_db_path)

    def delete_project(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor selecciona un proyecto.")
            return

        project_id = self.tree.item(selected_item[0])["values"][0]
        conn = connect_to_db(self.current_db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM proyecto WHERE id = ?", (project_id,))
        conn.commit()
        conn.close()
        self.load_projects()
        messagebox.showinfo("Éxito", "Proyecto eliminado exitosamente.")