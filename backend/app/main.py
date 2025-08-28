import os
import json
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from backend.app.agents.specialist import crear_agente_evaluador

from sqlalchemy.orm import Session
from .database import database, models
from typing import List, Dict
from backend.app.agents.orchestrator import build_graph

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

class ResultadoIndividual(BaseModel):
     prueba: str
     resultado: str
     razonamiento: str

class PerfilEvaluacionResponse(BaseModel):
     paciente_id: str
     veredicto_general: str
     evaluaciones: List[ResultadoIndividual]

@app.post("/evaluar-perfil/{paciente_id}", response_model=PerfilEvaluacionResponse)
async def evaluar_paciente(
     paciente_id: str, 
     db: Session = Depends(get_db)     
     ):
      """
      Invoca al agente orquestador para una evaluación completa del perfil del paciente
      """
      graph = build_graph(db)

      initial_input = {"patient_id": paciente_id}

      final_state = graph.invoke(initial_input)

      resultados_individuales = [
           ResultadoIndividual(prueba = test, resultado=res["verdict"], razonamiento=res["reasoning"])
           for test, res in final_state["test_results"].items()
      ]

      return PerfilEvaluacionResponse(
           paciente_id=final_state["patient_id"],
           veredicto_general=final_state["final_veredict"],
           evaluaciones = resultados_individuales
      )