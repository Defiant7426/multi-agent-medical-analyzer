from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(String, unique=True, index=True) # <-- "P00x"
    empresa = Column(String)
    perfil = Column(String)
    puesto_ocupacional = Column(String)
    sexo = Column(String)
    tipo_examen = Column(String)

    # Un paciente tiene mucho resultados
    resultados = relationship("Resultado", back_populates="paciente")

class Resultado(Base):
    __tablename__ = 'resultados'

    id = Column(Integer, primary_key=True, index = True)
    nombre_prueba = Column(String)
    valor = Column(String)
    paciente_id = Column(Integer, ForeignKey('pacientes.id'))

    # Relacion inversa: Un resultado pertenece a un paciente
    paciente = relationship("Paciente", back_populates="resultados")

class Criterio(Base):
    __tablename__ = 'criterios'

    id = Column(Integer, primary_key=True, index=True)
    empresa = Column(String, index=True)
    perfil = Column(String, index=True)
    nombre_prueba=Column(String, index=True)

    # Guardamos las reglas como texto (el agente sabra como interpretarlos)
    apto = Column(String)
    observado = Column(String)
    no_apto = Column(String)