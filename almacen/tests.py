from almacen.models import Almacen, TipoMovimiento, Pedido, DetallePedido, \
    Movimiento
from django.test import TestCase
from model_mommy import mommy
from datetime import date, datetime
from compras.models import OrdenCompra


class AlmacenTest(TestCase):

    def setUp(self):
        self.a1 = mommy.make(Almacen)
        self.a2 = mommy.make(Almacen)
        self.a3 = mommy.make(Almacen)

    def test_creacion_profesion_mommy(self):
        self.assertTrue(isinstance(self.a1, Almacen))
        self.assertEqual(self.a1.__str__(), self.a1.descripcion)

    def test_siguiente_almacen(self):
        self.assertEqual(self.a3.pk, self.a2.siguiente())

    def test_anterior_almacen(self):
        self.assertEqual(self.a2.pk, self.a3.anterior())

    def test_primer_almacen(self):
        self.assertEqual(self.a1.pk, self.a3.siguiente())

    def test_ultimo_almacen(self):
        self.assertEqual(self.a3.pk, self.a1.anterior())


class TipoMovimientoTest(TestCase):

    def setUp(self):
        self.tm1 = mommy.make(TipoMovimiento, codigo='')
        self.tm2 = mommy.make(TipoMovimiento, codigo='')
        self.tm3 = mommy.make(TipoMovimiento, codigo='')

    def test_creacion_tipo_movimiento_mommy(self):
        self.assertTrue(isinstance(self.tm1, TipoMovimiento))
        self.assertEqual(self.tm1.__str__(), self.tm1.descripcion)

    def test_siguiente_tipo_movimiento(self):
        self.assertEqual(self.tm3.pk, self.tm2.siguiente())

    def test_anterior_tipo_movimiento(self):
        self.assertEqual(self.tm2.pk, self.tm3.anterior())

    def test_primer_tipo_movimiento(self):
        self.assertEqual(self.tm1.pk, self.tm3.siguiente())

    def test_ultimo_tipo_movimiento(self):
        self.assertEqual(self.tm3.pk, self.tm1.anterior())

    def test_tipo_movimiento_ingreso(self):
        tm1 = mommy.make(TipoMovimiento, codigo='', incrementa=True)
        self.assertEqual("I", tm1.codigo[0])


class PedidoTest(TestCase):

    def setUp(self):
        self.fecha_actual = date.today()
        self.fecha_proxima = date(2017, 1, 1)
        self.pe1 = mommy.make(Pedido, codigo='', fecha=self.fecha_actual)
        self.pe2 = mommy.make(Pedido, codigo='', fecha=self.fecha_actual)
        self.pe3 = mommy.make(Pedido, codigo='', fecha=self.fecha_actual)
        self.pe4 = mommy.make(Pedido, codigo='', fecha=self.fecha_proxima)

    def test_creacion_pedido_mommy(self):
        self.assertTrue(isinstance(self.pe1, Pedido))
        self.assertEqual(self.pe1.__str__(), self.pe1.codigo)
        self.assertEqual("PE" + str(self.pe1.fecha.year) + "000001", self.pe1.codigo)
        self.assertEqual("PE" + str(self.pe2.fecha.year) + "000002", self.pe2.codigo)
        self.assertEqual("PE" + str(self.pe4.fecha.year) + "000001", self.pe4.codigo)

    def test_actualizacion_pedido(self):
        pe5 = mommy.make(Pedido, codigo=self.pe1.pk, fecha=self.fecha_proxima)
        self.assertEqual(pe5.pk, self.pe1.pk)

    def test_siguiente_pedido(self):
        self.assertEqual(self.pe3.pk, self.pe2.siguiente())

    def test_anterior_pedido(self):
        self.assertEqual(self.pe2.pk, self.pe3.anterior())

    def test_primer_pedido(self):
        self.assertEqual(self.pe1.pk, self.pe4.siguiente())

    def test_ultimo_pedido(self):
        self.assertEqual(self.pe4.pk, self.pe1.anterior())


class DetallePedidoTest(TestCase):

    def setUp(self):
        self.fecha_actual = date.today()
        self.pe1 = mommy.make(Pedido, codigo='', fecha=self.fecha_actual)
        self.dpe1 = mommy.make(DetallePedido, pedido=self.pe1)

    def test_creacion_detalle_pedido(self):
        self.assertTrue(isinstance(self.dpe1, DetallePedido))
        self.assertEqual(self.dpe1.__str__(), self.dpe1.pedido.codigo + ' ' + str(self.dpe1.nro_detalle))

    def test_cantidad_por_atender(self):
        resultado = self.dpe1.cantidad - self.dpe1.cantidad_atendida
        self.assertEqual(resultado, self.dpe1.cantidad_por_atender())


class MovimientoTest(TestCase):

    def test_creacion_movimiento(self):
        mov1 = mommy.make(Movimiento, id_movimiento='', fecha_operacion=datetime.now())
        self.assertTrue(isinstance(mov1, Movimiento))
        self.assertEqual(mov1.__str__(), mov1.id_movimiento)

    def test_creacion_movimiento_ingreso(self):
        tipo_movimiento = mommy.make(TipoMovimiento, codigo='', incrementa=True)
        mov1 = mommy.make(Movimiento, id_movimiento='', fecha_operacion=datetime.now(), tipo_movimiento=tipo_movimiento)
        mov2 = mommy.make(Movimiento, id_movimiento='', fecha_operacion=datetime.now(), tipo_movimiento=tipo_movimiento)
        self.assertEqual("I" + str(mov1.fecha_operacion.year) + str(1).zfill(7), mov1.id_movimiento)
        self.assertEqual("I" + str(mov2.fecha_operacion.year) + str(2).zfill(7), mov2.id_movimiento)

    def test_creacion_movimiento_salida(self):
        tipo_movimiento = mommy.make(TipoMovimiento, codigo='', incrementa=False)
        mov1 = mommy.make(Movimiento, id_movimiento='', fecha_operacion=datetime.now(), tipo_movimiento=tipo_movimiento)
        mov2 = mommy.make(Movimiento, id_movimiento='', fecha_operacion=datetime.now(), tipo_movimiento=tipo_movimiento)
        self.assertEqual("S" + str(mov1.fecha_operacion.year) + str(1).zfill(7), mov1.id_movimiento)
        self.assertEqual("S" + str(mov2.fecha_operacion.year) + str(2).zfill(7), mov2.id_movimiento)

    def test_siguiente_movimiento(self):
        tipo_movimiento = mommy.make(TipoMovimiento, codigo='', incrementa=True)
        mov1 = mommy.make(Movimiento, id_movimiento='', fecha_operacion=datetime.now(), tipo_movimiento=tipo_movimiento)
        mov2 = mommy.make(Movimiento, id_movimiento='', fecha_operacion=datetime.now(), tipo_movimiento=tipo_movimiento)
        mov3 = mommy.make(Movimiento, id_movimiento='', fecha_operacion=datetime.now(), tipo_movimiento=tipo_movimiento)
        self.assertEqual(mov2.pk, mov1.siguiente())
        self.assertEqual(mov3.pk, mov2.siguiente())

    def test_anterior_movimiento(self):
        tipo_movimiento = mommy.make(TipoMovimiento, codigo='', incrementa=False)
        mov1 = mommy.make(Movimiento, id_movimiento='', fecha_operacion=datetime.now(), tipo_movimiento=tipo_movimiento)
        mov2 = mommy.make(Movimiento, id_movimiento='', fecha_operacion=datetime.now(), tipo_movimiento=tipo_movimiento)
        mov3 = mommy.make(Movimiento, id_movimiento='', fecha_operacion=datetime.now(), tipo_movimiento=tipo_movimiento)
        self.assertEqual(mov1.pk, mov2.anterior())
        self.assertEqual(mov2.pk, mov3.anterior())

    def test_primer_movimiento(self):
        tipo_movimiento = mommy.make(TipoMovimiento, codigo='', incrementa=True)
        mov1 = mommy.make(Movimiento, id_movimiento='', fecha_operacion=datetime.now(), tipo_movimiento=tipo_movimiento)
        mov2 = mommy.make(Movimiento, id_movimiento='', fecha_operacion=datetime.now(), tipo_movimiento=tipo_movimiento)
        self.assertEqual(mov1.pk, mov2.siguiente())

    def test_ultimo_movimiento(self):
        tipo_movimiento = mommy.make(TipoMovimiento, codigo='', incrementa=False)
        mov1 = mommy.make(Movimiento, id_movimiento='', fecha_operacion=datetime.now(), tipo_movimiento=tipo_movimiento)
        mov2 = mommy.make(Movimiento, id_movimiento='', fecha_operacion=datetime.now(), tipo_movimiento=tipo_movimiento)
        self.assertEqual(mov2.pk, mov1.anterior())

    def test_modificar_referencia(self):
        tipo_movimiento = mommy.make(TipoMovimiento, codigo='', incrementa=True, pide_referencia=True)
        referencia = mommy.make(OrdenCompra)
        mov1 = mommy.make(Movimiento, id_movimiento='', fecha_operacion=datetime.now(), tipo_movimiento=tipo_movimiento,
                          referencia=referencia)
        mov1.modificar_estado_referencia()
        self.assertEqual(mov1.referencia.estado, OrdenCompra.STATUS.PEND)
