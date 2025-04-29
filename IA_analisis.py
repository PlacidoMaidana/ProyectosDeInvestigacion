import sqlite3
import csv
from tkinter import ttk,filedialog, messagebox

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
            tree.item(item, "values")[1]  # Se asume que cite_key está en la columna 2
            for item in selected_items
        ]

        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Preparar la consulta para obtener Cid y otros campos de los registros seleccionados
        placeholders = ", ".join(["?"] * len(selected_cite_keys))  # Crear marcadores de posición
        query = f"""
            SELECT Cid, cite_key, title, author, year, etiqueta, cumplimiento_de_criterios
            FROM documentos
            WHERE cite_key IN ({placeholders})
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