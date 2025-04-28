import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class ImportarTextoVentana:
    def __init__(self, master, db_connection):
        self.master = master
        self.db_connection = db_connection

        # Crear la ventana modal
        self.modal_window = tk.Toplevel(self.master)
        self.modal_window.title("Importar Texto")
        self.modal_window.geometry("600x400")
        self.modal_window.transient(self.master)
        self.modal_window.grab_set()

        # Etiqueta
        ttk.Label(self.modal_window, text="Introduce el texto:", font=("Arial", 12)).pack(pady=10)

        # Control de entrada de texto
        self.text_input = tk.Text(self.modal_window, wrap="word", font=("Arial", 10))
        self.text_input.pack(fill="both", expand=True, padx=10, pady=10)

        # Botón para procesar texto
        ttk.Button(self.modal_window, text="Procesar e Importar", command=self.procesar_texto).pack(pady=10)

    def procesar_texto(self):
        # Leer el texto del control Text
        texto = self.text_input.get("1.0", tk.END).strip()
        if not texto:
            messagebox.showerror("Error", "El texto está vacío. Por favor ingresa datos.")
            return

        # Procesar el texto en pares de título y enlace
        documentos = self._procesar_texto_a_documentos(texto)

        if documentos:
            # Insertar los documentos en la base de datos
            self._insertar_documentos(documentos, self.db_connection)
            messagebox.showinfo("Éxito", f"Se han importado {len(documentos)} documentos correctamente.")
            self.modal_window.destroy()  # Cerrar la ventana modal
        else:
            messagebox.showwarning("Advertencia", "No se encontraron títulos y enlaces válidos.")

    def _procesar_texto_a_documentos(self, texto):
        # Dividir el texto en líneas
        lineas = texto.split("\n")
        
        # Procesar líneas en pares (título y enlace)
        documentos = []
        for i in range(0, len(lineas), 3):  # Iterar cada 3 líneas (título, enlace, espacio)
            titulo = lineas[i].strip() if i < len(lineas) else None
            enlace = lineas[i + 1].strip() if i + 1 < len(lineas) else None
            if titulo and enlace:
                documentos.append((titulo, enlace))
        return documentos

    def _insertar_documentos(self, documentos, db_path):
        try:
            # Establecer conexión directa a la base de datos
            conn = sqlite3.connect(db_path)  # Conexión a la base de datos
            cursor = conn.cursor()  # Crear un cursor para ejecutar consultas

            # Consulta para insertar documentos
            query = "INSERT INTO documentos (title, enlace) VALUES (?, ?)"
            cursor.executemany(query, documentos)  # Insertar múltiples registros

            # Confirmar cambios y cerrar la conexión
            conn.commit()
            conn.close()
            print(f"Se han importado {len(documentos)} documentos correctamente.")
        except sqlite3.Error as e:
            # Manejo de errores
            messagebox.showerror("Error", f"No se pudo insertar los documentos: {str(e)}")