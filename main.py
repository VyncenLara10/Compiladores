import Analizador

# Ejemplo de uso

# Ejemplo de uso
codigo_ejemplo = """
int main(){
print "Hola mundo";
}
"""

# Analisis lexico
tokens = Analizador.identificar(codigo_ejemplo)
print("Tokens encontrados: ")
for tipo, valor in tokens:
    print(f"{tipo}: {valor}")

# Analisis sintactico
try:
    print("\nIniciando análisis sintáctico...")
    parser = Analizador.Parser(tokens)
    parser.parsear()
    print("Analisis sintáctico completado sin errores.")
except SyntaxError as e:
    print(e)
