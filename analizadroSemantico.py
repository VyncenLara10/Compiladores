from tabla_simbolo import TablaSimbolos

class AnalizadorSemantico:
    def __init__(self):
        self.tabla_simbolos = TablaSimbolos()
        self.tabla_simbolos = TablaSimbolos()

    def analizar(self, nodo):
        metodo = f'visitar_{type(nodo).__name__}'
        if hasattr(self, metodo):
            method = getattr(self, metodo)(nodo)
            return method
        else:
            raise Exception(f'No se ha implemtado el ánalisis semántico para {type(nodo).__name__}')

    def visitar_NodoFuncion(self, nodo):
        if nodo.nombre[1] in self.tabla_simbolos:
            raise Exception(f'Error semántico: la función {nodo.nombre[1]} ya está definida')
        self.tabla_simbolos[nodo.nombre[1]] = {'tipo': nodo.parametros[0].tipo[1], 'parametros':nodo.parametros}

        for param in nodo.parametros:
            self.tabla_simbolos[param.nombre[1]] = {'tipo': param.tipo[1]}

        for instruccion in nodo.cuerpo:
            self.analizar(instruccion)


    def visitar_NodoAsignacion(self, nodo):
        tipo_expresion = self.analizar(nodo.expresion)
        self.tabla_simbolos[nodo.nombre[1]] = {'tipo': tipo_expresion}


    def visitar_NodoOperacion(self, nodo):
        tipo_izquierda = self.analizar(nodo.izquierda)
        tipo_derecha = self.analizar(nodo.derecha)

        if tipo_izquierda != tipo_derecha:
            raise Exception(f'Error semántico: Operación entre tipos incompatibles')

        return tipo_izquierda

    def visitar_NodoNumero(self, nodo):
        return 'int' if '.' not in nodo.valor[1] else 'float'


    def visitar_NodoIdentificador(self, nodo):
        if nodo.nombre[1] not in self.tabla_simbolos:
            raise Exception(f'Error semántico: La variable { nodo.nombre[1]} no existe')
        return self.tabla_simbolos[nodo.nombre[1]]['tipo']


    def visitar_NodoRetorno(self, nodo):
        return self.analizar(nodo.expresion)


