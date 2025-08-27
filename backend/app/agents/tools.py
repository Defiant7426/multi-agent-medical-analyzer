from langchain.tools import tool
import re

def _parse_input(input_str: str) -> tuple[float, float]:
    """Función interna para procesar el string de entrada del agente."""
    # Limpiamos la entrada de paréntesis y espacios
    cleaned_str = input_str.strip().strip('()')
    
    # Usamos una expresión regular para encontrar todos los números (enteros o decimales)
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", cleaned_str)
    
    if len(numbers) != 2:
        raise ValueError(f"Se esperaban 2 números, pero se encontraron {len(numbers)} en la entrada: '{input_str}'")
    
    num1 = float(numbers[0])
    num2 = float(numbers[1])
    return num1, num2

@tool
def es_mayor_que(input_str: str) -> bool:
    """
    Compara dos números para ver si el primero es estrictamente mayor que el segundo.
    La entrada debe ser una cadena de texto con dos números separados por coma. Ejemplo: '37.1, 18.5'
    """
    a, b = _parse_input(input_str)
    return a > b

@tool
def es_menor_que(input_str: str) -> bool:
    """
    Compara dos números para ver si el primero es estrictamente menor que el segundo.
    La entrada debe ser una cadena de texto con dos números separados por coma. Ejemplo: '10.2, 20.5'
    """
    a, b = _parse_input(input_str)
    return a < b

@tool
def es_mayor_o_igual_que(input_str: str) -> bool:
    """
    Compara dos números para ver si el primero es mayor o igual que el segundo.
    La entrada debe ser una cadena de texto con dos números separados por coma. Ejemplo: '37.1, 18.5'
    """
    a, b = _parse_input(input_str)
    return a >= b

@tool
def es_menor_o_igual_que(input_str: str) -> bool:
    """
    Compara dos números para ver si el primero es menor o igual que el segundo.
    La entrada debe ser una cadena de texto con dos números separados por coma. Ejemplo: '24.9, 37.1'
    """
    a, b = _parse_input(input_str)
    return a <= b