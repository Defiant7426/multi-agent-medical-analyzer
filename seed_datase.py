import json
from backend.app.database.database import SessionLocal
from backend.app.database.models import Paciente, Resultado, Criterio

def seed_data():
    """
    Lee los archivos JSON y los inserta en la base de datos.
    Se ejecuta una sola vez para poblar a la BD
    """
    db= SessionLocal()

    print("Poblando pacientes y resultados...")

    with open("backend/app/data/pacientes.json", "r", encoding="utf-8") as f:
        pacientes_data = json.load(f)
    
    for p_data in pacientes_data:
        # Evitamos duplicados
        paciente_existente = db.query(Paciente).filter_by(paciente_id=p_data["paciente_id"]).first()

        if not paciente_existente:
            nuevo_paciente = Paciente(
                paciente_id = p_data["paciente_id"],
                empresa=p_data["empresa"],
                perfil=p_data["perfil"],
                puesto_ocupacional=p_data["puesto_ocupacional"],
                sexo=p_data["sexo"],
                tipo_examen=p_data["tipo_examen"]
            )

            db.add(nuevo_paciente)
            # Hacemos un flust
            db.flush()

            for r_data in p_data["resultados"]:
                nuevo_resultado = Resultado(
                    nombre_prueba=r_data["nombre_prueba"],
                    valor=r_data["valor"],
                    paciente_id=nuevo_paciente.id
                )
                db.add(nuevo_resultado)
    db.commit()
    print("Poblando criterios...")

    with open("backend/app/data/criterios.json", "r", encoding="utf-8") as f:
        criterios_data = json.load(f)
    
    for empresa, perfiles in criterios_data.items():
        for perfil, tipos_examen in perfiles.items():
            pruebas = tipos_examen.get("INGRESO", {}).get("General",{})
            for nombre_prueba, detalles in pruebas.items():
                if isinstance(detalles, dict) and "rangos" in detalles:
                    rangos = detalles["rangos"]
                    # Evitamos duplicados
                    criterio_existente = db.query(Criterio).filter_by(empresa=empresa, perfil=perfil, nombre_prueba=nombre_prueba).first()
                    if not criterio_existente:
                        nuevo_criterio = Criterio(
                            empresa = empresa,
                            perfil=perfil,
                            nombre_prueba=nombre_prueba,
                            apto=rangos.get("apto", ''),
                            observado=rangos.get("observado", ''),
                            no_apto=rangos.get('no_apto', '')
                        )
                        db.add(nuevo_criterio)
    db.commit()
    print("Criterios poblados")

    db.close()
    print("Proceso completado.")

if __name__ == "__main__":
    seed_data()