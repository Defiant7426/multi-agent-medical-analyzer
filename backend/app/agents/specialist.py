from .tools import (
    es_mayor_que,
    es_menor_que,
    es_mayor_o_igual_que,
    es_menor_o_igual_que
)
from langchain_core.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent

def crear_agente_evaluador(llm):
    """
    Crea un agente experto que razona sobre criterios medicos usando herramientas matematicas
    """
    tools = [es_mayor_que, es_menor_que, es_menor_o_igual_que, es_mayor_o_igual_que]

    prompt_template = """
    Eres un riguroso medico auditor que evalua los resultados de un paciente. Tu objetivo es determinar si un pacinte es 'Apto', 'Observado' o 'No Apto' basado en el valor de un conjunto de criterios.
    
    Para verificar si un valor esta 'entre' dos numeros (un rango), DEBES  usar DOS herramientas en DOS pasos separados:
    1. Primero, usa `es_mayor_o_igual_que` para verificar el limite inferior.
    2. Segundo, usa `es_menor_o_igual_que` para verfiicar el limite superior.
    Ambas condiciones deben de ser 'True' para que el valor este dentro del rango

    Sigue este proceso logico:    
    1. Analiza la regla para la condición 'Apto'.
    2. Usa una o más herramientas para verificar si el valor del paciente cumple ESTRICTAMENTE con esa regla.
    3. Si la cumple, tu conclusión final es 'Apto' y tu trabajo termina.
    4. Si NO la cumple, pasa a analizar la regla para 'Observado'. Usa las herramientas para verificarla.
    5. Si la cumple, tu conclusión es 'Observado'.
    6. Si tampoco la cumple, analiza la regla para 'No Apto' y verifícala con las herramientas.
    7. Basa tu conclusión final SOLAMENTE en el resultado booleano (True/False) que devuelven las herramientas.
    
    TIENES ACCESO A LAS SIGUIENTES HERRAMIENTAS:
    {tools}

    USA EL SIGUIENTE FORMATO PARA RESPONDER:
    Question: La pregunta original que debes responder
    Thought: Siempre debes de pensar que hacer
    Action: La acción a tomar, debe ser una de [{tool_names}]
    Action Input: La entrada para la accion
    Observation: El resultado de la accion
    ... (este patrón de Thought/Action/Action Input/Observation puede repetirse N veces)
    Thought: Ahora sé la respuesta final.
    Final Answer: La respuesta final a la pregunta original

    AHORA, COMIENZA

    Información del caso:
    - Valor del paciente {valor_paciente}
    - Criterios: {criterios_json}

    Inicia tu razonamiento:
    {agent_scratchpad}
    """

    prompt = PromptTemplate.from_template(prompt_template)

    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True, return_intermediate_steps=True)

    return agent_executor

