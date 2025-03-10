class NodoAST:
    pass

class NodoFuncion(NodoAST):
    def __init__(self, nombre, parametros, cuerpo):
        self.nombre = nombre
        self.parametros = parametros
        self.cuerpo = cuerpo

class NodoParametro(NodoAST):
    def __init__(self, tipo, nombre):
        self.tipo = tipo
        self.nombre = nombre

class NodoAsignacion(NodoAST):
    def __init__(self, nombre, expresion):
        self.nombre = nombre
        self.expresion = expresion

class NodoOperacion(NodoAST):
    def __init__(self, izquierda, operador, derecha):
        self.izquierda = izquierda
        self.operador = operador
        self.derecha = derecha

class NodoRetorno(NodoAST):
    def __init__(self, expresion):
        self.expresion = expresion

class NodoIdentificador(NodoAST):
    def __init__(self, nombre):
        self.nombre = nombre

class NodoNumero(NodoAST):
    def __init__(self, valor):
        self.valor = valor

# -----------------------------
# FUNCION PARA IMPRIMIR AST
# -----------------------------
import json

def imprimir_ast(nodo):
    if isinstance(nodo, NodoFuncion):
        return {'Funcion': nodo.nombre,
                'Parametros': [imprimir_ast(p) for p in nodo.parametros],
                'Cuerpo': [imprimir_ast(c) for c in nodo.cuerpo]}
    elif isinstance(nodo, NodoParametro):
        return {'Parametro': nodo.nombre, 'Tipo': nodo.tipo}
    elif isinstance(nodo, NodoAsignacion):
        return {'Asignacion': nodo.nombre,
                'Expresion': imprimir_ast(nodo.expresion)}
    elif isinstance(nodo, NodoOperacion):
        return {'Operacion': nodo.operador,
                'Izquierda': imprimir_ast(nodo.izquierda),
                'Derecha': imprimir_ast(nodo.derecha)}
    elif isinstance(nodo, NodoRetorno):
        return {'Return': imprimir_ast(nodo.expresion)}
    elif isinstance(nodo, NodoIdentificador):
        return {'Identificador': nodo.nombre}
    elif isinstance(nodo, NodoNumero):
        return {'Numero': nodo.valor}
    return {}

# -----------------------------
# EJEMPLO DE USO
# -----------------------------
arbol_ast = NodoFuncion("suma", 
    [NodoParametro("int", "a"), NodoParametro("int", "b")], 
    [NodoRetorno(NodoOperacion(NodoIdentificador("a"), "+", NodoIdentificador("b")))]
)

print(json.dumps(imprimir_ast(arbol_ast), indent=2))
