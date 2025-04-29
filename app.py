import tkinter as tk
from tkinter import Menu, filedialog, ttk, Label, Entry, Toplevel, Button, messagebox, Frame, Scrollbar, Text
from list_manager import ListManager
from db_setup import init_db, connect_to_db  # Importar lógica de base de datos
from analisis import AnalysisForm  # Archivo que maneja la ficha de análisis
from proyecto import ProyectoManager  # Importar el gestor de proyectos
from bib_importer import BibImporter, ImportarBibVentana
import sqlite3 
from importar_enlaces import importar_enlaces
import webbrowser
import os
from importar_texto import ImportarTextoVentana
from IA_analisis import copiar_seleccion_como_csv, exportar_a_csv

# Crear una instancia global (o puedes pasarla como parámetro)
list_manager = ListManager()
# Ventana principal
class App:
    def __init__(self, master):
        self.master = master
        self.master.title("Gestión de Documentos y Análisis")
        self.analysis_windows = {}  # Diccionario para manejar las ventanas de análisis

        # Inicializar atributos
        self.current_db_path = "default_project.db"  # Ruta inicial predeterminada
        self.db_connection = None  # Inicialización de la conexión
        self.bib_importer = None  # Inicialización del importador
        
        
        
        # Inicializar archivos CSV al inicio del programa
        list_manager.inicializar_archivos_csv()

        # Menú principal
        self.menu_bar = Menu(self.master)
        self.master.config(menu=self.menu_bar)

        # Menú Archivo
        self.file_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Archivo", menu=self.file_menu)
        self.file_menu.add_command(label="Crear Nueva Base de Datos", command=self.create_new_database)
        self.file_menu.add_command(label="Abrir...", command=self.open_database)
        self.file_menu.add_command(label="Guardar", command=self.save_database)
        self.file_menu.add_command(label="Guardar como...", command=self.save_database_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Salir", command=self.master.quit)

        # Menú Proyecto
        self.project_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Proyecto", menu=self.project_menu)
        self.project_menu.add_command(label="Gestión de Proyectos", command=self.open_project_manager)

        # Menú Importaciones
        self.import_menu = Menu(self.menu_bar, tearoff=0)
        self.import_menu.add_command(
            label="Importar desde BibTeX",
            command=self.import_from_bib,
            state=tk.DISABLED  # Inicialmente deshabilitado
        )
        # Nueva opción: Importar desde Excel
        self.import_menu.add_command(
            label="Importar desde Excel",
            command=self.import_links_from_excel,  # Método que implementamos para importar enlaces desde Excel
            state=tk.NORMAL  # Activado de forma predeterminada, puedes cambiarlo si lo necesitas
        )
        # IMPORTAR CAPTURA DE TABS, BASICAMENTE CAPTURA E IMPORTA TEXTO ESTO SERA MUY UTIL PARA IMPORTAR ANALISIS IA
        self.import_menu.add_command(
        label="Importar Texto desde Archivo o Entrada",  # Título del menú
        command=self.import_text_to_database,  # Llama al método intermedio
        state=tk.NORMAL  # Activado de forma predeterminada
        )
        self.import_menu.add_command(
            label="Importar desde .bib",
            command=lambda: ImportarBibVentana(self.master, self.current_db_path),
            state=tk.NORMAL
        )

        
        self.menu_bar.add_cascade(label="Importaciones", menu=self.import_menu)
        
        
        # Crear el Combobox para seleccionar etiquetas (el filtro)
        self.filter_combobox = ttk.Combobox(self.master, state="readonly")
        self.filter_combobox['values'] = ["Todos", "INCLUIDO", "EXCLUIDO", "INTERESANTE"]
        self.filter_combobox.current(0)  # Por defecto, mostrar "Todos"
        self.filter_combobox.pack(pady=10)

        # Conectar el evento de cambio de selección
        self.filter_combobox.bind("<<ComboboxSelected>>", self.filtrar_por_etiqueta)


        
        
        
        

        # Configurar Treeview
        tree_frame = ttk.Frame(self.master)
        tree_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("Cid", "CiteKey", "Title", "Author", "Year", "Etiqueta", "Cumplimiento", "ReferenciaAPA","Enlace", "Actions"),
            show="headings",
            selectmode="extended"  # Permitir selección múltiple
        )
        self.tree.heading("Cid", text="ID")
        self.tree.heading("CiteKey", text="CiteKey")
        self.tree.heading("Title", text="Título")
        self.tree.heading("Author", text="Autor")
        self.tree.heading("Year", text="Año")
        self.tree.heading("Etiqueta", text="Etiqueta")
        self.tree.heading("Cumplimiento", text="Cumplimiento de Criterios")
        self.tree.heading("ReferenciaAPA", text="Referencia APA")
        self.tree.heading("Enlace", text="Enlace")
        self.tree.heading("Actions", text="Acciones")

        self.tree.column("Cid", width=50, anchor="center")
        self.tree.column("CiteKey", width=100, anchor="center")
        self.tree.column("Title", width=200, anchor="center")
        self.tree.column("Author", width=150, anchor="center")
        self.tree.column("Year", width=80, anchor="center")
        self.tree.column("Etiqueta", width=100, anchor="center")
        self.tree.column("Cumplimiento", width=150, anchor="center")
        self.tree.column("ReferenciaAPA", width=200, anchor="center")
        self.tree.column("Enlace", width=200, anchor="center")
        self.tree.column("Actions", width=120, anchor="center")

        self.tree.bind("<Button-1>", self.on_tree_click)
        


        # Crear la barra de desplazamiento vertical
        scrollbar = Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")

        # Vincular la barra de desplazamiento al Treeview
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Empaquetar el Treeview
        self.tree.pack(fill=tk.BOTH, expand=True)


        self.crear_menu_contextual()

        # Botones CRUD
        self.crud_frame = tk.Frame(self.master)
        self.crud_frame.pack(pady=10)
        Button(self.crud_frame, text="Crear Documento", command=self.create_document).pack(side=tk.LEFT, padx=5)
        Button(self.crud_frame, text="Modificar Documento", command=self.update_document).pack(side=tk.LEFT, padx=5)
        Button(self.crud_frame, text="Eliminar Documento", command=self.delete_document).pack(side=tk.LEFT, padx=5)
        Button(self.crud_frame, text="Refrescar", command=self.refresh_ui).pack(side=tk.LEFT, padx=5)

        # Conectar a la base de datos por defecto
        self.switch_database(self.current_db_path)



    def filtrar_por_etiqueta(self, event=None):
        """
        Filtra los registros en el Treeview según la etiqueta seleccionada.
        """
        etiqueta_seleccionada = self.filter_combobox.get()
    
        # Conectar a la base de datos
        try:
            conn = sqlite3.connect(self.current_db_path)
            cursor = conn.cursor()
    
            # Construir la consulta SQL
            if etiqueta_seleccionada == "Todos":
                query = "SELECT Cid, cite_key, title, author, year, etiqueta, cumplimiento_de_criterios FROM documentos"
                cursor.execute(query)
            else:
                query = """
                    SELECT Cid, cite_key, title, author, year, etiqueta, cumplimiento_de_criterios
                    FROM documentos
                    WHERE etiqueta = ?
                """
                cursor.execute(query, (etiqueta_seleccionada,))
    
            # Obtener los resultados
            registros = cursor.fetchall()
    
            # Limpiar el Treeview antes de cargar los nuevos datos
            for item in self.tree.get_children():
                self.tree.delete(item)
    
            # Insertar los registros filtrados en el Treeview
            for registro in registros:
                self.tree.insert("", "end", values=registro)
    
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al filtrar los registros: {e}")
        finally:
            if conn:
                conn.close()







    def switch_database(self, new_db_path):
        # Desconectar base anterior
        if self.db_connection:
            self.db_connection.disconnect()

        # Conectar a la nueva base
        self.db_connection = BibImporter(new_db_path)
        if not self.db_connection.connect():
            messagebox.showerror("Error", f"No se pudo conectar a la base de datos: {new_db_path}")
            return

        self.current_db_path = new_db_path  # Actualizar ruta actual
        self.refresh_ui()  # Refrescar la interfaz (cargar datos en Treeview)


        
    def refresh_ui(self):
        try:
            # Limpiar los elementos existentes en el Treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Obtener todos los registros de la base de datos activa
            cursor = self.db_connection.conn.cursor()
            query = "SELECT Cid, cite_key, title, author, year, etiqueta, cumplimiento_de_criterios, referencia_apa, enlace FROM documentos"
            cursor.execute(query)
            rows = cursor.fetchall()

            # Insertar cada registro en el Treeview con colores alternados
            for i, row in enumerate(rows):
                # Determinar etiqueta de color para filas alternadas
                tag = "odd_row" if i % 2 == 0 else "even_row"

                # Insertar en el Treeview con etiqueta
                self.tree.insert("", "end", values=(*row, "📝 Analizar"), tags=(tag,))

            # Configurar los estilos para las filas
            self.tree.tag_configure("odd_row", background="#F0F0F0")  # Color para filas pares
            self.tree.tag_configure("even_row", background="#FFFFFF")  # Color para filas impares

            print("Interfaz actualizada con los datos de la base de datos activa.")  # Debug

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo cargar la interfaz: {str(e)}")       
        
    def create_new_database(self):
        db_path = filedialog.asksaveasfilename(
            defaultextension=".db", 
            filetypes=[("SQLite Database", "*.db")]
        )
        if db_path:
            try:
                # Inicializar la nueva base de datos
                init_db(db_path)  # Crear la base con su esquema inicial

                # Cambiar a la nueva base usando switch_database
                self.switch_database(db_path)

                messagebox.showinfo("Éxito", f"Se creó una nueva base de datos: {db_path}")

            except Exception as e:
                messagebox.showerror("Error", f"Hubo un problema al crear la base de datos: {str(e)}")
 
    
    # Añade este nuevo método para manejar clics en el Treeview
  

    def on_tree_click(self, event):
        # Identificar la región y la columna
        region = self.tree.identify("region", event.x, event.y)
        column = self.tree.identify_column(event.x)

        if region == "cell":
            if column == "#9":  # Columna de enlaces
                self.on_link_click(event)
            elif column == "#10":  # Columna de acciones
                self.on_action_click(event)

    def on_link_click(self, event):
        # Obtener el registro seleccionado
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor selecciona un documento.")
            return

        try:
            # Obtener el enlace desde la columna correspondiente
            item_values = self.tree.item(selected_item[0])["values"]
            enlace = item_values[8]  # Índice 8: Columna 'Enlace'

            if not enlace:
                messagebox.showerror("Error", "No se encontró un enlace válido.")
                return

            # Verificar si el enlace es una URL o un path local
            if enlace.startswith("http://") or enlace.startswith("https://"):
                webbrowser.open(enlace)  # Abrir el enlace en el navegador
            elif os.path.exists(enlace):
                os.startfile(enlace)  # Abrir el archivo con el editor asociado
            else:
                messagebox.showerror("Error", "El enlace o archivo no es válido o no se puede abrir.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el enlace: {str(e)}")

    def on_action_click(self, event):
        # Obtener el registro seleccionado
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
            analysis_window = AnalysisForm(self.master, document_id, self.current_db_path)
            self.analysis_windows[document_id] = analysis_window.window

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el análisis: {str(e)}")
    
    def crear_menu_contextual(self):
        # Crear el menú contextual
        self.menu_contextual = tk.Menu(self.master, tearoff=0)
        self.menu_contextual.add_command(label="Copiar selección como CSV", command=self.copiar_seleccion_como_csv)

        # Vincular el evento de clic derecho al Treeview
        self.tree.bind("<Button-3>", self.mostrar_menu_contextual)  # Botón derecho del mouse
    
    def mostrar_menu_contextual(self, event):
        try:
            self.menu_contextual.tk_popup(event.x_root, event.y_root)  # Mostrar el menú en la posición del clic
        except Exception as e:
            print(f"Error al mostrar el menú contextual: {str(e)}")
    
    def copiar_seleccion_como_csv(self):
        try:
            selected_items = self.tree.selection()
            if not selected_items:
                messagebox.showwarning("Advertencia", "No se seleccionaron registros para copiar.")
                return

            csv_data = ""
            for item in selected_items:
                row_values = self.tree.item(item, "values")
                csv_data += ",".join(str(value) for value in row_values) + "\n"

            # Copiar al portapapeles
            self.master.clipboard_clear()
            self.master.clipboard_append(csv_data.strip())
            self.master.update()

            messagebox.showinfo("Éxito", "Registros seleccionados copiados como CSV.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo copiar los registros: {str(e)}")
    
    
    
    
    
                        
    def open_project_manager(self):
        ProyectoManager(self.master)        
                
    # Modifica el método load_documents:
    def load_documents(self):
        # Cargar documentos desde la base de datos y actualizar la grilla
        self.db_connection.conn = sqlite3.connect(self.current_db_path)
        cursor = self.db_connection.conn.cursor()
         
        cursor.execute("SELECT Cid, cite_key, title, author, year, etiqueta, cumplimiento_de_criterios, referencia_apa, enlace FROM documentos")
        rows = cursor.fetchall()
        
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert("", "end", values=(*row, "📝 Analizar"))  # Icono añadido aquí
                
    
    def open_database(self):
        db_path = filedialog.askopenfilename(filetypes=[("SQLite Database", "*.db")])
        if db_path:
            try:
                # Llamamos al método switch_database para cambiar a la nueva base de datos
                self.switch_database(db_path)

                # Habilitar el menú de importación si la conexión es exitosa
                self.import_menu.entryconfig(0, state=tk.NORMAL)
                messagebox.showinfo("Éxito", f"Base de datos abierta: {db_path}")

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir la base de datos: {str(e)}")
            
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
            
            
            
 
 
 
 
            
 # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
 # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
 # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
 # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
 #                            IMPORTACIONES
 # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<  
 # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<  
 # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<  
 # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<  
 
 
 
 
 
 
 
          
    def import_from_bib(self):
        if not self.current_db_path:
            messagebox.showerror("Error", "Primero abra una base de datos")
            return

        try:
             # Crear una nueva instancia de BibImporter
            self.bib_importer = BibImporter(self.current_db_path)
            imported_count = self.bib_importer.import_bib_file(self.master)

            if imported_count > 0:
                self.refresh_documents_list()
                messagebox.showinfo("Éxito", f"Importados {imported_count} documentos")
                self.save_database()  
            else:
                messagebox.showinfo("Info", "No se importaron documentos nuevos")

        except Exception as e:
            messagebox.showerror("Error", f"Fallo en importación: {str(e)}")
        
 

    def import_links_from_excel(self):
        if not self.current_db_path:
            messagebox.showerror("Error", "Primero abra una base de datos.")
            return

        try:
            ruta_archivo = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
            if ruta_archivo:
                imported_count = importar_enlaces(ruta_archivo, self.current_db_path)
                if imported_count > 0:
                    self.refresh_documents_list()
                    messagebox.showinfo("Éxito", f"Importados {imported_count} enlaces.")
                else:
                    messagebox.showinfo("Info", "No se importaron enlaces nuevos.")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo en importación: {str(e)}")       
        
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
                       "etiqueta", "cumplimiento_de_criterios", "referencia_apa", "enlace" 
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

    def import_text_to_database(self):
        if not self.current_db_path:
            messagebox.showerror("Error", "Primero abra una base de datos.")
            return
        try:
            # Crear una ventana modal para importar texto
            from importar_texto import ImportarTextoVentana
            ImportarTextoVentana(self.master, self.current_db_path)  # Pasar la ventana principal y el path de la base
            self.refresh_documents_list()
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al abrir ventana de importación: {str(e)}")
    
      
    def create_document(self):
        # Abrir el formulario para crear un documento
        DocumentForm(self.master, mode="create")
        
        
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
                form = DocumentForm(self, mode="edit", document_id=document_id)
                form.parent_app = self  # Esto permite acceder a current_db_path

                # No es necesario llamar a load_document aquí, ya se llama en DocumentForm.__init__
                # form.load_document()  

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

            #conn = connect_to_db(self.current_db_path)  # Usar la variable de instancia
            # Obtener la base de datos activa
            cursor = self.db_connection.conn.cursor()
            
            #cursor = conn.cursor()

            # Usar el nombre correcto de la columna (Cid)
            cursor.execute("DELETE FROM documentos WHERE Cid = ?", (document_id,))
            
            self.db_connection.conn.commit()
            self.db_connection.conn.close()
            #conn.commit()
            #conn.close()

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
        analysis_window = AnalysisForm(self.master, document_id, current_db_path)
        self.analysis_windows[document_id] = analysis_window.window  # Guardar referencia







 # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
 # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
 # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
 #                         FORMULARIO DE DOCUMENTOS
 # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<  
 # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<  
 # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<  
 # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<  
 
 
 
 
 



# Formulario para manejar creación y edición de documentos
class DocumentForm:
    def __init__(self, parent, mode, document_id=None):
        self.parent_app = parent  # Aquí guardamos la referencia a App

        self.window = Toplevel(parent.master)  # Definir la ventana como un Toplevel

        self.window.title("Formulario Documento")
        self.mode = mode
        self.document_id = document_id

        try:  # Capturar errores durante la inicialización
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
         
            # Referencia APA
            ttk.Label(main_frame, text="Enlace:").grid(row=13, column=0, sticky="e", padx=padx_default, pady=pady_default)
            self.enlace_entry = ttk.Entry(main_frame, width=entry_width)
            self.enlace_entry.grid(row=13, column=1, sticky="ew", pady=pady_default)

            # Botón Guardar
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=14, column=0, columnspan=2, pady=(20, 0))

            ttk.Button(button_frame, text="Guardar", command=self.save_document).pack(pady=10, ipadx=20)

            # Configuración de grid para expansión
            main_frame.rowconfigure(6, weight=1)  # Hacer que la fila del resumen se expanda

            if self.mode == "edit":
                self.load_document()

            # Cargar combobox después de inicializar
            list_manager.actualizar_combobox(self.combobox_etiquetas, 'etiquetas.csv')

        except Exception as e:
            messagebox.showerror("Error", f"Error en la inicialización de DocumentForm: {str(e)}")
            print(f"Error en DocumentForm.__init__: {str(e)}")
            raise  # Re-lanzar el error para que se maneje en update_document       
        
    def load_document(self):
            if not self.document_id:
                print("Error: No hay document_id definido")
                return

            try:
                # Usar connect_to_db en lugar de sqlite3.connect directamente
                conn = connect_to_db(self.parent_app.current_db_path)  # Usar la conexión de la App
                cursor = conn.cursor()

                print(f"Consultando documento con ID: {self.document_id}")

                cursor.execute("""
                    SELECT cite_key, title, author, year, abstract, 
                           scolr_tags, etiqueta, cumplimiento_de_criterios, referencia_apa, enlace 
                    FROM documentos 
                    WHERE Cid = ?
                """, (self.document_id,))

                document = cursor.fetchone()
                conn.close()  # Cerrar la conexión aquí

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
                self.enlace_entry.delete(0, tk.END)

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
                self.enlace_entry.insert(0, document[9] or "")

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
        enlace = self.enlace_entry.get()

        # Validación básica de campos requeridos
        if not all([cite_key, title, author, year]):
            messagebox.showwarning("Advertencia", "Por favor complete los campos obligatorios: CiteKey, Título, Autor y Año")
            return

        conn = None
        try:
            conn = connect_to_db(self.parent_app.current_db_path)
            cursor = conn.cursor()

            if self.mode == "create":
                cursor.execute("""
                    INSERT INTO documentos (cite_key, title, author, year, abstract, 
                                        scolr_tags, etiqueta, cumplimiento_de_criterios, referencia_apa, enlace)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?)
                """, (cite_key, title, author, year, abstract, scolr_tags, etiqueta, cumplimiento, referencia_apa, enlace))
                messagebox.showinfo("Éxito", "Documento creado exitosamente.")
            elif self.mode == "edit":
                cursor.execute("""
                    UPDATE documentos
                    SET cite_key = ?, title = ?, author = ?, year = ?, abstract = ?, 
                        scolr_tags = ?, etiqueta = ?, cumplimiento_de_criterios = ?, referencia_apa = ?, enlace = ?
                    WHERE Cid = ?
                """, (cite_key, title, author, year, abstract, scolr_tags, etiqueta, cumplimiento, referencia_apa, enlace, self.document_id))
                messagebox.showinfo("Éxito", "Documento actualizado exitosamente.")

            conn.commit()

            # Actualizar la lista de documentos en la ventana principal
            app_instance = self.window.master._app_instance
            if app_instance:
                #app_instance.load_documents()
                self.refresh_ui()

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
                
                


if __name__ == "__main__":
    root = tk.Tk()  # Crear la ventana principal
    app = App(root)  # Instanciar la clase App
    root._app_instance = app  # Hacer accesible la instancia de App
    root.mainloop()  # Iniciar el bucle de eventos de la aplicación