import json


class NodoAST:
    def generarCodigo(self):
        raise NotImplementedError(f"generarCodigo() no implementado en {type(self).__name__}")

    def a_dict(self):
        raise NotImplementedError(f"a_dict() no implementado en {type(self).__name__}")


class NodoPrograma(NodoAST):
    def __init__(self, instrucciones, funciones=None):
        self.instrucciones = instrucciones
        self.funciones = funciones or []

    def a_dict(self):
        d = {"tipo": "Programa", "instrucciones": [i.a_dict() for i in self.instrucciones]}
        if self.funciones:
            d["funciones"] = [f.a_dict() for f in self.funciones]
        return d

    def _recolectar_variables(self):
        vars_encontradas = set()
        def visitar(nodo):
            if isinstance(nodo, NodoAsignacion):
                vars_encontradas.add(nodo.nombre)
            if isinstance(nodo, NodoCondicional):
                for inst in nodo.cuerpo_entonces:
                    visitar(inst)
                for inst in nodo.cuerpo_sino:
                    visitar(inst)
        for inst in self.instrucciones:
            visitar(inst)
        return vars_encontradas

    def generarCodigo(self):
        self.variables = []
        variables = self._recolectar_variables()

        codigo = [
            "section .text",
            "global _start"
        ]

        data = [
            "section .data",
            "    newline: db 10"
        ]

        bss = [
            "section .bss",
            "    print_buffer: resb 32"
        ]

        # Variables globales
        for var in sorted(variables):
            bss.append(f"    {var}: resd 1")

        # Funciones
        for funcion in self.funciones:
            codigo.append(funcion.generarCodigo())
            codigo.append("")

        # Main
        codigo.append("main:")
        for instruccion in self.instrucciones:
            codigo.append(instruccion.generarCodigo())

        codigo.append("    mov eax, 0")
        codigo.append("    ret")
        codigo.append("")

        # Punto de entrada Linux
        codigo.append("_start:")
        codigo.append("    call main")
        codigo.append("    mov ebx, eax")
        codigo.append("    mov eax, 1")
        codigo.append("    int 0x80")

        return (
            "\n".join(data)
            + "\n\n"
            + "\n".join(bss)
            + "\n\n"
            + "\n".join(codigo)
        )

class NodoAsignacion(NodoAST):
    def __init__(self, nombre, expresion):
        self.nombre = nombre
        self.expresion = expresion

    def a_dict(self):
        return {
            "tipo": "Asignacion",
            "variable": self.nombre,
            "expresion": self.expresion.a_dict()
        }

    def generarCodigo(self):
        codigo = []

        codigo.append(self.expresion.generarCodigo())
        codigo.append(f"    mov [{self.nombre}], eax")

        return "\n".join(codigo)

class NodoCondicional(NodoAST):
    _label_counter = 0

    def __init__(self, condicion, cuerpo_entonces, cuerpo_sino=None):
        self.condicion = condicion
        self.cuerpo_entonces = cuerpo_entonces
        self.cuerpo_sino = cuerpo_sino or []

    def a_dict(self):
        d = {
            "tipo": "Condicional",
            "condicion": self.condicion.a_dict(),
            "entonces": [i.a_dict() for i in self.cuerpo_entonces],
        }
        if self.cuerpo_sino:
            d["sino"] = [i.a_dict() for i in self.cuerpo_sino]
        return d

    def generarCodigo(self):
        NodoCondicional._label_counter += 1
        n = NodoCondicional._label_counter

        etiq_sino = f"else_{n}"
        etiq_fin = f"endif_{n}"

        codigo = []

        codigo.append(self.condicion.generarCodigo())
        codigo.append("    cmp eax, 0")

        if self.cuerpo_sino:
            codigo.append(f"    jz {etiq_sino}")
        else:
            codigo.append(f"    jz {etiq_fin}")

        # THEN
        for inst in self.cuerpo_entonces:
            codigo.append(inst.generarCodigo())

        # ELSE
        if self.cuerpo_sino:
            codigo.append(f"    jmp {etiq_fin}")
            codigo.append(f"{etiq_sino}:")

            for inst in self.cuerpo_sino:
                codigo.append(inst.generarCodigo())

        codigo.append(f"{etiq_fin}:")

        return "\n".join(codigo)


class NodoEscribir(NodoAST):
    def __init__(self, expresion):
        self.expresion = expresion

    def a_dict(self):
        return {"tipo": "Escribir", "expresion": self.expresion.a_dict()}

    def generarCodigo(self):
        codigo = []

        codigo.append(self.expresion.generarCodigo())

        # Guardar registros
        codigo.append("    push eax")
        codigo.append("    push ebx")
        codigo.append("    push ecx")
        codigo.append("    push edx")
        codigo.append("    push esi")
        codigo.append("    push edi")

        # Convertir entero a string
        codigo.append("    mov edi, print_buffer + 11")
        codigo.append("    mov byte [edi], 0")

        codigo.append("    xor esi, esi")
        codigo.append("    cmp eax, 0")
        codigo.append("    jne print_num_inicio")

        codigo.append("    dec edi")
        codigo.append("    mov byte [edi], '0'")
        codigo.append("    jmp print_num_escribir")

        codigo.append("print_num_inicio:")
        codigo.append("    cmp eax, 0")
        codigo.append("    jge print_num_convertir")

        codigo.append("    mov esi, 1")
        codigo.append("    neg eax")

        codigo.append("print_num_convertir:")
        codigo.append("    mov ebx, 10")

        codigo.append("print_num_digito:")
        codigo.append("    xor edx, edx")
        codigo.append("    div ebx")
        codigo.append("    add dl, '0'")
        codigo.append("    dec edi")
        codigo.append("    mov [edi], dl")
        codigo.append("    test eax, eax")
        codigo.append("    jnz print_num_digito")

        codigo.append("    cmp esi, 0")
        codigo.append("    je print_num_escribir")

        codigo.append("    dec edi")
        codigo.append("    mov byte [edi], '-'")

        codigo.append("print_num_escribir:")
        codigo.append("    mov ecx, edi")
        codigo.append("    mov edx, print_buffer + 11")
        codigo.append("    sub edx, ecx")

        codigo.append("    mov ebx, 1")
        codigo.append("    mov eax, 4")
        codigo.append("    int 0x80")

        # Salto de línea
        codigo.append("    mov edx, 1")
        codigo.append("    mov ecx, newline")
        codigo.append("    mov ebx, 1")
        codigo.append("    mov eax, 4")
        codigo.append("    int 0x80")

        # Restaurar registros
        codigo.append("    pop edi")
        codigo.append("    pop esi")
        codigo.append("    pop edx")
        codigo.append("    pop ecx")
        codigo.append("    pop ebx")
        codigo.append("    pop eax")

        return "\n".join(codigo)


class NodoComparacion(NodoAST):
    def __init__(self, izquierda, operador, derecha):
        self.izquierda = izquierda
        self.operador = operador
        self.derecha = derecha

    def a_dict(self):
        return {
            "tipo": "Comparacion",
            "izquierda": self.izquierda.a_dict(),
            "operador": self.operador,
            "derecha": self.derecha.a_dict()
        }

    def generarCodigo(self):
        codigo = []

        codigo.append(self.izquierda.generarCodigo())
        codigo.append("    push eax")

        codigo.append(self.derecha.generarCodigo())
        codigo.append("    mov ebx, eax")

        codigo.append("    pop eax")
        codigo.append("    cmp eax, ebx")

        op = self.operador

        if op == ">":
            codigo.append("    setg al")
        elif op == "<":
            codigo.append("    setl al")
        elif op == ">=":
            codigo.append("    setge al")
        elif op == "<=":
            codigo.append("    setle al")
        elif op == "==":
            codigo.append("    sete al")
        elif op == "!=":
            codigo.append("    setne al")

        codigo.append("    movzx eax, al")

        return "\n".join(codigo)


class NodoOperacion(NodoAST):
    def __init__(self, izquierda, operador, derecha):
        self.izquierda = izquierda
        self.operador = operador
        self.derecha = derecha

    def a_dict(self):
        return {
            "tipo": "Operacion",
            "operador": self.operador,
            "izquierda": self.izquierda.a_dict(),
            "derecha": self.derecha.a_dict()
        }

    def generarCodigo(self):
        codigo = []

        codigo.append(self.izquierda.generarCodigo())
        codigo.append("    push eax")

        codigo.append(self.derecha.generarCodigo())
        codigo.append("    mov ebx, eax")

        codigo.append("    pop eax")

        op = self.operador

        if op == "+":
            codigo.append("    add eax, ebx")

        elif op == "-":
            codigo.append("    sub eax, ebx")

        elif op == "*":
            codigo.append("    imul ebx")

        elif op == "/":
            codigo.append("    cdq")
            codigo.append("    idiv ebx")

        return "\n".join(codigo)

    def optimizar(self):
        izq = self.izquierda.optimizar() if isinstance(self.izquierda, NodoOperacion) else self.izquierda
        der = self.derecha.optimizar()   if isinstance(self.derecha,   NodoOperacion) else self.derecha

        if isinstance(izq, NodoNumero) and isinstance(der, NodoNumero):
            vi = float(izq.valor)
            vd = float(der.valor)
            ops = {"+": vi + vd, "-": vi - vd, "*": vi * vd}
            if self.operador in ops:
                resultado = ops[self.operador]
                resultado = int(resultado) if resultado == int(resultado) else resultado
                return NodoNumero(str(resultado))
            if self.operador == "/" and vd != 0:
                return NodoNumero(str(int(vi / vd)))

        if self.operador == "*":
            if isinstance(der, NodoNumero) and der.valor == "1": return izq
            if isinstance(izq, NodoNumero) and izq.valor == "1": return der
            if isinstance(der, NodoNumero) and der.valor == "0": return NodoNumero("0")
            if isinstance(izq, NodoNumero) and izq.valor == "0": return NodoNumero("0")
        if self.operador == "+":
            if isinstance(der, NodoNumero) and der.valor == "0": return izq
            if isinstance(izq, NodoNumero) and izq.valor == "0": return der
        if self.operador == "-":
            if isinstance(der, NodoNumero) and der.valor == "0": return izq

        return NodoOperacion(izq, self.operador, der)


class NodoIdentificador(NodoAST):
    def __init__(self, nombre):
        self.nombre = nombre

    def a_dict(self):
        return {"tipo": "Identificador", "nombre": self.nombre}

    def generarCodigo(self):
        return f"    lw $t0, {self.nombre}"


class NodoNumero(NodoAST):
    def __init__(self, valor):
        self.valor = str(valor)

    def a_dict(self):
        return {"tipo": "Numero", "valor": self.valor}

    def generarCodigo(self):
        return f"    li $t0, {self.valor}"

    def optimizar(self):
        return self


class NodoFuncion(NodoAST):
    def __init__(self, tipo_retorno, nombre, parametros, cuerpo):
        self.tipo_retorno = tipo_retorno
        self.nombre = nombre
        self.parametros = parametros
        self.cuerpo = cuerpo

    def a_dict(self):
        return {
            "tipo": "Funcion",
            "tipo_retorno": self.tipo_retorno,
            "nombre": self.nombre,
            "parametros": self.parametros,
            "cuerpo": [i.a_dict() for i in self.cuerpo]
        }

    def generarCodigo(self):
        lineas = [f"{self.nombre}:"]
        for inst in self.cuerpo:
            lineas.append(inst.generarCodigo())
        lineas.append("    ret")
        return "\n".join(lineas)


class NodoRetorno(NodoAST):
    def __init__(self, expresion):
        self.expresion = expresion

    def a_dict(self):
        return {"tipo": "Retorno", "expresion": self.expresion.a_dict()}

    def generarCodigo(self):
        lineas = [self.expresion.generarCodigo()]
        lineas.append("    move $v0, $t0")
        return "\n".join(lineas)


class NodoLlamadaFuncion(NodoAST):
    def __init__(self, nombre, argumentos):
        self.nombre = nombre
        self.argumentos = argumentos

    def a_dict(self):
        return {
            "tipo": "LlamadaFuncion",
            "nombre": self.nombre,
            "argumentos": [a.a_dict() for a in self.argumentos]
        }

    def generarCodigo(self):
        lineas = []
        for arg in reversed(self.argumentos):
            lineas.append(arg.generarCodigo())
            lineas.append("    sw $t0, 0($sp)")
            lineas.append("    addiu $sp, $sp, -4")
        lineas.append(f"    jal {self.nombre}")
        lineas.append(f"    addiu $sp, $sp, {len(self.argumentos) * 4}")
        lineas.append("    move $t0, $v0")
        return "\n".join(lineas)

class NodoDeclaracion(NodoAST):
    def __init__(self, tipo_var, nombre, expresion=None):
        self.tipo_var = tipo_var
        self.nombre = nombre
        self.expresion = expresion

    def a_dict(self):
        return {
            "tipo": "Declaracion",
            "tipo_var": self.tipo_var,
            "nombre": self.nombre,
            "expresion": self.expresion.a_dict() if self.expresion else None
        }

    def generarCodigo(self):
        if self.expresion:
            return self.expresion.generarCodigo() + f"\n    mov [{self.nombre}], eax"
        return f"    ; declarar {self.tipo_var} {self.nombre}"

class NodoBloque(NodoAST):
    def __init__(self, instrucciones):
        self.instrucciones = instrucciones

    def a_dict(self):
        return {
            "tipo": "Bloque",
            "instrucciones": [i.a_dict() for i in self.instrucciones]
        }

    def generarCodigo(self):
        return "\n".join(i.generarCodigo() for i in self.instrucciones)


class Parser:
    OPERADORES_COMPARACION = {">", "<", ">=", "<=", "==", "!="}

    def __init__(self, tokens):
        if isinstance(tokens, str):
            from lexico import identificar_tokens
            tokens = identificar_tokens(tokens)
        self.tokens = tokens
        self.pos = 0

    def _actual(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _valor(self):
        t = self._actual()
        return t[1] if t else None

    def _tipo(self):
        t = self._actual()
        return t[0] if t else None

    def _coincidir(self, tipo_esperado, valor_esperado=None):
        t = self._actual()
        if t is None:
            raise SyntaxError(f"Fin inesperado: se esperaba '{valor_esperado or tipo_esperado}'")
        if t[0] != tipo_esperado:
            raise SyntaxError(f"Se esperaba {tipo_esperado}, se encontro {t[0]} ('{t[1]}')")
        if valor_esperado is not None and t[1] != valor_esperado:
            raise SyntaxError(f"Se esperaba '{valor_esperado}', se encontro '{t[1]}'")
        self.pos += 1
        return t[1]

    TIPOS = {"int", "float", "void"}

    def parsear(self):
        instrucciones = []
        funciones = []

        while self._actual() is not None:
            if self._valor() in self.TIPOS:
                tipo = self._valor()

                if tipo == "void":
                    funciones.append(self._funcion())
                else:
                    # Puede ser declaracion global o funcion con retorno int/float
                    if (
                        self.pos + 2 < len(self.tokens)
                        and self.tokens[self.pos + 1][0] == "IDENTIFIER"
                        and self.tokens[self.pos + 2][1] == "("
                    ):
                        funciones.append(self._funcion())
                    else:
                        instrucciones.append(self._declaracion())
            else:
                instrucciones.append(self._instruccion())

        return NodoPrograma(instrucciones, funciones)

    def _funcion(self):
        tipo_retorno = self._coincidir("KEYWORD")
        nombre = self._coincidir("IDENTIFIER")

        self._coincidir("DELIMITER", "(")

        parametros = []
        if self._valor() != ")":
            while True:
                tipo_param = self._coincidir("KEYWORD")
                nombre_param = self._coincidir("IDENTIFIER")
                parametros.append((nombre_param, tipo_param))

                if self._valor() == ",":
                    self._coincidir("DELIMITER", ",")
                else:
                    break

        self._coincidir("DELIMITER", ")")
        self._coincidir("DELIMITER", "{")

        cuerpo = self._instrucciones_hasta_llave()

        self._coincidir("DELIMITER", "}")

        return NodoFuncion(tipo_retorno, nombre, parametros, cuerpo)

    def _instrucciones_hasta_llave(self):
        instrucciones = []

        while self._actual() is not None and self._valor() != "}":
            instrucciones.append(self._instruccion())

        return instrucciones

    def _instruccion(self):
        val = self._valor()
        tipo = self._tipo()

        if val in ("int", "float"):
            return self._declaracion()

        elif val == "{":
            return self._bloque()

        elif val == "si":
            return self._condicional()

        elif val == "escribir":
            return self._escribir()

        elif val == "retornar":
            return self._retorno()

        elif tipo == "IDENTIFIER":
            return self._asignacion()

        else:
            raise SyntaxError(f"Instruccion no reconocida: '{val}'")

    def _declaracion(self):
        tipo_var = self._coincidir("KEYWORD")
        nombre = self._coincidir("IDENTIFIER")

        expresion = None
        if self._valor() == "=":
            self._coincidir("OPERATOR", "=")
            expresion = self._expresion()

        self._coincidir("DELIMITER", ";")
        return NodoDeclaracion(tipo_var, nombre, expresion)

    def _bloque(self):
        self._coincidir("DELIMITER", "{")
        instrucciones = self._instrucciones_hasta_llave()
        self._coincidir("DELIMITER", "}")
        return NodoBloque(instrucciones)

    def _asignacion(self):
        nombre = self._coincidir("IDENTIFIER")
        self._coincidir("OPERATOR", "=")
        expr = self._expresion()
        self._coincidir("DELIMITER", ";")
        return NodoAsignacion(nombre, expr)

    def _escribir(self):
        self._coincidir("KEYWORD", "escribir")
        self._coincidir("DELIMITER", "(")
        expr = self._expresion()
        self._coincidir("DELIMITER", ")")
        self._coincidir("DELIMITER", ";")
        return NodoEscribir(expr)

    def _retorno(self):
        self._coincidir("KEYWORD", "retornar")
        expr = self._expresion()
        return NodoRetorno(expr)

    def _comparacion(self):
        izq = self._expresion()
        op = self._valor()
        if op not in self.OPERADORES_COMPARACION:
            raise SyntaxError(f"Se esperaba operador de comparacion, se encontro '{op}'")
        self._coincidir("OPERATOR")
        der = self._expresion()
        return NodoComparacion(izq, op, der)

    def _expresion(self):
        nodo = self._termino()
        while self._tipo() == "OPERATOR" and self._valor() in ("+", "-"):
            op = self._coincidir("OPERATOR")
            der = self._termino()
            nodo = NodoOperacion(nodo, op, der)
        return nodo

    def _termino(self):
        nodo = self._factor()
        while self._tipo() == "OPERATOR" and self._valor() in ("*", "/"):
            op = self._coincidir("OPERATOR")
            der = self._factor()
            nodo = NodoOperacion(nodo, op, der)
        return nodo

    def _factor(self):
        t = self._actual()
        if t is None:
            raise SyntaxError("Se esperaba una expresion pero se llego al fin del codigo")
        if t[0] == "NUMBER":
            self.pos += 1
            return NodoNumero(t[1])
        elif t[0] == "IDENTIFIER":
            nombre = self._coincidir("IDENTIFIER")
            if self._valor() == "(":
                self._coincidir("DELIMITER", "(")
                args = []
                if self._valor() != ")":
                    args.append(self._expresion())
                    while self._valor() == ",":
                        self._coincidir("DELIMITER", ",")
                        args.append(self._expresion())
                self._coincidir("DELIMITER", ")")
                return NodoLlamadaFuncion(nombre, args)
            return NodoIdentificador(nombre)
        elif t[0] == "DELIMITER" and t[1] == "(":
            self._coincidir("DELIMITER", "(")
            expr = self._expresion()
            self._coincidir("DELIMITER", ")")
            return expr
        else:
            raise SyntaxError(f"Factor no valido: '{t[1]}'")