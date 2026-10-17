# ============================================================
#   TRANSFORMADA DE LAPLACE - SOLUCIONADOR TIPO PAUTA
#   Control automatico - Ogata, cap. 2 y 4
#   Tabla 2-1 (pares) y Tabla 2-2 (propiedades) de Ogata
#   Compatible TI-Nspire CX II (Python 3.6+)
# ============================================================
#
# La Nspire no transforma simbolos: este programa recorre con
# NUMEROS el camino de un ejercicio tipico:
#   EDO -> Y(s) (M2) -> fracciones parciales -> y(t) (M3)
# Limites: grado de D(s) hasta 3, solo polos simples en M3.
# Los polos dobles tipicos (rampa en 1er orden, zeta=1) se
# resuelven en M4 con las formulas cerradas de la Tabla 2-1.

import math

TOL_REP = 1e-4     # tolerancia relativa para detectar polo repetido
TOL_CERO = 1e-12   # umbral de coeficiente nulo

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

def pausa_suave():
    """pausa_manual() solo si hay lineas sin ver desde la ultima
    pausa -- evita pedir dos Enter seguidos cuando out() acaba
    de hacer su propia pausa."""
    if _contador_lineas[0] > 0:
        pausa_manual()

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

def paso_txt(n, desc, formula, texto):
    """Igual que paso(), pero el resultado es texto (un polinomio,
    un polo complejo, una expresion) en vez de un numero."""
    out("[{}] {}".format(n, desc))
    if formula:
        out("  " + formula)
    out("  = " + texto)

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
# FORMATO DE NUMEROS Y POLINOMIOS
# Polinomio = lista de coeficientes, de mayor a menor grado:
#   [1, 3, 2]  ->  s^2 + 3s + 2
# ============================================================

def fmt(x):
    if abs(x) < TOL_CERO:
        return "0"
    if abs(x - round(x)) < 1e-9 and abs(x) < 1e9:
        return str(int(round(x)))
    return "{:.5g}".format(x)

def fmt_c(z):
    """Numero complejo como texto: -1+2j, -1-2j, o solo real."""
    re = z.real
    im = z.imag
    if abs(im) < 1e-9 * (1 + abs(re)):
        return fmt(re)
    signo = "+" if im >= 0 else "-"
    return "{}{}{}j".format(fmt(re), signo, fmt(abs(im)))

def con_signo(x):
    """'+2.5' o '-2.5', para encadenar terminos."""
    if x < 0:
        return "-" + fmt(-x)
    return "+" + fmt(x)

def fact(n):
    r = 1
    for i in range(2, n + 1):
        r *= i
    return r

def p_trim(c):
    c = [float(x) for x in c]
    escala = max([abs(x) for x in c] + [1.0])
    i = 0
    while i < len(c) - 1 and abs(c[i]) < TOL_CERO * escala:
        i += 1
    return c[i:]

def p_eval(c, x):
    """Horner. Funciona con x real o complejo."""
    v = 0
    for a in c:
        v = v * x + a
    return v

def p_der(c):
    g = len(c) - 1
    if g == 0:
        return [0.0]
    return [c[i] * (g - i) for i in range(g)]

def p_mul(a, b):
    r = [0.0] * (len(a) + len(b) - 1)
    for i in range(len(a)):
        for j in range(len(b)):
            r[i + j] += a[i] * b[j]
    return r

def p_add(a, b):
    n = max(len(a), len(b))
    a = [0.0] * (n - len(a)) + list(a)
    b = [0.0] * (n - len(b)) + list(b)
    return [a[i] + b[i] for i in range(n)]

def p_div(num, den):
    """Division larga: devuelve (cociente, resto)."""
    num = list(num)
    den = p_trim(den)
    if len(num) < len(den):
        return [0.0], p_trim(num)
    q = [0.0] * (len(num) - len(den) + 1)
    for i in range(len(q)):
        coef = num[i] / den[0]
        q[i] = coef
        for j in range(len(den)):
            num[i + j] -= coef * den[j]
    resto = num[len(q):]
    if not resto:
        resto = [0.0]
    return q, p_trim(resto)

def p_str(c, v="s"):
    c = p_trim(c)
    g = len(c) - 1
    txt = ""
    for i in range(len(c)):
        a = c[i]
        pw = g - i
        if abs(a) < TOL_CERO:
            continue
        mag = abs(a)
        if pw == 0:
            t = fmt(mag)
        else:
            base = v if pw == 1 else "{}^{}".format(v, pw)
            t = base if abs(mag - 1) < 1e-12 else fmt(mag) + base
        if txt == "":
            txt = ("-" if a < 0 else "") + t
        else:
            txt += ("-" if a < 0 else "+") + t
    return txt if txt else "0"

def pedir_poli(nombre, gmin, gmax):
    g = pedir_int("  Grado de {} ({}-{})".format(nombre, gmin, gmax),
                  list(range(gmin, gmax + 1)))
    c = []
    for pw in range(g, -1, -1):
        c.append(pedir_float("  {}: coef. de s^{}".format(nombre, pw)))
    if abs(c[0]) < TOL_CERO:
        out("Coef. principal = 0, se recorta el grado")
    return p_trim(c)


# ============================================================
# RAICES DE POLINOMIOS (grado 1 a 3)
# grado 2: formula cuadratica exacta
# grado 3: una raiz real por biseccion (un cubico real siempre
#          tiene una) + division sintetica -> cuadratica
# ============================================================

def raices_cuadratica(a, b, c):
    disc = b * b - 4 * a * c
    if disc >= 0:
        rd = math.sqrt(disc)
        q = -0.5 * (b + rd) if b >= 0 else -0.5 * (b - rd)
        if abs(q) < TOL_CERO:
            return [complex(0, 0), complex(0, 0)]
        return [complex(q / a, 0), complex(c / q, 0)]
    re = -b / (2 * a)
    im = abs(math.sqrt(-disc) / (2 * a))
    return [complex(re, im), complex(re, -im)]

def raiz_real_cubica(c):
    a = c[0]
    m = [x / a for x in c]
    R = 1 + max(abs(m[1]), abs(m[2]), abs(m[3]))
    lo = -R
    hi = R
    flo = p_eval(m, lo)
    for i in range(200):
        mid = 0.5 * (lo + hi)
        fm = p_eval(m, mid)
        if fm == 0:
            return mid
        if (fm < 0) == (flo < 0):
            lo = mid
            flo = fm
        else:
            hi = mid
    return 0.5 * (lo + hi)

def raices(c):
    c = p_trim(c)
    g = len(c) - 1
    if g == 1:
        return [complex(-c[1] / c[0], 0)]
    if g == 2:
        return raices_cuadratica(c[0], c[1], c[2])
    if g == 3:
        r = raiz_real_cubica(c)
        q0 = c[0]
        q1 = c[1] + r * q0
        q2 = c[2] + r * q1
        return [complex(r, 0)] + raices_cuadratica(q0, q1, q2)
    return None

def hay_repetido(polos):
    for i in range(len(polos)):
        for j in range(i + 1, len(polos)):
            if abs(polos[i] - polos[j]) < TOL_REP * (1 + abs(polos[i])):
                return polos[i]
    return None

def es_real(z):
    return abs(z.imag) < 1e-9 * (1 + abs(z.real))


# ============================================================
# MÓDULO 1: TABLA DE PARES (Tabla 2-1) Y PROPIEDADES (Tabla 2-2)
# ============================================================

def _sq1z(p):
    return math.sqrt(1 - p["z"] ** 2)

def _phi(p):
    return math.atan(_sq1z(p) / p["z"])

def _senh(x):
    return (math.exp(x) - math.exp(-x)) / 2.0

def _cosh(x):
    return (math.exp(x) + math.exp(-x)) / 2.0

# (numero, f(t), F(s), parametros, f(t, p) o None, nota)
PARES = [
 (1, "d(t) impulso unitario", "1", [], None, ""),
 (2, "1(t) escalon unitario", "1/s", [],
  lambda t, p: 1.0, ""),
 (3, "t", "1/s^2", [],
  lambda t, p: t, ""),
 (4, "t^(n-1)/(n-1)!", "1/s^n", ["n"],
  lambda t, p: t ** (p["n"] - 1) / fact(p["n"] - 1), "n=1,2,3..."),
 (5, "t^n", "n!/s^(n+1)", ["n"],
  lambda t, p: t ** p["n"], "n=1,2,3..."),
 (6, "e^(-at)", "1/(s+a)", ["a"],
  lambda t, p: math.exp(-p["a"] * t), ""),
 (7, "t*e^(-at)", "1/(s+a)^2", ["a"],
  lambda t, p: t * math.exp(-p["a"] * t), ""),
 (8, "t^(n-1)*e^(-at)/(n-1)!", "1/(s+a)^n", ["n", "a"],
  lambda t, p: t ** (p["n"] - 1) * math.exp(-p["a"] * t) / fact(p["n"] - 1),
  "(!) es 1/(s+a)^n, no 1/(s+a)"),
 (9, "t^n*e^(-at)", "n!/(s+a)^(n+1)", ["n", "a"],
  lambda t, p: t ** p["n"] * math.exp(-p["a"] * t), "n=1,2,3..."),
 (10, "sen(wt)", "w/(s^2+w^2)", ["w"],
  lambda t, p: math.sin(p["w"] * t), ""),
 (11, "cos(wt)", "s/(s^2+w^2)", ["w"],
  lambda t, p: math.cos(p["w"] * t), ""),
 (12, "senh(wt)", "w/(s^2-w^2)", ["w"],
  lambda t, p: _senh(p["w"] * t), ""),
 (13, "cosh(wt)", "s/(s^2-w^2)", ["w"],
  lambda t, p: _cosh(p["w"] * t), ""),
 (14, "(1/a)(1-e^(-at))", "1/(s(s+a))", ["a"],
  lambda t, p: (1 - math.exp(-p["a"] * t)) / p["a"], ""),
 (15, "(e^(-at)-e^(-bt))/(b-a)", "1/((s+a)(s+b))", ["a", "b"],
  lambda t, p: (math.exp(-p["a"] * t) - math.exp(-p["b"] * t)) / (p["b"] - p["a"]),
  "a distinto de b"),
 (16, "(b*e^(-bt)-a*e^(-at))/(b-a)", "s/((s+a)(s+b))", ["a", "b"],
  lambda t, p: (p["b"] * math.exp(-p["b"] * t) - p["a"] * math.exp(-p["a"] * t)) / (p["b"] - p["a"]),
  "a distinto de b"),
 (17, "(1/ab)[1+(b*e^(-at)-a*e^(-bt))/(a-b)]", "1/(s(s+a)(s+b))", ["a", "b"],
  lambda t, p: (1 + (p["b"] * math.exp(-p["a"] * t) - p["a"] * math.exp(-p["b"] * t)) / (p["a"] - p["b"])) / (p["a"] * p["b"]),
  "a distinto de b"),
 (18, "(1/a^2)(1-e^(-at)-a*t*e^(-at))", "1/(s(s+a)^2)", ["a"],
  lambda t, p: (1 - math.exp(-p["a"] * t) - p["a"] * t * math.exp(-p["a"] * t)) / p["a"] ** 2, ""),
 (19, "(1/a^2)(a*t-1+e^(-at))", "1/(s^2(s+a))", ["a"],
  lambda t, p: (p["a"] * t - 1 + math.exp(-p["a"] * t)) / p["a"] ** 2, ""),
 (20, "e^(-at)*sen(wt)", "w/((s+a)^2+w^2)", ["a", "w"],
  lambda t, p: math.exp(-p["a"] * t) * math.sin(p["w"] * t), ""),
 (21, "e^(-at)*cos(wt)", "(s+a)/((s+a)^2+w^2)", ["a", "w"],
  lambda t, p: math.exp(-p["a"] * t) * math.cos(p["w"] * t), ""),
 (22, "wn/sqrt(1-z^2)*e^(-z*wn*t)*sen(wd*t)", "wn^2/(s^2+2z*wn*s+wn^2)", ["z", "wn"],
  lambda t, p: p["wn"] / _sq1z(p) * math.exp(-p["z"] * p["wn"] * t) * math.sin(p["wn"] * _sq1z(p) * t),
  "0<z<1, wd=wn*sqrt(1-z^2)"),
 (23, "-1/sqrt(1-z^2)*e^(-z*wn*t)*sen(wd*t-phi)", "s/(s^2+2z*wn*s+wn^2)", ["z", "wn"],
  lambda t, p: -1 / _sq1z(p) * math.exp(-p["z"] * p["wn"] * t) * math.sin(p["wn"] * _sq1z(p) * t - _phi(p)),
  "0<z<1, phi=atan(sqrt(1-z^2)/z)"),
 (24, "1-1/sqrt(1-z^2)*e^(-z*wn*t)*sen(wd*t+phi)", "wn^2/(s(s^2+2z*wn*s+wn^2))", ["z", "wn"],
  lambda t, p: 1 - 1 / _sq1z(p) * math.exp(-p["z"] * p["wn"] * t) * math.sin(p["wn"] * _sq1z(p) * t + _phi(p)),
  "0<z<1, phi=atan(sqrt(1-z^2)/z)"),
 (25, "1-cos(wt)", "w^2/(s(s^2+w^2))", ["w"],
  lambda t, p: 1 - math.cos(p["w"] * t), ""),
 (26, "wt-sen(wt)", "w^3/(s^2(s^2+w^2))", ["w"],
  lambda t, p: p["w"] * t - math.sin(p["w"] * t), ""),
 (27, "sen(wt)-wt*cos(wt)", "2w^3/(s^2+w^2)^2", ["w"],
  lambda t, p: math.sin(p["w"] * t) - p["w"] * t * math.cos(p["w"] * t), ""),
 (28, "t*sen(wt)/(2w)", "s/(s^2+w^2)^2", ["w"],
  lambda t, p: t * math.sin(p["w"] * t) / (2 * p["w"]), ""),
 (29, "t*cos(wt)", "(s^2-w^2)/(s^2+w^2)^2", ["w"],
  lambda t, p: t * math.cos(p["w"] * t), ""),
 (30, "(cos(w1*t)-cos(w2*t))/(w2^2-w1^2)", "s/((s^2+w1^2)(s^2+w2^2))", ["w1", "w2"],
  lambda t, p: (math.cos(p["w1"] * t) - math.cos(p["w2"] * t)) / (p["w2"] ** 2 - p["w1"] ** 2),
  "w1^2 distinto de w2^2"),
 (31, "(sen(wt)+wt*cos(wt))/(2w)", "s^2/(s^2+w^2)^2", ["w"],
  lambda t, p: (math.sin(p["w"] * t) + p["w"] * t * math.cos(p["w"] * t)) / (2 * p["w"]), ""),
]

FAMILIAS = [
 ("Impulso, escalon, potencias", [1, 2, 3, 4, 5]),
 ("Exponenciales", [6, 7, 8, 9]),
 ("Seno, coseno, hiperbolicas", [10, 11, 12, 13]),
 ("Combinaciones exponenciales", [14, 15, 16, 17, 18, 19]),
 ("Amortiguados / 2do orden", [20, 21, 22, 23, 24]),
 ("Combinaciones trigonometricas", [25, 26, 27, 28, 29, 30, 31]),
]

PROPIEDADES = [
 "[1] L[A*f] = A*F(s)",
 "[2] L[f1+-f2] = F1(s)+-F2(s)",
 "[3] L[f'] = s*F(s)-f(0)",
 "[4] L[f''] = s^2*F(s)-s*f(0)-f'(0)",
 "[5] L[f^(n)] = s^n*F(s)",
 "    - suma(k=1..n) s^(n-k)*f^(k-1)(0)",
 "[6] L[int f dt] = F(s)/s",
 "    + (1/s)*[int f dt] en t=0",
 "[7] L[int..int f (dt)^n] = F(s)/s^n",
 "    + suma(k=1..n) [int^k f](0)/s^(n-k+1)",
 "[8] L[int_0^t f dt] = F(s)/s",
 "[9] int_0^inf f dt = lim(s->0) F(s)",
 "[10] L[e^(-at)*f] = F(s+a)",
 "[11] L[f(t-a)*1(t-a)] = e^(-as)*F(s)",
 "     a >= 0",
 "[12] L[t*f] = -dF/ds",
 "[13] L[t^2*f] = d^2F/ds^2",
 "[14] L[t^n*f] = (-1)^n d^nF/ds^n",
 "[15] L[f/t] = int_s^inf F(s) ds",
 "[16] L[f(t/a)] = a*F(as)",
 "[17] L[int_0^t f1(t-u)f2(u)du]",
 "     = F1(s)*F2(s)  (convolucion)",
 "[18] L[f*g] = (1/2pi*j)*",
 "     int F(p)G(s-p)dp",
]

def buscar_par(n):
    for par in PARES:
        if par[0] == n:
            return par
    return None

def mostrar_par(par):
    out("[{}] f(t)={}".format(par[0], par[1]))
    out("    F(s)={}".format(par[2]))
    if par[5]:
        out("    " + par[5])

def evaluar_par(par):
    reset_contador()
    if par[4] is None:
        out("Impulso: no se evalua en un t")
        return None
    p = {}
    for nombre in par[3]:
        if nombre == "n":
            p["n"] = pedir_int("  n (entero 1-10)", list(range(1, 11)))
        else:
            p[nombre] = pedir_float("  " + nombre)
    if par[0] in (22, 23, 24):
        if not (0 < p["z"] < 1):
            out("Par valido solo para 0<zeta<1")
            out("Para otro zeta usar M4 (2do orden)")
            return None
    t = pedir_float("  t")
    reset_contador()
    try:
        v = par[4](t, p)
    except (ZeroDivisionError, ValueError, OverflowError):
        out("Parametros invalidos para este par")
        return None
    paso(1, "f(t) del par {} en t={}".format(par[0], fmt(t)),
         par[1], v, "")
    return v

def tabla_pares():
    separador("M1: TABLA DE LAPLACE")
    reset_contador()

    lineas = ["Tabla 2-1 (pares) / 2-2 (propiedades):"]
    for i in range(len(FAMILIAS)):
        lineas.append("  {}) {}".format(i + 1, FAMILIAS[i][0]))
    lineas.append("  7) Propiedades (Tabla 2-2)")
    menu_texto(*lineas)
    op = pedir_int("Opcion", [1, 2, 3, 4, 5, 6, 7])

    reset_contador()
    if op == 7:
        for linea in PROPIEDADES:
            out(linea)
        return {"familia": 7}

    nombre, numeros = FAMILIAS[op - 1]
    out("--- " + nombre + " ---")
    for n in numeros:
        mostrar_par(buscar_par(n))

    reset_contador()
    ev = pedir_int("Evaluar un par? 1=Si 0=No", [0, 1])
    resultado = {"familia": op, "valor": None}
    while ev == 1:
        n = pedir_int("  Numero de par", numeros)
        resultado["valor"] = evaluar_par(buscar_par(n))
        reset_contador()
        ev = pedir_int("Evaluar otro? 1=Si 0=No", [0, 1])
    return resultado


# ============================================================
# MÓDULO 2: DE LA EDO A Y(s)
#   a_n*y^(n) + ... + a1*y' + a0*y = r(t)
# Aplica propiedades 1, 2 y 3-5 de la Tabla 2-2:
#   (sum a_k*s^k) Y(s) - IC(s) = R(s)
#   Y(s) = [R(s) + IC(s)] / P(s)
# ============================================================

def edo_a_Ys(desde_otro_modulo=False):
    if not desde_otro_modulo:
        separador("M2: EDO -> Y(s)")
        reset_contador()

    menu_texto(
        "Orden de la EDO:",
        "  1) y'  (1er orden)",
        "  2) y'' (2do orden)",
        "  3) y'''(3er orden)")
    n = pedir_int("Orden", [1, 2, 3])

    reset_contador()
    out("a{}*y^({})+...+a1*y'+a0*y = r(t)".format(n, n))
    a = [0.0] * (n + 1)
    for k in range(n, -1, -1):
        a[k] = pedir_float("  a{} (coef. de y{})".format(k, "'" * k))
        while k == n and abs(a[k]) < TOL_CERO:
            out("a{} no puede ser 0".format(n))
            a[k] = pedir_float("  a{} (coef. de y{})".format(k, "'" * k))

    menu_texto(
        "Entrada r(t):",
        "  1) Impulso A*d(t)",
        "  2) Escalon A*1(t)",
        "  3) Rampa A*t",
        "  4) Seno A*sen(wt)",
        "  5) Coseno A*cos(wt)",
        "  6) Sin entrada (resp. libre)")
    ent = pedir_int("Entrada", [1, 2, 3, 4, 5, 6])

    reset_contador()
    A = 0.0
    w = 0.0
    if ent != 6:
        A = pedir_float("  Amplitud A", 1.0)
    if ent in (4, 5):
        w = pedir_float("  w [rad/s]")

    if ent == 1:
        Rn, Rd, r_txt = [A], [1.0], "A"
    elif ent == 2:
        Rn, Rd, r_txt = [A], [1.0, 0.0], "A/s"
    elif ent == 3:
        Rn, Rd, r_txt = [A], [1.0, 0.0, 0.0], "A/s^2"
    elif ent == 4:
        Rn, Rd, r_txt = [A * w], [1.0, 0.0, w * w], "A*w/(s^2+w^2)"
    elif ent == 5:
        Rn, Rd, r_txt = [A, 0.0], [1.0, 0.0, w * w], "A*s/(s^2+w^2)"
    else:
        Rn, Rd, r_txt = [0.0], [1.0], "0"

    reset_contador()
    out("Condiciones iniciales:")
    ci = []
    for j in range(n):
        ci.append(pedir_float("  y{}(0)".format("'" * j), 0.0))

    # P(s) = sum a_k s^k   (de mayor a menor grado)
    P = [a[k] for k in range(n, -1, -1)]

    # IC(s): coef. de s^m = sum_{k=m+1..n} a_k * y^(k-m-1)(0)
    asc = [0.0] * n
    for m in range(n):
        acum = 0.0
        for k in range(m + 1, n + 1):
            acum += a[k] * ci[k - m - 1]
        asc[m] = acum
    IC = list(reversed(asc))

    N = p_trim(p_add(Rn, p_mul(IC, Rd)))
    D = p_trim(p_mul(P, Rd))

    reset_contador()
    out("[1] Transformar cada termino")
    out("  (Tabla 2-2, prop. 1-5):")
    out("  L[y']=sY-y(0)")
    if n >= 2:
        out("  L[y'']=s^2Y-s*y(0)-y'(0)")
    if n >= 3:
        out("  L[y''']=s^3Y-s^2y(0)-s*y'(0)")
        out("         -y''(0)")
    paso_txt(2, "P(s) (coef. de Y)", "sum a_k*s^k", p_str(P))
    paso_txt(3, "Terminos de CI", "IC(s)", p_str(IC))
    pausa_suave()
    paso_txt(4, "Entrada R(s)", r_txt,
             p_str(Rn) + " / " + p_str(Rd) if ent != 6 else "0")
    out("[5] Y(s)=[R(s)+IC(s)]/P(s)")
    paso_txt(6, "Numerador N(s)", "Rn+IC*Rd", p_str(N))
    paso_txt(7, "Denominador D(s)", "P*Rd", p_str(D))

    ci_nulas = all(abs(x) < TOL_CERO for x in ci)
    if ci_nulas:
        out("CI=0 -> G(s)=Y(s)/R(s)=1/P(s)")
        out_final("G(s) = 1/(" + p_str(P) + ")")
    g_D = len(D) - 1
    if g_D > 3:
        out_final("(!) grado D(s)={} > 3:".format(g_D))
        out_final("    M3 no lo invierte")

    return {"N": N, "D": D, "P": P, "IC": IC,
            "Rn": Rn, "Rd": Rd, "orden": n, "entrada": ent,
            "ci": ci, "ci_nulas": ci_nulas}


# ============================================================
# MÓDULO 3: TRANSFORMADA INVERSA POR FRACCIONES PARCIALES
# Polos simples, grado de D(s) <= 3.
#   residuo en p_k: r_k = N(p_k) / D'(p_k)
#   polo real p      -> r*e^(p*t)
#   par complejo s+-jw con residuo a+jb en s+jw
#                    -> e^(s*t)*[2a*cos(wt) - 2b*sen(wt)]
# ============================================================

def evaluar_terminos(terminos, t):
    v = 0.0
    for term in terminos:
        if term[0] == "exp":
            v += term[1] * math.exp(term[2] * t)
        elif term[0] == "osc":
            _, A, B, sg, w = term
            v += math.exp(sg * t) * (A * math.cos(w * t) + B * math.sin(w * t))
    return v

def _exp_txt(p):
    """e^(pt) sin el 1 sobrante: e^(-t) en vez de e^(-1t)."""
    if abs(p + 1) < 1e-12:
        return "e^(-t)"
    if abs(p - 1) < 1e-12:
        return "e^(t)"
    return "e^({}t)".format(fmt(p))

def texto_termino(term):
    if term[0] == "delta":
        return con_signo(term[1]) + "*d(t)"
    if term[0] == "exp":
        r, p = term[1], term[2]
        if abs(p) < TOL_CERO:
            return con_signo(r)
        if abs(abs(r) - 1) < 1e-12:
            return ("-" if r < 0 else "+") + _exp_txt(p)
        return con_signo(r) + "*" + _exp_txt(p)
    _, A, B, sg, w = term
    base = "[{}*cos({}t){}*sen({}t)]".format(fmt(A), fmt(w), con_signo(B), fmt(w))
    if abs(sg) < TOL_CERO:
        return "+" + base
    return "+e^({}t)*".format(fmt(sg)) + base

def evaluar_loop(fn, nombre="y(t)"):
    k = 1
    while True:
        reset_contador()
        op = pedir_int("Evaluar {}? 1=Si 0=No".format(nombre), [0, 1])
        if op == 0:
            break
        t = pedir_float("  t")
        reset_contador()
        try:
            v = fn(t)
        except (ValueError, OverflowError, ZeroDivisionError):
            out("No evaluable en ese t")
            continue
        paso(k, "{} en t={}".format(nombre, fmt(t)), "suma de terminos", v, "")
        k += 1

def inversa(desde_otro_modulo=False):
    if not desde_otro_modulo:
        separador("M3: INVERSA (FRACC. PARC.)")
        reset_contador()

    menu_texto(
        "Obtener Y(s)=N(s)/D(s):",
        "  1) Encadenar M2 (EDO)",
        "  2) Ingresar N(s) y D(s)")
    modo = pedir_int("Opcion", [1, 2])

    if modo == 1:
        datos = edo_a_Ys(desde_otro_modulo=True)
        pausa_suave()
        N = datos["N"]
        D = datos["D"]
    else:
        reset_contador()
        D = pedir_poli("D(s)", 1, 3)
        N = pedir_poli("N(s)", 0, 3)

    reset_contador()
    g_D = len(D) - 1
    if g_D < 1:
        out("D(s) debe ser de grado >= 1")
        return None
    if g_D > 3:
        out("[!] grado de D(s) = {} > 3".format(g_D))
        out("  M3 solo invierte hasta grado 3")
        return None
    if len(N) - 1 > g_D:
        out("[!] grado N(s) > grado D(s)")
        out("  Da derivadas del impulso:")
        out("  fuera del alcance de M3")
        return None

    paso_txt(1, "Y(s)", "N(s)/D(s)", "(" + p_str(N) + ")/(" + p_str(D) + ")")
    k = 2

    terminos = []
    if len(N) - 1 == g_D:
        q, N = p_div(N, D)
        terminos.append(("delta", q[-1]))
        paso_txt(k, "Division: parte constante", "N/D = q + resto/D",
                 fmt(q[-1]) + " -> " + fmt(q[-1]) + "*d(t)")
        k += 1

    polos = raices(D)
    out("[{}] Polos: D(s)=0".format(k))
    k += 1
    for i in range(len(polos)):
        out("  p{} = {}".format(i + 1, fmt_c(polos[i])))

    rep = hay_repetido(polos)
    if rep is not None:
        out("[!] Polo repetido en s={}".format(fmt_c(rep)))
        out("  M3 solo maneja polos simples.")
        out("  Rampa 1er orden / zeta=1: M4")
        out("  Otros: Tabla 2-1, pares 7,18,19")
        return {"repetido": True, "polos": polos, "N": N, "D": D}

    pausa_suave()
    dD = p_der(D)
    residuos = []
    for p in polos:
        if not es_real(p) and p.imag < 0:
            residuos.append(None)
            continue
        r = p_eval(N, p) / p_eval(dD, p)
        residuos.append(r)
        paso_txt(k, "Residuo en p={}".format(fmt_c(p)),
                 "r=N(p)/D'(p)", fmt_c(r))
        k += 1

    for i in range(len(polos)):
        p = polos[i]
        r = residuos[i]
        if r is None:
            continue
        if es_real(p):
            terminos.append(("exp", r.real, p.real))
        else:
            terminos.append(("osc", 2 * r.real, -2 * r.imag, p.real, p.imag))

    pausa_suave()
    out_final("y(t) =  (t >= 0)")
    for term in terminos:
        out_final("  " + texto_termino(term))
    if any(tr[0] == "osc" for tr in terminos):
        out_final("(par complejo: s+-jw)")

    evaluar_loop(lambda t: evaluar_terminos(terminos, t))

    return {"terminos": terminos, "polos": polos,
            "residuos": residuos, "N": N, "D": D}


# ============================================================
# MÓDULO 4: RESPUESTA DE 1er Y 2do ORDEN + VALOR FINAL/INICIAL
# (Ogata, cap. 4). Cubre los polos dobles que
# M3 no maneja (rampa en 1er orden, zeta=1) con Tabla 2-1.
# ============================================================

def primer_orden():
    separador("M4a: 1er ORDEN K/(tau*s+1)")
    reset_contador()
    K = pedir_float("  Ganancia K", 1.0)
    tau = pedir_float("  Constante de tiempo tau")
    while tau <= 0:
        out("tau debe ser > 0")
        tau = pedir_float("  Constante de tiempo tau")

    menu_texto(
        "Entrada:",
        "  1) Impulso A*d(t)",
        "  2) Escalon A*1(t)",
        "  3) Rampa A*t")
    ent = pedir_int("Entrada", [1, 2, 3])
    A = pedir_float("  Amplitud A", 1.0)
    AK = A * K

    reset_contador()
    if ent == 1:
        c0 = AK / tau
        paso(1, "Coeficiente", "A*K/tau", c0, "")
        out_final("c(t) = {}*e^({}t)".format(fmt(c0), fmt(-1 / tau)))
        out_final("(Tabla 2-1 par 6, a=1/tau)")
        fn = lambda t: c0 * math.exp(-t / tau)
    elif ent == 2:
        paso(1, "Valor final", "A*K", AK, "")
        out("[2] c(t)=A*K*(1-e^(-t/tau))")
        for k in range(1, 6):
            pct = 1 - math.exp(-k)
            out("  t={}tau={}: c={} ({:.1f}%)".format(
                k, fmt(k * tau), fmt(AK * pct), pct * 100))
        out_final("c(t) = {}*(1-e^({}t))".format(fmt(AK), fmt(-1 / tau)))
        out_final("(Tabla 2-1 par 14, a=1/tau)")
        fn = lambda t: AK * (1 - math.exp(-t / tau))
    else:
        out("[1] C(s)=A*K/(s^2*(tau*s+1))")
        out("  polo doble en s=0 -> par 19")
        out_final("c(t) = {}*(t-{}+{}*e^({}t))".format(
            fmt(AK), fmt(tau), fmt(tau), fmt(-1 / tau)))
        if abs(K - 1) < 1e-12:
            paso(2, "Error en regimen (K=1)", "e_ss=A*tau", A * tau, "")
        fn = lambda t: AK * (t - tau + tau * math.exp(-t / tau))

    evaluar_loop(fn, "c(t)")
    return {"K": K, "tau": tau, "entrada": ent, "A": A}


def segundo_orden():
    separador("M4b: 2do ORDEN")
    reset_contador()
    out("K*wn^2/(s^2+2*z*wn*s+wn^2)")
    K = pedir_float("  Ganancia K", 1.0)
    wn = pedir_float("  wn [rad/s]")
    while wn <= 0:
        out("wn debe ser > 0")
        wn = pedir_float("  wn [rad/s]")
    z = pedir_float("  zeta (amortiguamiento)")
    while z < 0:
        out("zeta debe ser >= 0")
        z = pedir_float("  zeta (amortiguamiento)")

    menu_texto(
        "Entrada:",
        "  1) Impulso A*d(t)",
        "  2) Escalon A*1(t)")
    ent = pedir_int("Entrada", [1, 2])
    A = pedir_float("  Amplitud A", 1.0)
    AK = A * K

    reset_contador()
    sg = z * wn
    paso(1, "sigma", "z*wn", sg, "1/s")

    if z < TOL_CERO:
        out("[2] zeta=0: NO AMORTIGUADO")
        out("  oscila indefinidamente")
        if ent == 1:
            c0 = AK * wn
            out_final("c(t) = {}*sen({}t)".format(fmt(c0), fmt(wn)))
            out_final("(Tabla 2-1 par 10, x wn)")
            fn = lambda t: c0 * math.sin(wn * t)
        else:
            out_final("c(t) = {}*(1-cos({}t))".format(fmt(AK), fmt(wn)))
            out_final("(Tabla 2-1 par 25)")
            fn = lambda t: AK * (1 - math.cos(wn * t))

    elif z < 1 - 1e-9:
        out("[2] 0<zeta<1: SUBAMORTIGUADO")
        wd = wn * math.sqrt(1 - z * z)
        paso(3, "Frec. amortiguada", "wd=wn*sqrt(1-z^2)", wd, "rad/s")
        if ent == 1:
            c0 = AK * wn / math.sqrt(1 - z * z)
            out_final("c(t) = {}*e^({}t)*sen({}t)".format(
                fmt(c0), fmt(-sg), fmt(wd)))
            out_final("(Tabla 2-1 par 22)")
            fn = lambda t: c0 * math.exp(-sg * t) * math.sin(wd * t)
        else:
            phi = math.atan2(math.sqrt(1 - z * z), z)
            paso(4, "Fase", "phi=atan(sqrt(1-z^2)/z)", phi, "rad")
            c1 = 1 / math.sqrt(1 - z * z)
            out_final("c(t) = {}*[1-{}*e^({}t)".format(fmt(AK), fmt(c1), fmt(-sg)))
            out_final("       *sen({}t+{})]".format(fmt(wd), fmt(phi)))
            out_final("(Tabla 2-1 par 24)")
            fn = lambda t: AK * (1 - c1 * math.exp(-sg * t) * math.sin(wd * t + phi))

    elif z <= 1 + 1e-9:
        out("[2] zeta=1: CRITICAMENTE AMORT.")
        out("  polo doble en s=-wn")
        if ent == 1:
            c0 = AK * wn * wn
            out_final("c(t) = {}*t*e^({}t)".format(fmt(c0), fmt(-wn)))
            out_final("(Tabla 2-1 par 7, x wn^2)")
            fn = lambda t: c0 * t * math.exp(-wn * t)
        else:
            out_final("c(t) = {}*[1-e^({}t)*(1+{}t)]".format(
                fmt(AK), fmt(-wn), fmt(wn)))
            out_final("(Tabla 2-1 par 18, x wn^2)")
            fn = lambda t: AK * (1 - math.exp(-wn * t) * (1 + wn * t))

    else:
        out("[2] zeta>1: SOBREAMORTIGUADO")
        rz = math.sqrt(z * z - 1)
        p1 = -sg + wn * rz
        p2 = -sg - wn * rz
        paso(3, "Polo lento", "p1=-z*wn+wn*sqrt(z^2-1)", p1, "1/s")
        paso(4, "Polo rapido", "p2=-z*wn-wn*sqrt(z^2-1)", p2, "1/s")
        if z > 2:
            out("zeta>2: similar a 1er orden")
            paso(5, "tau equivalente", "tau=-1/p1", -1 / p1, "s")
        if ent == 1:
            c0 = AK * wn * wn / (p1 - p2)
            out_final("c(t) = {}*[e^({}t)-e^({}t)]".format(
                fmt(c0), fmt(p1), fmt(p2)))
            out_final("(Tabla 2-1 par 15, x wn^2)")
            fn = lambda t: c0 * (math.exp(p1 * t) - math.exp(p2 * t))
        else:
            c1 = p2 / (p1 - p2)
            c2 = -p1 / (p1 - p2)
            out_final("c(t) = {}*[1{}*e^({}t)".format(fmt(AK), con_signo(c1), fmt(p1)))
            out_final("       {}*e^({}t)]".format(con_signo(c2), fmt(p2)))
            out_final("(Tabla 2-1 par 17, x wn^2)")
            fn = lambda t: AK * (1 + c1 * math.exp(p1 * t) + c2 * math.exp(p2 * t))

    if ent == 2:
        out_final("Valor final = {}".format(fmt(AK)))

    evaluar_loop(fn, "c(t)")
    return {"K": K, "wn": wn, "z": z, "entrada": ent, "A": A}


def valor_final_inicial():
    separador("M4c: VALOR FINAL / INICIAL")
    reset_contador()

    menu_texto(
        "Obtener Y(s)=N(s)/D(s):",
        "  1) Encadenar M2 (EDO)",
        "  2) Ingresar N(s) y D(s)")
    modo = pedir_int("Opcion", [1, 2])

    if modo == 1:
        datos = edo_a_Ys(desde_otro_modulo=True)
        pausa_suave()
        N = datos["N"]
        D = datos["D"]
    else:
        reset_contador()
        D = pedir_poli("D(s)", 1, 4)
        N = pedir_poli("N(s)", 0, 4)

    reset_contador()
    paso_txt(1, "Y(s)", "N(s)/D(s)", "(" + p_str(N) + ")/(" + p_str(D) + ")")

    # --- valor inicial: lim s->inf s*Y(s)
    salto = (len(D) - 1) - (len(N) - 1)
    out("[2] Valor inicial:")
    out("  y(0+)=lim(s->inf) s*Y(s)")
    if salto >= 2:
        y0 = 0.0
        out("  grado D - grado N >= 2 -> 0")
    elif salto == 1:
        y0 = N[0] / D[0]
        out("  = N lider / D lider")
    else:
        y0 = None
        out("  No aplica: Y(s) impropia")
        out("  (impulso en t=0)")
    if y0 is not None:
        out("  = " + fmt(y0))

    # --- valor final: lim s->0 s*Y(s), solo si sY(s) es estable
    pausa_suave()
    out("[3] Valor final:")
    out("  y(inf)=lim(s->0) s*Y(s)")
    if abs(D[-1]) > TOL_CERO:
        D1 = D
        yf = 0.0
        out("  D(0)<>0 -> s*Y(s) en 0 = 0")
    else:
        D1 = p_trim(D[:-1])
        if len(D1) > 1 and abs(D1[-1]) < TOL_CERO:
            out("  Polo doble en s=0 (ej. rampa)")
            out_final("  y(t) no converge: diverge")
            return {"y0": y0, "yf": None}
        yf = p_eval(N, 0.0) / D1[-1]
        out("  = N(0)/[D(s)/s](0)")

    estable = None
    if len(D1) - 1 >= 1:
        polos = raices(D1)
        if polos is None:
            out("  (grado > 3: no reviso")
            out("   estabilidad, verificar a mano)")
        else:
            estable = all(p.real < -1e-9 for p in polos)
            if not estable:
                malo = [p for p in polos if p.real >= -1e-9][0]
                out("[!] Polo con Re>=0: s={}".format(fmt_c(malo)))
                out("  Teorema NO aplica (inestable")
                out("  u oscilacion sostenida)")
                return {"y0": y0, "yf": None, "estable": False}
    else:
        estable = True

    if estable:
        out("  s*Y(s): polos con Re<0 -> OK")
    out_final("y(inf) = " + fmt(yf))
    return {"y0": y0, "yf": yf, "estable": estable}


def menu_respuesta():
    while True:
        menu_texto(
            "=== M4: RESPUESTA ===",
            "  1) 1er orden K/(tau*s+1)",
            "  2) 2do orden (wn, zeta)",
            "  3) Valor final / inicial",
            "  0) Volver")
        op = pedir_int("Opcion", [0, 1, 2, 3])
        if op == 1:
            primer_orden()
        elif op == 2:
            segundo_orden()
        elif op == 3:
            valor_final_inicial()
        elif op == 0:
            break
        pausa_manual()


# ============================================================
# MENÚ MAESTRO
# ============================================================

def menu_maestro():
    while True:
        menu_texto(
            "=== LAPLACE - PROGRAMA GENERAL ===",
            "  1) M1: Tabla de pares",
            "  2) M2: EDO -> Y(s)",
            "  3) M3: Inversa (fracc. parc.)",
            "  4) M4: Respuesta / valor final",
            "  0) Salir")

        op = pedir_int("Opcion", [0, 1, 2, 3, 4])

        if op == 1:
            tabla_pares()
        elif op == 2:
            edo_a_Ys()
        elif op == 3:
            inversa()
        elif op == 4:
            menu_respuesta()
            continue
        elif op == 0:
            out("Saliendo...")
            break

        pausa_manual()


menu_maestro()
