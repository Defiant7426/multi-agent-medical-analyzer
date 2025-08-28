import streamlit as st
import requests
import json

st.set_page_config(page_title="Agente Médigo", layout="wide")

st.title("Analizador Médica con agentes de IA")

st.info("Seleccciona un paciente y el Agente evaluará todas sus pruebas")

paciente_id = st.selectbox(
    "Seleccione un Paciente para una evaluacion completa",
    ("P001", "P002", "P003", "P004"),
    index = 0,
    help="El sistema buscará todas las pruebas necesarias para el perfil de este paciente"
)


if st.button(f"Iniciar evaluación para {paciente_id}"):
    api_url = f"http://127.0.0.1:8000/evaluar-perfil/{paciente_id}"

    with st.spinner(f"El agente esta analizando el paciente {paciente_id}..."):
        try:
            response = requests.post(api_url)

            if response.status_code == 200:
                data = response.json()
                st.success("Evaluación Completada.")

                veredicto_general = data.get("veredicto_general", "N/A")
                evaluaciones = data.get("evaluaciones", [])

                st.subheader("Veredicto General")

                col1, col2 = st.columns([1, 4])

                with col1:
                    if "No Apto" in veredicto_general:
                        st.error(f"**{veredicto_general}**")
                    elif "Observado" in veredicto_general:
                        st.warning(f"**{veredicto_general}**")
                    else:
                        st.success(f"**{veredicto_general}**")
                st.subheader("Desglose de Resultado por prueba")

                if not evaluaciones:
                    st.warning("No se encontrarion evaluaciones individuales.")
                else:
                    cols = st.columns(len(evaluaciones))
                    for i, evaluacion in enumerate(evaluaciones):
                        with cols[i]:
                            # resultado = evaluacion.get("resultado", "N/A")
                            st.metric(
                                label = evaluacion.get("prueba", "Prueba Desconocida"),
                                value= evaluacion.get("resultado", "N/A")
                            )
                            with st.expander("Ver razonamiento del agente"):
                                st.text(evaluacion.get("razonamiento", "No disponible."))
                
            else:
                st.error(f"Error en la API: {response.status_code}")
                try:
                    st.json(response.json())
                except json.JSONDecoderError:
                    st.text(response.text)
        except requests.exceptions.ConnectionError:
            st.error("No se puedo conectar con el backend")