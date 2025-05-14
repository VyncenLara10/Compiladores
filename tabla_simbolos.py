class TablaSimbolos:
    def _init_(self):
        self.variables = {} #Almacenar variables {nombre: tipo}
        self.funciones = {} #Almacenar funciones {nombre : tipo_retorno, [parametros]}

    def declarar_variables(self, nombre, tipo):
        if nombre in self.variables:
            raise Exception(f"ERROR: Variable {nombre} ya declarada")
        self.variables[nombre] = tipo

    def obtener_tipo_variable(self, nombre):
        if nombre not in self.variables:
            raise Exception(f"Error: variable {nombre} no declarada")
        return self.variables(nombre)
    
    def declarar_funcion(self, nombre, tipo_retorno, parametros):
        if nombre in self.funciones:
            raise Exception(f"Error: Funcion {nombre} ya declarada")
        self.funciones[nombre] = (tipo_retorno, parametros)

    def obtener_info_funcion(self, nombre):
        if nombre not in self.funciones:
            raise Exception(f"Error: Funcion {nombre} no declarada")
        return self.funciones(nombre)