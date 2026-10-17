# ============================================================
#   ESFUERZOS EN VIGAS - SOLUCIONADOR TIPO PAUTA
#   Resistencia de Materiales - convencion Philpot (sonrisa/frown)
#   Unidades SI base (m, N, Pa) en toda la entrada/salida
#   Compatible TI-Nspire CX II (Python 3.6+)
# ============================================================
#
# NOTA: esfuerzo combinado / circulo de Mohr / teorias de falla
# NO estan aca -- ya existen en Mohr.tns y fallas.tns. Este
# programa entrega sigma y tau en un punto, listos para pasarlos
# a esos programas si se necesita el estado de esfuerzo combinado.

import math

# ------------------------------------------------------------
# CONTROL DE PANTALLA (igual patron que Piping.txt)
# ------------------------------------------------------------

LINEAS_PANTALLA = 9
_contador_lineas = [0]

def out(texto=""):
    print(texto)
    _contador_lineas[0] += 1
    if _contador_lineas[0] >= LINEAS_PANTALLA:
        input("--mas--[Enter]")
        _contador_lineas[0] = 0

def out_final(texto=""):
    print(texto)

def menu_texto(*lineas):
    """Imprime varias lineas de menu SIN que cuenten para la
    auto-pausa de out() (evita que un menu largo se corte a
    mitad y el Enter de '--mas--' se lea como la opcion)."""
    for linea in lineas:
        print(linea)
    reset_contador()

def pausa_manual():
    input("  -- [Enter] continuar --")
    _contador_lineas[0] = 0

def reset_contador():
    _contador_lineas[0] = 0

def separador(titulo=""):
    if titulo:
        out("=== " + titulo + " ===")
    else:
        out("-" * 20)

def paso(n, desc, formula, resultado, unidad=""):
    out("[{}] {}".format(n, desc))
    out("  " + formula)
    out("  = {:.5f} {}".format(resultado, unidad))

def verificar(condicion, ok_msg, fail_msg):
    simbolo = "OK" if condicion else "FALLA"
    msg = ok_msg if condicion else fail_msg
    out("[{}] {}".format(simbolo, msg))
    return condicion

def pedir_float(msg, default=None):
    while True:
        if default is not None:
            s = input("{}[{}]: ".format(msg, default))
            if s.strip() == "":
                return default
        else:
            s = input(msg + ": ")
        # Normaliza el signo menos matematico de la Nspire (U+2212 "-")
        # al guion ASCII estandar, que es el unico que float() reconoce.
        s = s.replace("−", "-").replace(",", ".")
        try:
            return float(s)
        except ValueError:
            out("Valor invalido, ingrese un numero")

def pedir_int(msg, opciones):
    while True:
        try:
            v = int(input(msg + ": "))
            if v in opciones:
                return v
        except:
            pass
        out("Opcion invalida: " + str(opciones))


# ============================================================
# MÓDULO 1: PROPIEDADES DE LA SECCION
# ============================================================

def propiedades_rectangular(b, h):
    A = b * h
    I = b * h**3 / 12.0
    c = h / 2.0
    return A, I, c

def propiedades_circular(D):
    A = math.pi * D**2 / 4.0
    I = math.pi * D**4 / 64.0
    c = D / 2.0
    return A, I, c

def propiedades_seccion(desde_otro_modulo=False):
    """Calcula A, I, c_sup, c_inf y modulo de seccion S para una
    seccion estandar, o los recibe directos si es irregular."""
    if not desde_otro_modulo:
        separador("M1: PROPIEDADES DE LA SECCION")
        reset_contador()

    menu_texto(
        "Tipo de seccion:",
        "  1) Rectangular (b, h)",
        "  2) Circular (D)",
        "  3) Ingresar A, I, c directos")
    tipo = pedir_int("Opcion", [1, 2, 3])

    reset_contador()
    if tipo == 1:
        b = pedir_float("  Base b [m]")
        h = pedir_float("  Altura h [m]")
        A, I, c = propiedades_rectangular(b, h)
        c_sup = c
        c_inf = c
        paso(1, "Area", "A=b*h", A, "m2")
        paso(2, "Momento de inercia", "I=b*h^3/12", I, "m4")
        paso(3, "Distancia a fibra extrema", "c=h/2", c, "m")

    elif tipo == 2:
        D = pedir_float("  Diametro D [m]")
        A, I, c = propiedades_circular(D)
        c_sup = c
        c_inf = c
        paso(1, "Area", "A=pi*D^2/4", A, "m2")
        paso(2, "Momento de inercia", "I=pi*D^4/64", I, "m4")
        paso(3, "Distancia a fibra extrema", "c=D/2", c, "m")

    else:
        A = pedir_float("  Area A [m2]")
        I = pedir_float("  Momento de inercia I [m4]")
        menu_texto(
            "Seccion simetrica (c_sup=c_inf)?",
            "  1) Si",
            "  2) No, dar ambas")
        sim = pedir_int("Opcion", [1, 2])
        reset_contador()
        if sim == 1:
            c = pedir_float("  Distancia c a fibra extrema [m]")
            c_sup = c
            c_inf = c
        else:
            c_sup = pedir_float("  Distancia a fibra superior c_sup [m]")
            c_inf = pedir_float("  Distancia a fibra inferior c_inf [m]")

    S_sup = I / c_sup
    S_inf = I / c_inf
    reset_contador()
    paso(4, "Modulo de seccion (fibra sup)", "S_sup=I/c_sup", S_sup, "m3")
    if c_inf != c_sup:
        paso(5, "Modulo de seccion (fibra inf)", "S_inf=I/c_inf", S_inf, "m3")

    return {"A": A, "I": I, "c_sup": c_sup, "c_inf": c_inf,
            "S_sup": S_sup, "S_inf": S_inf}


# ============================================================
# MÓDULO 2: CORTE Y MOMENTO MAXIMOS (catalogo de casos)
# Convencion Philpot: M positivo = concava hacia arriba (sonrisa),
# fibra superior en compresion, fibra inferior en tension.
# ============================================================

def caso_simple_carga_centro():
    P = pedir_float("  Carga P [N]")
    L = pedir_float("  Longitud L [m]")
    reset_contador()
    V_max = P / 2.0
    M_max = P * L / 4.0
    paso(1, "Cortante maximo", "V_max=P/2", V_max, "N")
    paso(2, "Momento maximo (en el centro)", "M_max=P*L/4", M_max, "N.m")
    return V_max, M_max

def caso_simple_carga_arbitraria():
    P = pedir_float("  Carga P [N]")
    L = pedir_float("  Longitud L [m]")
    a = pedir_float("  Distancia desde apoyo izquierdo a [m]")
    b = L - a
    reset_contador()
    R1 = P * b / L
    R2 = P * a / L
    V_max = max(R1, R2)
    M_max = P * a * b / L
    paso(1, "Reaccion izquierda", "R1=P*b/L", R1, "N")
    paso(2, "Reaccion derecha", "R2=P*a/L", R2, "N")
    paso(3, "Cortante maximo", "V_max=max(R1,R2)", V_max, "N")
    paso(4, "Momento maximo (en x=a)", "M_max=P*a*b/L", M_max, "N.m")
    return V_max, M_max

def caso_simple_distribuida():
    w = pedir_float("  Carga distribuida w [N/m]")
    L = pedir_float("  Longitud L [m]")
    reset_contador()
    V_max = w * L / 2.0
    M_max = w * L**2 / 8.0
    paso(1, "Cortante maximo (en apoyos)", "V_max=w*L/2", V_max, "N")
    paso(2, "Momento maximo (en el centro)", "M_max=w*L^2/8", M_max, "N.m")
    return V_max, M_max

def caso_simple_momento_extremo():
    M0 = pedir_float("  Momento aplicado M0 [N.m]")
    L = pedir_float("  Longitud L [m]")
    reset_contador()
    V_max = M0 / L
    M_max = M0
    paso(1, "Cortante (constante)", "V=M0/L", V_max, "N")
    paso(2, "Momento maximo (en el extremo cargado)", "M_max=M0", M_max, "N.m")
    return V_max, M_max

def caso_volado_carga_extremo():
    P = pedir_float("  Carga P en el extremo libre [N]")
    L = pedir_float("  Longitud L [m]")
    reset_contador()
    V_max = P
    M_max = P * L
    paso(1, "Cortante maximo (constante)", "V_max=P", V_max, "N")
    paso(2, "Momento maximo (en el empotramiento)", "M_max=P*L", M_max, "N.m")
    return V_max, M_max

def caso_volado_distribuida():
    w = pedir_float("  Carga distribuida w [N/m]")
    L = pedir_float("  Longitud L [m]")
    reset_contador()
    V_max = w * L
    M_max = w * L**2 / 2.0
    paso(1, "Cortante maximo (en el empotramiento)", "V_max=w*L", V_max, "N")
    paso(2, "Momento maximo (en el empotramiento)", "M_max=w*L^2/2", M_max, "N.m")
    return V_max, M_max

def caso_volado_momento_extremo():
    M0 = pedir_float("  Momento aplicado en el extremo libre M0 [N.m]")
    reset_contador()
    V_max = 0.0
    M_max = M0
    out("Cortante = 0 (no hay carga transversal)")
    paso(1, "Momento maximo (constante)", "M_max=M0", M_max, "N.m")
    return V_max, M_max


def corte_momento_max(desde_otro_modulo=False):
    """Entrega V_max y M_max para un caso de carga estandar.
    No es un solver general -- cubre los casos clasicos de
    viga simplemente apoyada y viga en voladizo."""
    if not desde_otro_modulo:
        separador("M2: CORTE Y MOMENTO MAXIMOS")
        reset_contador()

    menu_texto(
        "=== VIGA SIMPLEMENTE APOYADA ===",
        "  1) Carga puntual al centro",
        "  2) Carga puntual en posicion a",
        "  3) Carga distribuida uniforme",
        "  4) Momento aplicado en un extremo",
        "=== VIGA EN VOLADIZO ===",
        "  5) Carga puntual en el extremo libre",
        "  6) Carga distribuida uniforme",
        "  7) Momento aplicado en el extremo libre")
    caso = pedir_int("Opcion", [1, 2, 3, 4, 5, 6, 7])

    reset_contador()
    if caso == 1:
        V_max, M_max = caso_simple_carga_centro()
    elif caso == 2:
        V_max, M_max = caso_simple_carga_arbitraria()
    elif caso == 3:
        V_max, M_max = caso_simple_distribuida()
    elif caso == 4:
        V_max, M_max = caso_simple_momento_extremo()
    elif caso == 5:
        V_max, M_max = caso_volado_carga_extremo()
    elif caso == 6:
        V_max, M_max = caso_volado_distribuida()
    else:
        V_max, M_max = caso_volado_momento_extremo()

    return {"V_max": V_max, "M_max": M_max, "caso": caso}


# ============================================================
# MÓDULO 3: ESFUERZO NORMAL POR FLEXION
# sigma = -M*y/I (y positivo hacia arriba desde el eje neutro).
# M positivo -> fibra superior en compresion, inferior en tension.
# ============================================================

def esfuerzo_flexion(desde_otro_modulo=False):
    if not desde_otro_modulo:
        separador("M3: ESFUERZO POR FLEXION")
        reset_contador()

    menu_texto(
        "Obtener M, I, c:",
        "  1) Encadenar M2 (V-M) + M1 (seccion)",
        "  2) Ingresar M, I, c_sup, c_inf directos")
    modo = pedir_int("Opcion", [1, 2])

    if modo == 1:
        reset_contador()
        out("Primero el caso de carga (M2):")
        pausa_manual()
        datos_vm = corte_momento_max(desde_otro_modulo=True)
        pausa_manual()
        out("Ahora la seccion (M1):")
        pausa_manual()
        datos_sec = propiedades_seccion(desde_otro_modulo=True)
        M = datos_vm["M_max"]
        I = datos_sec["I"]
        c_sup = datos_sec["c_sup"]
        c_inf = datos_sec["c_inf"]
    else:
        reset_contador()
        M = pedir_float("  Momento M [N.m] (signo segun convencion)")
        I = pedir_float("  Momento de inercia I [m4]")
        c_sup = pedir_float("  Distancia a fibra superior c_sup [m]")
        c_inf = pedir_float("  Distancia a fibra inferior c_inf [m]")

    reset_contador()
    sigma_sup = -M * c_sup / I
    sigma_inf = M * c_inf / I

    paso(1, "Esfuerzo fibra superior", "sigma_sup=-M*c_sup/I", sigma_sup, "Pa")
    paso(2, "Esfuerzo fibra inferior", "sigma_inf=M*c_inf/I", sigma_inf, "Pa")

    out("Fibra superior: " + ("COMPRESION" if sigma_sup < 0 else "TENSION"))
    out("Fibra inferior: " + ("COMPRESION" if sigma_inf < 0 else "TENSION"))

    out_final("sigma_max (mayor magnitud) = {:.4f} Pa".format(
        max(abs(sigma_sup), abs(sigma_inf))))

    return {"M": M, "I": I, "c_sup": c_sup, "c_inf": c_inf,
            "sigma_sup": sigma_sup, "sigma_inf": sigma_inf}


# ============================================================
# MÓDULO 4: ESFUERZO CORTANTE TRANSVERSAL
# Formula general: tau = V*Q/(I*b)
# Atajos: rectangular tau_max=1.5*V/A ; circular tau_max=(4/3)*V/A
# ============================================================

def _obtener_V_A_desde_modulos():
    out("Caso de carga (M2):")
    pausa_manual()
    datos_vm = corte_momento_max(desde_otro_modulo=True)
    pausa_manual()
    out("Seccion (M1):")
    pausa_manual()
    datos_sec = propiedades_seccion(desde_otro_modulo=True)
    return datos_vm["V_max"], datos_sec["A"]

def cortante_transversal(desde_otro_modulo=False):
    if not desde_otro_modulo:
        separador("M4: ESFUERZO CORTANTE TRANSVERSAL")
        reset_contador()

    menu_texto(
        "Metodo:",
        "  1) Formula general tau=V*Q/(I*b)",
        "  2) Atajo seccion rectangular: tau_max=1.5*V/A",
        "  3) Atajo seccion circular: tau_max=(4/3)*V/A")
    metodo = pedir_int("Opcion", [1, 2, 3])

    reset_contador()
    if metodo == 1:
        V = pedir_float("  Cortante V [N]")
        Q = pedir_float("  Primer momento de area Q [m3]")
        I = pedir_float("  Momento de inercia I [m4]")
        b = pedir_float("  Ancho de la seccion en el punto b [m]")
        reset_contador()
        tau = V * Q / (I * b)
        paso(1, "Esfuerzo cortante", "tau=V*Q/(I*b)", tau, "Pa")
        return {"tau": tau, "V": V, "Q": Q, "I": I, "b": b}

    menu_texto(
        "Obtener V y A:",
        "  1) Encadenar M2 (V-M) + M1 (seccion)",
        "  2) Ingresar V y A directos")
    modo = pedir_int("Opcion", [1, 2])

    if modo == 1:
        V, A = _obtener_V_A_desde_modulos()
    else:
        reset_contador()
        V = pedir_float("  Cortante V [N]")
        A = pedir_float("  Area A [m2]")

    reset_contador()
    if metodo == 2:
        tau_max = 1.5 * V / A
        paso(1, "Esfuerzo cortante maximo", "tau_max=1.5*V/A", tau_max, "Pa")
    else:
        tau_max = (4.0 / 3.0) * V / A
        paso(1, "Esfuerzo cortante maximo", "tau_max=(4/3)*V/A", tau_max, "Pa")

    return {"tau_max": tau_max, "V": V, "A": A}


# ============================================================
# MENÚ MAESTRO
# ============================================================

def menu_vigas():
    while True:
        menu_texto(
            "=== ESFUERZOS EN VIGAS - MENU ===",
            "  1) M1: Propiedades de seccion",
            "  2) M2: Corte y momento maximos",
            "  3) M3: Esfuerzo por flexion",
            "  4) M4: Esfuerzo cortante transversal",
            "  0) Salir")

        op = pedir_int("Opcion", [0, 1, 2, 3, 4])

        if op == 1:
            propiedades_seccion()
        elif op == 2:
            corte_momento_max()
        elif op == 3:
            esfuerzo_flexion()
        elif op == 4:
            cortante_transversal()
        elif op == 0:
            out("Saliendo...")
            break

        pausa_manual()


menu_vigas()
