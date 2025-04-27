import tkinter as tk
from tkinter import ttk, messagebox
import os

class ListManager:
    def __init__(self):
        # Puedes inicializar configuraciones aquí si es necesario
        pass

    def cargar_lista_desde_csv(self, archivo, valor_predeterminado="Seleccionar"):
        """Carga una lista desde un archivo CSV"""
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                elementos = [linea.strip() for linea in f.readlines() if linea.strip()]
            return [valor_predeterminado] + elementos
        except FileNotFoundError:
            # Si el archivo no existe, lo crea con valores por defecto
            with open(archivo, 'w', encoding='utf-8') as f:
                f.write("")
            return [valor_predeterminado]
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar {archivo}: {str(e)}")
            return [valor_predeterminado]

    def actualizar_combobox(self, combobox, archivo, valor_predeterminado="Seleccionar"):
        """Actualiza los valores de un Combobox"""
        valores = self.cargar_lista_desde_csv(archivo, valor_predeterminado)
        combobox['values'] = valores
        combobox.set(valor_predeterminado)

    def editar_lista_csv(self, archivo, titulo):
        """Ventana para editar listas CSV"""
        def guardar_cambios():
            nuevo_contenido = text_editor.get("1.0", tk.END).strip()
            try:
                with open(archivo, 'w', encoding='utf-8') as f:
                    f.write(nuevo_contenido)
                messagebox.showinfo("Éxito", f"Cambios guardados en {archivo}")
                editor.destroy()
                return True
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {str(e)}")
                return False

        # Crear ventana de edición
        editor = tk.Toplevel()
        editor.title(f"Editar {titulo}")
        editor.geometry("300x400")
        editor.minsize(300, 200)  # Tamaño mínimo

        # Frame principal
        main_frame = ttk.Frame(editor, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Texto explicativo
        ttk.Label(main_frame, text=f"Editar {titulo} (un elemento por línea)").pack(pady=5)

        # Editor de texto con scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        text_editor = tk.Text(text_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_editor.yview)
        text_editor.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Botones en un frame separado (ajuste clave)
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10, fill=tk.X)  # Ocupa el ancho completo

        ttk.Button(btn_frame, text="Guardar", command=guardar_cambios).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=editor.destroy).pack(side=tk.LEFT, padx=5)

        # Cargar contenido actual
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                contenido = f.read()
            text_editor.insert(tk.END, contenido)
        except FileNotFoundError:
            pass
        
        # Hacer que la ventana sea modal (opcional)
        editor.grab_set()
        editor.wait_window()

    def inicializar_archivos_csv(self):
        """Crea los archivos CSV iniciales si no existen"""
        listas = {
            'etiquetas.csv': ["Investigación", "Tesis", "Artículo", "Revisión", "Experimental"],
            'dimensiones.csv': ["Metodología", "Resultados", "Discusión", "Conclusiones", "Limitaciones"]
        }
        
        for archivo, valores in listas.items():
            if not os.path.exists(archivo):
                with open(archivo, 'w', encoding='utf-8') as f:
                    f.write("\n".join(valores))