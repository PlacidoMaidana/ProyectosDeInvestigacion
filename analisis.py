import tkinter as tk
from tkinter import ttk, Label, Entry, Toplevel, Button, messagebox, Frame, Scrollbar, Text
from tkinter import ttk  # Asegúrate de incluir ttk
from tkinter import Toplevel, Label, Entry, Button, messagebox
from db_setup import init_db, connect_to_db  # Importar lógica de base de datos


class AnalysisForm:
    def __init__(self, parent, document_id, current_db_path):
        self.document_id = document_id
        self.window = Toplevel(parent)
        self.window.title(f"Análisis del Documento ID: {document_id}")

        self.tree = ttk.Treeview(self.window, columns=("ID", "Dimension", "Descripcion"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Dimension", text="Dimensión")
        self.tree.heading("Descripcion", text="Descripción")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.load_analysis()

        self.crud_frame = tk.Frame(self.window)
        self.crud_frame.pack(pady=10)

        Button(self.crud_frame, text="Crear Análisis", command=self.create_analysis).pack(side=tk.LEFT, padx=5)
        Button(self.crud_frame, text="Modificar Análisis", command=self.update_analysis).pack(side=tk.LEFT, padx=5)
        Button(self.crud_frame, text="Eliminar Análisis", command=self.delete_analysis).pack(side=tk.LEFT, padx=5)

    def load_analysis(self):
        conn = connect_to_db(current_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, dimension, descripcion FROM analisis WHERE documento_id = ?", (self.document_id,))
        rows = cursor.fetchall()
        conn.close()

        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert("", "end", values=row)

    def create_analysis(self):
        AnalysisFormEditor(self.window, self.document_id, mode="create")

    def update_analysis(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor selecciona un análisis.")
            return

        analysis_id = self.tree.item(selected_item[0])["values"][0]
        AnalysisFormEditor(self.window, self.document_id, mode="edit", analysis_id=analysis_id)

    def delete_analysis(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor selecciona un análisis.")
            return

        analysis_id = self.tree.item(selected_item[0])["values"][0]
        conn = connect_to_db(current_db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM analisis WHERE id = ?", (analysis_id,))
        conn.commit()
        conn.close()
        self.load_analysis()
        messagebox.showinfo("Éxito", "Análisis eliminado exitosamente.")

class AnalysisFormEditor:
    def __init__(self, parent, document_id, mode, analysis_id=None):
        self.window = Toplevel(parent)
        self.window.title("Formulario de Análisis")
        self.mode = mode
        self.analysis_id = analysis_id
        self.document_id = document_id

        Label(self.window, text="Dimensión:").pack()
        self.dimension_entry = Entry(self.window, width=40)  # Ampliar tamaño
        self.dimension_entry.pack(pady=5)

        Label(self.window, text="Descripción:").pack()
        # Campo multilínea para Descripción con barra de desplazamiento vertical
        self.description_frame = tk.Frame(self.window)
        self.description_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(self.description_frame, orient=tk.VERTICAL)
        self.description_text = tk.Text(self.description_frame, wrap=tk.WORD, height=6, width=50, yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.description_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.description_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        Button(self.window, text="Guardar", command=self.save_analysis).pack(pady=10)

    def load_analysis(self):
        if not self.analysis_id:
            return  # Si no hay ID, no hacer nada

        conn = connect_to_db(current_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT dimension, descripcion FROM analisis WHERE id = ?", (self.analysis_id,))
        analysis = cursor.fetchone()
        conn.close()

        if analysis:
            self.dimension_entry.insert(0, analysis[0])
            self.description_text.insert("1.0", analysis[1])  # Insertar texto completo en Text

    def save_analysis(self):
        dimension = self.dimension_entry.get()
        descripcion = self.description_text.get("1.0", tk.END).strip()  # Obtener texto de Text

        conn = connect_to_db(current_db_path)
        cursor = conn.cursor()

        if self.mode == "create":
            cursor.execute("""
                INSERT INTO analisis (documento_id, dimension, descripcion)
                VALUES (?, ?, ?)
            """, (self.document_id, dimension, descripcion))
        elif self.mode == "edit":
            cursor.execute("""
                UPDATE analisis
                SET dimension = ?, descripcion = ?
                WHERE id = ?
            """, (dimension, descripcion, self.analysis_id))

        conn.commit()
        conn.close()
        self.window.destroy()
        messagebox.showinfo("Éxito", "Análisis guardado exitosamente.")

        # Actualizar la grilla de análisis
        parent = self.window.master
        for child in parent.winfo_children():
            if isinstance(child, AnalysisForm):
                child.load_analysis()