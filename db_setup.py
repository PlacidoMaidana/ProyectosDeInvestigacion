import sqlite3

# Conexión dinámica basada en la base de datos activa
def connect_to_db(db_path):
    if not db_path:
        raise ValueError("No se proporcionó una ruta de base de datos.")
    return sqlite3.connect(db_path)

# Inicializar tablas si no existen
def init_db(db_path):
    conn = connect_to_db(db_path)
    cursor = conn.cursor()
    
    # Crear tabla Documentos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documentos (
        Cid INTEGER PRIMARY KEY AUTOINCREMENT,
        cite_key TEXT,
        title TEXT,
        author TEXT,
        year INTEGER,
        abstract TEXT,
        scolr_tags TEXT,
        etiqueta TEXT,
        cumplimiento_de_criterios TEXT,
        referencia_apa TEXT  
    )
    """)
    
    # Crear tabla Análisis (corrigiendo la clave foránea)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analisis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        documento_id INTEGER,
        dimension TEXT,
        descripcion TEXT,
        FOREIGN KEY (documento_id) REFERENCES documentos(Cid)
    )
    """)
    
    # Crear tabla Proyecto
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proyecto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        descripcion TEXT
    )
    """)
    
    
    conn.commit()
    conn.close()