import re
from nodos import *
import json
from keystone import Ks, KS_ARCH_X86, KS_MODE_32, KS_MODE_16
from analizadroSemantico import *

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
        funciones = []
        while self.pos < len(self.tokens):
            funcion = self.funcion()
            funciones.append(funcion)
        existe_main = any(funcion.nombre == 'main' for funcion in funciones)
        if not existe_main:
            raise SyntaxError("Error sintactico: Debe existir una funcion 'main' en el codigo.")
        if funciones[-1].nombre != 'main':
            raise SyntaxError("Error sintactico: La funcion 'main' debe ser la ultima en el codigo.")
        return NodoPrograma(funciones)

    def llamada_funcion(self):
        nombre_funcion = self.coincidir('IDENTIFIER')  # Nombre de la funcion
        self.coincidir('DELIMITER')  # Se espera un '('
        argumentos = self.argumentos()  # Analizar los argumentos
        self.coincidir('DELIMITER')  # Se espera un ')'
        self.coincidir('DELIMITER')  # Se espera un ';'
        return NodoLlamadaFuncion(nombre_funcion[1], argumentos)

    def funcion(self):
        tipo_retorno = self.coincidir('KEYWORD')  # Tipo de retorno (ej. int)
        nombre_funcion = self.coincidir('IDENTIFIER')  # Nombre de la funcion
        self.coincidir('DELIMITER')  # Se espera un '('
        parametros = self.parametros()  # Analizar los parametros
        self.coincidir('DELIMITER')  # Se espera un ')'
        self.coincidir('DELIMITER')  # Se espera un '{'
        cuerpo = self.cuerpo()  # Analizar el cuerpo de la funcion
        self.coincidir('DELIMITER')  # Se espera un '}'
        return NodoFuncion(nombre_funcion[1], parametros, cuerpo)

    def argumentos(self):
        argumentos = []
        while self.obtener_token_actual() and self.obtener_token_actual()[1] != ')':
            argumentos.append(self.expresion_ing())  # Analizar la expresion
            if self.obtener_token_actual() and self.obtener_token_actual()[1] == ',':
                self.coincidir('DELIMITER')  # Consumir la coma
        return argumentos

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
        tipo = self.coincidir('KEYWORD')  # Tipo de dato (ej. 'int')
        nombre = self.coincidir('IDENTIFIER')  # Nombre de la variable (ej. 'c')

        # Manejar asignación opcional (ej. '= a + b')
        if self.obtener_token_actual() and self.obtener_token_actual()[1] == '=':
            self.coincidir('OPERATOR')  # Consumir '='
            expresion = self.expresion_ing()  # Analizar la expresión (ej. 'a + b')
            nodo = NodoAsignacion(nombre, expresion)
        else:
            nodo = NodoDeclaracion(tipo[1], nombre[1])

        self.coincidir('DELIMITER')  # Consumir ';'
        return nodo

    def asignacion(self):
        # Gramatica para el cuerpo: return IDENTIFIER OPERATOR IDENTIFIER
        tipo = self.coincidir('KEYWORD')
        nombre = self.coincidir('IDENTIFIER')  
        self.coincidir('OPERATOR')
        expresion = self.expresion_ing()
        self.coincidir('DELIMITER')
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

            if token_actual[0] == 'DELIMITER' and token_actual[1] == ';':
                self.coincidir('DELIMITER')
                continue

            if token_actual[0] == 'KEYWORD':
                if token_actual[1] == 'if':
                    instrucciones.append(self.bucle_if())
                elif token_actual[1] == 'print':
                    instrucciones.append(self.llamada_printf())
                elif token_actual[1] == 'return':
                    instrucciones.append(self.retorno())
                elif token_actual[1] in ['int', 'float', 'void', 'double', 'char']:
                    instrucciones.append(self.declaracion())
                else:
                    raise SyntaxError(f'Error sintactico: Keyword no reconocido: {token_actual}')

            elif token_actual[0] == 'IDENTIFIER':
                siguiente_token = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
                if siguiente_token and siguiente_token[1] == '(':
                    instrucciones.append(self.llamada_funcion())
                else:
                    instrucciones.append(self.asignacion())

            elif token_actual[0] in ['NUMBER', 'STRING']:
                instrucciones.append(self.expresion_ing())
                self.coincidir('DELIMITER')

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
        # Para concatenar
        if self.obtener_token_actual()[0] in ['IDENTIFIER', 'NUMBER', 'STRING']:
            self.coincidir(self.obtener_token_actual()[0]) 
        else:
            raise SyntaxError(
                f"Error sintactico: Se esperaba IDENTIFIER, NUMBER o STRING, pero se encontro {self.obtener_token_actual()}")

        while self.obtener_token_actual() and self.obtener_token_actual()[0] in ['OPERATOR']:
            self.coincidir('OPERATOR') 
            if self.obtener_token_actual()[0] in ['IDENTIFIER', 'NUMBER', 'STRING']:
                self.coincidir(self.obtener_token_actual()[0])  
            else:
                raise SyntaxError(
                    f"Error sintactico: Se esperaba IDENTIFIER, NUMBER o STRING despues de {self.obtener_token_anterior()}")

    def bucle_if(self):
        self.coincidir('KEYWORD')  # Se espera un if
        self.coincidir('DELIMITER')
        self.expresion_logica()
        self.coincidir('DELIMITER')
        self.coincidir('DELIMITER')
        self.cuerpo()
        self.coincidir('DELIMITER')

        if self.obtener_token_actual() and self.obtener_token_actual()[1] == 'else':
            self.coincidir('KEYWORD')  # Se espera un else
            self.coincidir('DELIMITER')  # Se espera un {
            self.cuerpo()
            self.coincidir('DELIMITER')

    def expresion_logica(self):
        if self.obtener_token_actual()[0] in ['IDENTIFIER', 'NUMBER']:
            self.coincidir(self.obtener_token_actual()[0])
        else:
            raise SyntaxError(
                f"Error sintactico: Se esperaba IDENTIFIER o NUMBER, pero se encontro {self.obtener_token_actual()}")
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

        if self.obtener_token_actual()[0] in ['IDENTIFIER', 'NUMBER']:
            self.coincidir(self.obtener_token_actual()[0])  # Consumir el identificador o numero
        else:
            raise SyntaxError(
                f"Error sintactico: Se esperaba IDENTIFIER o NUMBER, pero se encontro {self.obtener_token_actual()}")

        while self.obtener_token_actual() and self.obtener_token_actual()[1] in ['&&', '||']:
            self.coincidir('OPERATOR')  # Consumir operador logico
            if self.obtener_token_actual()[0] in ['IDENTIFIER', 'NUMBER']:
                self.coincidir(self.obtener_token_actual()[0])  # Consumir el identificador o numero
            else:
                raise SyntaxError(
                    f"Error sintactico: Se esperaba IDENTIFIER o NUMBER despues de {self.obtener_token_anterior()}")

    def llamada_printf(self):
        self.coincidir('KEYWORD')  # Se espera un printf
        self.coincidir('DELIMITER')  # Se espera (
        token_actual = self.obtener_token_actual()
        if token_actual[0] == 'STRING' or token_actual[0] == 'IDENTIFIER':
            self.coincidir(token_actual[0])  # Se espera una cadena o un identificador
        else:
            raise SyntaxError(f"Error sintáctico: Se esperaba STRING o IDENTIFIER, pero se encontro {token_actual}")
        while self.obtener_token_actual() and self.obtener_token_actual()[1] == ',':
            self.coincidir('DELIMITER')
            self.expresion()

        self.coincidir('DELIMITER')
        self.coincidir('DELIMITER')

    def bucle_for(self):
        self.coincidir('KEYWORD')  # Se espera un for
        self.coincidir('DELIMITER')  # Se espera un (
        self.declaracion()
        self.expresion_logica()
        self.coincidir('DELIMITER')  # Se espera un ;
        self.operador_abreviado()
        if self.obtener_token_actual()[0] == 'KEYWORD':
            self.cuerpo()
        else:
            self.coincidir('DELIMITER')  # Se espera un {
            self.cuerpo()
            self.coincidir('DELIMITER')  # Se espera un }

    def llamada_return(self):
        self.coincidir('KEYWORD')
        self.expresion()
        self.coincidir('DELIMITER')

    def llamada_brake(self):
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

    def llamada_while(self):
        # Regla para bucle while: KEYWORD DELIMITER EXPRESION_LOGICA DELIMITER DELIMITER CUERPO DELIMITER
        self.coincidir('KEYWORD')  # Se espera un while
        self.coincidir('DELIMITER')  # Se espera un (
        self.expresion_logica()
        self.coincidir('DELIMITER')  # Se espera un )
        self.coincidir('DELIMITER')  # Se espera un {
        self.cuerpo()
        self.coincidir('DELIMITER')  # Se espera un }


# === Ejemplo de Uso ===
codigo_fuente = """
int suma(int a, int b) {
    int c = a + b;
    return c;
}
"""
# =====Aqui es el fin de uso =====

# Analisis lexico
tokens = identificar_tokens(codigo_fuente)
print("Tokens encontrados:")
for tipo, valor in tokens:
    print(f'{tipo}: {valor}')

# Analisis Sintactico
print('\nIniciando analisis sintactico...')
parser = Parser(tokens)
arbol_ast = parser.parsear()
print('Analisis sintactico completado sin errores')


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


print(json.dumps(imprimir_ast(arbol_ast), indent=1))
codigo_asm = arbol_ast.generar_codigo()
print(codigo_asm)


def ensamblador_a_maquina2(codigo_asm):
    instrucciones = {
        'push ebp': '55',
        'mov ebp, esp': '89 E5',
        'pop ebx': '5B',
        'pop ebp': '5D',
        'add eax, ebx': '01 D8',
        'ret': 'C3',
        'mov esp, ebp': '89 EC',
    }
    variables = {
        '[a]': '00 00 00 00',
        '[b]': '04 00 00 00',
        '[c]': '08 00 00 00',
        '[suma]': '0C 00 00 00',
        '[resultado]': '10 00 00 00',
    }

    codigo_maquina = []
    lineas = [line.strip() for line in codigo_asm.split('\n') if line.strip()]

    for linea in lineas:
        if linea.endswith(':'):
            continue

        if linea in instrucciones:
            codigo_maquina.append(instrucciones[linea])
        elif linea.startswith('mov eax, ['):
            var = linea[linea.find('['):linea.find(']') + 1]
            codigo_maquina.append(f"A1 {variables[var]}")
        elif linea.startswith('mov [') and 'eax' in linea:
            var = linea[linea.find('['):linea.find(']') + 1]
            codigo_maquina.append(f"A3 {variables[var]}")
        elif linea.startswith('mov eax, '):
            valor = linea.split(', ')[1]
            if valor.isdigit():
                hex_val = f"{int(valor):04X}"
                little_endian = ' '.join([hex_val[i:i + 2] for i in range(0, len(hex_val), 2)][::-1])
                codigo_maquina.append(f"B8 {little_endian}")
        elif linea == 'push eax':
            codigo_maquina.append('50')
        else:
            codigo_maquina.append(f"; Instrucción no soportada: {linea}")

    return ' '.join(codigo_maquina)


def ensamblador_a_maquina(codigo_asm):
    ks = Ks(KS_ARCH_X86, KS_MODE_16)

    try:
        encoding, _ = ks.asm(codigo_asm)
        codigo_hex = ' '.join(f"{b:02X}" for b in encoding)
        return codigo_hex
    except Exception as e:
        return f"Error: {str(e)}"

print(ensamblador_a_maquina(codigo_asm))

analizador_semantico = AnalizadorSemantico()
analisis = analizador_semantico.analizar(arbol_ast)
print(analisis)

for llave in (analizador_semantico.tabla_simbolos.keys()):
    valor = analizador_semantico.tabla_simbolos.get(llave)
    print(f'{llave}:{valor}')