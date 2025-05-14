class NodoAST:
    def traducir(self):
        raise NotImplementedError("Metodo traducir() no implementado")
    def generar_codigo(self):
        raise NotImplementedError("Metodo generar_codigo() no implementado")

class NodoPrograma(NodoAST):
    def __init__(self, funciones):
        self.funciones = funciones
        
    def traducir(self):
        return [f.traducir() for f in self.funciones]
    
    def generar_codigo(self):
        codigo = "section .text\n"
        codigo += "\tglobal _start\n\n"
        codigo += "\n".join(f.generar_codigo() for f in self.funciones)
        
        # Añadir sección de datos para buffers de impresión
        codigo += "\n\nsection .data\n"
        codigo += "\tnewline db 10, 0\n"
        codigo += "section .bss\n"
        codigo += "\tnum_buffer resb 12\n"
        
        return codigo

class NodoFuncion(NodoAST):
    def __init__(self, tipo, nombre, parametros, cuerpo):
        self.tipo = tipo
        self.nombre = nombre
        self.parametros = parametros
        self.cuerpo = cuerpo
        
    def traducir(self):
        params = ", ".join(p.traducir() for p in self.parametros)
        cuerpo = "\n\t".join(c.traducir() for c in self.cuerpo)
        return f"def {self.nombre}({params}):\n\t{cuerpo}\n"
    
    def generar_codigo(self):
        codigo = f"{self.nombre}:\n"
        codigo += "\tpush ebp\n"
        codigo += "\tmov ebp, esp\n"
        
        # Reservar espacio para variables locales
        stack_space = 4 * sum(1 for inst in self.cuerpo if isinstance(inst, NodoDeclaracion))
        if stack_space > 0:
            codigo += f"\tsub esp, {stack_space}\n"
        
        codigo += "\n".join(c.generar_codigo() for c in self.cuerpo)
        
        if self.nombre != 'main':
            codigo += "\n\tmov esp, ebp\n"
            codigo += "\tpop ebp\n"
            codigo += "\tret\n"
        else:
            codigo += "\n\tmov eax, 1    ; sys_exit\n"
            codigo += "\tmov ebx, 0    ; status 0\n"
            codigo += "\tint 0x80\n"
        
        return codigo

class NodoParametro(NodoAST):
    def __init__(self, tipo, nombre):
        self.tipo = tipo
        self.nombre = nombre
        
    def traducir(self):
        return f"{self.tipo} {self.nombre}"
    
    def generar_codigo(self):
        return f"; Parametro: {self.tipo} {self.nombre}"

class NodoAsignacion(NodoAST):
    def __init__(self, nombre, expresion):
        self.nombre = nombre 
        self.expresion = expresion
        
    def traducir(self):
        return f"{self.nombre[1]} = {self.expresion.traducir()}"
    
    def generar_codigo(self):
        codigo = self.expresion.generar_codigo()
        codigo += f"\n\tmov [{self.nombre[1]}], eax ; asignar a {self.nombre[1]}"
        return codigo

class NodoOperacion(NodoAST):
    def __init__(self, izquierda, operador, derecha):
        self.izquierda = izquierda
        self.operador = operador
        self.derecha = derecha
        
    def traducir(self):
        return f"{self.izquierda.traducir()} {self.operador} {self.derecha.traducir()}"

    def generar_codigo(self):
        codigo = []
        codigo.append(self.izquierda.generar_codigo())
        codigo.append('\tpush eax')
        
        codigo.append(self.derecha.generar_codigo())
        codigo.append('\tpop ebx')
        
        if self.operador == '+':
            codigo.append('\tadd eax, ebx')
        elif self.operador == '-':
            codigo.append('\tsub ebx, eax')
            codigo.append('\tmov eax, ebx')
        elif self.operador == '*':
            codigo.append('\timul ebx')
        elif self.operador == '/':
            codigo.append('\txchg eax, ebx')
            codigo.append('\tcdq')
            codigo.append('\tidiv ebx')
        
        return '\n'.join(codigo)

class NodoOperacionLogica(NodoAST):
    def __init__(self, izquierda, operador, derecha):
        self.izquierda = izquierda
        self.operador = operador
        self.derecha = derecha
        
    def traducir(self):
        return f"{self.izquierda.traducir()} {self.operador} {self.derecha.traducir()}"
    
    def generar_codigo(self):
        codigo = []
        codigo.append(self.izquierda.generar_codigo())
        codigo.append("\tpush eax")
        
        codigo.append(self.derecha.generar_codigo())
        codigo.append("\tpop ebx")
        
        codigo.append("\tcmp ebx, eax")
        
        if self.operador == '==':
            codigo.append("\tsete al")
        elif self.operador == '!=':
            codigo.append("\tsetne al")
        elif self.operador == '<':
            codigo.append("\tsetl al")
        elif self.operador == '<=':
            codigo.append("\tsetle al")
        elif self.operador == '>':
            codigo.append("\tsetg al")
        elif self.operador == '>=':
            codigo.append("\tsetge al")
        elif self.operador == '&&':
            codigo.append("\tand eax, ebx")
        elif self.operador == '||':
            codigo.append("\tor eax, ebx")
        
        codigo.append("\tmovzx eax, al")
        
        return "\n".join(codigo)

class NodoRetorno(NodoAST):
    def __init__(self, expresion):
        self.expresion = expresion
        
    def traducir(self):
        return f"return {self.expresion.traducir()}"
    
    def generar_codigo(self):
        return self.expresion.generar_codigo() + '\n\tret'

class NodoIdentificador(NodoAST):
    def __init__(self, nombre):
        self.nombre = nombre
        
    def traducir(self):
        return self.nombre[1]

    def generar_codigo(self):
        return f"\tmov eax, [{self.nombre[1]}] ; cargar variable {self.nombre[1]}"

class NodoNumero(NodoAST):
    def __init__(self, valor):
        self.valor = valor
        
    def traducir(self):
        return str(self.valor[1])
        
    def generar_codigo(self):
        return f"\tmov eax, {self.valor[1]} ; cargar constante {self.valor[1]}"

class NodoBooleano(NodoAST):
    def __init__(self, valor):
        self.valor = valor

    def traducir(self):
        return str(self.valor[1]).capitalize()

class NodoLlamarFuncion(NodoAST):
    def __init__(self, nombre, argumentos):
        self.nombre = nombre
        self.argumentos = argumentos
        
    def traducir(self):
        params = ", ".join(p.traducir() for p in self.argumentos)
        return f"{self.nombre[1]}({params})"
    
    def generar_codigo(self):
        codigo = []
        for arg in reversed(self.argumentos):
            codigo.append(arg.generar_codigo())
            codigo.append("\tpush eax")
        
        codigo.append(f"\tcall {self.nombre}")
        
        if self.argumentos:
            codigo.append(f"\tadd esp, {4*len(self.argumentos)}")
        
        return "\n".join(codigo)

class NodoString(NodoAST):
    def __init__(self, valor):
        self.valor = valor
        
    def traducir(self):
        return self.valor[1]
        
    def generar_codigo(self):
        return f'\tmov eax, {self.valor[1]} ; cargar string'

class NodoDeclaracion(NodoAST):
    def __init__(self, tipo, nombre):
        self.tipo = tipo
        self.nombre = nombre
        
    def traducir(self):
        return f"{self.nombre}: {self.tipo} = 0" if self.tipo == 'int' else f"{self.nombre}: {self.tipo} = ''"
        
    def generar_codigo(self):
        return f"; Declaración de variable: {self.tipo} {self.nombre}"

class NodoIf(NodoAST):
    def __init__(self, condicion, cuerpo_if, cuerpo_else=None):
        self.condicion = condicion
        self.cuerpo_if = cuerpo_if
        self.cuerpo_else = cuerpo_else if cuerpo_else else []
        
    def traducir(self):
        if_part = f"if {self.condicion.traducir()}:\n"
        if_part += "\n".join(f"\t\t{inst.traducir()}" for inst in self.cuerpo_if)
        
        if not self.cuerpo_else:
            return if_part
            
        else_part = "else:\n"
        else_part += "\n".join(f"\t\t{inst.traducir()}" for inst in self.cuerpo_else)
        
        return f"{if_part}\n{else_part}"

    def generar_codigo(self):
        label_else = f"else_{id(self)}"
        label_end = f"endif_{id(self)}"
        
        codigo = []
        codigo.append(self.condicion.generar_codigo())
        codigo.append(f"\tcmp eax, 0")
        codigo.append(f"\tje {label_else}")
        
        for instruccion in self.cuerpo_if:
            codigo.append(instruccion.generar_codigo())
        
        codigo.append(f"\tjmp {label_end}")
        codigo.append(f"{label_else}:")
        
        for instruccion in self.cuerpo_else:
            codigo.append(instruccion.generar_codigo())
        
        codigo.append(f"{label_end}:")
        
        return "\n".join(codigo)

class NodoWhile(NodoAST):
    def __init__(self, condicion, cuerpo):
        self.condicion = condicion
        self.cuerpo = cuerpo
        
    def traducir(self):
        cuerpo = "\n\t".join(inst.traducir() for inst in self.cuerpo)
        return f"while {self.condicion.traducir()}:\n\t\t{cuerpo}"
    
    def generar_codigo(self):
        label_start = f"while_start_{id(self)}"
        label_end = f"while_end_{id(self)}"
        
        codigo = []
        codigo.append(f"{label_start}:")
        
        # Generar código para la condición
        codigo.append(self.condicion.generar_codigo())
        codigo.append("\tcmp eax, 0")
        codigo.append(f"\tje {label_end}")
        
        # Generar código para el cuerpo
        for instruccion in self.cuerpo:
            codigo.append(instruccion.generar_codigo())
        
        # Volver al inicio del while
        codigo.append(f"\tjmp {label_start}")
        codigo.append(f"{label_end}:")
        
        return "\n".join(codigo)

class NodoFor(NodoAST):
    def __init__(self, inicializacion, condicion, incremento, cuerpo):
        self.inicializacion = inicializacion
        self.condicion = condicion
        self.incremento = incremento
        self.cuerpo = cuerpo
        
    def traducir(self):
        init = self.inicializacion.traducir()
        cond = self.condicion.traducir()
        incr = self.incremento.rstrip(';')
        cuerpo = "\n\t".join(inst.traducir() for inst in self.cuerpo)
        return f"for ({init}; {cond}; {incr}):\n\t\t{cuerpo}"
    
    def generar_codigo(self):
        label_start = f"for_start_{id(self)}"
        label_end = f"for_end_{id(self)}"
        
        codigo = []
        
        # Inicialización
        codigo.append(self.inicializacion.generar_codigo())
        
        # Inicio del bucle
        codigo.append(f"{label_start}:")
        
        # Condición
        codigo.append(self.condicion.generar_codigo())
        codigo.append("\tcmp eax, 0")
        codigo.append(f"\tje {label_end}")
        
        # Cuerpo del for
        for instruccion in self.cuerpo:
            codigo.append(instruccion.generar_codigo())
        
        # Incremento
        codigo.append(self.incremento.generar_codigo())
        
        # Volver a evaluar condición
        codigo.append(f"\tjmp {label_start}")
        codigo.append(f"{label_end}:")
        
        return "\n".join(codigo)

class NodoPrintf(NodoAST):
    def __init__(self, argumentos, formato_str):
        self.argumentos = argumentos
        self.cadenaFormato = formato_str
        
    def traducir(self):
        import re

        variables = [nombre[1] for ((_, nombre), _) in self.argumentos]
        partes = re.split(r'(%[dfscl])', self.cadenaFormato.strip('"'))

        resultado = []
        var_index = 0
        for parte in partes:
            if re.fullmatch(r'%[dfscl]', parte):
                if var_index < len(variables):
                    resultado.append(f"{{{variables[var_index]}}}")
                    var_index += 1
                else:
                    resultado.append(parte)
            else:
                resultado.append(parte)

        cuerpo = ''.join(resultado)
        return f'print(f"{cuerpo}")'
    
    def generar_codigo(self):
        codigo = []
        codigo.append("\t; Preparación para imprimir")
        
        for arg in self.argumentos:
            codigo.append(arg.generar_codigo())
            
            if isinstance(arg, NodoString):
                # Para strings
                codigo.append("\tmov ecx, eax  ; dirección del string")
                codigo.append("\tmov edx, 0    ; contador de longitud")
                codigo.append("\t.strlen_loop:")
                codigo.append("\tcmp byte [ecx+edx], 0")
                codigo.append("\tje .strlen_done")
                codigo.append("\tinc edx")
                codigo.append("\tjmp .strlen_loop")
                codigo.append("\t.strlen_done:")
            else:
                # Para números (convertir a string)
                codigo.append("\t; Conversión de número a string")
                codigo.append("\tmov ecx, num_buffer")
                codigo.append("\tmov ebx, 10")
                codigo.append("\tmov edi, 0")
                codigo.append("\t.convert_loop:")
                codigo.append("\txor edx, edx")
                codigo.append("\tdiv ebx")
                codigo.append("\tadd dl, '0'")
                codigo.append("\tmov [ecx+edi], dl")
                codigo.append("\tinc edi")
                codigo.append("\ttest eax, eax")
                codigo.append("\tjnz .convert_loop")
                codigo.append("\tmov edx, edi  ; longitud")
                
                # Invertir el string
                codigo.append("\tmov esi, 0")
                codigo.append("\tdec edi")
                codigo.append("\t.reverse_loop:")
                codigo.append("\tcmp esi, edi")
                codigo.append("\tjge .reverse_done")
                codigo.append("\tmov al, [ecx+esi]")
                codigo.append("\tmov bl, [ecx+edi]")
                codigo.append("\tmov [ecx+esi], bl")
                codigo.append("\tmov [ecx+edi], al")
                codigo.append("\tinc esi")
                codigo.append("\tdec edi")
                codigo.append("\tjmp .reverse_loop")
                codigo.append("\t.reverse_done:")
                codigo.append("\tmov ecx, num_buffer")
            
            # Llamada al sistema para escribir
            codigo.append("\tmov eax, 4      ; sys_write")
            codigo.append("\tmov ebx, 1      ; stdout")
            codigo.append("\tint 0x80")
        
        return "\n".join(codigo)

class NodoScan(NodoAST):
    def __init__(self, argumentos):
        self.argumentos = argumentos
        
    def traducir(self):
        lineas = []

        for variable, tipo_dato in self.argumentos:
            if variable[0] == 'IDENTIFIER':
                if tipo_dato == str:
                    lineas.append(f"{variable[1]} = input()")
                else:
                    lineas.append(f"{variable[1]} = {tipo_dato.__name__}(input())")

        return '\n'.join(lineas)

class NodoDeclaracion(NodoAST):
    def __init__(self, tipo, nombre, expresion=None):
        self.tipo = tipo
        self.nombre = nombre
        self.expresion = expresion
        
    def traducir(self):
        if self.expresion:
            return f"{self.nombre}: {self.tipo} = {self.expresion.traducir()};"
        return f"{self.nombre}: {self.tipo} = 0" if self.tipo == 'int' else f"{self.nombre}: {self.tipo} = ''"
        
    def generar_codigo(self):
        codigo = f"; Declaración de {self.tipo} {self.nombre}"
        if self.expresion:
            codigo += "\n" + self.expresion.generar_codigo()
            codigo += f"\n\tmov [{self.nombre}], eax"
        return codigo