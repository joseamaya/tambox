"""Auditoria del vocabulario: falla si queda un identificador en espanol.

Se revisan los identificadores de Python (`.py`) y los que aparecen dentro de las
etiquetas de plantilla (`.html`), separando cada nombre en segmentos por guion
bajo y por camelCase, y buscando cada segmento en una lista de palabras
espanolas. Asi `quantity` no cuenta como `cant`, y `get_month_display` no cuenta
como `mes`.

Lo que no se revisa, a proposito:

- los paquetes de app (`warehouse`, `purchases`, ...), que son palabras inglesas;
- los codenames de permisos personalizados (`ver_tabla_*`, `cargar_*`), que son
  la voz del sistema y quedan en espanol;
- los acronimos (`dni`, `ciiu`) y las palabras que son iguales en ingles y en
  espanol (`total`, `subtotal`, `superior`);
- las cadenas que lee el usuario: la auditoria mira identificadores, no prosa.

Uso:
    .venv/bin/python scripts/audit_identifiers.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PACKAGES = {'administration', 'warehouse', 'purchases', 'accounting', 'products',
            'requirements', 'security', 'tambox', 'scripts'}

# Palabras que no se renombran: acronimos y vocablos comunes a los dos idiomas.
ALLOWED_WORDS = {
    'dni', 'ciiu', 'sunat', 'pec', 'ruc', 'isbn', 'stock', 'kardex', 'login',
    'total', 'subtotal', 'superior', 'conf', 'index', 'normal', 'legal',
    'admin', 'message', 'messages', 'namespace', 'constants', 'valid',
}
# Nombres completos que la auditoria ignora (ficheros de terceros, etc.).
# `es_locador` se omite a proposito: es codigo roto (`Supplier` no tiene ese
# campo) y entra en el bloque de bugs, no en el de vocabulario.
ALLOWED_NAMES = {'numeroaletras', 'es_locador'}

SPANISH_WORDS = {
    'cantidad', 'precio', 'valor', 'fecha', 'nombre', 'apellido', 'codigo',
    'descripcion', 'observacion', 'estado', 'usuario', 'empresa', 'oficina',
    'puesto', 'trabajador', 'productor', 'producto', 'pedido', 'movimiento',
    'almacen', 'cotizacion', 'proveedor', 'orden', 'conformidad',
    'requerimiento', 'detalle', 'cuenta', 'documento', 'tipo', 'impuesto',
    'existencia', 'unidad', 'grupo', 'nivel', 'aprobacion', 'cargo', 'lugar',
    'calle', 'distrito', 'provincia', 'departamento', 'marca', 'modelo',
    'imagen', 'motivo', 'mes', 'annio', 'informe', 'proceso', 'numero',
    'solicitante', 'referencia', 'firma', 'foto', 'tabla', 'salida', 'ingreso',
    'anterior', 'siguiente', 'obtener', 'establecer', 'verificar', 'generar',
    'eliminar', 'actualizar', 'crear', 'guardar', 'enviar', 'recibir',
    'calcular', 'validar', 'listar', 'buscar', 'cargar', 'imprimir', 'reporte',
    'saldo', 'fila', 'ruta', 'parametro', 'faltante', 'instancia', 'pagina',
    'datos', 'clave', 'lote', 'hoja', 'jefe', 'resumen', 'texto', 'pie',
    'anio', 'tempo', 'razon', 'social', 'pago', 'medida', 'servicio',
    'gerencia', 'jefatura', 'asistente', 'profesion', 'direccion', 'telefono',
    'correo', 'condicion', 'vacio', 'parcial', 'completo', 'conforme',
    'atendida', 'cotizada', 'comprada', 'ingresada', 'valorizada',
    'consolidada', 'apellidos', 'nombres', 'archivo', 'factura', 'boleta',
    'guia', 'anular', 'representante', 'solicitud', 'pintando', 'desempata',
    # Plurales y palabras que la primera pasada no cubria.
    'respuesta', 'registro', 'permiso', 'permisos', 'formato', 'formatos',
    'parametro', 'parametros', 'seleccion', 'consolidado', 'consolidados',
    'protegidas', 'paginas', 'tablero', 'maestro', 'periodo',
    'receptor', 'receptores', 'productos', 'productores', 'requerimientos',
    'movimientos', 'pedidos', 'cuentas', 'grupos', 'unidades', 'existencias',
    'impuestos', 'cotizaciones', 'conformidades', 'ordenes', 'documentos',
    'almacenes', 'proveedores', 'trabajadores', 'oficinas', 'profesiones',
    'puestos', 'tipos', 'servicios', 'administracion', 'seguridad',
    'contabilidad', 'compras', 'izquierda', 'lista', 'titulo', 'encabezado',
    'columna', 'nota', 'elemento', 'objeto', 'arreglo', 'diccionario',
    'cadena', 'indice', 'moneda', 'porcentaje', 'nuevo', 'mayor', 'menor',
    'igual', 'suma', 'resta', 'promedio', 'unitario', 'valorado',
    'notificacion', 'notificaciones', 'facturado', 'pagado',
}


def split_segments(name):
    segments = []
    for piece in name.split('_'):
        segments.extend(re.findall(r'[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z0-9]+|[A-Z]+', piece)
                        or [piece])
    return [s.lower() for s in segments if s]


def python_identifiers(source):
    source = re.sub(r'"""[\s\S]*?"""', '', source)
    source = re.sub(r"'''[\s\S]*?'''", '', source)
    source = re.sub(r'#[^\n]*', '', source)
    source = re.sub(r"'[^'\n]*'", "''", source)
    source = re.sub(r'"[^"\n]*"', '""', source)
    return re.findall(r'[A-Za-z_][A-Za-z0-9_]*', source)


def template_identifiers(source):
    identifiers = []
    for block in re.findall(r'\{\{[\s\S]*?\}\}|\{%[\s\S]*?%\}', source):
        # Los codenames de permisos son la voz del sistema: no se revisan.
        block = re.sub(r'perms\.[A-Za-z_]+\.[A-Za-z_]+', '', block)
        identifiers.extend(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', block))
    return identifiers


def template_files():
    for path in sorted((ROOT / 'templates').rglob('*.html')):
        yield path


def source_files():
    for pattern in ('*/*.py', '*/*/*.py', '*/*/*/*.py', 'templates/**/*.html'):
        for path in sorted(ROOT.glob(pattern)):
            parts = path.relative_to(ROOT).parts
            if 'migrations' in parts or '.venv' in parts:
                continue
            yield path


def findings():
    found = {}
    for path in template_files():
        for segment in split_segments(path.stem):
            if segment in ALLOWED_WORDS:
                continue
            if segment in SPANISH_WORDS:
                key = str(path.relative_to(ROOT))
                found.setdefault(key, set()).add(path.stem)
                break
    for path in source_files():
        if path.suffix == '.py':
            # El nombre del modulo tambien es un identificador.
            for segment in split_segments(path.stem):
                if segment in PACKAGES or segment in ALLOWED_WORDS:
                    continue
                if segment in SPANISH_WORDS:
                    key = str(path.relative_to(ROOT))
                    found.setdefault(key, set()).add(path.stem)
                    break
        source = path.read_text(encoding='utf8')
        if path.suffix == '.py':
            identifiers = python_identifiers(source)
        else:
            identifiers = template_identifiers(source)
        for name in identifiers:
            if name in PACKAGES or name.startswith('__') or name.lower() in ALLOWED_NAMES:
                continue
            for segment in split_segments(name):
                if segment in PACKAGES or segment in ALLOWED_WORDS:
                    continue
                if segment in SPANISH_WORDS:
                    key = str(path.relative_to(ROOT))
                    found.setdefault(key, set()).add(name)
                    break
    return found


def main():
    found = findings()
    if found:
        for path in sorted(found):
            print('%s: %s' % (path, ', '.join(sorted(found[path]))))
        print('Quedan identificadores en espanol.')
        return 1
    print('Sin identificadores en espanol.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
