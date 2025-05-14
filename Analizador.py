from AST import *
from analizador_sintactico import *
from analizador_semantico import *

# === Ejemplo de Uso ===
codigo_fuente = """
int sumar(int a, int b) {
    return a + b;
}

int main() {
    int x;
    int y;
    printf("Ingrese Primer Numero: ")
    scanf("%d", &x);
    printf("Ingrese Segundo Numero: ")
    scanf("%d", &y);
    int resultado = sumar(x, y);

    if (resultado <= 0){
        printf("La suma %d + %d es: %d", &x, &y, &resultado);
    }

    while (resultado <= 5) {
        printf("%d", &resultado);
    }
    for (int i = 1; i <= 5; i++) {
        printf("%d", &i);
    }

    return 0;
}
"""

def main():
    tokens = identificar_tokens(codigo_fuente)
    print("Tokens encontrados:")
    for tipo, valor in tokens:
        print(f'{tipo}: {valor}')

    try:
        print('\nIniciando analisis sintactico...')
        parser = Parser(tokens)
        arbol_ast = parser.parsear()
        print('Analisis sintactico completado sin errores')
    except SyntaxError as e:
        print(e)

    try:
        parser = Parser(tokens)
        arbol_ast = parser.parsear()
        codigo_py = arbol_ast.traducir()
        print("------------------------------")
        print("Codigo Python")
        codigo_py = [linea.replace('\t', '    ') for linea in codigo_py]
        codigo_completo = "\n".join(codigo_py)
        print(codigo_completo)
        print("------------------------------")
        print('')
        codigo_asm = arbol_ast.generar_codigo()
        print("------------------------------")
        print("Código Ensamblador Generado:")
        print(codigo_asm)
        print("------------------------------")
    except SyntaxError as e:
        print(e)

    try:
        analizador_semantico = AnalizadorSemantico()
        analisis = analizador_semantico.analizar(arbol_ast)
        print('Analizador Semantico Tabla Simbolos')

        for llave in (analizador_semantico.tabla_simbolos.keys()):
            valor = analizador_semantico.tabla_simbolos.get(llave)
            print(f'{llave}: {valor}')
    except SyntaxError as e:
        print(e)

main()
