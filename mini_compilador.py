from lexico import identificar_tokens
from sintactico import *

codigo = """
inicio
    a = 10
    b = 20
    c = a + b * 2
    si (c > 30) entonces
        escribir(c)
        d = c - 10
    finsi
    escribir(d)
fin
"""

parser_codigo = Parser(codigo)
arbol_ast = parser_codigo.parsear()

codigo_asm = arbol_ast.generarCodigo()
print(codigo.asm)

print(identificar_tokens(codigo))