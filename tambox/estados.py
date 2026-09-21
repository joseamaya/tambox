VACIO = 'vacio'
PARCIAL = 'parcial'
COMPLETO = 'completo'


def clasificar(cantidad_actual, total_quantity):
    """Clasifica el avance de una cantidad frente a su total.

    Es la regla unica detras de la maquina de estados de pedidos, cotizaciones y
    requerimientos: sin avance, avance parcial o avance completo.
    """
    if cantidad_actual == 0:
        return VACIO
    if cantidad_actual < total_quantity:
        return PARCIAL
    return COMPLETO
