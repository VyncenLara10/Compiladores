class NodoAST:
    # Clase base para todos los nodos del AST
    pass

    def traducir(self):
        raise NotImplementedError("Metodo traducir () no implementado en este nodo")

    def generar_codigo(self):
        raise NotImplementedError("Metodo generar_codigo () no implementado en este nodo")


class NodoFuncion(NodoAST):
    def __init__(self, nombre, parametros, cuerpo):
        self.nombre = nombre
        self.parametros = parametros
        self.cuerpo = cuerpo

    def traducir(self):
        params = ",".join(p.traducir() for p in self.parametros)
        cuerpo = "\n    ".join(c.traducir() for c in self.cuerpo)
        return f"def {self.nombre}({params}):\n    {cuerpo}"

    def generar_codigo(self):
        codigo = f'{self.nombre}:\n'
        codigo += "    push ebp\n"
        codigo += "    mov ebp, esp\n"
        codigo += "\n".join(c.generar_codigo() for c in self.cuerpo)
        codigo += "\n    mov esp, ebp\n"
        codigo += "    pop ebp\n"
        codigo += "    ret\n"
        return codigo


class NodoParametro(NodoAST):
    # Nodo que representa un parametro de funcion
    def __init__(self, tipo, nombre):
        self.tipo = tipo
        self.nombre = nombre

    def traducir(self):
        return self.nombre[1]

    def generar_codigo(self):
        codigo = f'{self.nombre[1]}:\n'
        codigo += "\n".join(c.generar_codigo() for c in self.cuerpo)
        return codigo


class NodoAsignacion(NodoAST):
    def __init__(self, nombre, expresion):
        self.nombre = nombre
        self.expresion = expresion

    def traducir(self):
        return f"{self.nombre[1]} = {self.expresion.traducir()}"

    def generar_codigo(self):
        codigo = self.expresion.generar_codigo()
        codigo += f"\n    mov [{self.nombre[1]}], eax ; asignar a {self.nombre[1]}"
        return codigo


class NodoOperacion(NodoAST):
    def __init__(self, izquierda, operador, derecha):
        self.izquierda = izquierda
        self.operador = operador
        self.derecha = derecha

    def traducir(self):
        return f"{self.izquierda.traducir()} {self.operador[1]} {self.derecha.traducir()}"

    def generar_codigo(self):
        codigo = []
        codigo.append(self.izquierda.generar_codigo())
        codigo.append('    push eax; guardar en la pila')
        codigo.append(self.derecha.generar_codigo())
        codigo.append('    pop ebx; recuperar el primer operando')  # ebx = opoerando 1 y eax= operando 2

        if self.operador == '+':
            codigo.append('    add eax, ebx ; eax = eax + ebx')

        elif self.operador == '-':
            codigo.append('    sub ebx, eax; ebx = ebx - eax')
            codigo.append('    mov eax, ebx; eax = ebx')

        elif self.operador == '*':
            pass

        elif self.operador == '/':
            pass

        return '\n'.join(codigo)

    def optimizar(self):
        if isinstance(self.izquierda, NodoOperacion):
            izquierda = self.izquierda.optimizar()
        else:
            izquierda = self.izquierda
        if isinstance(self.derecha, NodoOperacion):
            derecha = self.derecha.optimizar()
        else:
            derecha = self.derecha
        if isinstance(izquierda, NodoNumero) and isinstance(derecha, NodoNumero):
            if self.operador == '+':
                return NodoNumero(izquierda.valor + derecha.valor)
            elif self.operador == '-':
                return NodoNumero(izquierda.valor - derecha.valor)
            elif self.operador == '*':
                return NodoNumero(izquierda.valor * derecha.valor)
            elif self.operador == '/' and derecha.valor != 0:
                return NodoNumero(izquierda.valor / derecha.valor)

        # Simplificacion algebraica
        if self.operador in ['+', '*', '-', '/']:
            # Normalizar el orden de los operandos (numeros a la derecha)
            if isinstance(izquierda, NodoNumero) and not isinstance(derecha, NodoNumero):
                izquierda, derecha = derecha, izquierda

            # Multiplicacion por 1
            if self.operador == '*' and isinstance(derecha, NodoNumero) and derecha.valor == 1:
                return izquierda
            if self.operador == '*' and isinstance(izquierda, NodoNumero) and izquierda.valor == 1:
                return derecha

            # Suma con 0
            if self.operador == '+' and isinstance(derecha, NodoNumero) and derecha.valor == 0:
                return izquierda
            if self.operador == '+' and isinstance(izquierda, NodoNumero) and izquierda.valor == 0:
                return derecha

            # Multiplicacion por 0
            if self.operador == '*' and isinstance(derecha, NodoNumero) and derecha.valor == 0:
                return NodoNumero(0)
            if self.operador == '*' and isinstance(izquierda, NodoNumero) and izquierda.valor == 0:
                return NodoNumero(0)

            # Suma con negativo
            if self.operador == '+' and isinstance(derecha, NodoOperacion) and derecha.operador == '-' and isinstance(
                    derecha.derecha, NodoNumero):
                return NodoOperacion(izquierda, '-', derecha.derecha)

            # Multiplicacion con negativo
            if self.operador == '*' and isinstance(derecha, NodoOperacion) and derecha.operador == '-' and isinstance(
                    derecha.derecha, NodoNumero):
                return NodoOperacion(NodoOperacion(izquierda, '*', derecha.derecha), '-', NodoNumero(0))

            # Resta con 0
            if self.operador == '-' and isinstance(derecha, NodoNumero) and derecha.valor == 0:
                return izquierda

            # Resta de un numero negativo
            if self.operador == '-' and isinstance(derecha, NodoOperacion) and derecha.operador == '-' and isinstance(
                    derecha.derecha, NodoNumero):
                return NodoOperacion(izquierda, '+', derecha.derecha)

            # Resta de si mismo
            if self.operador == '-' and isinstance(izquierda, NodoIdentificador) and isinstance(derecha,
                                                                                                NodoIdentificador):
                if izquierda.nombre == derecha.nombre:
                    return NodoNumero(0)

            # Division por 1
            if self.operador == '/' and isinstance(derecha, NodoNumero) and derecha.valor == 1:
                return izquierda

            # Division de si mismo
            if self.operador == '/' and isinstance(izquierda, NodoIdentificador) and isinstance(derecha,
                                                                                                NodoIdentificador):
                if izquierda.nombre == derecha.nombre:
                    return NodoNumero(1)

            # Division de 0 por un numero
            if self.operador == '/' and isinstance(izquierda, NodoNumero) and izquierda.valor == 0:
                return NodoNumero(0)

            # Division por 0 (error)
            if self.operador == '/' and isinstance(derecha, NodoNumero) and derecha.valor == 0:
                raise ValueError("Error: División por cero.")

        # Si no se puede optimizar mas devolvemos la misma operacion
        return NodoOperacion(izquierda, self.operador, derecha)

class NodoNumero(NodoAST):
    def __init__(self, valor):
        self.valor = valor

    def traducir(self):
        return str(self.valor[1])

    def generar_codigo(self):
        return f"    mov eax, {self.valor[1]} ; cargar constante {self.valor[1]}"

class NodoLlamadaFuncion(NodoAST):
    # Nodo que representa una llamada a funcion
    def __init__(self, nombre, argumentos):
        self.nombre = nombre
        self.argumentos = argumentos

    def traducir(self):
        params = ",".join(p.traducir() for p in self.argumentos)
        return f"{self.nombre}({params})"

    def generar_codigo(self):
        # Generar codigo para empujar argumentos a la pila (en orden inverso)
        codigo = []
        for arg in reversed(self.argumentos):
            codigo.append(arg.generar_codigo())
            codigo.append("    push eax")

        # Llamar a la funcion
        codigo.append(f"    call {self.nombre}")

        # Limpiar los argumentos de la pila (si es necesario)
        if self.argumentos:
            codigo.append(f"    add esp, {4 * len(self.argumentos)}")

        return "\n".join(codigo)



class NodoRetorno(NodoAST):
    # Nodo que representa la sentencia return
    def __init__(self, expresion):
        self.expresion = expresion

    def traducir(self):
        return f"return {self.expresion.traducir()}"

    def generar_codigo(self):
        return self.expresion.generar_codigo() + '\n    ret ; retorno desde la subrutina'


class NodoIdentificador(NodoAST):
    def __init__(self, nombre):
        self.nombre = nombre

    def traducir(self):
        return self.nombre[1]

    def generar_codigo(self):
        return f"    mov eax, [{self.nombre[1]}] ; cargar variable {self.nombre[1]}"


class NodoPrograma(NodoAST):
    """
    Nodo que representa un programa completo.
    Contiene una lista de funciones.
    """

    def __init__(self, funciones):
        self.funciones = funciones

    def traducir(self):
        return self.funciones

    def generar_codigo(self):
        codigo = ""
        for funcion in self.funciones:
            codigo += funcion.generar_codigo() + "\n\n"
        return codigo


class NodoString(NodoAST):
    def __init__(self, valor):
        self.valor = valor

    def traducir(self):
        return self.valor[1]

    def generar_codigo(self):
        return f'    mov eax, {self.valor[1]} ; cargar string'


class NodoDeclaracion(NodoAST):
    def __init__(self, tipo, nombre):
        self.tipo = tipo
        self.nombre = nombre

    def traducir(self):
        return f"{self.tipo} {self.nombre};"

    def generar_codigo(self):
        return f"; Declaración de variable: {self.tipo} {self.nombre}"
