class TablaSimbolos:
    def __init__(self):
        self.variables = {}  # Almacena varibles {nombre: tipo}
        self.funciones = {}  # Almacenar funciones{nombre: tipo_retorno[parametros]}

    def declarar_variables(self, nombre, tipo):
        if nombre in self.variables:
            raise Exception(f"Error: Variable'{nombre}' ya declarada ")
        self.variables[nombre] = tipo

    def declarar_funcion(self, nombre, tipo_retorno, parametros):
        if nombre in self.funciones:
            raise Exception(f"Error: Función '{nombre}' ya declarada")
        self.funciones[nombre] = (tipo_retorno, parametros)

    def obtener_info_funcion(self, nombre):
        if nombre not in self.funciones:
            raise Exception(f"Error; Función '{nombre}' no delcarada")
        return self.funciones[nombre]

