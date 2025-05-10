import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json

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
            
   



class CapturaInteligenteEnlaces:
    def __init__(self, master, db_connection):
        self.master = master
        self.db_connection = db_connection

        # Crear la ventana modal
        self.modal_window = tk.Toplevel(self.master)
        self.modal_window.title("Captura Inteligente de Enlaces")
        self.modal_window.geometry("650x600")
        self.modal_window.transient(self.master)
        self.modal_window.grab_set()

        # Etiqueta JSON
        ttk.Label(self.modal_window, text="Ingresa los datos generales en formato JSON:", font=("Arial", 12)).pack(pady=5)

        # Modelo de JSON de muestra sin enlaces
        json_modelo = """{
           
            "cite_key": "asdf",
            "title": "",
            "author": "asdf",
            "year": "2025",
            "abstract": "",
            "scolr_tags": ["NADA"],
            "etiqueta": "",
            "cumplimiento_de_criterios": "",
            "referencia_apa": ""
        }"""

        # Campo de texto para JSON
        self.json_input = tk.Text(self.modal_window, wrap="word", font=("Arial", 10), height=10)
        self.json_input.insert("1.0", json_modelo)
        self.json_input.pack(fill="both", expand=True, padx=10, pady=5)

        # Etiqueta enlaces
        ttk.Label(self.modal_window, text="Ingresa los enlaces abajo (uno por línea, con o sin título):", font=("Arial", 12)).pack(pady=5)

        # Campo de texto para enlaces
        self.enlaces_input = tk.Text(self.modal_window, wrap="word", font=("Arial", 10), height=8)
        self.enlaces_input.pack(fill="both", expand=True, padx=10, pady=5)

        # Botón para procesar
        ttk.Button(self.modal_window, text="Procesar e Importar", command=self.procesar_datos).pack(pady=10)

    def procesar_datos(self):
        # Obtener JSON
        json_texto = self.json_input.get("1.0", tk.END).strip()
        enlaces_texto = self.enlaces_input.get("1.0", tk.END).strip()

        if not json_texto or not enlaces_texto:
            messagebox.showerror("Error", "Debes ingresar el JSON y los enlaces antes de procesar.")
            return

        try:
            datos = json.loads(json_texto)  # Cargar el JSON sin validaciones estrictas
        except json.JSONDecodeError:
            messagebox.showerror("Error", "El formato JSON no es válido.")
            return

        documentos = self._procesar_enlaces(datos, enlaces_texto)

        if documentos:
            self._insertar_documentos(documentos, self.db_connection)
            messagebox.showinfo("Éxito", f"Se han importado {len(documentos)} documentos correctamente.")
            self.modal_window.destroy()
        else:
            messagebox.showwarning("Advertencia", "No se encontraron datos válidos.")

  
    def _procesar_enlaces(self, datos, enlaces_texto):
        documentos = []
        lineas = enlaces_texto.split("\n")

        i = 0
        while i < len(lineas):
            enlace = lineas[i].strip()
            titulo = None

            if i + 1 < len(lineas) and lineas[i + 1].startswith("http"):
                titulo = enlace
                enlace = lineas[i + 1].strip()
                i += 1

            # Crear registro sin "Cid" ni "con_titulo"
            registro = {k: json.dumps(v) if isinstance(v, list) else (None if v == "" else v)
                        for k, v in datos.items() if k not in ["Cid", "con_titulo"]}  
            registro.update({"title": titulo or datos.get("title", ""), "enlace": enlace})

            documentos.append(registro)
            i += 1

        return documentos

    def _insertar_documentos(self, documentos, db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Generar la consulta excluyendo "Cid"
            columnas = list(documentos[0].keys())  # Obtener todas las claves del primer registro
            query = f"""INSERT INTO documentos ({', '.join(columnas)}) 
                        VALUES ({', '.join('?' * len(columnas))})"""

            cursor.executemany(query, [tuple(doc.values()) for doc in documentos])

            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo insertar los documentos: {str(e)}")