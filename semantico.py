import copy
import re

from sintactico import (
    NodoPrograma, NodoAsignacion, NodoCondicional, NodoEscribir,
    NodoOperacion, NodoComparacion, NodoIdentificador, NodoNumero,
    NodoFuncion, NodoRetorno, NodoLlamadaFuncion,
    NodoDeclaracion, NodoBloque
)


class TablaSimbolos:
    def __init__(self):
        self.ambitos = [{}]
        self.funciones = {}
        self.advertencias = []
        self.historial_ambitos = []

    def guardar_momento(self, nombre):
        self.historial_ambitos.append((nombre, copy.deepcopy(self.ambitos)))

    def entrar_ambito(self):
        self.ambitos.append({})

    def salir_ambito(self):
        if len(self.ambitos) > 1:
            self.ambitos.pop()
        else:
            raise Exception("No se puede salir del ambito global")

    @property
    def ambito_actual(self):
        return self.ambitos[-1]

    def declarar_variable(self, nombre, tipo):
        if nombre in self.ambito_actual:
            raise Exception(f"Error semantico: variable '{nombre}' ya declarada en este ambito")
        self.ambito_actual[nombre] = {"tipo": tipo}

    def existe_variable(self, nombre):
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return True
        return False

    def obtener_tipo_variable(self, nombre):
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre]["tipo"]
        raise Exception(f"Error semantico: variable '{nombre}' no declarada")

    def declarar_funcion(self, nombre, tipo_retorno, parametros):
        if nombre in self.funciones:
            raise Exception(f"Error semantico: funcion '{nombre}' ya declarada")
        self.funciones[nombre] = {
            "retorno": tipo_retorno,
            "parametros": parametros
        }

    def obtener_funcion(self, nombre):
        if nombre not in self.funciones:
            raise Exception(f"Error semantico: funcion '{nombre}' no declarada")
        return self.funciones[nombre]

    def resumen(self):
        lineas = ["TABLA DE SIMBOLOS", "-" * 50]

        for i, ambito in enumerate(self.ambitos):
            lineas.append(f"Ambito {i}:")
            for nombre, info in ambito.items():
                lineas.append(f"  {nombre}: {info}")

        if self.funciones:
            lineas.append("")
            lineas.append("FUNCIONES:")
            for nombre, info in self.funciones.items():
                lineas.append(f"  {nombre}: {info}")

        return "\n".join(lineas)

    def imprimir_resumen_final(self):
        print("\nRESUMEN FINAL DE AMBITOS")
        print("=" * 50)

        for nombre_momento, ambitos in self.historial_ambitos:
            print(f"\n{nombre_momento}")
            print("-" * 50)

            for i, ambito in enumerate(ambitos):
                print(f"Ambito {i}: {ambito}")


class SistemaTipos:
    @staticmethod
    def tipo_resultante(t1, t2):
        if t1 == "float" or t2 == "float":
            return "float"
        return "int"

    @staticmethod
    def puede_asignar(tipo_destino, tipo_origen):
        if tipo_destino == tipo_origen:
            return True

        # int puede convertirse a float
        if tipo_destino == "float" and tipo_origen == "int":
            return True

        # float NO puede asignarse a int
        return False


class AnalizadorSemantico:
    def __init__(self):
        self.tabla = TablaSimbolos()

    def analizar(self, nodo):
        metodo = getattr(self, f"_analizar_{type(nodo).__name__}", None)
        if metodo is None:
            raise Exception(f"No hay metodo semantico para {type(nodo).__name__}")
        return metodo(nodo)

    def _analizar_NodoPrograma(self, nodo):
        for funcion in nodo.funciones:
            self.tabla.declarar_funcion(
                funcion.nombre,
                funcion.tipo_retorno,
                funcion.parametros
            )

        for inst in nodo.instrucciones:
            self.analizar(inst)

        for funcion in nodo.funciones:
            self.analizar(funcion)

    def _analizar_NodoFuncion(self, nodo):
        self.tabla.entrar_ambito()

        for nombre_param, tipo_param in nodo.parametros:
            self.tabla.declarar_variable(nombre_param, tipo_param)

        for inst in nodo.cuerpo:
            self.analizar(inst)

        self.tabla.salir_ambito()

    def _analizar_NodoBloque(self, nodo):
        self.tabla.entrar_ambito()

        for inst in nodo.instrucciones:
            self.analizar(inst)

        self.tabla.salir_ambito()

    def _analizar_NodoDeclaracion(self, nodo):
        if nodo.expresion:
            tipo_expr = self.analizar(nodo.expresion)

            if not SistemaTipos.puede_asignar(nodo.tipo_var, tipo_expr):
                raise Exception(
                    f"Error semantico: no se puede inicializar '{nodo.nombre}' "
                    f"de tipo {nodo.tipo_var} con una expresion {tipo_expr}"
                )

        self.tabla.declarar_variable(nodo.nombre, nodo.tipo_var)

        # Momentos pedidos en el ejercicio
        if nodo.nombre == "y":
            self.tabla.guardar_momento("Momento A: despues de declarar int y = a * 2")

        if nodo.nombre == "x" and nodo.tipo_var == "float":
            self.tabla.guardar_momento("Momento B: justo antes de cerrar bloque interno")

        return nodo.tipo_var

    def _analizar_NodoAsignacion(self, nodo):
        if not self.tabla.existe_variable(nodo.nombre):
            raise Exception(f"Error semantico: variable '{nodo.nombre}' no declarada")

        tipo_var = self.tabla.obtener_tipo_variable(nodo.nombre)
        tipo_expr = self.analizar(nodo.expresion)

        if not SistemaTipos.puede_asignar(tipo_var, tipo_expr):
            raise Exception(
                f"Error semantico: no se puede asignar {tipo_expr} a variable "
                f"'{nodo.nombre}' de tipo {tipo_var}"
            )

        return tipo_var

    def _analizar_NodoEscribir(self, nodo):
        # Momento C del ejercicio
        if isinstance(nodo.expresion, NodoIdentificador) and nodo.expresion.nombre == "z":
            self.tabla.guardar_momento("Momento C: al llegar a escribir(z)")

        return self.analizar(nodo.expresion)

    def _analizar_NodoOperacion(self, nodo):
        tipo_izq = self.analizar(nodo.izquierda)
        tipo_der = self.analizar(nodo.derecha)

        if tipo_izq != tipo_der:
            self.tabla.advertencias.append(
                f"Advertencia: operacion con tipos mixtos "
                f"({tipo_izq} {nodo.operador} {tipo_der})"
            )

        return SistemaTipos.tipo_resultante(tipo_izq, tipo_der)

    def _analizar_NodoComparacion(self, nodo):
        self.analizar(nodo.izquierda)
        self.analizar(nodo.derecha)
        return "bool"

    def _analizar_NodoIdentificador(self, nodo):
        return self.tabla.obtener_tipo_variable(nodo.nombre)

    def _analizar_NodoNumero(self, nodo):
        return "float" if "." in nodo.valor else "int"

    def _analizar_NodoRetorno(self, nodo):
        return self.analizar(nodo.expresion)

    def _analizar_NodoCondicional(self, nodo):
        self.analizar(nodo.condicion)

        for inst in nodo.cuerpo_entonces:
            self.analizar(inst)

        for inst in nodo.cuerpo_sino:
            self.analizar(inst)

    def _analizar_NodoLlamadaFuncion(self, nodo):
        info = self.tabla.obtener_funcion(nodo.nombre)

        if len(nodo.argumentos) != len(info["parametros"]):
            raise Exception(
                f"Error semantico: funcion '{nodo.nombre}' esperaba "
                f"{len(info['parametros'])} argumentos"
            )

        for arg, (_, tipo_param) in zip(nodo.argumentos, info["parametros"]):
            tipo_arg = self.analizar(arg)

            if not SistemaTipos.puede_asignar(tipo_param, tipo_arg):
                raise Exception(
                    f"Error semantico: argumento incompatible. "
                    f"Se esperaba {tipo_param}, se recibio {tipo_arg}"
                )

        return info["retorno"]


class Generador3Direcciones:
    def __init__(self):
        self.codigo = []
        self.temp = 0
        self.ambitos = [{}]
        self.contador_vars = {}

    def nuevo_temp(self):
        self.temp += 1
        return f"t{self.temp}"

    def entrar_ambito(self):
        self.ambitos.append({})

    def salir_ambito(self):
        self.ambitos.pop()

    def nombre_unico(self, nombre):
        self.contador_vars[nombre] = self.contador_vars.get(nombre, 0) + 1

        if self.contador_vars[nombre] == 1:
            unico = f"{nombre}_global"
        else:
            unico = f"{nombre}_local{self.contador_vars[nombre] - 1}"

        self.ambitos[-1][nombre] = unico
        return unico

    def buscar_nombre(self, nombre):
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return nombre

    def generar(self, nodo):
        metodo = getattr(self, f"_gen_{type(nodo).__name__}", None)
        if metodo:
            return metodo(nodo)

    def _gen_NodoPrograma(self, nodo):
        for inst in nodo.instrucciones:
            self.generar(inst)

        for funcion in nodo.funciones:
            self.generar(funcion)

    def _gen_NodoFuncion(self, nodo):
        self.codigo.append(f"funcion {nodo.nombre}:")
        self.entrar_ambito()

        for nombre_param, _ in nodo.parametros:
            unico = self.nombre_unico(nombre_param)
            self.codigo.append(f"  param {unico}")

        for inst in nodo.cuerpo:
            self.generar(inst)

        self.salir_ambito()
        self.codigo.append(f"fin_funcion {nodo.nombre}")

    def _gen_NodoBloque(self, nodo):
        self.entrar_ambito()

        for inst in nodo.instrucciones:
            self.generar(inst)

        self.salir_ambito()

    def _gen_NodoDeclaracion(self, nodo):
        unico = self.nombre_unico(nodo.nombre)

        if nodo.expresion:
            valor = self.generar(nodo.expresion)
            self.codigo.append(f"  {unico} = {valor}")
        else:
            self.codigo.append(f"  declarar {unico}")

    def _gen_NodoAsignacion(self, nodo):
        nombre = self.buscar_nombre(nodo.nombre)
        valor = self.generar(nodo.expresion)
        self.codigo.append(f"  {nombre} = {valor}")

    def _gen_NodoOperacion(self, nodo):
        izq = self.generar(nodo.izquierda)
        der = self.generar(nodo.derecha)
        t = self.nuevo_temp()
        self.codigo.append(f"  {t} = {izq} {nodo.operador} {der}")
        return t

    def _gen_NodoIdentificador(self, nodo):
        return self.buscar_nombre(nodo.nombre)

    def _gen_NodoNumero(self, nodo):
        return nodo.valor

    def _gen_NodoEscribir(self, nodo):
        valor = self.generar(nodo.expresion)
        self.codigo.append(f"  escribir {valor}")

    def _gen_NodoRetorno(self, nodo):
        valor = self.generar(nodo.expresion)
        self.codigo.append(f"  retornar {valor}")

    def _gen_NodoComparacion(self, nodo):
        izq = self.generar(nodo.izquierda)
        der = self.generar(nodo.derecha)
        t = self.nuevo_temp()
        self.codigo.append(f"  {t} = {izq} {nodo.operador} {der}")
        return t

    def _gen_NodoLlamadaFuncion(self, nodo):
        for arg in nodo.argumentos:
            valor = self.generar(arg)
            self.codigo.append(f"  param {valor}")

        t = self.nuevo_temp()
        self.codigo.append(f"  {t} = call {nodo.nombre}, {len(nodo.argumentos)}")
        return t


class Optimizador:
    def __init__(self, codigo_lineas):
        self.lineas = codigo_lineas

    def optimizar(self):
        return self.lineas