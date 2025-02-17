import Analizador

# Ejemplo de uso
codigo_fuente = """
int suma(int a, int b) {

    int x = a + b * 2;
    int y = x - 5;
    return y;
}

"""

# Analisis lexico
tokens = Analizador.identificar(codigo_fuente)
print("Tokens encontrados: ")
for tipo, valor in tokens:
    print(f"{tipo}: {valor}")

# Analisis sintactico
try:
    print("\nIniciando analisis sintáctico...")
    parser = Analizador.Parser(tokens)
    parser.parsear()
    print("Analisis sintáctico completado sin errores.")
except SyntaxError as e:
    print(e)
