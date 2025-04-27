import re
import sqlite3
from tkinter import filedialog, messagebox
import tkinter as tk
from typing import Optional

class BibImporter:
    def __init__(self, db_path: str = None):
        """Inicializa con ruta a la base de datos (opcional)"""
        self.db_path = db_path
        self.conn = None
        print(f"la ruta de la base de datos en bib_importer constructor {db_path}")
        
    def connect(self, db_path: Optional[str] = None) -> bool:
        """Establece conexión a la base de datos"""
        print(f"la ruta de la base de datos en bib_importer connect {db_path}")
        if db_path:
            self.db_path = db_path
        
        if not self.db_path:
            messagebox.showerror("Error", "No se ha especificado la ruta a la base de datos")
            return False
        
        try:
            self.conn = sqlite3.connect(self.db_path)
            # Activar foreign keys si es necesario
            self.conn.execute("PRAGMA foreign_keys = ON")
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo conectar a la base de datos: {str(e)}")
            return False
    
    def disconnect(self):
        """Cierra la conexión a la base de datos"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        """Para uso con context manager"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Para uso con context manager"""
        self.disconnect()
    
    def parse_bib_file(self, filepath: str) -> Optional[list]:
        """Parsea archivo .bib con manejo de errores mejorado"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            entries = []
            # Expresión regular mejorada para mayor robustez
            entry_pattern = re.compile(
                r'@(?P<type>\w+)\s*{\s*(?P<key>[^,\s]+)\s*,\s*(?P<fields>.*?)(?=\s*@|\s*$)',
                re.DOTALL | re.UNICODE
            )
            
            for match in entry_pattern.finditer(content):
                entry = {
                    'cite_key': match.group('key'),
                    'type': match.group('type'),
                    'fields': {}
                }
                
                # Parseo de campos con manejo de comillas y llaves
                field_pattern = re.compile(
                    r'(?P<name>\w+)\s*=\s*(?P<value>\{.*?\}|".*?"|\w+)',
                    re.DOTALL | re.UNICODE
                )
                
                for field_match in field_pattern.finditer(match.group('fields')):
                    field_name = field_match.group('name').lower()
                    field_value = field_match.group('value')
                    
                    # Eliminar llaves/comillas exteriores
                    if field_value.startswith('{') and field_value.endswith('}'):
                        field_value = field_value[1:-1]
                    elif field_value.startswith('"') and field_value.endswith('"'):
                        field_value = field_value[1:-1]
                    
                    entry['fields'][field_name] = field_value.strip()
                
                entries.append(entry)
            
            return entries
        
        except UnicodeDecodeError:
            messagebox.showerror("Error", "El archivo no está en UTF-8. Por favor guarda el archivo con codificación UTF-8.")
            return None
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar el archivo .bib: {str(e)}")
            return None
    def insert_entry(self, entry: dict) -> bool:
        """Inserta una entrada individual con manejo de transacciones"""
        if not self.conn:
            if not self.connect():
                return False

        try:
            cursor = self.conn.cursor()

            # Construcción de la consulta SQL segura
            columns = []
            placeholders = []
            values = []

            field_mapping = {
                'cite_key': entry['cite_key'],
                'title': entry['fields'].get('title', ''),
                'author': entry['fields'].get('author', '').replace(' and ', '; '),
                'year': int(entry['fields'].get('year', 0)) if entry['fields'].get('year', '').isdigit() else None,
                'abstract': entry['fields'].get('abstract', ''),
                'scolr_tags': entry['fields'].get('keywords', ''),
                'etiqueta': entry['type'],
                'cumplimiento_de_criterios': '',
                'referencia_apa': self.generate_apa_citation(entry)
            }

            for col, val in field_mapping.items():
                if val is not None:  # Incluir todos los campos excepto None explícito
                    columns.append(f'"{col}"')  # Entre comillas para nombres con mayúsculas
                    placeholders.append('?')
                    values.append(val)

            if not columns:
                return False

            query = f"""
                INSERT INTO documentos ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """

            print(f"Ejecutando consulta: {query}")  # Debug
            print(f"Con valores: {values}")  # Debug

            cursor.execute(query, values)
            self.conn.commit()  # Commit explícito
            return True

        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Error en inserción: {str(e)}")  # Debug
            return False
    
           
    def generate_apa_citation(self, entry: dict) -> str:
        """Genera cita APA con más campos y validaciones"""
        authors = entry['fields'].get('author', '')
        year = entry['fields'].get('year', '')
        title = entry['fields'].get('title', '')
        journal = entry['fields'].get('journal', '')
        
        # Formatear autores
        if authors:
            authors_list = [a.strip() for a in authors.split(' and ')]
            formatted_authors = []
            
            for author in authors_list:
                if ',' in author:
                    last, first = [x.strip() for x in author.split(',', 1)]
                    initials = '. '.join([n[0] for n in first.split()]) + '.'
                    formatted_authors.append(f"{last}, {initials}")
                else:
                    parts = author.split()
                    if len(parts) > 1:
                        last = parts[-1]
                        initials = '. '.join([n[0] for n in parts[:-1]]) + '.'
                        formatted_authors.append(f"{last}, {initials}")
                    else:
                        formatted_authors.append(parts[0])
            
            authors_str = ', '.join(formatted_authors[:7])
            if len(formatted_authors) > 7:
                authors_str += ' et al.'
        else:
            authors_str = '[Autor desconocido]'
        
        # Construir cita APA
        citation_parts = []
        if authors_str:
            citation_parts.append(authors_str)
            citation_parts.append(f'({year})' if year else '[s.f.]')
        
        if title:
            citation_parts.append(title + '.')
        
        if journal:
            citation_parts.append(f'<i>{journal}</i>.')
        
        return ' '.join(citation_parts)
    
    def import_bib_file(self, parent_window=None) -> int:
        """Flujo completo de importación con manejo de conexión"""
        if not self.db_path:
            messagebox.showerror("Error", "Primero configure la ruta a la base de datos")
            return 0

        filepath = filedialog.askopenfilename(
            parent=parent_window,
            title="Seleccionar archivo BibTeX",
            filetypes=[("Archivos BibTeX", "*.bib"), ("Todos los archivos", "*.*")]
        )

        if not filepath:
            return 0

        try:
            if not self.connect():
                return 0

            entries = self.parse_bib_file(filepath)
            if not entries:
                return 0

            success_count = 0
            progress = self.show_progress_dialog(parent_window, len(entries))

            for i, entry in enumerate(entries, 1):
                if self.insert_entry(entry):  # <-- Aquí se llama a insert_entry()
                    success_count += 1

                if progress and progress.winfo_exists():
                    progress.update_progress(i, len(entries))
                else:
                    break
                
            messagebox.showinfo(
                "Importación completada",
                f"Proceso finalizado.\nDocumentos importados: {success_count}\nErrores: {len(entries) - success_count}"
            )
            return success_count

        except Exception as e:
            messagebox.showerror("Error crítico", f"Error durante la importación: {str(e)}")
            return 0
        finally:
            self.disconnect()
            if 'progress' in locals() and progress.winfo_exists():
                progress.destroy()
            
    def show_progress_dialog(self, parent, total_entries):
        """Muestra diálogo de progreso (implementación básica)"""
        # Implementación de un diálogo de progreso personalizado
        # Puedes usar tkinter.ttk.Progressbar o una solución más compleja
        class ProgressDialog:
            def __init__(self, parent, total):
                self.top = tk.Toplevel(parent)
                self.top.title("Importando documentos...")
                
                self.label = tk.Label(self.top, text="Procesando 0 de {total} documentos...")
                self.label.pack(pady=10)
                
                self.progress = tk.ttk.Progressbar(
                    self.top, 
                    orient="horizontal",
                    length=300,
                    mode="determinate",
                    maximum=total
                )
                self.progress.pack(pady=5)
                
                self.cancel_button = tk.Button(
                    self.top, 
                    text="Cancelar", 
                    command=self.top.destroy
                )
                self.cancel_button.pack(pady=5)
            
            def update_progress(self, current, total):
                self.label.config(text=f"Procesando {current} de {total} documentos...")
                self.progress['value'] = current
                self.top.update()
            
            def winfo_exists(self):
                return self.top.winfo_exists()
            
            def destroy(self):
                self.top.destroy()
        
        return ProgressDialog(parent, total_entries)