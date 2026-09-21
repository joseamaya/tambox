EMPTY = 'vacio'
PARTIAL = 'parcial'
COMPLETE = 'completo'


def classify(current_quantity, total_quantity):
    """Clasifica el avance de una cantidad frente a su total.

    Es la regla unica detras de la maquina de estados de pedidos, cotizaciones y
    requerimientos: sin avance, avance parcial o avance completo.
    """
    if current_quantity == 0:
        return EMPTY
    if current_quantity < total_quantity:
        return PARTIAL
    return COMPLETE
