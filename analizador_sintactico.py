import re
from AST import *

# === Analisis Lexico ===
token_patron = {
    "KEYWORD": r'\b(if|else|while|switch|case|return|printf|break|for|int|float|void|double|char|bool|scanf)\b',
    "BOOLEAN":r'\b(true|false)\b',
    "IDENTIFIER": r'\b[a-zA-Z_][a-zA-Z0-9_]*\b',
    "NUMBER": r'\b\d+(\.\d+)?\b',
    "OPERATOR": r'[\+\-\*\/\=\<\>\!\_]',
    "DELIMITER": r'[(),;{}]',
    "WHITESPACE": r'\s+',
    "STRING": r'"[^"]*"',  
}

def identificar_tokens(texto):
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

        if not any(funcion.nombre == 'main' for funcion in funciones):
            raise SyntaxError("Error sintactico: Debe existir una funcion 'main' en el codigo.")

        if funciones[-1].nombre != 'main':
            raise SyntaxError("Error sintactico: La funcion 'main' debe ser la ultima en el codigo.")

        return NodoPrograma(funciones)
    
    def llamar_funcion(self):
        nombre_funcion = self.coincidir('IDENTIFIER')
        self.coincidir('DELIMITER')  # '('
        argumentos = self.argumentos()
        self.coincidir('DELIMITER')  # ')'
        return NodoLlamarFuncion(nombre_funcion[1], argumentos)
    
    def argumentos(self):
        argumentos = []
        while self.obtener_token_actual() and self.obtener_token_actual()[1] != ')':
            argumentos.append(self.expresion_ing())
            if self.obtener_token_actual() and self.obtener_token_actual()[1] == ',':
                self.coincidir('DELIMITER')
        return argumentos
    
    def funcion(self):
        tipo_retorno = self.coincidir('KEYWORD')
        nombre_funcion = self.coincidir('IDENTIFIER')
        self.coincidir('DELIMITER')  # '('
        parametros = self.parametros()
        self.coincidir('DELIMITER')  # ')'
        self.coincidir('DELIMITER')  # '{'
        cuerpo = self.cuerpo()
        self.coincidir('DELIMITER')  # '}'
        return NodoFuncion(tipo_retorno, nombre_funcion[1], parametros, cuerpo)

    def parametros(self):
        parametros = []
        while self.obtener_token_actual() and self.obtener_token_actual()[1] != ')':
            tipo = self.coincidir('KEYWORD')
            nombre = self.coincidir('IDENTIFIER')
            parametros.append(NodoParametro(tipo[1], nombre[1]))
            if self.obtener_token_actual() and self.obtener_token_actual()[1] == ',':
                self.coincidir('DELIMITER')
        return parametros

    def declaracion(self):
        tipo = self.coincidir('KEYWORD')
        nombre = self.coincidir('IDENTIFIER')

        if self.obtener_token_actual() and self.obtener_token_actual()[1] == '=':
            self.coincidir('OPERATOR')
            expresion = self.expresion_ing()
            nodo = NodoAsignacion(nombre, expresion)
        else:
            nodo = NodoDeclaracion(tipo[1], nombre[1])

        self.coincidir('DELIMITER')
        return nodo

    def asignacion(self):
        tipo = self.coincidir('KEYWORD')
        nombre = self.coincidir('IDENTIFIER')
        self.coincidir('OPERATOR')
        expresion = self.expresion_ing()
        self.coincidir('DELIMITER')
        return NodoAsignacion(nombre, expresion)

    def retorno(self):
        self.coincidir('KEYWORD')
        expresion = self.expresion_ing()
        self.coincidir('DELIMITER')
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
                elif token_actual[1] == 'while':
                    instrucciones.append(self.bucle_while())
                elif token_actual[1] == 'for':
                    instrucciones.append(self.bucle_for())
                elif token_actual[1] == 'scanf':
                    instrucciones.append(self.scanf_llamada())
                elif token_actual[1] == 'printf':
                    instrucciones.append(self.printf_llamada())
                elif token_actual[1] == 'return':
                    instrucciones.append(self.retorno())
                elif token_actual[1] in ['int', 'float', 'void', 'double', 'char', 'bool']:
                    instrucciones.append(self.declaracion())
                else:
                    raise SyntaxError(f'Error sintactico: Keyword no reconocido: {token_actual}')

            elif token_actual[0] == 'IDENTIFIER':
                siguiente_token = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
                if siguiente_token and siguiente_token[1] == '(':
                    instrucciones.append(self.llamar_funcion())
                    self.coincidir('DELIMITER') # ';'
                else:
                    instrucciones.append(self.asignacion())

            elif token_actual[0] in ['NUMBER', 'STRING']:
                instrucciones.append(self.expresion_ing())
                self.coincidir('DELIMITER')

            else:
                raise SyntaxError(f'Error sintactico: se esperaba una declaracion valida, pero se encontro: {token_actual}')

        return instrucciones

    def expresion_ing(self):
        izquierda = self.termino()
        
        if isinstance(izquierda, NodoIdentificador) and (self.obtener_token_actual()[1] == '('):
            llamada = izquierda.nombre
            self.coincidir('DELIMITER') # (
            argumentos = self.argumentos()
            self.coincidir('DELIMITER') # )
            izquierda = NodoLlamarFuncion(llamada, argumentos)

        while self.obtener_token_actual() and self.obtener_token_actual()[0] == 'OPERATOR':
            operador = self.coincidir('OPERATOR')
            if self.obtener_token_actual() and self.obtener_token_actual()[0] == 'OPERATOR':
                break
            derecha = self.termino()
            izquierda = NodoOperacion(izquierda, operador[1], derecha)
        return izquierda

    def termino(self):
        token = self.obtener_token_actual()
        if token[0] == 'NUMBER':
            return NodoNumero(self.coincidir('NUMBER'))
        elif token[0] == 'BOOLEAN':
            return NodoBooleano(self.coincidir('BOOLEAN'))
        elif token[0] == 'IDENTIFIER':
            return NodoIdentificador(self.coincidir('IDENTIFIER'))
        elif token[0] == 'STRING':
            return NodoString(self.coincidir('STRING'))
        else:
            raise SyntaxError(f'Error sintactico: Termino no valido {token}')
            
    def expresion(self):
        if self.obtener_token_actual()[0] in ['IDENTIFIER', 'NUMBER', 'STRING', 'BOOLEAN']:
            self.coincidir(self.obtener_token_actual()[0])
        else:
            raise SyntaxError(f"Error sintactico: Se esperaba IDENTIFIER, NUMBER, BOOLEAN o STRING, pero se encontro {self.obtener_token_actual()}")

        while self.obtener_token_actual() and self.obtener_token_actual()[0] in ['OPERATOR']:
            self.coincidir('OPERATOR')
            if self.obtener_token_actual()[0] in ['IDENTIFIER', 'NUMBER', 'STRING', 'BOOLEAN']:
                self.coincidir(self.obtener_token_actual()[0])
            else:
                raise SyntaxError(f"Error sintactico: Se esperaba IDENTIFIER, NUMBER, BOOLEAN o STRING despues de {self.obtener_token_anterior()}")

    def bucle_if(self):
        self.coincidir('KEYWORD')  # 'if'
        self.coincidir('DELIMITER')  # '('
        
        condicion = self.expresion_logica()
        
        self.coincidir('DELIMITER')  # ')'
        cuerpo_else = []
        if self.obtener_token_actual() and self.obtener_token_actual()[0] == 'DELIMITER':
            self.coincidir('DELIMITER')  # '{'
            
            cuerpo_if = self.cuerpo()
            
            self.coincidir('DELIMITER')  # '}'
            
            if self.obtener_token_actual() and self.obtener_token_actual()[1] == 'else':
                self.coincidir('KEYWORD')  # 'else'
                self.coincidir('DELIMITER')  # '{'
                cuerpo_else = self.cuerpo()
                self.coincidir('DELIMITER')  # '}'
            
            return NodoIf(condicion, cuerpo_if, cuerpo_else)
        else:
            cuerpo_if = self.cuerpo()
            if self.obtener_token_actual() and self.obtener_token_actual()[1] == 'else':
                self.coincidir('KEYWORD')  # 'else'
                cuerpo_else = self.cuerpo()
            
            return NodoIf(condicion, cuerpo_if, cuerpo_else)

    def expresion_logica(self):
        izquierda = self.expresion_ing()

        if isinstance(izquierda, NodoIdentificador) and (self.obtener_token_actual()[1] == '('):
            llamada = izquierda.nombre
            self.coincidir('DELIMITER') # (
            argumentos = self.argumentos()
            self.coincidir('DELIMITER') # )
            return NodoLlamarFuncion(llamada, argumentos)
        
        if self.obtener_token_actual() and self.obtener_token_actual()[0] == 'OPERATOR':
            operador = self.obtener_token_actual()
            print(operador)
            
            if operador[1] in ['=', '!', '<', '>']:
                self.coincidir('OPERATOR')
                if self.obtener_token_actual() and self.obtener_token_actual()[1] == '=':
                    operador = (operador[0], operador[1]+self.obtener_token_actual()[1])
                    print(operador)
                    self.coincidir('OPERATOR')
            
            derecha = self.expresion_ing()
            return NodoOperacionLogica(izquierda, operador[1], derecha)
        
        return izquierda

    def printf_llamada(self):
        formato_a_tipo_python = {
            '%d': int,
            '%f': float,
            '%lf': float,
            '%c': str,
            '%s': str
        }
        self.coincidir('KEYWORD')
        self.coincidir('DELIMITER')

        argumentos = []
        while self.obtener_token_actual() and self.obtener_token_actual()[1] != ')':
            argumentos.append(self.expresion_ing())
            if self.obtener_token_actual() and self.obtener_token_actual()[1] == ',':
                self.coincidir('DELIMITER')

        formato_str = None
        for argumento in argumentos:
            if isinstance(argumento, NodoString):
                formato_str = argumento.valor[1]
                break

        if not formato_str:
            raise Exception("No se encontró cadena de formato en printf.")

        formatos = formato_str.strip('"').split()

        variables = [valor.nombre for valor in argumentos if isinstance(valor, NodoIdentificador)]

        resultado = [(('IDENTIFIER', var), formato_a_tipo_python.get(fmt, None)) for fmt, var in zip(formatos, variables)]

        self.coincidir('DELIMITER')
        return NodoPrintf(resultado, formato_str)

    def scanf_llamada(self):
        formato_a_tipo_python = {
            '%d': int,
            '%f': float,
            '%lf': float,
            '%c': str,
            '%s': str
        }
        self.coincidir('KEYWORD')
        self.coincidir('DELIMITER')

        argumentos = []
        while self.obtener_token_actual() and self.obtener_token_actual()[1] != ')':
            argumentos.append(self.expresion_ing())
            if self.obtener_token_actual() and self.obtener_token_actual()[1] == ',':
                self.coincidir('DELIMITER')

        for argumento in argumentos:
            if isinstance(argumento, NodoString):
                tupla = argumento.valor
                formato_str = tupla[1]
                break

        formatos = formato_str.strip('"').split()

        variables = [valor.nombre for valor in argumentos if isinstance(valor, NodoIdentificador)]

        resultado = [(var, formato_a_tipo_python.get(fmt, None)) for fmt, var in zip(formatos, variables)]

        self.coincidir('DELIMITER')
        return NodoScan(resultado)

    def bucle_for(self):
        self.coincidir('KEYWORD')
        self.coincidir('DELIMITER')

        inicializacion = self.declaracion()

        condicion = self.expresion_logica() 
        self.coincidir('DELIMITER')

        var = self.obtener_token_actual()[1]
        self.coincidir('IDENTIFIER')
        incremento = var+self.operador_abreviado()

        if self.obtener_token_actual()[0] == 'KEYWORD':
            cuerpo = self.cuerpo()
            return NodoFor(inicializacion, condicion, incremento, cuerpo)
        else:
            self.coincidir('DELIMITER')
            cuerpo = self.cuerpo()
            self.coincidir('DELIMITER')
            return NodoFor(inicializacion, condicion, incremento, cuerpo)

    def return_statement(self):
        self.coincidir('KEYWORD')
        self.expresion()
        self.coincidir('DELIMITER')

    def break_statement(self):
        self.coincidir('KEYWORD')
        self.coincidir('DELIMITER')

    def operador_abreviado(self):
        operador_actual1 = self.obtener_token_actual()
        self.coincidir('OPERATOR')
        operador_actual2 = self.obtener_token_actual()
        op_conjunto = operador_actual1[1]+operador_actual2[1]
        self.coincidir('OPERATOR')
        if operador_actual1[1] + operador_actual2[1] not in ['++','--', '+=', '-=', '*=', '/=']:
            raise SyntaxError(f'Error sintactico: se esperaba una declaracion valida, pero se encontro: {operador_actual1[1],operador_actual2[1]}')
        self.coincidir('DELIMITER')
        return op_conjunto

    def bucle_while(self):
        self.coincidir('KEYWORD')
        self.coincidir('DELIMITER')
        condicion = self.expresion_logica()
        self.coincidir('DELIMITER')
        self.coincidir('DELIMITER')
        cuerpo = self.cuerpo()
        self.coincidir('DELIMITER')
        return NodoWhile(condicion, cuerpo)