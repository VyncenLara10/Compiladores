import Analizador

# Ejemplo de uso
codigo_fuente = """
int suma(int a, int b) {

    int x = a + b * 2;
    int y = x - 5;
    return y;
}

"""

import json
class NodoAST:
    #Clase base para todos los nodos del AST
    pass
class NodoFuncion(NodoAST):
    #Nodo que representa una funcion
    def _init_(self, nombre, parametros,cuerpo):
        self.nombre = nombre
        self.parametros = parametros
        self.cuerpo = cuerpo
    

class NodeParametro(NodoAST):
    #Nodo que representa un parámetro de función
    def _init_(self, tipo, nombre):
        self.tipo = tipo
        self.nombre = nombre

class NodoAsignacion(NodoAST):
    def _init_(self, nombre, expresion):
        self.nombre = nombre
        self.expresion = expresion

class NodoOperacion(NodoAST):
    def _init_(self, izquierda, operador, derecha):
        self.izquierda = izquierda
        self.operador = operador
        self.derecha = derecha

class NodoRetorno(NodoAST):
    #Nodo que representa a la sentencia return
    def _init_(self, expresion):
        self.expresion = expresion
        
class NodoIdentificador(NodoAST):
    def _init_(self, nombre):
        self.nombre = nombre

class NodoNumero(NodoAST):
    def _init_(self, valor):
        self.valor = valor

def imprimir_ast(nodo):
    if isinstance(nodo, NodoFuncion):
        return {'Funcion': nodo.nombre,
                'Parametros': [imprimir_ast(p) for p in nodo.parametros],
                'Cuerpo': [imprimir_ast(c) for c in nodo.cuerpo]}
    elif isinstance(nodo, NodeParametro):
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


arbolast = NodoFuncion("suma", 
    [NodeParametro("int", "a"), NodeParametro("int", "b")], 
    [NodoRetorno(NodoOperacion(NodoIdentificador("a"), "+", NodoIdentificador("b")))]
)

print(json.dumps(imprimir_ast(arbolast),indent=1))
