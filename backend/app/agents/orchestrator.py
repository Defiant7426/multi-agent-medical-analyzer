from typing import List, TypedDict, Dict
from sqlalchemy.orm import Session
from backend.app.database import models
from langgraph.graph import StateGraph
from functools import partial
from .specialist import crear_agente_evaluador
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json

load_dotenv()

class GraphState(TypedDict):
    patient_id: str # ID del paciente a evaluar
    tests_to_run: List[str] # Lista con los nombres de las pruebas a realizar
    test_results: Dict[str, Dict[str,str]] # Un diccionario para guardar los resultados de cada prueba
    final_veredict: str # El veredicto final consolidado

def fetch_patient_test(state:GraphState, db:Session) -> GraphState:
    """
    Primer nodo: Se conecta a la BD para buscar todas las pruebas 
    asociadas al perfil del paciente.
    """ 
    print("Obteniendo las pruebas del paciente...")
    patient_id = state["patient_id"]

    # Buscamos al paciente
    paciente = db.query(models.Paciente).filter(models.Paciente.paciente_id == patient_id).first()
    if not paciente:
        raise ValueError(f"No se encontro al paciente con ID {patient_id}")

    # Buscamos todos los criterios y pruebas asociados
    criterios = db.query(models.Criterio).filter(
        models.Criterio.empresa == paciente.empresa,
        models.Criterio.perfil == paciente.perfil
    ).all()

    if not criterios:
        raise ValueError(f"No se encontraron criterios para el perfil {paciente.perfil}")

    # Extraemos los nombres de las pruebas
    test = [c.nombre_prueba for c in criterios]

    print(f"-> Pruebas a realizar para el perfil '{paciente.perfil}': {test}")

    # Actualizamos los estados
    state["tests_to_run"] = test
    state["test_results"] = {}

    return state

llm = ChatOpenAI(model="gpt-4o", temperature = 0)
evaluation_agent_executor = crear_agente_evaluador(llm)

def run_evaluation_agent(state: GraphState, db: Session) -> GraphState:
    """
    Segundo nodo: Ejecuta el agente evaluador para una prueba especifica
    """
    print("Nodo: Ejecutando Agente Evaluador")

    # Tomamos la primera prueba de la lista de pendientes
    tests_pending = state["tests_to_run"]
    current_test = tests_pending.pop(0)
    print(f"-> Evaluando prueba: '{current_test}'")

    patient_id = state['patient_id']

    # Obtenemos de la BD los datos necesarios para esta prueba
    paciente = db.query(models.Paciente).filter(models.Paciente.paciente_id == patient_id).first()
    resultado_paciente = db.query(models.Resultado).filter(
        models.Resultado.paciente_id == paciente.id,
        models.Resultado.nombre_prueba == current_test
    ).first()
    criterio = db.query(models.Criterio). filter(
        models.Criterio.empresa == paciente.empresa,
        models.Criterio.perfil == paciente.perfil,
        models.Criterio.nombre_prueba == current_test
    ).first()

    valor_paciente_str = resultado_paciente.valor

    try:
        valor_para_agente = float(valor_paciente_str.split()[0].replace(",","."))
    except (ValueError, IndexError):
        valor_para_agente = valor_paciente_str.strip()

    # Preparamos la entrada para el agente evaluador
    criterio_para_agente = {
        "apto": criterio.apto, 
        "observado": criterio.observado,
        "no_apto": criterio.no_apto
    }
    input_data = {
        "valor_paciente": valor_para_agente,
        "criterios_json": json.dumps(criterio_para_agente)
    }

    # Invocamos al agente
    result = evaluation_agent_executor.invoke(input_data)
    conclusion = result.get("output", "Error")

    reasoning_steps = result.get("intermediate_steps", [])
    formatted_reasoning = ""

    for action, observation in reasoning_steps:
        formatted_reasoning += (
            f"Pensamiento: {action.log.strip()}\n"
            f"Accion: {action.tool}({action.tool_input})\n"
            f"Observacion: {observation}\n---\n"
        )

    print(f"-> Conclusión del agente: {conclusion}")

    # Actualizamos el estado
    current_results = state["test_results"]
    current_results[current_test] = {
        "verdict":conclusion,
        "reasoning": formatted_reasoning
    }

    state["tests_to_run"] = tests_pending
    state["test_results"] = current_results

    return state

def decide_next_step(state:GraphState) -> str:
    """
    Tercer nodo (condicional): Revisa si aun quedan pruebas por evaluar.
    """
    print("Nodo: Decidiendo siguiente paso...")

    if len(state["tests_to_run"]) > 0:
        print("-> Aun quedan pruebas. Continuando evaluación.")
        return "continue_evaluation"
    
    else:
        print("-> No quedan mas pruebas. Finalizado.")
        return "finish_evaluation"

def consolidate_result(state: GraphState) -> GraphState:
    """
    Nodo final: Revisa todos los resultados individuales
    y genera el veredicto final del paciente.
    """
    print("Nodo: Consolidando Resultados")

    test_results = state["test_results"]

    verdicts = [res["verdict"] for res in test_results.values()]

    final_verdicts = "Apto"
    if any("No Apto" in v for v in verdicts):
        final_verdicts = "No Apto"
    elif any("Observado" in v for v in verdicts):
        final_verdicts = "Observado"
    
    print(f"-> Veredicto final consolidado: {final_verdicts}")

    state["final_veredict"] = final_verdicts
    return state

def build_graph(db_session: Session):
    """
    Construye y compila el grafo del orquestador con el bucle de evaluacion
    """
    workflow = StateGraph(GraphState)

    # Inyectamos la BD
    fetch_patient_test_with_db = partial(fetch_patient_test, db=db_session)
    run_evaluation_agent_with_db = partial(run_evaluation_agent, db=db_session)

    # Primer nodo del grafo
    workflow.add_node("fetch_tests", fetch_patient_test_with_db)
    workflow.add_node("run_agent", run_evaluation_agent_with_db)
    #workflow.add_node("router", decide_next_step) # No necesita la BD
    workflow.add_node("consolidate", consolidate_result)

    # Punto de entrada del grafo
    workflow.set_entry_point("fetch_tests")

    # Vamos al router para decidir
    #workflow.add_edge("fetch_tests", "router")
    #workflow.add_edge("run_agent", "router")

    workflow.add_edge("consolidate", "__end__")

    # Creamos la ARISTA CONDICIONAL
    workflow.add_conditional_edges(
        "fetch_tests",
        decide_next_step,
        {
            "continue_evaluation": "run_agent",
            "finish_evaluation": "consolidate"
        }
    )
    workflow.add_conditional_edges(
        "run_agent",
        decide_next_step,
        {
            "continue_evaluation": "run_agent",
            "finish_evaluation":  "consolidate"
        }
    )
    # Compilamos el grafo
    return workflow.compile()