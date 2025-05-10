import sqlite3
import csv
from tkinter import ttk,filedialog, messagebox
from list_manager import ListManager
import tkinter as tk
import json
           





# #########################################################


# MODIFICACIONES PARA QUE INCLUYA EL ABSTRACT Y TRABAJAR POR EL CID

# ########################################################





def copiar_seleccion_como_csv(tree, db_path, master):
    """
    Copia los registros seleccionados del Treeview en formato CSV al portapapeles, incluyendo el Cid.
    
    Argumentos:
        tree: El widget Treeview con los datos cargados.
        db_path: Ruta a la base de datos SQLite.
        master: Ventana principal (para acceder al portapapeles).
    """
    try:
        # Obtener las filas seleccionadas del Treeview
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showwarning("Advertencia", "No se seleccionaron registros para copiar.")
            return

        # Extraer los Cite Key de los registros seleccionados
        selected_cite_keys = [
            tree.item(item, "values")[0]  # Se asume que cite_key está en la columna 2
            for item in selected_items #Se modifica para que trabaje por el CID
        ]

        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Preparar la consulta para obtener Cid y otros campos de los registros seleccionados
        placeholders = ", ".join(["?"] * len(selected_cite_keys))  # Crear marcadores de posición
        query = f"""
            SELECT Cid, cite_key, title, author, year,abstract, etiqueta, cumplimiento_de_criterios
            FROM documentos
            WHERE Cid IN ({placeholders})
        """
        cursor.execute(query, selected_cite_keys)
        registros = cursor.fetchall()

        # Crear el contenido CSV
        csv_data = "Cid,Cite Key,Title,Author,Year,Etiqueta,Cumplimiento\n"
        for registro in registros:
            csv_data += ",".join(str(campo) if campo is not None else "" for campo in registro) + "\n"

        # Copiar al portapapeles
        master.clipboard_clear()
        master.clipboard_append(csv_data.strip())
        master.update()  # Actualizar el portapapeles

        messagebox.showinfo("Éxito", "Registros seleccionados copiados al portapapeles en formato CSV.")
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Error al consultar la base de datos: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"Error inesperado: {e}")
    finally:
        if conn:
            conn.close()

def exportar_a_csv(db_path, salida_csv, tabla="documentos"):
    """
    Exporta todos los registros de la tabla especificada a un archivo CSV.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query = f"SELECT * FROM {tabla}"
        cursor.execute(query)
        registros = cursor.fetchall()

        # Obtener los nombres de las columnas
        columnas = [desc[0] for desc in cursor.description]

        # Crear archivo CSV
        with open(salida_csv, mode="w", newline="", encoding="utf-8") as archivo_csv:
            writer = csv.writer(archivo_csv)
            writer.writerow(columnas)  # Escribir encabezados
            writer.writerows(registros)  # Escribir registros

        conn.close()
        print(f"Registros exportados a {salida_csv} correctamente.")
    except sqlite3.Error as e:
        print(f"Error al exportar registros: {e}")
        raise
    
    
    
    
    
    
    
    
    
 

def copiar_analisis_como_csv(tree, db_path, master):
    """
    Copia los registros seleccionados de análisis en formato CSV al portapapeles.
    
    Argumentos:
        tree: Widget Treeview con los datos de análisis.
        db_path: Ruta a la base de datos SQLite.
        master: Ventana principal.
    """
    try:
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showwarning("Advertencia", "No se seleccionaron análisis para copiar.")
            return

        # Obtener IDs de los análisis seleccionados
        selected_ids = [tree.item(item, "values")[0] for item in selected_items]

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        placeholders = ", ".join(["?"] * len(selected_ids))
        query = f"""
            SELECT a.id, d.cite_key, d.title, a.dimension, a.descripcion, a.archivo
            FROM analisis a
            JOIN documentos d ON a.documento_id = d.Cid
            WHERE a.id IN ({placeholders})
            ORDER BY a.dimension, d.cite_key
        """
        cursor.execute(query, selected_ids)
        registros = cursor.fetchall()

        # Crear contenido CSV con encabezados
        csv_data = "ID,Cite Key,Title,Dimensión,Descripción,Archivo\n"
        for registro in registros:
            csv_data += ",".join(f'"{str(campo)}"' if campo is not None else '""' for campo in registro) + "\n"

        # Copiar al portapeles
        master.clipboard_clear()
        master.clipboard_append(csv_data.strip())
        master.update()

        messagebox.showinfo("Éxito", f"{len(selected_ids)} análisis copiados como CSV.")
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Error en la base de datos: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"Error inesperado: {e}")
    finally:
        if conn:
            conn.close()

def exportar_analisis_a_csv(db_path, salida_csv, dimension=None):
    """
    Exporta análisis a CSV, opcionalmente filtrados por dimensión.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if dimension:
            query = """
                SELECT a.id, d.cite_key, d.title, a.dimension, a.descripcion, a.archivo
                FROM analisis a
                JOIN documentos d ON a.documento_id = d.Cid
                WHERE a.dimension = ?
                ORDER BY d.cite_key
            """
            cursor.execute(query, (dimension,))
        else:
            query = """
                SELECT a.id, d.cite_key, d.title, a.dimension, a.descripcion, a.archivo
                FROM analisis a
                JOIN documentos d ON a.documento_id = d.Cid
                ORDER BY a.dimension, d.cite_key
            """
            cursor.execute(query)

        registros = cursor.fetchall()
        columnas = [desc[0] for desc in cursor.description]

        with open(salida_csv, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columnas)
            writer.writerows(registros)

        return True
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Error al exportar: {e}")
        return False
    finally:
        if conn:
            conn.close()
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            # ###############################################################################
            
            
            #     MODIFICAREMOS UN CONJUTO DE REGISTROS SELECCIONADOS
            
            
            # ################################################################################
            
   

def modificar_metadatos(tree, db_path, master):
    """Abre una ventana modal para modificar los metadatos de los registros seleccionados."""
    selected_items = tree.selection()
    if not selected_items:
        messagebox.showwarning("Advertencia", "Selecciona al menos un registro para modificar.")
        return

    # Obtener los Cid de los registros seleccionados
    selected_cid = [tree.item(item, "values")[0] for item in selected_items]

    # Conectar a la base de datos y obtener los datos actuales
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    placeholders = ", ".join(["?"] * len(selected_cid))
    query = f"""SELECT cite_key, title, author, year, abstract, scolr_tags, etiqueta, 
                       cumplimiento_de_criterios, referencia_apa FROM documentos WHERE Cid IN ({placeholders})"""

    cursor.execute(query, selected_cid)
    registros = cursor.fetchall()
    conn.close()

    # Construir JSON inicial con los valores actuales
    json_data = [dict(zip(["cite_key", "title", "author", "year", "abstract", "scolr_tags", "etiqueta",
                           "cumplimiento_de_criterios", "referencia_apa"], registro)) for registro in registros]

    # Crear ventana modal
    edit_window = tk.Toplevel(master)  # Ahora usa el argumento `master`
    edit_window.title("Modificar Metadatos")
    edit_window.geometry("700x500")

    # Área de texto para editar JSON
    text_widget = tk.Text(edit_window, wrap="word", font=("Arial", 10))
    text_widget.pack(fill="both", expand=True, padx=10, pady=10)
    text_widget.insert("1.0", json.dumps(json_data, indent=4))

    # Función para guardar cambios
    def guardar_cambios():
        try:
            nuevos_datos = json.loads(text_widget.get("1.0", tk.END).strip())

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            for cid, datos in zip(selected_cid, nuevos_datos):
                cursor.execute("""
                    UPDATE documentos SET cite_key=?, title=?, author=?, year=?, abstract=?, scolr_tags=?, 
                    etiqueta=?, cumplimiento_de_criterios=?, referencia_apa=? WHERE Cid=?
                """, (datos["cite_key"], datos["title"], datos["author"], datos["year"], datos["abstract"], 
                      json.dumps(datos["scolr_tags"]), datos["etiqueta"], datos["cumplimiento_de_criterios"], 
                      datos["referencia_apa"], cid))

            conn.commit()
            conn.close()

            messagebox.showinfo("Éxito", "Los metadatos fueron actualizados correctamente.")
            edit_window.destroy()  

        except json.JSONDecodeError:
            messagebox.showerror("Error", "El formato JSON no es válido. Revisa la estructura antes de guardar.")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo actualizar los registros en la base de datos: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")

    # Botón para guardar cambios
    btn_guardar = ttk.Button(edit_window, text="Guardar Cambios", command=guardar_cambios)
    btn_guardar.pack(fill="x", padx=10, pady=10)
    
    
    
    
    
def aplicar_metadatos_a_grupo(tree, db_path, master):
    """Permite aplicar los mismos metadatos a un conjunto de registros seleccionados."""
    selected_items = tree.selection()
    if not selected_items:
        messagebox.showwarning("Advertencia", "Selecciona al menos un registro para modificar.")
        return

    # Obtener los Cid de los registros seleccionados
    selected_cid = [tree.item(item, "values")[0] for item in selected_items]

    # Crear ventana modal
    edit_window = tk.Toplevel(master)
    edit_window.title("Aplicar Metadatos a Grupo")
    edit_window.geometry("700x500")

    # JSON de muestra para completar
    json_modelo = """{
        "cite_key": "nuevo_cite",
        "title": "Nuevo título",
        "author": "Autor",
        "year": "2025",
        "abstract": "Resumen aquí",
        "scolr_tags": ["NADA"],
        "etiqueta": "Etiqueta común",
        "cumplimiento_de_criterios": "Criterio válido",
        "referencia_apa": "Referencia estándar"
    }"""

    # Área de texto para editar JSON
    text_widget = tk.Text(edit_window, wrap="word", font=("Arial", 10))
    text_widget.pack(fill="both", expand=True, padx=10, pady=10)
    text_widget.insert("1.0", json_modelo)

    # Función para aplicar los cambios a todos los registros seleccionados
    def guardar_cambios():
        try:
            nuevos_datos = json.loads(text_widget.get("1.0", tk.END).strip())

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            for cid in selected_cid:
                cursor.execute("""
                    UPDATE documentos SET cite_key=?, title=?, author=?, year=?, abstract=?, scolr_tags=?, 
                    etiqueta=?, cumplimiento_de_criterios=?, referencia_apa=? WHERE Cid=?
                """, (nuevos_datos["cite_key"], nuevos_datos["title"], nuevos_datos["author"], nuevos_datos["year"], 
                      nuevos_datos["abstract"], json.dumps(nuevos_datos["scolr_tags"]), nuevos_datos["etiqueta"], 
                      nuevos_datos["cumplimiento_de_criterios"], nuevos_datos["referencia_apa"], cid))

            conn.commit()
            conn.close()

            messagebox.showinfo("Éxito", "Los metadatos fueron aplicados correctamente a todos los registros seleccionados.")
            edit_window.destroy()  

        except json.JSONDecodeError:
            messagebox.showerror("Error", "El formato JSON no es válido. Revisa la estructura antes de guardar.")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo actualizar los registros en la base de datos: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")

    # Botón para guardar cambios
    btn_guardar = ttk.Button(edit_window, text="Aplicar Metadatos", command=guardar_cambios)
    btn_guardar.pack(fill="x", padx=10, pady=10)
