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

print("\nShadowing")
print("""2. Detección de Errores Semanticos


Error 1: Y es int pero y+x produce un float
Error 2: Se reasigna x sin tipo declarado 
Error 3: Z nunca fue definida


3. Fenómeno del Shadowing

¿Cómo decide su método obtener_tipo_variable cuál utilizar?
Al encontrar un Identificador, esta revisa la lista de ámbitos de manera invertida, si el nombre del identificador se encuentra en la lista de ámbitos de donde se encuentra, retorna el ámbito para ser analizado, si esta no es retornada, todo funciona correctamente

¿Qué valor (o tipo) se usaría para x en la línea y = y + x;?
La segunda, el float según shadowing ya que al estar en un ámbito interno y diferente {} al externo, no va tocar al externo mientras no salga.""")

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