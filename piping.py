# ============================================================
#   PIPING HIDRAULICO - SOLUCIONADOR TIPO PAUTA
#   EITH - Bombeo de agua, sistema de cañerias
#   Compatible TI-Nspire CX II (Python 3.6+)
# ============================================================

import math

INF = 1e15

# ------------------------------------------------------------
# CONTROL DE PANTALLA (igual patron que diseño mecanico)
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
    auto-pausa de out(). Evita que la pausa caiga a mitad de un
    menu largo y se coma la respuesta del usuario (bug real:
    un menu de 9+ lineas se corta justo antes de mostrar todas
    las opciones, y el Enter de '--mas--' termina siendo leido
    como la opcion elegida)."""
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
        # Normaliza el signo menos matematico de la Nspire (U+2212 "−")
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
# CONSTANTES DEL FLUIDO (agua 20C) - editar si cambia el problema
# ============================================================

RHO   = 998.0          # kg/m3
GAMMA = 9787.04         # N/m3
MU    = 0.001020        # Pa.s
NU    = 0.000001022     # m2/s
PV    = 2337.81         # Pa (presion de vapor)
PATM  = 101325.0        # Pa
G     = 9.81            # m/s2
EPS   = 0.0003          # m (rugosidad acero, 0.3mm)


# ============================================================
# MÓDULO 1: VELOCIDAD Y REYNOLDS
# ============================================================

def vel_reynolds(desde_otro_modulo=False):
    """Calcula velocidad, Reynolds y rugosidad relativa
    para un tramo de cañeria dado Q y D.
    Si desde_otro_modulo=True, no resetea numeracion de pasos
    (se la pasa el modulo que la llama) y no imprime separador
    propio, para que se vea como un bloque continuo."""
    if not desde_otro_modulo:
        separador("M1: VELOCIDAD Y REYNOLDS")
        reset_contador()

    out("Datos del tramo:")
    Q_h = pedir_float("  Caudal Q [m3/h]")
    D   = pedir_float("  Diametro interior D [m]")
    eps = pedir_float("  Rugosidad eps [m]", EPS)
    nu  = pedir_float("  Visc. cinematica nu [m2/s]", NU)

    Q = Q_h / 3600.0
    A = math.pi * D**2 / 4.0
    v = Q / A

    reset_contador()
    paso(1, "Caudal en m3/s", "Q=Q_h/3600", Q, "m3/s")
    paso(2, "Area", "A=pi*D^2/4", A, "m2")
    paso(3, "Velocidad", "v=Q/A", v, "m/s")

    Re = v * D / nu
    epsD = eps / D

    paso(4, "Reynolds", "Re=v*D/nu", Re, "")
    paso(5, "Rugosidad relativa", "eps/D", epsD, "")

    if Re < 2300:
        out("[6] Regimen LAMINAR")
    elif Re < 4000:
        out("[6] Regimen TRANSICION")
    else:
        out("[6] Regimen TURBULENTO")

    return {"Q": Q, "Q_h": Q_h, "D": D, "v": v, "Re": Re,
            "epsD": epsD, "eps": eps, "nu": nu, "A": A}


# ============================================================
# MÓDULO 2: FACTOR DE FRICCION (Swamee-Jain y/o Colebrook-White)
# ============================================================

def f_swamee_jain(Re, epsD):
    """Formula explicita, una sola evaluacion, sin iterar."""
    denom = math.log10(epsD/3.7 + 5.74/(Re**0.9))
    f = 0.25 / (denom**2)
    return f


def f_colebrook(Re, epsD, f0, tol=0.0001, max_iter=20):
    """Itera Colebrook-White desde una semilla f0.
    Retorna f final, numero de iteraciones, y la lista
    de valores de f en cada paso (para mostrar la convergencia)."""
    f = f0
    historial = [f0]
    for i in range(max_iter):
        raiz_f = math.sqrt(f)
        dentro = epsD/3.7 + 2.51/(Re*raiz_f)
        inv_raiz_f_nuevo = -2.0 * math.log10(dentro)
        f_nuevo = 1.0 / (inv_raiz_f_nuevo**2)
        historial.append(f_nuevo)
        if abs(f_nuevo - f) < tol:
            return f_nuevo, i + 1, historial
        f = f_nuevo
    return f, max_iter, historial


def factor_friccion(desde_otro_modulo=False):
    """Pide Re y eps/D (calculandolos via M1 si se desea),
    y entrega f por Swamee-Jain y/o Colebrook-White iterado."""
    if not desde_otro_modulo:
        separador("M2: FACTOR DE FRICCION")
        reset_contador()

    menu_texto(
        "Como obtener Re y eps/D?",
        "  1) Calcular con M1 (pide Q, D)",
        "  2) Ingresar Re y eps/D directos")
    modo = pedir_int("Opcion", [1, 2])

    if modo == 1:
        datos = vel_reynolds(desde_otro_modulo=True)
        Re = datos["Re"]
        epsD = datos["epsD"]
    else:
        reset_contador()
        Re = pedir_float("  Reynolds Re")
        epsD = pedir_float("  Rugosidad relativa eps/D")
        datos = {"Re": Re, "epsD": epsD}

    menu_texto(
        "Metodo para f:",
        "  1) Swamee-Jain (directo, sin iterar)",
        "  2) Colebrook-White (iterado)",
        "  3) Ambos (Swamee-Jain como semilla)")
    metodo = pedir_int("Opcion", [1, 2, 3])

    reset_contador()
    resultado = {"Re": Re, "epsD": epsD}
    resultado.update(datos)

    if metodo in (1, 3):
        f_sj = f_swamee_jain(Re, epsD)
        paso(1, "Swamee-Jain", "f=0.25/[log(epsD/3.7+5.74/Re^0.9)]^2",
             f_sj, "")
        resultado["f_swamee_jain"] = f_sj

    if metodo == 2:
        reset_contador()
        f0 = pedir_float("  Semilla inicial f0", 0.02)
        f_final, n_iter, hist = f_colebrook(Re, epsD, f0)
        reset_contador()
        for idx, val in enumerate(hist):
            out("  f[{}] = {:.6f}".format(idx, val))
        paso(2, "Colebrook-White convergido",
             "iteraciones={}".format(n_iter), f_final, "")
        resultado["f_colebrook"] = f_final
        resultado["iteraciones"] = n_iter

    if metodo == 3:
        f0 = f_sj
        f_final, n_iter, hist = f_colebrook(Re, epsD, f0)
        reset_contador()
        out("Iterando desde semilla Swamee-Jain:")
        for idx, val in enumerate(hist):
            out("  f[{}] = {:.6f}".format(idx, val))
        paso(2, "Colebrook-White convergido",
             "iteraciones={}".format(n_iter), f_final, "")
        resultado["f_colebrook"] = f_final
        resultado["iteraciones"] = n_iter

    f_usar = resultado.get("f_colebrook", resultado.get("f_swamee_jain"))
    out_final("f a usar = {:.6f}".format(f_usar))
    resultado["f"] = f_usar

    return resultado


# ============================================================
# MÓDULO 3: PERDIDAS DE CARGA (Darcy-Weisbach + singulares)
# ============================================================

def perdida_friccional(f, L, D, v, g=G):
    """Darcy-Weisbach: hf = f*(L/D)*(v^2/2g)"""
    v2_2g = v**2 / (2.0 * g)
    hf = f * (L / D) * v2_2g
    return hf, v2_2g


def perdida_singular(suma_k, v, g=G):
    """Metodo de coeficientes k: hs = (suma_k)*(v^2/2g)"""
    v2_2g = v**2 / (2.0 * g)
    hs = suma_k * v2_2g
    return hs, v2_2g


def perdidas_tramo(nombre_tramo="TRAMO"):
    """Calcula hf y hs para UN tramo (succion o descarga),
    encadenando M1->M2 si se desea, y pide Sk ya sumado a mano."""
    separador("M3: PERDIDAS - " + nombre_tramo)
    reset_contador()

    menu_texto(
        "Obtener v y f para este tramo:",
        "  1) Calcular con M1+M2 (pide Q,D)",
        "  2) Ingresar v y f directos")
    modo = pedir_int("Opcion", [1, 2])

    if modo == 1:
        datos = factor_friccion(desde_otro_modulo=True)
        v = datos["v"]
        f = datos["f"]
        D = datos["D"]
    else:
        reset_contador()
        v = pedir_float("  Velocidad v [m/s]")
        f = pedir_float("  Factor de friccion f")
        D = pedir_float("  Diametro D [m]")

    reset_contador()
    out("Datos geometricos del tramo:")
    L  = pedir_float("  Longitud L [m]")
    Sk = pedir_float("  Suma de k (singularidades) [Sk]")
    g  = pedir_float("  Gravedad g [m/s2]", G)

    reset_contador()
    hf, v2_2g = perdida_friccional(f, L, D, v, g)
    paso(1, "v^2/2g", "v2_2g=v^2/(2g)", v2_2g, "m")
    paso(2, "hf Darcy-Weisbach", "hf=f*(L/D)*v2_2g", hf, "m")

    hs, _ = perdida_singular(Sk, v, g)
    paso(3, "hs singulares", "hs=Sk*v2_2g", hs, "m")

    h_total = hf + hs
    paso(4, "h_perdidas total", "h_total=hf+hs", h_total, "m")

    return {"v": v, "f": f, "D": D, "L": L, "Sk": Sk,
            "v2_2g": v2_2g, "hf": hf, "hs": hs, "h_total": h_total}


def perdidas_sistema():
    """Suma las perdidas de succion + descarga para tener
    el h_perdidas total del sistema (lo que se usa en M4 H_bomba)."""
    separador("M3: PERDIDAS SISTEMA COMPLETO")
    reset_contador()
    out("Se calculara SUCCION y luego DESCARGA")
    pausa_manual()

    suc = perdidas_tramo("SUCCION")
    pausa_manual()
    desc = perdidas_tramo("DESCARGA")

    reset_contador()
    separador("RESUMEN SISTEMA")
    paso(1, "hf succion", "hf_suc", suc["hf"], "m")
    paso(2, "hs succion", "hs_suc", suc["hs"], "m")
    pausa_manual()
    paso(3, "hf descarga", "hf_desc", desc["hf"], "m")
    paso(4, "hs descarga", "hs_desc", desc["hs"], "m")

    h_perd_total = suc["h_total"] + desc["h_total"]
    out_final("h_perdidas TOTAL = {:.5f} m".format(h_perd_total))

    return {"succion": suc, "descarga": desc, "h_perd_total": h_perd_total}


# ============================================================
# MÓDULO 4: ALTURA DE BOMBA (Bernoulli estanque -> consumo)
# ============================================================

def h_bomba_caso(z_consumo, z_nivel, P_req_mca, h_perd, v2_2g_desc,
                  unidades_p="mca"):
    """Bernoulli entre superficie libre del estanque (1) y punto
    de consumo (2):
    H_bomba = (z2-z1) + P_req/gamma + v2^2/2g + h_perdidas
    Si P_req ya viene en m.c.a, se usa directo (no se divide por gamma)."""
    dz = z_consumo - z_nivel
    H_bomba = dz + P_req_mca + v2_2g_desc + h_perd
    return H_bomba, dz


def modulo4_h_bomba():
    """Calcula H_bomba para UN caso (una combinacion de
    nivel de estanque + presion requerida). Se llama tantas
    veces como casos extremos se necesiten evaluar."""
    separador("M4: ALTURA DE BOMBA (H_bomba)")
    reset_contador()

    out("Cotas (mismo datum, ej. nivel bomba=0):")
    z_consumo = pedir_float("  Cota punto consumo z2 [m]")
    z_nivel   = pedir_float("  Cota nivel agua TK z1 [m]")

    reset_contador()
    out("Presion requerida en el consumo:")
    P_req = pedir_float("  P_req [m.c.a]")

    menu_texto(
        "Perdidas y velocidad:",
        "  1) Usar h_perd_total de M3 (se pide L,D,f,Sk de nuevo)",
        "  2) Ingresar h_perd y v2/2g directos")
    modo = pedir_int("Opcion", [1, 2])

    if modo == 1:
        datos_sis = perdidas_sistema()
        h_perd = datos_sis["h_perd_total"]
        v2_2g_desc = datos_sis["descarga"]["v2_2g"]
    else:
        reset_contador()
        h_perd = pedir_float("  h_perdidas total [m]")
        v2_2g_desc = pedir_float("  v_descarga^2/2g [m]")

    reset_contador()
    H_bomba, dz = h_bomba_caso(z_consumo, z_nivel, P_req, h_perd, v2_2g_desc)

    paso(1, "Desnivel", "dz=z_consumo-z_nivel", dz, "m")
    paso(2, "P_req", "P_req (dado en m.c.a)", P_req, "m")
    pausa_manual()
    paso(3, "v_desc^2/2g", "v2_2g_desc", v2_2g_desc, "m")
    paso(4, "h_perdidas total", "h_perd", h_perd, "m")

    out_final("H_bomba = dz+P_req+v2_2g+h_perd")
    out_final("H_bomba = {:.4f} m".format(H_bomba))

    return {"H_bomba": H_bomba, "dz": dz, "P_req": P_req,
            "h_perd": h_perd, "v2_2g_desc": v2_2g_desc,
            "z_consumo": z_consumo, "z_nivel": z_nivel}


def modulo4_casos_extremos():
    """Evalua varios casos extremos en secuencia (ej. nivel
    MAX/MIN x Presion min/max) y al final muestra cual exige
    la mayor H_bomba (caso de diseño)."""
    separador("M4: CASOS EXTREMOS")
    reset_contador()

    n_casos = pedir_int("Cuantos casos a evaluar?", [1, 2, 3, 4, 5, 6, 7, 8])

    resultados = []
    for i in range(n_casos):
        reset_contador()
        out("--- CASO {} de {} ---".format(i + 1, n_casos))
        etiqueta = input("  Etiqueta del caso (ej. E2-MIN-Pmax): ")
        r = modulo4_h_bomba()
        r["etiqueta"] = etiqueta
        resultados.append(r)
        pausa_manual()

    reset_contador()
    separador("RESUMEN CASOS")
    for r in resultados:
        out("{}: H={:.4f} m".format(r["etiqueta"], r["H_bomba"]))

    caso_max = max(resultados, key=lambda r: r["H_bomba"])
    out_final("CASO DE DISEÑO (H maxima):")
    out_final("  {} -> H_bomba = {:.4f} m".format(
        caso_max["etiqueta"], caso_max["H_bomba"]))

    return resultados, caso_max


# ============================================================
# MÓDULO 5a: NPSH DISPONIBLE
# ============================================================

def npsh_disponible():
    """NPSHd = (Patm-Pv)/(rho*g) + z_nivel - h_perd_succion
    Compara contra NPSHr*2 (criterio estricto del proveedor)."""
    separador("M5a: NPSH DISPONIBLE")
    reset_contador()

    out("Presiones y fluido:")
    Patm = pedir_float("  Presion atmosferica [Pa]", PATM)
    Pv   = pedir_float("  Presion de vapor [Pa]", PV)
    rho  = pedir_float("  Densidad [kg/m3]", RHO)
    g    = pedir_float("  Gravedad [m/s2]", G)

    reset_contador()
    out("Geometria y perdidas de succion:")
    z_nivel = pedir_float("  Cota nivel agua TK z_nivel [m] (signo segun datum)")
    h_perd_suc = pedir_float("  h_perdidas succion [m] (hf+hs)")

    reset_contador()
    term_presion = (Patm - Pv) / (rho * g)
    paso(1, "Termino presion", "(Patm-Pv)/(rho*g)", term_presion, "m")
    paso(2, "z_nivel", "cota nivel TK", z_nivel, "m")
    paso(3, "h_perd succion", "hf_suc+hs_suc", h_perd_suc, "m")

    NPSHd = term_presion + z_nivel - h_perd_suc
    out_final("NPSHd = term_presion+z_nivel-h_perd_suc")
    out_final("NPSHd = {:.4f} m".format(NPSHd))

    reset_contador()
    out("Comparar con NPSHr de la bomba?")
    comparar = pedir_int("  1=Si  0=No", [0, 1])

    if comparar:
        reset_contador()
        NPSHr = pedir_float("  NPSHr de la bomba [m]")
        factor_exigido = pedir_float("  Factor exigido (ej. 2.0)", 2.0)

        ratio = NPSHd / NPSHr if NPSHr != 0 else INF
        limite = factor_exigido * NPSHr

        reset_contador()
        paso(4, "NPSHr", "dato bomba", NPSHr, "m")
        paso(5, "Ratio NPSHd/NPSHr", "NPSHd/NPSHr", ratio, "")
        paso(6, "Limite exigido", "factor*NPSHr", limite, "m")

        verificar(NPSHd >= limite,
                  "CUMPLE NPSHd>={:.2f}*NPSHr".format(factor_exigido),
                  "NO CUMPLE, falta {:.4f} m".format(limite - NPSHd))

        return {"NPSHd": NPSHd, "NPSHr": NPSHr, "ratio": ratio,
                "limite": limite, "cumple": NPSHd >= limite}

    return {"NPSHd": NPSHd}


# ============================================================
# MÓDULO 5b: ESPESOR MINIMO ASME B31.3
# ============================================================

def espesor_asme(P, D_ext, S, E_factor, Y):
    """t = P*D / (2*(S*E+P*Y))   -- ASME B31.3 304.1.2
    P y S deben estar en las MISMAS unidades de presion."""
    t = (P * D_ext) / (2.0 * (S * E_factor + P * Y))
    return t


def espesor_asme_modulo():
    separador("M5b: ESPESOR MINIMO ASME B31.3")
    reset_contador()

    menu_texto(
        "Presion de diseño:",
        "  Si tienes H_bomba en m, se convierte a Pa con gamma")
    modo_p = pedir_int("  1) Tengo H_bomba [m]  2) Tengo P [MPa]", [1, 2])

    if modo_p == 1:
        reset_contador()
        H_bomba = pedir_float("  H_bomba (presion max diseño) [m]")
        gamma = pedir_float("  Peso especifico gamma [N/m3]", GAMMA)
        P_pa = H_bomba * gamma
        P_mpa = P_pa / 1.0e6
        reset_contador()
        paso(1, "P en Pa", "P=H_bomba*gamma", P_pa, "Pa")
        paso(2, "P en MPa", "P=P_pa/1e6", P_mpa, "MPa")
    else:
        reset_contador()
        P_mpa = pedir_float("  Presion de diseño P [MPa]")

    reset_contador()
    out("Geometria y material de la cañeria:")
    D_ext = pedir_float("  Diametro exterior D [mm]")
    e_nom = pedir_float("  Espesor nominal cañeria [mm]")
    S     = pedir_float("  Resistencia fluencia S [MPa]", 250.0)
    Ef    = pedir_float("  Factor de calidad E", 1.0)
    Y     = pedir_float("  Coef. relacion espesor Y", 0.4)

    reset_contador()
    t_min = espesor_asme(P_mpa, D_ext, S, Ef, Y)
    paso(3, "t minimo (sin corrosion)",
         "t=P*D/(2*(S*E+P*Y))", t_min, "mm")

    margen = e_nom - t_min
    paso(4, "Margen", "margen=e_nom-t_min", margen, "mm")

    verificar(e_nom >= t_min,
              "RESISTE: e_nom>=t_min (margen={:.4f}mm)".format(margen),
              "NO RESISTE: e_nom<t_min (falta {:.4f}mm)".format(-margen))

    return {"t_min": t_min, "e_nom": e_nom, "margen": margen,
            "P_mpa": P_mpa}


# ============================================================
# MÓDULO 6: SUMERGENCIA MINIMA
# ============================================================

def sumergencia_minima(desde_otro_modulo=False):
    """Hmin = v_suc^2/(2g) + 0.2
    Formula de sumergencia minima requerida sobre la boca de
    succion (valvula de pie), para evitar entrada de aire/vortice."""
    if not desde_otro_modulo:
        separador("M6: SUMERGENCIA MINIMA")
        reset_contador()

    menu_texto(
        "Obtener v_succion:",
        "  1) Calcular con M1 (pide Q, D)",
        "  2) Ingresar v directo")
    modo = pedir_int("Opcion", [1, 2])

    if modo == 1:
        datos = vel_reynolds(desde_otro_modulo=True)
        v_suc = datos["v"]
    else:
        reset_contador()
        v_suc = pedir_float("  Velocidad succion v [m/s]")

    reset_contador()
    g = pedir_float("  Gravedad g [m/s2]", G)
    offset = pedir_float("  Termino constante [m]", 0.2)

    reset_contador()
    v2_2g = v_suc**2 / (2.0 * g)
    paso(1, "v_suc^2/2g", "v2_2g=v_suc^2/(2g)", v2_2g, "m")

    H_min = v2_2g + offset
    out_final("H_min = v2_2g + {:.2f}".format(offset))
    out_final("H_min = {:.4f} m".format(H_min))

    return {"v_suc": v_suc, "v2_2g": v2_2g, "H_min": H_min}


# ============================================================

# ============================================================
# ALTURA NETA - TURBINA DE ACCION (PELTON)
# ============================================================

def altura_neta_accion():
    """Para Pelton, la altura neta es directamente la energia
    disponible en el embalse menos las perdidas de la conduccion
    forzada hasta la entrada del inyector (no hay Ps/gamma porque
    el chorro descarga a presion atmosferica, Cs ya esta incluido
    en H bruta - perdidas, segun el balance de energia entre el
    embalse y la salida del inyector)."""
    separador("ALTURA NETA - ACCION (PELTON)")
    reset_contador()

    out("Datos de la instalacion:")
    z_embalse = pedir_float("  Cota embalse z_emb [m]")
    z_inyector = pedir_float("  Cota inyector z_iny [m]")
    h_perd_conduccion = pedir_float("  Perdidas en conduccion forzada [m]")

    reset_contador()
    H_bruta = z_embalse - z_inyector
    paso(1, "Altura bruta", "H_bruta=z_emb-z_iny", H_bruta, "m")
    paso(2, "Perdidas conduccion", "h_perd", h_perd_conduccion, "m")

    H_neta = H_bruta - h_perd_conduccion
    out_final("H_neta = H_bruta - h_perd")
    out_final("H_neta = {:.4f} m".format(H_neta))

    return {"H_bruta": H_bruta, "h_perd": h_perd_conduccion,
            "H_neta": H_neta}


# ============================================================
# ALTURA NETA - TURBINA DE REACCION (FRANCIS/KAPLAN)
# ============================================================

def altura_neta_reaccion():
    """H = (zE-zS) + (PE-PS)/gamma + (cE^2-cS^2)/2g - h_perd_conduccion
    Pregunta caso a caso si Ps/gamma y Cs^2/2g se desprecian,
    en vez de asumirlo automaticamente (advertencia:
    revisar bien el punto de entrada/salida antes de despreciar).
    Usa G y GAMMA (definidos en el bloque de piping) como
    constantes compartidas del agua."""
    separador("ALTURA NETA - REACCION (FRANCIS/KAPLAN)")
    reset_contador()

    out("Punto E = entrada turbina (camara espiral)")
    out("Punto S = salida difusor (descarga)")
    pausa_manual()

    reset_contador()
    out("Cotas:")
    zE = pedir_float("  Cota entrada zE [m]")
    zS = pedir_float("  Cota salida zS [m]")

    reset_contador()
    out("Presiones (entrada):")
    PE_dato = pedir_float("  PE/gamma directo en [m] (o -1 si tienes PE en Pa)")
    if PE_dato < 0:
        PE_pa = pedir_float("  PE [Pa]")
        gamma = pedir_float("  Peso especifico gamma [N/m3]", GAMMA)
        PE_gamma = PE_pa / gamma
    else:
        PE_gamma = PE_dato

    reset_contador()
    menu_texto(
        "Presion en la salida (S):",
        "  Atencion: revisar la instalacion real antes de",
        "  asumir PS/gamma=0 (verificar antes)")
    desprecia_PS = pedir_int("  Despreciar PS/gamma (=0)? 1=Si 0=No", [0, 1])
    if desprecia_PS:
        PS_gamma = 0.0
    else:
        PS_dato = pedir_float("  PS/gamma directo en [m] (o -1 si tienes PS en Pa)")
        if PS_dato < 0:
            PS_pa = pedir_float("  PS [Pa]")
            gamma2 = pedir_float("  Peso especifico gamma [N/m3]", GAMMA)
            PS_gamma = PS_pa / gamma2
        else:
            PS_gamma = PS_dato

    reset_contador()
    out("Velocidades:")
    cE = pedir_float("  Velocidad entrada cE [m/s]", 0.0)

    menu_texto(
        "  Atencion: revisar si Cs^2/2g es significativo",
        "  antes de despreciarlo (verificar antes)")
    desprecia_CS = pedir_int("  Despreciar CS^2/2g (=0)? 1=Si 0=No", [0, 1])
    if desprecia_CS:
        cS = 0.0
    else:
        cS = pedir_float("  Velocidad salida cS [m/s]")

    reset_contador()
    out("Perdidas:")
    h_perd_conduccion = pedir_float("  Perdidas conduccion forzada [m]", 0.0)
    g = pedir_float("  Gravedad g [m/s2]", G)

    reset_contador()
    dz = zE - zS
    dP_gamma = PE_gamma - PS_gamma
    dc2_2g = (cE**2 - cS**2) / (2.0 * g)

    paso(1, "Desnivel", "dz=zE-zS", dz, "m")
    paso(2, "Termino presion", "(PE-PS)/gamma", dP_gamma, "m")
    pausa_manual()
    paso(3, "Termino cinetico", "(cE^2-cS^2)/2g", dc2_2g, "m")
    paso(4, "Perdidas conduccion", "h_perd", h_perd_conduccion, "m")

    H_neta = dz + dP_gamma + dc2_2g - h_perd_conduccion

    out_final("H = dz+(PE-PS)/g+(cE^2-cS^2)/2g-h_perd")
    out_final("H_neta = {:.4f} m".format(H_neta))

    if desprecia_PS or desprecia_CS:
        out_final("Nota: se desprecio " +
                  ("PS/g " if desprecia_PS else "") +
                  ("CS^2/2g" if desprecia_CS else ""))

    return {"dz": dz, "dP_gamma": dP_gamma, "dc2_2g": dc2_2g,
            "h_perd": h_perd_conduccion, "H_neta": H_neta,
            "PE_gamma": PE_gamma, "PS_gamma": PS_gamma,
            "cE": cE, "cS": cS}


def menu_altura_neta():
    while True:
        menu_texto(
            "=== ALTURA NETA - MENU ===",
            "  1) Accion (Pelton)",
            "  2) Reaccion (Francis/Kaplan)",
            "  0) Volver")

        op = pedir_int("Opcion", [0, 1, 2])

        if op == 1:
            altura_neta_accion()
        elif op == 2:
            altura_neta_reaccion()
        elif op == 0:
            break

        pausa_manual()


# ============================================================
# MENÚ MAESTRO - PIPING + TURBINAS
# ============================================================

def menu_piping():
    while True:
        menu_texto(
            "=== PIPING EITH - MENU ===",
            "  1) M1: Velocidad y Reynolds",
            "  2) M2: Factor de friccion",
            "  3) M3: Perdidas de carga",
            "  4) M4: H_bomba",
            "  5) M5a: NPSH disponible",
            "  6) M5b: Espesor ASME B31.3",
            "  7) M6: Sumergencia minima",
            "  0) Volver")

        op = pedir_int("Opcion", [0, 1, 2, 3, 4, 5, 6, 7])

        if op == 1:
            vel_reynolds()
        elif op == 2:
            factor_friccion()
        elif op == 3:
            menu_texto(
                "M3 Perdidas de carga:",
                "  1) Un tramo (succion/descarga)",
                "  2) Sistema completo (ambos)")
            sub = pedir_int("Opcion", [1, 2])
            if sub == 1:
                menu_texto(
                    "Nombre del tramo:",
                    "  1) Succion  2) Descarga")
                t = pedir_int("Opcion", [1, 2])
                nombre = "SUCCION" if t == 1 else "DESCARGA"
                perdidas_tramo(nombre)
            else:
                perdidas_sistema()
        elif op == 4:
            menu_texto(
                "M4 H_bomba:",
                "  1) Un caso puntual",
                "  2) Varios casos extremos")
            sub = pedir_int("Opcion", [1, 2])
            if sub == 1:
                modulo4_h_bomba()
            else:
                modulo4_casos_extremos()
        elif op == 5:
            npsh_disponible()
        elif op == 6:
            espesor_asme_modulo()
        elif op == 7:
            sumergencia_minima()
        elif op == 0:
            break

        pausa_manual()


def menu_maestro():
    while True:
        menu_texto(
            "=== EITH - PROGRAMA GENERAL ===",
            "  1) Piping (bombeo, M1-M5)",
            "  2) Altura neta (turbinas)",
            "  0) Salir")

        op = pedir_int("Opcion", [0, 1, 2])

        if op == 1:
            menu_piping()
        elif op == 2:
            menu_altura_neta()
        elif op == 0:
            out("Saliendo...")
            break


menu_maestro()
