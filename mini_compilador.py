import json

from lexico import identificar_tokens
from sintactico import Parser
from semantico import AnalizadorSemantico, Generador3Direcciones


codigo = """
int x = 10;

void test(int a) {
    int y = a * 2;
    {
        float x = 5.5;
        y = y + x;
    }
    x = y + 1;
    escribir(z);
}
"""


print("TOKENS")
tokens = identificar_tokens(codigo)
for t in tokens:
    print(t)

print("\nAST")
parser = Parser(tokens)
ast = parser.parsear()
print(json.dumps(ast.a_dict(), indent=2, ensure_ascii=False))

print("\nSEMANTICO")
sem = AnalizadorSemantico()

try:
    sem.analizar(ast)
except Exception as e:
    print(e)

print("\nHISTORIAL DE AMBITOS")
sem.tabla.imprimir_resumen_final()

print("\nC3D")
gen = Generador3Direcciones()
gen.generar(ast)

for linea in gen.codigo:
    print(linea)