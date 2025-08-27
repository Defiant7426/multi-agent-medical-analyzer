import streamlit as st
import requests
import json

st.set_page_config(page_title="Agente Médigo", layout="centered")

st.title("Analizador Médica con agentes de IA")

st.info("MVP de un unico agente para clasificar la aptitud de un empleado en una empresa")

paciente_id = st.selectbox(
    "Seleccione un Paciente para Evaluar",
    ("P001", "P002", "P003", "P004"),
    index = 0
)

prueba_a_evaluar = st.selectbox(
    "Seleccione la Prueba",
    ("Índice de Masa Corporal (IMC)", "Colesterol Total", "Edad")
)

if st.button(f"Evaluar '{prueba_a_evaluar}' para {paciente_id}"):
    api_url = f"http://127.0.0.1:8000/evaluar/{paciente_id}"
    params = {"prueba": prueba_a_evaluar}

    with st.spinner(f"El agente esta analizando el paciente {paciente_id}..."):
        try:
            response = requests.post(api_url,params=params)

            if response.status_code == 200:
                data = response.json()
                st.success("Evaluación Completada.")

                conclusion = data.get('conclusion', 'N/A')

                if "No Apto" in conclusion:
                    st.error(f"**Conclusion: {conclusion}**")
                elif "Observado" in conclusion:
                    st.warning(f"**Conclusion: {conclusion}**")
                else:
                    st.success(f"**Conclusion: {conclusion}**")
                
            else:
                st.error(f"Error en la API: {response.status_code}")
                try:
                    st.json(response.json())
                except json.JSONDecoderError:
                    st.text(response.text)
        except requests.exceptions.ConnectionError:
            st.error("No se puedo conectar con el backend")