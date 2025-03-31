class AnalizadorSemantico:
    def __init__(self):
        self.tabla_simbolos = {}

    def analizar(self, nodo):
        metodo = f'visitar_{type(nodo).__name__}'
        if hasattr(self, metodo)(nodo):
            return getattr(self, metodo)(nodo)
        else:
            raise Exception(f'No se ha implemtado el ánalisis semántico para {type(nodo).__name__}')


    def visitar_NodoFuncion(self, nodo):
        if nodo.nombre[1] in self.tabla_simbolos:
            raise Exception(f'Error semántico: la función {nodo.nombre[1]} ya está definida')
        self.tabla_simbolos[nodo.nombre[1]] = {'tipo':nodo.parametros[0].tipo[1], 'parametros':nodo.parametros}
        for param in nodo.parametros:
            self.tabla_simbolos[param.nombre[1]] = {'tipo':param.tipo[1]}

        for instruccion in nodo.cuerpo:
            self.analizar(instruccion)
