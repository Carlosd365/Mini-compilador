class NodoAST:
    # Clase para todos los nodos de AST
        
    def generarCodigo(self):                                      
        #Traducir de C++ a Assembler
        raise NotImplementedError('Metodo generarCodigo() no implementado en este Nodo')

class NodoPrograma(NodoAST):
    # Nodo que representa a un programa completo
    def __init__(self,  funciones, main):
        
        self.variables = []
        self.funciones = funciones
        self.main = main

    def generarCodigo(self):
        codigo = [ "section .text", "global _start"]
        data = ["section .bss"]
        # Generar Código de Todas las Funciones
        for funcion in self.funciones:
            codigo.append(funcion.generarCodigo())
            self.variables.append((funcion.cuerpo[0].tipo[1], funcion.cuerpo[0].nombre[1]))
            if len(funcion.parametros) > 0:
                for parametro in funcion.parametros:
                    self.variables.append((parametro.tipo[1], parametro.nombre[1]))
        # Generar el punto de entrada del programa
        codigo.append("_start:")
        codigo.append(self.main.generarCodigo())
        #Finalizar programa
        codigo.append("    mov eax, 1  ; syscall exit")
        codigo.append("    xor ebx, ebx  ; Código de salida 0")
        codigo.append("    int 0x80")

        # Seccion de reserva de memoria para las variables
        for variable in self.variables:
            if variable[0] == 'int':
                data.append(f'    {variable[1]}:    resd 1')
        codigo = '\n'.join(codigo)
        return '\n'.join(data) + '\n' + codigo

class NodoLlamadaFuncion(NodoAST):
    # Nodo que representa una llamada a función
    def __init__(self, nombref, argumentos):
        self.nombre_funcion = nombref
        self.argumentos = argumentos

    def generarCodigo(self):
        codigo = []
        for arg in reversed(self.argumentos):
            codigo.append(arg.generarCodigo())                   
            codigo.append("    push eax  ; Pasar argumento a la pila")

        codigo.append(f"    call {self.nombre_funcion}  ; Llamar a la funcion {self.nombre_funcion}") 
        codigo.append(f"    add esp, {len(self.argumentos) * 4}  ; Limpiar pila de argumentos")
        return "\n".join(codigo)                                

class NodoFuncion(NodoAST):
    # Nodo que representa la funcion
    def __init__(self, tipo_retorno, nombre, parametros, cuerpo):
        self.tipo_retorno = tipo_retorno
        self.nombre = nombre
        self.parametros = parametros
        self.cuerpo = cuerpo

    def generarCodigo(self):
        codigo = f'{self.nombre[1]}:\n'
        if len(self.parametros) > 0:
            #Aca guardamos en pila el registro ax que usaremos
            for parametro in self.parametros:
                codigo += '\n    pop    eax'
                codigo += f'\n    mov [{parametro.nombre[1]}], eax'
        codigo += '\n'.join(c.generarCodigo() for c in self.cuerpo)
        codigo += '\n    ret'
        codigo += '\n'
        return codigo

class NodoParametros(NodoAST):
    # Nodo que representa a un parametro de funcion
    def __init__(self, tipo, nombre):
        self.tipo = tipo
        self.nombre = nombre

    def generarCodigo(self):                                      
        return f'\n    mov eax, [{self.nombre[1]}]'

class NodoAsignacion(NodoAST):
    # Nodo que representa un asignacion de variables
    def __init__(self, tipo, nombre, expresion):
        self.tipo = tipo
        self.nombre = nombre
        self.expresion = expresion

    def generarCodigo(self):
        codigo = self.expresion.generarCodigo()
        codigo += f'\n    mov [{self.nombre[1]}], eax'
        return codigo

class NodoOperacion(NodoAST):
    # Nodo que representa una operacion aritmetica
    def __init__(self, izquierda, operador, derecha):
        self.izquierda = izquierda
        self.operador = operador
        self.derecha = derecha

    def generarCodigo(self):
        codigo = []
        codigo.append(self.izquierda.generarCodigo())
        codigo.append('    push    eax')
        codigo.append(self.derecha.generarCodigo())
        codigo.append('    mov     ebx, eax')
        codigo.append('    pop     eax')                          
        if self.operador[1] == '+':
            codigo.append('    add    eax, ebx')
        elif self.operador[1] == '-':
            codigo.append('    sub eax, ebx ; eax - ebx')
        elif self.operador[1] == '*':
            codigo.append('    imul ebx ; eax * ebx ')
        elif self.operador[1] == '/':
            codigo.append('    cdq')
            codigo.append('    idiv ebx ; eax / ebx') 
        return '\n'.join(codigo)

    def optimizar(self):
        if isinstance(self.izquierda, NodoOperacion):
            self.izquierda.optimizar()
        else:
            izquierda = self.izquierda

        if isinstance(self.derecha, NodoOperacion):
            self.derecha.optimizar()
        else:
            derecha = self.derecha

        # Si ambos nodos son numeros realizamos la operacion de manera directa
        if isinstance(izquierda, NodoNumero) and isinstance(derecha, NodoNumero):
            izq = int(izquierda.valor[1])
            der = int(derecha.valor[1])
            if self.operador[1] == '+':
                valor = izq + der
            elif self.operador[1] == '-':
                valor = izq - der
            elif self.operador[1] == '*':
                valor = izq * der
            elif self.operador[1] == '/':
                valor = izq / der
            return NodoNumero(('NUMBER', valor))

        #Simplificación algebraica (valores neutros)
        if self.operador == '*' and isinstance(derecha, NodoNumero) and derecha.valor[1] == 1:
            return izquierda
        if self.operador == '*' and isinstance(izquierda, NodoNumero) and izquierda.valor[1] == 1:
            return derecha
        if self.operador == '+' and isinstance(derecha, NodoNumero) and derecha.valor[1] == 0:
            return izquierda
        if self.operador == '+' and isinstance(izquierda, NodoNumero) and izquierda.valor[1] == 1:
            return derecha

        # Si no se puede optimizar más, se devueve la expresión
        return NodoOperacion(izquierda, self.operador, derecha)

class NodoRetorno(NodoAST):
    # Nodo que representa a la sentencia return
    def __init__(self, expresion):
        self.expresion = expresion

    def generarCodigo(self):
        return self.expresion.generarCodigo()

class NodoIdentificador(NodoAST):
    # Nodo que representa a un identificador
    def __init__(self, nombre):
        self.nombre = nombre

    def generarCodigo(self):
        return f'\n    mov eax, [{self.nombre[1]}]'

class NodoNumero(NodoAST):
    # Nodo que representa a un numero
    def __init__(self,valor):
        self.valor = valor

    def generarCodigo(self):
        return f'\n    mov eax, {self.valor[1]}'             

class NodoImpresion(NodoAST):
    def __init__(self, texto):
        self.texto = texto

    def generarCodigo(self):                                      
        raise NotImplementedError('generarCodigo() no implementado para NodoImpresion')

    def traducirPy(self):
        return f'print({self.texto[1]})'

# Analizador sintactico
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
        else:
            raise SyntaxError(f'Error sintactico: se esperaba {tipo_esperado}, pero se encontro: {token_actual}')

    def parsear(self):
        # Punto de entrada: se espera una funcion
        return self.programa()

    def programa(self):
        funciones = []
        main = None
    
        while self.obtener_token_actual() is not None:
            nodo = self.funcion()
            if nodo.nombre[1] == 'inicio':
                main = nodo
            else:
                funciones.append(nodo)
    
        if main is None:
            raise SyntaxError('Error: no se encontro una funcion main')
    
        return NodoPrograma(funciones, main)

    def funcion(self):
        # Gramatica para una funcion: int IDENTIFIER (int IDENTIFIER) {cuerpo}
        tipo_retorno = self.coincidir('KEYWORD') # Tipo de retorno (ej. int)
        nombre_funcion = self.coincidir('IDENTIFIER') # Nombre de la funcion
        self.coincidir('DELIMITER') # Se espera un (
        if nombre_funcion[1] == 'main':
            parametros = []
        else:
            parametros = self.parametros() # Regla para los parametros
        self.coincidir('DELIMITER') # Se espera un )
        self.coincidir('DELIMITER') # Se espera un {
        cuerpo = self.cuerpo() # Regla parael cuerpo de la funcino
        self.coincidir('DELIMITER') # Se espera un }
        return NodoFuncion(tipo_retorno, nombre_funcion, parametros, cuerpo)

    def parametros(self):
        lista_parametros = []
        # Reglas para parametros: int IDENTIFIER (, int IDENTIFIER)*
        tipo = self.coincidir('KEYWORD') # Tipo de parametro
        nombre = self.coincidir('IDENTIFIER') # Nombre del parametro
        lista_parametros.append(NodoParametros(tipo, nombre))
        while self.obtener_token_actual() and self.obtener_token_actual()[1] == ',': 
            self.coincidir('DELIMITER') # Se espera una ,
            tipo = self.coincidir('KEYWORD') # Tipo de parametro
            nombre = self.coincidir('IDENTIFIER') # Nombre del parametro
            lista_parametros.append(NodoParametros(tipo, nombre))
        return lista_parametros

    def cuerpo(self):
        # Gramatica para el cuerpo: return IDENTIFIER OPERATOR IDENTIFIER:
        instrucciones = []
        while self.obtener_token_actual() and self.obtener_token_actual()[1] != '}':
            if self.obtener_token_actual()[1] == 'return':
                instrucciones.append(self.retorno())

            elif self.obtener_token_actual()[1] == 'print':
                instrucciones.append(self.impresion())
                
            else:
                instrucciones.append(self.asignacion())
        return instrucciones

    def asignacion(self):
        #Gramatica para la estructura de una asignación
        tipo = self.coincidir('KEYWORD') #Se espera un tipo
        nombre = self.coincidir('IDENTIFIER')
        self.coincidir('OPERATOR') # Se espera un =
        expresion = self.expresion()
        self.coincidir('DELIMITER') #Se espera un ;
        return NodoAsignacion(tipo, nombre, expresion)

    def retorno(self):
        self.coincidir('KEYWORD') #Se espera un return
        expresion = self.expresion()
        self.coincidir('DELIMITER') #Se espera un ;
        return NodoRetorno(expresion)

    def expresion(self):
        izquierda = self.termino()
        while self.obtener_token_actual() and self.obtener_token_actual()[0] == 'OPERATOR':
            operador = self.coincidir('OPERATOR')
            derecha = self.termino()
            izquierda = NodoOperacion(izquierda, operador, derecha)
        return izquierda

    def termino(self):
        token = self.obtener_token_actual()
        if token[0] == 'NUMBER':
            return NodoNumero(self.coincidir('NUMBER'))

        elif token[0] == 'IDENTIFIER':
            identificador = self.coincidir('IDENTIFIER')
            if self.obtener_token_actual() and self.obtener_token_actual()[1] == '(':
                self.coincidir('DELIMITER')
                argumentos = self.llamadaFuncion()
                self.coincidir('DELIMITER')
                return NodoLlamadaFuncion(identificador[1], argumentos)

            else:
                return NodoIdentificador(identificador)
        else:
            raise SyntaxError(f'Expresion no válida: {token}')

    def llamadaFuncion(self):
        argumentos = []
        # Reglas para Argumentos: IDENTIFIERE | NUMBER (, IDENTIFIER | NUMBER)*
        sigue = True
        token = self.obtener_token_actual()
        while sigue:
            sigue = False
            if token[0] == 'NUMBER':
                argumento = NodoNumero(self.coincidir('NUMBER'))
            elif token[0] == 'IDENTIFIER':
                argumento = NodoIdentificador(self.coincidir('IDENTIFIER'))
            else:
                raise SyntaxError(f'Error de Sintaxis, Se Esperaba un IDENTIFICADOR|Numero pero se encontró {token}')
            argumentos.append(argumento)

            if self.obtener_token_actual() and self.obtener_token_actual()[1] == ',':
                self.coincidir('DELIMITER') # Se espera una coma
                token = self.obtener_token_actual()
                sigue = True

        return argumentos

    def impresion(self):
        token_print = self.coincidir('KEYWORD')
        self.coincidir('DELIMITER')
        
        token_actual = self.obtener_token_actual()
        
        if token_actual[0] == 'STRING':
            contenido = self.coincidir('STRING')
        else:
            contenido = self.expresion()
            
        self.coincidir('DELIMITER')
        self.coincidir('DELIMITER')
        return NodoImpresion(contenido)