"""CRUD de proveedores y reportes de compras."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from purchases.models import PurchaseOrder, Quotation, ServiceOrder, Supplier


class PurchasesViewsTest(TestCase):

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('a', 'a@example.com', 'clave'))

    def test_supplier_crud(self):
        response = self.client.post(reverse('purchases:supplier_create'),
                                    {'tax_id': '12345678901', 'business_name': 'PROVEEDOR UNO',
                                     'address': 'DIRECCION UNO', 'sunat_status': 'ACTIVO',
                                     'sunat_condition': 'HABIDO', 'ciiu': 'CUALQUIERA',
                                     'registration_date': '01/01/2024'})
        self.assertEqual(302, response.status_code)
        supplier = Supplier.objects.get(tax_id='12345678901')

        self.assertEqual(200, self.client.get(
            reverse('purchases:supplier_detail', args=[supplier.pk])).status_code)
        response = self.client.post(reverse('purchases:supplier_update', args=[supplier.pk]),
                                    {'tax_id': '12345678901',
                                     'business_name': 'PROVEEDOR EDITADO',
                                     'address': 'DIRECCION UNO', 'sunat_status': 'ACTIVO',
                                     'sunat_condition': 'HABIDO', 'ciiu': 'CUALQUIERA',
                                     'registration_date': '01/01/2024'})
        self.assertEqual(302, response.status_code)
        supplier.refresh_from_db()
        self.assertEqual('PROVEEDOR EDITADO', supplier.business_name)

        response = self.client.post(reverse('purchases:supplier_delete'),
                                    {'tax_id': supplier.tax_id},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        supplier.refresh_from_db()
        self.assertFalse(supplier.is_active)

    def test_purchase_order_reports(self):
        order = baker.make(PurchaseOrder, supplier=baker.make(Supplier))

        pdf = self.client.get(reverse('purchases:purchase_order_pdf', args=[order.pk]))
        xls = self.client.get(reverse('purchases:purchase_order_xls', args=[order.pk]))

        self.assertEqual(200, pdf.status_code)
        self.assertTrue(pdf.content.startswith(b'%PDF'))
        self.assertEqual(200, xls.status_code)

    def test_quotation_and_service_order_reports(self):
        quotation = baker.make(Quotation, supplier=baker.make(Supplier))
        service_order = baker.make(ServiceOrder, supplier=baker.make(Supplier))

        quotation_pdf = self.client.get(
            reverse('purchases:quotation_pdf', args=[quotation.code]))
        service_pdf = self.client.get(
            reverse('purchases:service_order_pdf', args=[service_order.code]))

        self.assertTrue(quotation_pdf.content.startswith(b'%PDF'))
        self.assertTrue(service_pdf.content.startswith(b'%PDF'))

    def test_lists_and_dashboard(self):
        supplier = baker.make(Supplier)
        baker.make(PurchaseOrder, supplier=supplier)
        baker.make(Quotation, supplier=supplier)
        baker.make(ServiceOrder, supplier=supplier)

        for name in ('purchases:dashboard', 'purchases:supplier_list',
                     'purchases:quotation_list', 'purchases:purchase_order_list',
                     'purchases:service_order_list', 'purchases:service_conformity_list',
                     'purchases:supplier_excel_report'):
            with self.subTest(name=name):
                self.assertEqual(200, self.client.get(reverse(name)).status_code)
