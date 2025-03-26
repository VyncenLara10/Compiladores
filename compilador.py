import re
from nodos import *
import json

# === Analisis Lexico ===
# Definir los patrones para los diferentes tipos de tokens
token_patron = {
    "KEYWORD": r'\b(if|else|while|switch|case|return|print|break|for|int|float|void|double|char)\b',
    "IDENTIFIER": r'\b[a-zA-Z_][a-zA-Z0-9_]*\b',
    "NUMBER": r'\b\d+(\.\d+)?\b',
    "OPERATOR": r'[\+\-\*\/\=\<\>\!\_]',
    "DELIMITER": r'[(),;{}]',
    "WHITESPACE": r'\s+',
    "STRING": r'"[^"]*"',
}


def identificar_tokens(texto):
    # Unir todos los patrones en un unico patron realizando grupos nombrados
    patron_general = "|".join(f"(?P<{token}>{patron})" for token, patron in token_patron.items())
    patron_regex = re.compile(patron_general)
    tokens_encontrados = []
    for match in patron_regex.finditer(texto):
        for token, valor in match.groupdict().items():
            if valor is not None and token != "WHITESPACE":
                tokens_encontrados.append((token, valor))
    return tokens_encontrados


# === Analizador Sintactico ===
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.funciones = []

    def obtener_token_actual(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def coincidir(self, tipo_esperado):
        token_actual = self.obtener_token_actual()
        if token_actual and token_actual[0] == tipo_esperado:
            self.pos += 1
            return token_actual
        else:
            raise SyntaxError(f'Error sintactico: se esperaba {tipo_esperado}, pero se encontro: {token_actual}')

    def parsear(self):
        # Punto de entrada del analizador sintactico: se espera una o mas funciones
        funciones = []
        while self.pos < len(self.tokens):
            funcion = self.funcion()
            funciones.append(funcion)

        # Verificar que exista al menos una función 'main'
        existe_main = any(funcion.nombre == 'main' for funcion in funciones)
        if not existe_main:
            raise SyntaxError("Error sintactico: Debe existir una funcion 'main' en el codigo.")

        # Verificar que la ultima funcion sea 'main'
        if funciones[-1].nombre != 'main':
            raise SyntaxError("Error sintactico: La funcion 'main' debe ser la ultima en el codigo.")

        return NodoPrograma(funciones)  # Devolver un nodo Programa

    def llamada_funcion(self):
        """
        Procesa una llamada a funcion, como `suma(4, 3);`.
        """
        nombre_funcion = self.coincidir('IDENTIFIER')  # Nombre de la funcion
        self.coincidir('DELIMITER')  # Se espera un '('
        argumentos = self.argumentos()  # Analizar los argumentos
        self.coincidir('DELIMITER')  # Se espera un ')'
        self.coincidir('DELIMITER')  # Se espera un ';'
        return NodoLlamadaFuncion(nombre_funcion[1], argumentos)

    def argumentos(self):
        """
        Procesa los argumentos de una llamada a funcion.
        """
        argumentos = []
        while self.obtener_token_actual() and self.obtener_token_actual()[
            1] != ')':  # Mientras no se cierre el parentesis
            argumentos.append(self.expresion_ing())  # Analizar la expresion
            if self.obtener_token_actual() and self.obtener_token_actual()[1] == ',':
                self.coincidir('DELIMITER')  # Consumir la coma
        return argumentos

    def funcion(self):
        # Gramatica para una funcion: KEYWORD IDENTIFIER ( PARAMETROS ) { CUERPO }
        tipo_retorno = self.coincidir('KEYWORD')  # Tipo de retorno (ej. int)
        nombre_funcion = self.coincidir('IDENTIFIER')  # Nombre de la funcion
        self.coincidir('DELIMITER')  # Se espera un '('
        parametros = self.parametros()  # Analizar los parametros
        self.coincidir('DELIMITER')  # Se espera un ')'
        self.coincidir('DELIMITER')  # Se espera un '{'
        cuerpo = self.cuerpo()  # Analizar el cuerpo de la funcion
        self.coincidir('DELIMITER')  # Se espera un '}'
        return NodoFuncion(nombre_funcion[1], parametros, cuerpo)

    def parametros(self):
        parametros = []
        # Reglas para parametros: KEYWORD IDENTIFIER (, KEYWORD IDENTIFIER)*
        while self.obtener_token_actual() and self.obtener_token_actual()[
            1] != ')':  # Mientras no se cierre el paréntesis
            tipo = self.coincidir('KEYWORD')  # Tipo del parametro (ej. int)
            nombre = self.coincidir('IDENTIFIER')  # Nombre del parametro (ej. a)
            parametros.append(NodoParametro(tipo[1], nombre[1]))  # Guardar el tipo y nombre
            if self.obtener_token_actual() and self.obtener_token_actual()[1] == ',':
                self.coincidir('DELIMITER')  # Consumir la coma
        return parametros

    def declaracion(self):
        # Regla para declaracion: KEYWORD IDENTIFIER '=' EXPRESION DELIMITER
        self.coincidir('KEYWORD')
        self.coincidir('IDENTIFIER')

        token_actual = self.obtener_token_actual()
        if token_actual and token_actual[1] == '=':  # Si es una asignacion
            self.coincidir('OPERATOR')  # Se espera un =
            self.expresion()  # El resto de la declaracion aritmetica

        self.coincidir('DELIMITER')  # Se espera un ';'

    def asignacion(self):
        # Gramatica para el cuerpo: return IDENTIFIER OPERATOR IDENTIFIER;
        tipo = self.coincidir('KEYWORD')  # tipo
        nombre = self.coincidir('IDENTIFIER')  # Identificador <nombre de la variable>
        self.coincidir('OPERATOR')  # Operador ej. =
        expresion = self.expresion_ing()
        self.coincidir('DELIMITER')  # ;
        return NodoAsignacion(nombre, expresion)

    def retorno(self):
        self.coincidir('KEYWORD')  # return
        expresion = self.expresion_ing()
        self.coincidir('DELIMITER')  # ;
        return NodoRetorno(expresion)

    def cuerpo(self):
        instrucciones = []
        while self.obtener_token_actual() and self.obtener_token_actual()[1] != '}':
            token_actual = self.obtener_token_actual()

            if token_actual[0] == 'KEYWORD':
                if token_actual[1] == 'if':
                    instrucciones.append(self.bucle_if())
                elif token_actual[1] == 'print':
                    instrucciones.append(self.printf_llamada())
                elif token_actual[1] == 'return':
                    instrucciones.append(self.retorno())
                # ... otros keywords
                else:
                    instrucciones.append(self.declaracion())

            elif token_actual[0] == 'IDENTIFIER':
                siguiente_token = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
                if siguiente_token and siguiente_token[1] == '(':
                    instrucciones.append(self.llamada_funcion())
                else:
                    instrucciones.append(self.asignacion())

            # Añadir manejo de expresiones literales (números, strings)
            elif token_actual[0] in ['NUMBER', 'STRING']:
                # Si es un literal suelto, lo tratamos como expresión
                instrucciones.append(self.expresion_ing())
                self.coincidir('DELIMITER')  # Consumir el ;

            else:
                raise SyntaxError(
                    f'Error sintactico: se esperaba una declaracion valida, pero se encontro: {token_actual}')

        return instrucciones

    def expresion_ing(self):
        izquierda = self.termino()  # Obtener el primer término
        while self.obtener_token_actual() and self.obtener_token_actual()[0] == 'OPERATOR':
            operador = self.coincidir('OPERATOR')
            derecha = self.termino()
            izquierda = NodoOperacion(izquierda, operador[1], derecha)
        return izquierda

    def termino(self):
        token = self.obtener_token_actual()
        if token[0] == 'NUMBER':
            return NodoNumero(self.coincidir('NUMBER'))
        elif token[0] == 'IDENTIFIER':
            return NodoIdentificador(self.coincidir('IDENTIFIER'))
        elif token[0] == 'STRING':
            return NodoString(self.coincidir('STRING'))
        else:
            raise SyntaxError(f'Error sintactico: Termino no valido {token}')

    def expresion(self):
        """
        Analiza expresiones matematicas o de concatenacion, por ejemplo:
        - x + y * 2
        - "hola" + nombre
        """
        if self.obtener_token_actual()[0] in ['IDENTIFIER', 'NUMBER', 'STRING']:
            self.coincidir(self.obtener_token_actual()[0])  # Consumir identificador, número o cadena
        else:
            raise SyntaxError(
                f"Error sintactico: Se esperaba IDENTIFIER, NUMBER o STRING, pero se encontro {self.obtener_token_actual()}")

        while self.obtener_token_actual() and self.obtener_token_actual()[0] in ['OPERATOR']:
            self.coincidir('OPERATOR')  # Consumir operador
            if self.obtener_token_actual()[0] in ['IDENTIFIER', 'NUMBER', 'STRING']:
                self.coincidir(self.obtener_token_actual()[0])  # Consumir identificador, número o cadena
            else:
                raise SyntaxError(
                    f"Error sintactico: Se esperaba IDENTIFIER, NUMBER o STRING despues de {self.obtener_token_anterior()}")

    def bucle_if(self):
        """
        Analiza la estructura de una sentencia if-else.
        """
        self.coincidir('KEYWORD')  # Se espera un if
        self.coincidir('DELIMITER')  # Se espera un (

        # Llamar a expresion_logica() para procesar la condicion
        self.expresion_logica()

        self.coincidir('DELIMITER')  # Se espera un )
        self.coincidir('DELIMITER')  # Se espera un {
        self.cuerpo()
        self.coincidir('DELIMITER')  # Se espera un }

        # Manejo opcional de else
        if self.obtener_token_actual() and self.obtener_token_actual()[1] == 'else':
            self.coincidir('KEYWORD')  # Se espera un else
            self.coincidir('DELIMITER')  # Se espera un {
            self.cuerpo()
            self.coincidir('DELIMITER')  # Se espera un }

    def expresion_logica(self):
        """
        Analiza expresiones logicas como:
        - resultado > x
        - a == b
        - x != 10 && y < 5
        """
        # La expresion logica puede iniciar con un IDENTIFIER o un NUMBER
        if self.obtener_token_actual()[0] in ['IDENTIFIER', 'NUMBER']:
            self.coincidir(self.obtener_token_actual()[0])  # Consumir el identificador o numero
        else:
            raise SyntaxError(
                f"Error sintactico: Se esperaba IDENTIFIER o NUMBER, pero se encontro {self.obtener_token_actual()}")

        # Esperar un operador relacional (>=, <=, ==, !=, >, <, !)
        if self.obtener_token_actual()[1] in ['<', '>', '!']:
            self.coincidir('OPERATOR')  # Consumir operador
            if self.obtener_token_actual()[0] == 'OPERATOR' and self.obtener_token_actual()[1] == '=':
                self.coincidir('OPERATOR')
        elif self.obtener_token_actual()[1] == '=':
            self.coincidir('OPERATOR')
            if self.obtener_token_actual()[1] != '=':
                raise SyntaxError(f"Error sintactico: Se esperaba un =, pero se encontro {self.obtener_token_actual()}")
            self.coincidir('OPERATOR')
        else:
            raise SyntaxError(
                f"Error sintactico: Se esperaba un OPERADOR RELACIONAL, pero se encontro {self.obtener_token_actual()}")

        # Esperar otro IDENTIFIER o NUMBER despues del operador
        if self.obtener_token_actual()[0] in ['IDENTIFIER', 'NUMBER']:
            self.coincidir(self.obtener_token_actual()[0])  # Consumir el identificador o numero
        else:
            raise SyntaxError(
                f"Error sintactico: Se esperaba IDENTIFIER o NUMBER, pero se encontro {self.obtener_token_actual()}")

        # Manejo de operadores logicos compuestos (&&, ||)
        while self.obtener_token_actual() and self.obtener_token_actual()[1] in ['&&', '||']:
            self.coincidir('OPERATOR')  # Consumir operador logico
            if self.obtener_token_actual()[0] in ['IDENTIFIER', 'NUMBER']:
                self.coincidir(self.obtener_token_actual()[0])  # Consumir el identificador o numero
            else:
                raise SyntaxError(
                    f"Error sintactico: Se esperaba IDENTIFIER o NUMBER despues de {self.obtener_token_anterior()}")

    def printf_llamada(self):
        """
        Maneja las llamadas a printf como:
        printf("Mensaje", variable);
        printf(variable);
        """
        self.coincidir('KEYWORD')  # Se espera un printf
        self.coincidir('DELIMITER')  # Se espera (

        # Se espera una cadena o un identificador como primer argumento
        token_actual = self.obtener_token_actual()
        if token_actual[0] == 'STRING' or token_actual[0] == 'IDENTIFIER':
            self.coincidir(token_actual[0])  # Se espera una cadena o un identificador
        else:
            raise SyntaxError(f"Error sintáctico: Se esperaba STRING o IDENTIFIER, pero se encontro {token_actual}")

        # Puede haber mas argumentos separados por comas
        while self.obtener_token_actual() and self.obtener_token_actual()[1] == ',':
            self.coincidir('DELIMITER')  # Se espera un ,
            self.expresion()  # Puede ser un identificador o numero

        self.coincidir('DELIMITER')  # Se espera un )
        self.coincidir('DELIMITER')  # Se espera un ;

    def bucle_for(self):
        # Regla para el for KEYWORD DELIMITER DECLARACION EXPRESION_LOGICA DELIMITER INCREMENT DELIMITER DELIMITER
        """
        Maneja la estructura de un bucle for.
        """
        self.coincidir('KEYWORD')  # Se espera un for
        self.coincidir('DELIMITER')  # Se espera un (

        self.declaracion()

        self.expresion_logica()
        self.coincidir('DELIMITER')  # Se espera un ;

        self.operador_abreviado()
        # self.coincidir('DELIMITER')  # Se espera un )

        if self.obtener_token_actual()[0] == 'KEYWORD':
            self.cuerpo()
        else:
            self.coincidir('DELIMITER')  # Se espera un {
            self.cuerpo()
            self.coincidir('DELIMITER')  # Se espera un }

    def return_statement(self):
        self.coincidir('KEYWORD')
        self.expresion()
        self.coincidir('DELIMITER')

    def break_statement(self):
        """
        Maneja la sentencia break.
        """
        self.coincidir('KEYWORD')  # Se espera un break
        self.coincidir('DELIMITER')  # Se espera un ;

    def operador_abreviado(self):
        self.coincidir('IDENTIFIER')
        operador_actual1 = self.obtener_token_actual()
        self.coincidir('OPERATOR')
        operador_actual2 = self.obtener_token_actual()
        self.coincidir('OPERATOR')
        if operador_actual1[1] + operador_actual2[1] not in ['++', '--', '+=', '-=', '*=', '/=']:
            raise SyntaxError(
                f'Error sintactico: se esperaba una declaracion valida, pero se encontro: {operador_actual1[1], operador_actual2[1]}')
        self.coincidir('DELIMITER')

    def bucle_while(self):
        # Regla para bucle while: KEYWORD DELIMITER EXPRESION_LOGICA DELIMITER DELIMITER CUERPO DELIMITER
        self.coincidir('KEYWORD')  # Se espera un while
        self.coincidir('DELIMITER')  # Se espera un (
        self.expresion_logica()
        self.coincidir('DELIMITER')  # Se espera un )
        self.coincidir('DELIMITER')  # Se espera un {
        # self.printf_llamada()
        # self.increment()
        self.cuerpo()
        self.coincidir('DELIMITER')  # Se espera un }


# === Ejemplo de Uso ===
codigo_fuente = """
int comparar(int a, int b) {
    if (a > b) {
        return 1;
    } else {
        return 0;
    }
}

void main() {
    comparar(5, 3);        
}
"""

# Analisis lexico
tokens = identificar_tokens(codigo_fuente)
print("Tokens encontrados:")
for tipo, valor in tokens:
    print(f'{tipo}: {valor}')

# Analisis Sintactico
try:
    print('\nIniciando analisis sintactico...')
    parser = Parser(tokens)
    arbol_ast = parser.parsear()
    print('Analisis sintactico completado sin errores')

except SyntaxError as e:
    print(e)


def imprimir_ast(nodo):
    if isinstance(nodo, NodoPrograma):
        return {
            "Programa": [imprimir_ast(f) for f in nodo.funciones]
        }
    elif isinstance(nodo, NodoFuncion):
        return {
            "Funcion": nodo.nombre,
            "Parametros": [imprimir_ast(p) for p in nodo.parametros],
            "Cuerpo": [imprimir_ast(c) for c in nodo.cuerpo]
        }
    elif isinstance(nodo, NodoParametro):
        return {
            "Parametro": nodo.nombre,
            "Tipo": nodo.tipo
        }
    elif isinstance(nodo, NodoAsignacion):
        return {
            "Asignacion": nodo.nombre,
            "Expresion": imprimir_ast(nodo.expresion)
        }
    elif isinstance(nodo, NodoOperacion):
        return {
            "Operacion": nodo.operador,
            "Izquierda": imprimir_ast(nodo.izquierda),
            "Derecha": imprimir_ast(nodo.derecha)
        }
    elif isinstance(nodo, NodoRetorno):
        return {
            "Retorno": imprimir_ast(nodo.expresion)
        }
    elif isinstance(nodo, NodoIdentificador):
        return {
            "Identificador": nodo.nombre
        }
    elif isinstance(nodo, NodoNumero):
        return {
            "Numero": nodo.valor
        }
    elif isinstance(nodo, NodoLlamadaFuncion):
        return {
            "LlamadaFuncion": nodo.nombre,
            "Argumentos": [imprimir_ast(arg) for arg in nodo.argumentos]
        }
    return {}


parser = Parser(tokens)
arbol_ast = parser.parsear()
print(json.dumps(imprimir_ast(arbol_ast), indent=1))

codigo_asm = arbol_ast.generar_codigo()
print(codigo_asm)