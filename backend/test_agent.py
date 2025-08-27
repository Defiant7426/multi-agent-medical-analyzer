import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Funcion que crea nuestro agente
from app.agents.specialist import crear_agente_evaluador

def main():
    """
    Función para probar el agente
    """
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: No se encontro API key")
        return
    
    print("API Key cargada")

    with open("app/data/pacientes.json", "r", encoding="utf-8") as f:
        pacientes = json.load(f)
    with open("app/data/criterios.json", "r", encoding="utf-8") as f:
        criterios = json.load(f)
    
    paciente_prueba = next((p for p in pacientes if p["paciente_id"] == "P003"), None)
    criterios_prueba = criterios["ROBOCON SERVICIOS SAC"]["PERFIL C: Chofer"]["INGRESO"]["General"]["Índice de Masa Corporal (IMC)"]

    valor_imc_str = paciente_prueba["resultados"][1]["valor"]
    valor_imc_float = float(valor_imc_str.split()[0])

    print(f"Probando con paciente: {paciente_prueba['paciente_id']}, IMC: {valor_imc_float}")

    llm = ChatOpenAI(model="gpt-4o", temperature = 0)
    print("LLM inicializado")

    agente_executor = crear_agente_evaluador(llm)
    print("Agente Creado")

    input_data = {
        "valor_paciente": valor_imc_float,
        "criterios_json": json.dumps(criterios_prueba["rangos"])
    }

    print("\nInvocando al agente...")
    resultado = agente_executor.invoke(input_data)

    print("Resultado Final:")
    print(resultado["output"])

if __name__ == "__main__":
    main()