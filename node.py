class Node:
    # TIPO
    # 0  = INICIO de programa
    # 1 = Entrada de datos
    # 2 = Salida de datos
    # 3 = Proceso
    # 4 = Condición
    # 5 = Final
    # 6 = llamar funcion

    def __init__(self, tipo: int, informacion: str):
        self.tipo = tipo
        self.informacion = informacion

    def return_info_str(self):
        type = ""
        if self.tipo == 0:
            type = "Inicio"
        if self.tipo == 1:
            type = "Entradad de datos"
        if self.tipo == 2:
            type = "Salida de datos"
        if self.tipo == 3:
            type = "Prcoeso"
        if self.tipo == 4:
            type = "Condicion"
        if self.tipo == 5:
            type = "Final"
        if self.tipo == 6:
            type = "funcion"
        return "tipo: " + type + " | Informacion" + str(self.informacion)

    def return_tipo(self):
        return self.tipo

    def return_info(self):
        return str(self.informacion)