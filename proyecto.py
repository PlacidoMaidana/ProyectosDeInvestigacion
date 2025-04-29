import tkinter as tk
from tkinter import ttk, Label, Entry, Toplevel, Button, messagebox, Frame, Scrollbar, Text

from db_setup import connect_to_db

class ProyectoForm:
    def __init__(self, parent, mode, project_id=None, current_db_path=None):
        self.window = Toplevel(parent)
        self.window.title("Formulario Proyecto")
        self.mode = mode
        self.project_id = project_id
        self.current_db_path=current_db_path

        Label(self.window, text="Nombre del Proyecto:").pack()
        self.nombre_entry = Entry(self.window, width=40)
        self.nombre_entry.pack(pady=5)

        Label(self.window, text="Descripción:").pack()
        self.descripcion_entry = Entry(self.window, width=40)
        self.descripcion_entry.pack(pady=5)

        if self.mode == "edit":
            self.load_project()

        Button(self.window, text="Guardar", command=self.save_project).pack(pady=10)

    def load_project(self):
        if not self.project_id:
            return

        conn = connect_to_db(self.current_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, descripcion FROM proyecto WHERE id = ?", (self.project_id,))
        project = cursor.fetchone()
        conn.close()

        if project:
            self.nombre_entry.insert(0, project[0])
            self.descripcion_entry.insert(0, project[1])

    def save_project(self):
        nombre = self.nombre_entry.get()
        descripcion = self.descripcion_entry.get()

        conn = connect_to_db(self.current_db_path)
        cursor = conn.cursor()

        if self.mode == "create":
            cursor.execute("INSERT INTO proyecto (nombre, descripcion) VALUES (?, ?)", (nombre, descripcion))
        elif self.mode == "edit":
            cursor.execute("UPDATE proyecto SET nombre = ?, descripcion = ? WHERE id = ?", (nombre, descripcion, self.project_id))

        conn.commit()
        conn.close()
        self.window.destroy()
        messagebox.showinfo("Éxito", "Proyecto guardado exitosamente.")

        # Actualizar la lista de proyectos en la ventana principal
        parent = self.window.master
        for child in parent.winfo_children():
            if isinstance(child, App):  # Asegurarte de que es la clase principal
                child.load_projects()

class ProyectoManager:
    def __init__(self, parent,current_db_path ):
        self.window = Toplevel(parent)
        self.window.title("Gestión de Proyectos")

         # Almacenar la ruta de la base de datos y crear la conexión
        self.current_db_path = current_db_path
        self.conn = connect_to_db(current_db_path)  # Guardar la conexión como atributo


        self.tree = ttk.Treeview(self.window, columns=("ID", "Nombre", "Descripción"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre del Proyecto")
        self.tree.heading("Descripción", text="Descripción")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.load_projects()

        Button(self.window, text="Crear Proyecto", command=self.create_project).pack(side=tk.LEFT, padx=5)
        Button(self.window, text="Modificar Proyecto", command=self.update_project).pack(side=tk.LEFT, padx=5)
        Button(self.window, text="Eliminar Proyecto", command=self.delete_project).pack(side=tk.LEFT, padx=5)

    def load_projects(self):
        conn = connect_to_db(self.current_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, descripcion FROM proyecto")
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