import re

token_patron = {
    "KEYWORD":    r'\b(si|sino|entonces|finsi|fin|inicio|escribir|retornar|funcion|int|float|void)\b',
    "STRING":     r'"[^"\n]*"',
    "NUMBER":     r'\b\d+(\.\d+)?\b',
    "IDENTIFIER": r'\b[a-zA-Z_][a-zA-Z0-9_]*\b',
    "OPERATOR":   r'==|!=|<=|>=|[+\-*/=<>]',
    "DELIMITER":  r'[(),;{}]',
    "WHITESPACE": r'\s+',
}

def identificar_tokens(texto):
    patron_general = "|".join(
        f"(?P<{token}>{patron})" for token, patron in token_patron.items()
    )
    patron_regex = re.compile(patron_general)
    tokens_encontrados = []

    for match in patron_regex.finditer(texto):
        for token, valor in match.groupdict().items():
            if valor is not None and token != "WHITESPACE":
                tokens_encontrados.append((token, valor))

    return tokens_encontrados