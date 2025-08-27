import os
import json
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from backend.app.agents.specialist import crear_agente_evaluador

from sqlalchemy.orm import Session
from .database import database, models

def get_db(): # Dependencia de FastAPI (se ejecuta por cada peticion)
     db = database.SessionLocal()
     try:
          yield db
     finally:
          db.close()

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0)
agente_executor = crear_agente_evaluador(llm)

app = FastAPI(
      title="API de Agente Evaluador",
      description="Una API para evaluar la aptitud de un paciente."
)

class ResultadoEvaluacion(BaseModel):
      paciente_id: str
      prueba_evaluada: str
      valor_paciente: str
      conclusion: str
      razonamiento_completo: str

@app.post("/evaluar/{paciente_id}", response_model=ResultadoEvaluacion)
async def evaluar_paciente(
     paciente_id: str, 
     prueba: str = "IMC",
     db: Session = Depends(get_db)     
     ):
      """
      Recibe el ID del paciente y el nombre de la prueba,
      y utiliza al agente para determinar su aptitud
      """
      # Buscamos al paciente
      paciente = db.query(models.Paciente).filter(models.Paciente.paciente_id == paciente_id).first()

      if not paciente:
           raise HTTPException(status_code=404, detail="Paciente no encontrado")
      
      # Ahora buscamos su prueba dado el nombre de la prueba
      resultado_paciente = db.query(models.Resultado).filter(
           models.Resultado.paciente_id == paciente.id,
           models.Resultado.nombre_prueba == prueba
      ).first()
      if not resultado_paciente:
           raise HTTPException(status_code=404, detail=f"Prueba '{prueba}' no encontrada para el paciente {paciente_id}")
      
      #Extraemos la informacion que necesitamos
      valor_str = resultado_paciente.valor
      valor_float = float(valor_str.split()[0].replace(',','.'))

      # Buscamos el criterio para esta prueba y perfil
      criterio = db.query(models.Criterio).filter(
           models.Criterio.empresa == paciente.empresa,
           models.Criterio.perfil == paciente.perfil,
           models.Criterio.nombre_prueba == prueba
      ).first()
      if not criterio:
           raise HTTPException(status_code=404, detail="Criterios no encontrados para este paciente en especifico")
      
      criterios_para_agente = {
          "apto": criterio.apto,
          "observado": criterio.observado,
          "no_apto": criterio.no_apto
     }

      # Preparamos la entrada e invocamos al agente
      input_data = {
           "valor_paciente": valor_float,
           "criterios_json": json.dumps(criterios_para_agente)
      }

      try:
           resultado_agente = await agente_executor.ainvoke(input_data)
           conclusion = resultado_agente.get("output", "No se pudo obtener una conclusión")

           # Extraemos los pasos intermedios
           razonamiento = resultado_agente.get("intermediate_steps", [])

           razonamiento_formateado = ""
           
           for action, observation in razonamiento:
                razonamiento_formateado += f"Pensamiento: {action.log}\n"
                razonamiento_formateado += f"Acción: {action.tool}({action.tool_input})\n"
                razonamiento_formateado += f"Observación: {observation}\n-----\n"
           
      except Exception as e:
           raise HTTPException(status_code=500, detail=f"Error al invocal al agente: {e}")
      
      return ResultadoEvaluacion(
           paciente_id=paciente_id,
           prueba_evaluada=prueba,
           valor_paciente=valor_str,
           conclusion=conclusion,
           razonamiento_completo=razonamiento_formateado
      )