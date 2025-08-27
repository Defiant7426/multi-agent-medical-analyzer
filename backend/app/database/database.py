from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# Definimos la URL de nuestra base de datos SQLite
DATABASE_URL = "sqlite:///./medical_eval.db"

# Creamos el motor de la base de datos
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Crea todas las tablas en la base de datos
    basandose en los modelos definidos
    """
    print("Inicializando la base de datos y creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("Base de datos Creada.")