import re

# Análisis léxico
# Definir los patrones
token_patron = {
    "KEYWORD": r"\b(if|else|while|return|int|float|void|for|print)\b",
    "IDENTIFIER": r"\b[a-zA-Z_][a-zA-Z0-9_]*\b",
    "NUMBER": r"\b\d+(\.\d+)?\b",
    "OPERATOR": r"==|!=|<=|>=|<|>|\+\+|\+|--|-|\*|/|&&|\|\||!|=",
    "DELIMITER": r"[(),;{}]",
    "WHITESPACE": r"\s+",
    "COMILLAS": r"\""
}


def identificar(texto):
    # Unir todos los patrones en un único patrón utilizando grupos nombrados
    patron_general = "|".join(f"(?P<{token}>{patron})" for token, patron in token_patron.items())
    patron_regex = re.compile(patron_general)
    tokens_encontrados = []
    for match in patron_regex.finditer(texto):
        for token, valor in match.groupdict().items():
            if valor is not None and token != "WHITESPACE":
                tokens_encontrados.append((token, valor))
    return tokens_encontrados


# Analizador sintáctico
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def obtener_token_actual(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def coincidir(self, tipo_esperado):
        token_actual = self.obtener_token_actual()
        if token_actual and token_actual[0] == tipo_esperado:
            self.pos += 1
            return token_actual
        raise SyntaxError(f'Error Sintáctico: Se esperaba {tipo_esperado}, pero se encontró {token_actual}')

    def parsear(self):
        # Punto de entrada, se espera una función
        self.funcion()

    def funcion(self):
        self.coincidir("KEYWORD")  # Tipo de retorno (ej. int)
        self.coincidir("IDENTIFIER")  # Nombre de la función
        self.coincidir("DELIMITER")  # Se espera '('
        self.parametros()
        self.coincidir("DELIMITER")  # Se espera ')'
        self.coincidir("DELIMITER")  # Se espera '{'
        self.cuerpo()
        self.coincidir("DELIMITER")  # Se espera '}'

    def parametros(self):
        if self.obtener_token_actual() and self.obtener_token_actual()[0] == "KEYWORD":
            self.coincidir("KEYWORD")  # Tipo del parámetro (ej. int)
            self.coincidir("IDENTIFIER")  # Nombre del parámetro (ej. a)
            while self.obtener_token_actual() and self.obtener_token_actual()[1] == ",":
                self.coincidir("DELIMITER")  # Se espera la coma
                self.coincidir("KEYWORD")  # Se espera el tipo del siguiente parámetro
                self.coincidir("IDENTIFIER")  # Se espera el nombre del siguiente parámetro

    def asignacion(self):
        self.coincidir("KEYWORD")  # Tipo de dato (ej. int)
        self.coincidir("IDENTIFIER")  # Nombre de la variable
        self.coincidir("OPERATOR")  # Se espera un "="
        self.expresion()  # Procesar la expresión de asignación
        self.coincidir("DELIMITER")  # Se espera ';'

    def expresion(self):
        self.termino()
        while self.obtener_token_actual() and self.obtener_token_actual()[1] in "+-":
            self.coincidir("OPERATOR")  # Se espera `+` o `-`
            self.termino()

    def termino(self):
        self.factor()
        while self.obtener_token_actual() and self.obtener_token_actual()[1] in "*/":
            self.coincidir("OPERATOR")  # Se espera `*` o `/`
            self.factor()

    def factor(self):
        if self.obtener_token_actual()[0] == "IDENTIFIER" or self.obtener_token_actual()[0] == "NUMBER":
            self.coincidir(self.obtener_token_actual()[0])  # Se espera número o variable
        elif self.obtener_token_actual()[1] == "(":
            self.coincidir("DELIMITER")  # Se espera "("
            self.expresion()
            self.coincidir("DELIMITER")  # Se espera ")"
        else:
            raise SyntaxError(f"Error Sintáctico: Se esperaba un número, variable o paréntesis, pero se encontró {self.obtener_token_actual()}")

    def retorno(self):
        self.coincidir("KEYWORD")  # Se espera `return`
        self.expresion()  # Procesar la expresión de retorno
        self.coincidir("DELIMITER")  # Se espera `;`

    def cuerpo(self):
        while self.obtener_token_actual() and self.obtener_token_actual()[1] != "}":
            token_actual = self.obtener_token_actual()
            if token_actual[0] == "KEYWORD":
                if token_actual[1] == "if":
                    self.cuerpo_if()
                elif token_actual[1] == "while":
                    self.cuerpo_while()
                elif token_actual[1] == "for":
                    self.cuerpo_for()
                elif token_actual[1] == "return":
                    self.retorno()
                elif token_actual[1] == "print":
                    self.cuerpo_print()
                else:
                    self.asignacion()
            else:
                self.asignacion()

    def cuerpo_if(self):
        self.coincidir("KEYWORD")  # Se espera `if`
        self.coincidir("DELIMITER")  # Se espera '('
        self.expresion()  # Condición del if
        self.coincidir("DELIMITER")  # Se espera ')'
        self.coincidir("DELIMITER")  # Se espera '{'
        self.cuerpo()  # Cuerpo del if
        self.coincidir("DELIMITER")  # Se espera '}'
        if self.obtener_token_actual() and self.obtener_token_actual()[1] == "else":
            self.cuerpo_else()

    def cuerpo_else(self):
        self.coincidir("KEYWORD")  # Se espera `else`
        self.coincidir("DELIMITER")  # Se espera '{'
        self.cuerpo()  # Cuerpo del else
        self.coincidir("DELIMITER")  # Se espera '}'

    def cuerpo_while(self):
        self.coincidir("KEYWORD")  # Se espera `while`
        self.coincidir("DELIMITER")  # Se espera '('
        self.expresion()  # Condición del while
        self.coincidir("DELIMITER")  # Se espera ')'
        self.coincidir("DELIMITER")  # Se espera '{'
        self.cuerpo()  # Cuerpo del while
        self.coincidir("DELIMITER")  # Se espera '}'

    def cuerpo_for(self):
        self.coincidir("KEYWORD")  # Se espera `for`
        self.coincidir("DELIMITER")  # Se espera '('
        self.asignacion()  # Inicialización del for
        self.expresion()  # Condición del for
        self.coincidir("DELIMITER")  # Se espera ';'
        self.expresion()  # Incremento del for
        self.coincidir("DELIMITER")  # Se espera ')'
        self.coincidir("DELIMITER")  # Se espera '{'
        self.cuerpo()  # Cuerpo del for
        self.coincidir("DELIMITER")  # Se espera '}'

    def cuerpo_print(self):
        self.coincidir("KEYWORD")  # Se espera el print
        self.coincidir("COMILLAS")  # Se espera el inicio de las comillas
        while self.coincidir("COMILLAS") is not Exception:
            pass
            if self.obtener_token_actual()[1] == self.coincidir("COMILLAS"):
                break
            # No importa que exista lo vuelve cadena
        self.coincidir("DELIMITER")  # Se espera ';'

