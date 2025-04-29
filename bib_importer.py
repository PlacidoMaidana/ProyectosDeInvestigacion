import re
import sqlite3
from tkinter import ttk,filedialog, messagebox
import tkinter as tk

from typing import Optional
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode




class BibImporter:
    def __init__(self, db_path: str):
        """Inicializa con ruta obligatoria a la base de datos"""
        if not db_path:
            raise ValueError("Se requiere ruta de base de datos")
        self.db_path = db_path
        self.conn = None  # Conexión se creará cuando sea necesario

    def connect(self) -> bool:
        """Establece conexión a la base de datos"""
        try:
            if self.conn is None:
                print(f"Conectando a BD en: {self.db_path}")  # Debug
                self.conn = sqlite3.connect(self.db_path)
                self.conn.execute("PRAGMA foreign_keys = ON")
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Conexión fallida: {str(e)}")
            return False

    def disconnect(self):
        """Cierra la conexión de forma segura"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Para context manager"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Garantiza que la conexión se cierre"""
        self.disconnect()

    def insert_entry(self, entry: dict) -> bool:
        """Inserta una entrada con manejo robusto de conexión"""
        if not self.connect():  # Asegura conexión activa
            return False

        try:
            cursor = self.conn.cursor()
            
            # Construcción segura de la consulta
            columns = ['cite_key', 'title', 'author', 'year', 'abstract', 
                      'scolr_tags', 'etiqueta', 'cumplimiento_de_criterios', 'referencia_apa']
            
            # Preparar valores (manejo de None)
            values = (
                entry['cite_key'],
                entry['fields'].get('title', ''),
                entry['fields'].get('author', '').replace(' and ', '; '),
                int(entry['fields'].get('year', 0)) if entry['fields'].get('year', '').isdigit() else None,
                entry['fields'].get('abstract', ''),
                entry['fields'].get('keywords', ''),
                entry['type'],
                '',
                self.generate_apa_citation(entry)
            )

            query = """
                INSERT INTO documentos 
                (cite_key, title, author, year, abstract, 
                 scolr_tags, etiqueta, cumplimiento_de_criterios, referencia_apa)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(query, values)
            self.conn.commit()  # Commit explícito
            print(f"Documento insertado: {entry['cite_key']}")  # Debug
            return True
            
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Error al insertar {entry['cite_key']}: {str(e)}")  # Debug
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
    
    def parse_bib_file(self, filepath: str) -> list:
        """Analiza un archivo BibTeX y devuelve una lista de entradas estructuradas.

        Args:
            filepath: Ruta al archivo .bib a analizar

        Returns:
            Lista de diccionarios con la estructura:
            [
                {
                    'type': 'article|book|etc',
                    'cite_key': 'clave_de_referencia',
                    'fields': {
                        'title': '...',
                        'author': '...',
                        'year': '...',
                        # otros campos...
                    }
                },
                # más entradas...
            ]
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as bibfile:
                # Configurar el parser para mayor compatibilidad
                parser = BibTexParser()
                parser.customization = convert_to_unicode
                parser.ignore_nonstandard_types = False
                parser.homogenize_fields = True

                bib_database = bibtexparser.load(bibfile, parser=parser)

                # Convertir a nuestro formato estándar
                entries = []
                for entry in bib_database.entries:
                    processed_entry = {
                        'type': entry['ENTRYTYPE'],
                        'cite_key': entry['ID'],
                        'fields': {k.lower(): v for k, v in entry.items() 
                                  if k not in ['ENTRYTYPE', 'ID']}
                    }
                    entries.append(processed_entry)

                return entries

        except FileNotFoundError:
            messagebox.showerror("Error", f"No se encontró el archivo: {filepath}")
            return []
        except Exception as e:
            messagebox.showerror("Error", f"Error al analizar el archivo BibTeX: {str(e)}")
            return []
        
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
                try:
                    if self.insert_entry(entry):  # <-- Aquí se llama a insert_entry()
                        success_count += 1
                except Exception as e:
                    print(f"Error al insertar entrada: {str(e)}")  # Log individual

                if progress and progress.winfo_exists():
                    progress.update_progress(i, len(entries))
                else:
                    break

            self.conn.commit()  # Asegurar commit al final de todas las inserciones
            messagebox.showinfo(
                "Importación completada",
                f"Proceso finalizado.\nDocumentos importados: {success_count}\nErrores: {len(entries) - success_count}"
            )
            return success_count

        except Exception as e:
            if self.conn:
                self.conn.rollback()  # Rollback si hay error general
            messagebox.showerror("Error crítico", f"Error durante la importación: {str(e)}")
            print(f"Error de importación: {str(e)}")  # Log general
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
    
 
 
 
 
 
 
 
 
 
 
 
 
def obtener_campo_bib(bloque, campo):
    """
    Extrae el valor de un campo específico dentro de un bloque .bib.
    Limpia caracteres extraños como "}," al final de los valores.
    """
    for line in bloque.split("\n"):
        if campo in line:
            value = line.split("=", 1)[1].strip().strip("{}").strip(",}")
            return value
    raise ValueError(f"Campo '{campo}' no encontrado en el bloque.") 
 
 

 
def procesar_bib_generativo(contenido):
    registros = []
    bloques = contenido.split("@misc")
    for bloque in bloques:
        print(f"Bloque bruto: {bloque}")  # Depuración
        bloque = bloque.strip()
        if not bloque:
            continue

        try:
            Cid_raw = obtener_campo_bib(bloque, "id")
            Cid_cleaned = Cid_raw.strip(",}")
            if not Cid_cleaned.isdigit():
                raise ValueError(f"Valor inválido para Cid: {Cid_raw}")
            Cid = int(Cid_cleaned)
            evaluacion = obtener_campo_bib(bloque, "evaluacion")
            detalle = obtener_campo_bib(bloque, "detalle")
            analisis_detallado = obtener_campo_bib(bloque, "analisis_detallado")
            registros.append((Cid, evaluacion, detalle, analisis_detallado))
        except ValueError as e:
            print(f"Error procesando bloque .bib: {e}")

    print(f"Registros procesados: {registros}")  # Depuración final
    return registros



def actualizar_registros_generativos(registros, db_path):
    """
    Actualiza los registros de la tabla documentos y agrega análisis generativos.
    Cada registro utiliza Cid como identificador único.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        registros_actualizados = 0
        for Cid, evaluacion, detalle, analisis_detallado in registros:
            # Actualizar campos en la tabla documentos
            cursor.execute("""
                UPDATE documentos
                SET etiqueta = ?, cumplimiento_de_criterios = ?
                WHERE Cid = ?
            """, (evaluacion, detalle, Cid))

            if cursor.rowcount > 0:
                # Agregar análisis en la tabla analisis
                cursor.execute("""
                    INSERT INTO analisis (documento_id, dimension, descripcion)
                    VALUES (?, ?, ?)
                """, (Cid, "Resumen IA", analisis_detallado))
                registros_actualizados += 1
            else:
                print(f"Registro con Cid {Cid} no encontrado. Será ignorado.")

        conn.commit()
        print(f"Registros actualizados: {registros_actualizados}")
    except sqlite3.Error as e:
        raise Exception(f"Error al actualizar la base de datos: {e}")
    finally:
        if conn:
            conn.close()
            
            
            
            
            
            
                    
# Clase para la ventana modal

class ImportarBibVentana:
    def __init__(self, master, db_path):
        self.master = master
        self.db_path = db_path

        self.modal_window = tk.Toplevel(self.master)
        self.modal_window.title("Importar desde .bib generativo")
        self.modal_window.geometry("600x400")
        self.modal_window.transient(self.master)
        self.modal_window.grab_set()

        ttk.Label(self.modal_window, text="Introduce el contenido .bib:", font=("Arial", 12)).pack(pady=10)
        self.text_input = tk.Text(self.modal_window, wrap="word", font=("Arial", 10))
        self.text_input.pack(fill="both", expand=True, padx=10, pady=10)
        ttk.Button(self.modal_window, text="Procesar e Importar", command=self.procesar_bib_generativo).pack(pady=10)

    def procesar_bib_generativo(self):
        contenido = self.text_input.get("1.0", tk.END).strip()
        if not contenido:
            messagebox.showerror("Error", "El contenido está vacío. Por favor pega el listado .bib.")
            return

        try:
            registros = procesar_bib_generativo(contenido)
            if registros:
                actualizar_registros_generativos(registros, self.db_path)
                messagebox.showinfo("Éxito", f"Se procesaron e importaron {len(registros)} registros correctamente.")
                self.modal_window.destroy()
            else:
                messagebox.showwarning("Advertencia", "No se encontraron registros válidos en el contenido.")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo en el procesamiento: {e}")