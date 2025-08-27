import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from backend.app.agents.specialist import crear_agente_evaluador

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0)
agente_executor = crear_agente_evaluador(llm)

with open("backend/app/data/pacientes.json", "r", encoding="utf-8") as f:
    pacientes = json.load(f)
with open("backend/app/data/criterios.json", "r", encoding="utf-8") as f:
    criterios = json.load(f)

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
async def evaluar_paciente(paciente_id: str, prueba: str = "IMC"):
      """
      Recibe el ID del paciente y el nombre de la prueba,
      y utiliza al agente para determinar su aptitud
      """
      # Buscamos al paciente
      paciente = next((p for p in pacientes if p["paciente_id"]==paciente_id), None)

      if not paciente:
           raise HTTPException(status_code=404, detail="Paciente no encontrado")
      
      # Ahora buscamos su prueba dado el nombre de la prueba
      resultado_paciente = next((r for r in paciente["resultados"] if r["nombre_prueba"]==prueba), None)
      if not resultado_paciente:
           raise HTTPException(status_code=404, detail=f"Prueba '{prueba}' no encontrada para el paciente {paciente_id}")
      
      #Extraemos la informacion que necesitamos
      valor_str = resultado_paciente["valor"]
      valor_float = float(valor_str.split()[0])
      perfil = paciente["perfil"]
      empresa = paciente["empresa"]

      # Buscamos el criterio para esta prueba y perfil
      try:
           criterios_prueba = criterios[empresa][perfil]["INGRESO"]["General"][prueba]
      except KeyError:
           raise HTTPException(status_code=404, detail="Criterios no encontrados para el perfil y la prueba especificados")
      
      # Preparamos la entrada e invocamos al agente
      input_data = {
           "valor_paciente": valor_float,
           "criterios_json": json.dumps(criterios_prueba["rangos"])
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