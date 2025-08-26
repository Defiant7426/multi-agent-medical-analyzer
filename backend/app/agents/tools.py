from langchain.tools import tool

@tool
def es_mayor_que(a:float, b:float) -> bool:
    return a>b

@tool
def es_menor_que(a:float, b:float) -> bool:
    return a<b

@tool
def esta_entre(valor: float, minimo:float, maximo: float) -> bool:
    return minimo <= valor <= maximo