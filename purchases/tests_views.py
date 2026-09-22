"""CRUD de proveedores, reportes y los flujos de creacion con formset."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from administration.models import ApprovalLevel, Office, Position, Worker
from purchases.models import PurchaseOrder, Quotation, ServiceOrder, Supplier
from requirements.models import Requirement


def create_requirement(**kwargs):
    ApprovalLevel.objects.get_or_create(description='USUARIO')
    office = baker.make(Office)
    worker = baker.make(Worker)
    baker.make(Position, office=office, worker=worker, end_date=None)
    return baker.make(Requirement, code='', requester=worker, office=office, **kwargs)


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

    def test_quotation_create(self):
        supplier = baker.make(Supplier, tax_id='12345678901')
        requirement = create_requirement()
        requirement_detail = baker.make('requirements.RequirementDetail',
                                        requirement=requirement,
                                        product=baker.make('products.Product'),
                                        quantity=10, quoted_quantity=0)
        data = {'tax_id': '12345678901', 'business_name': 'PROVEEDOR UNO',
                'address': 'DIRECCION UNO', 'reference': requirement.pk,
                'order': '', 'code': '', 'date': '01/01/2024', 'notes': '',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-requirement': requirement_detail.pk, 'form-0-code': 'P000000001',
                'form-0-name': 'PRODUCTO', 'form-0-unit': 'UND01',
                'form-0-quantity': '5'}

        response = self.client.post(reverse('purchases:quotation_create'), data)

        self.assertEqual(302, response.status_code)
        quotation = Quotation.objects.get(requirement=requirement, supplier=supplier)
        self.assertEqual(1, quotation.details.count())
        requirement_detail.refresh_from_db()
        self.assertEqual(5, requirement_detail.quoted_quantity)

    def test_quotation_detail_rows_render_real_inputs(self):
        requirement = create_requirement()
        requirement_detail = baker.make('requirements.RequirementDetail',
                                        requirement=requirement,
                                        product=baker.make('products.Product'),
                                        quantity=10, served_quantity=0)

        response = self.client.get(reverse('purchases:quotation_detail_rows'),
                                   {'requirement': requirement.code})

        self.assertEqual(200, response.status_code)
        self.assertNotContains(response, '<html')
        self.assertContains(response, 'name="form-TOTAL_FORMS"')
        self.assertContains(response, 'name="form-0-requirement"')
        self.assertContains(response, str(requirement_detail.pk))

    def test_quotation_transfer_flow(self):
        """Lo que hace el navegador: pide las filas del requerimiento por htmx y
        luego envia el formset. Antes las filas se armaban a mano sin inputs y el
        POST llegaba vacio."""
        supplier = baker.make(Supplier, tax_id='12345678901',
                              business_name='PROVEEDOR UNO',
                              address='DIRECCION UNO')
        requirement = create_requirement()
        requirement_detail = baker.make('requirements.RequirementDetail',
                                        requirement=requirement,
                                        product=baker.make('products.Product'),
                                        quantity=10, served_quantity=0)

        rows = self.client.get(reverse('purchases:quotation_detail_rows'),
                               {'requirement': requirement.code})
        self.assertContains(rows, 'value="%s"' % requirement_detail.pk)

        data = {'tax_id': supplier.tax_id, 'business_name': 'PROVEEDOR UNO',
                'address': 'DIRECCION UNO', 'reference': requirement.pk,
                'order': '', 'code': '', 'date': '01/01/2024', 'notes': '',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-requirement': requirement_detail.pk,
                'form-0-code': requirement_detail.product.code,
                'form-0-name': requirement_detail.product.description,
                'form-0-unit': 'UND01', 'form-0-quantity': '5'}

        response = self.client.post(reverse('purchases:quotation_create'), data)

        self.assertEqual(302, response.status_code)
        quotation = Quotation.objects.get(requirement=requirement)
        self.assertEqual(1, quotation.details.count())

    def test_quotation_update(self):
        supplier = baker.make(Supplier, tax_id='12345678901')
        requirement = create_requirement()
        requirement_detail = baker.make('requirements.RequirementDetail',
                                        requirement=requirement,
                                        product=baker.make('products.Product'),
                                        quantity=10, quoted_quantity=0)
        quotation = baker.make(Quotation, supplier=supplier, requirement=requirement)
        data = {'tax_id': '12345678901', 'business_name': 'PROVEEDOR UNO',
                'address': 'DIRECCION UNO', 'reference': requirement.pk,
                'order': '', 'code': quotation.code, 'date': '01/01/2024', 'notes': '',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-requirement': requirement_detail.pk, 'form-0-code': 'P000000001',
                'form-0-name': 'PRODUCTO', 'form-0-unit': 'UND01',
                'form-0-quantity': '5'}

        response = self.client.post(
            reverse('purchases:quotation_update', args=[quotation.pk]), data)

        self.assertEqual(302, response.status_code)
        quotation.refresh_from_db()
        self.assertEqual(1, quotation.details.count())

    def test_purchase_order_create(self):
        from tambox.config import clear_cache

        supplier = baker.make(Supplier, tax_id='12345678901')
        payment_method = baker.make('accounting.PaymentMethod')
        product = baker.make('products.Product')
        baker.make('accounting.Configuration', purchase_tax=baker.make('accounting.Tax'))
        clear_cache()
        self.addCleanup(clear_cache)
        data = {'tax_id': '12345678901', 'business_name': 'PROVEEDOR UNO',
                'address': 'DIRECCION UNO', 'reference': 'NO-EXISTE',
                'current_tax': '18', 'subtotal': '0', 'tax': '0', 'total': '0',
                'total_in_words': 'CERO', 'code': '', 'date': '01/01/2024',
                'notes': '', 'payment_method': payment_method.pk,
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-quotation': '999999', 'form-0-code': product.pk,
                'form-0-name': 'PRODUCTO', 'form-0-unit': 'UND01',
                'form-0-quantity': '5', 'form-0-price': '3', 'form-0-tax': '1',
                'form-0-amount': '15'}

        response = self.client.post(reverse('purchases:purchase_order_create'), data)

        self.assertEqual(302, response.status_code)
        order = PurchaseOrder.objects.get(supplier=supplier)
        self.assertEqual(1, order.details.count())

    def test_service_order_create(self):
        supplier = baker.make(Supplier, tax_id='12345678901')
        payment_method = baker.make('accounting.PaymentMethod')
        product = baker.make('products.Product')
        data = {'tax_id': '12345678901', 'business_name': 'PROVEEDOR UNO',
                'address': 'DIRECCION UNO', 'reference': '999999',
                'subtotal': '0', 'tax': '0', 'total': '0', 'total_in_words': 'CERO',
                'code': '', 'process': '', 'notes': '', 'report_name': '',
                'date': '01/01/2024', 'payment_method': payment_method.pk,
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-quotation': '999999', 'form-0-code': product.pk,
                'form-0-name': 'SERVICIO', 'form-0-unit': 'UND01',
                'form-0-quantity': '5', 'form-0-price': '3', 'form-0-amount': '15'}

        response = self.client.post(reverse('purchases:service_order_create'), data)

        self.assertEqual(302, response.status_code)
        order = ServiceOrder.objects.get(supplier=supplier)
        self.assertEqual(1, order.details.count())

    def test_purchase_order_update(self):
        from tambox.config import clear_cache

        supplier = baker.make(Supplier, tax_id='12345678901')
        payment_method = baker.make('accounting.PaymentMethod')
        product = baker.make('products.Product')
        baker.make('accounting.Configuration', purchase_tax=baker.make('accounting.Tax'))
        clear_cache()
        self.addCleanup(clear_cache)
        order = baker.make(PurchaseOrder, supplier=supplier, quotation=None)
        data = {'tax_id': '12345678901', 'business_name': 'PROVEEDOR UNO',
                'address': 'DIRECCION UNO', 'reference': 'NO-EXISTE',
                'current_tax': '18', 'subtotal': '0', 'tax': '0', 'total': '0',
                'total_in_words': 'CERO', 'code': '', 'date': '01/01/2024',
                'notes': '', 'payment_method': payment_method.pk,
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-quotation': '999999', 'form-0-code': product.pk,
                'form-0-name': 'PRODUCTO', 'form-0-unit': 'UND01',
                'form-0-quantity': '5', 'form-0-price': '3', 'form-0-tax': '1',
                'form-0-amount': '15'}

        response = self.client.post(reverse('purchases:purchase_order_update',
                                            args=[order.pk]), data)

        self.assertEqual(302, response.status_code)
        order.refresh_from_db()
        self.assertEqual(1, order.details.count())

    def test_service_order_update(self):
        supplier = baker.make(Supplier, tax_id='12345678901')
        payment_method = baker.make('accounting.PaymentMethod')
        product = baker.make('products.Product')
        order = baker.make(ServiceOrder, supplier=supplier, quotation=None)
        data = {'tax_id': '12345678901', 'business_name': 'PROVEEDOR UNO',
                'address': 'DIRECCION UNO', 'reference': '999999',
                'subtotal': '0', 'tax': '0', 'total': '0', 'total_in_words': 'CERO',
                'code': '', 'process': '', 'notes': '', 'report_name': '',
                'date': '01/01/2024', 'payment_method': payment_method.pk,
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-quotation': '999999', 'form-0-code': product.pk,
                'form-0-name': 'SERVICIO', 'form-0-unit': 'UND01',
                'form-0-quantity': '5', 'form-0-price': '3', 'form-0-amount': '15'}

        response = self.client.post(reverse('purchases:service_order_update',
                                            args=[order.pk]), data)

        self.assertEqual(302, response.status_code)
        order.refresh_from_db()
        self.assertEqual(1, order.details.count())

    def test_service_conformity_create(self):
        requirement = create_requirement()
        requirement_detail = baker.make('requirements.RequirementDetail',
                                        requirement=requirement,
                                        product=baker.make('products.Product'),
                                        quantity=10, served_quantity=0)
        quotation = baker.make(Quotation, requirement=requirement,
                               supplier=baker.make(Supplier))
        quotation_detail = baker.make('purchases.QuotationDetail', quotation=quotation,
                                      requirement_detail=requirement_detail, quantity=10)
        service_order = baker.make(ServiceOrder, quotation=quotation,
                                   supplier=baker.make(Supplier))
        service_order_detail = baker.make('purchases.ServiceOrderDetail',
                                          order=service_order,
                                          quotation_detail=quotation_detail,
                                          quantity=10, conformed_quantity=0)
        data = {'reference': service_order.pk, 'subtotal': '0', 'total': '0',
                'total_in_words': 'CERO', 'code': '', 'supporting_document': '',
                'date': '01/01/2024',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-service_order': service_order_detail.pk, 'form-0-quantity': '4',
                'form-0-service': 'SERVICIO', 'form-0-use': 'USO',
                'form-0-price': '3', 'form-0-amount': '12'}

        response = self.client.post(reverse('purchases:service_conformity_create'), data)

        self.assertEqual(302, response.status_code)
        service_order_detail.refresh_from_db()
        self.assertEqual(4, service_order_detail.conformed_quantity)

    def test_service_conformity_update(self):
        requirement = create_requirement()
        requirement_detail = baker.make('requirements.RequirementDetail',
                                        requirement=requirement,
                                        product=baker.make('products.Product'),
                                        quantity=10, served_quantity=4)
        quotation = baker.make(Quotation, requirement=requirement,
                               supplier=baker.make(Supplier))
        quotation_detail = baker.make('purchases.QuotationDetail', quotation=quotation,
                                      requirement_detail=requirement_detail, quantity=10)
        service_order = baker.make(ServiceOrder, quotation=quotation,
                                   supplier=baker.make(Supplier))
        service_order_detail = baker.make('purchases.ServiceOrderDetail',
                                          order=service_order,
                                          quotation_detail=quotation_detail,
                                          quantity=10, conformed_quantity=4)
        conformity = baker.make('purchases.ServiceConformity',
                                service_order=service_order)
        baker.make('purchases.ServiceConformityDetail', conformity=conformity,
                   service_order_detail=service_order_detail, quantity=4)
        data = {'reference': service_order.pk, 'subtotal': '0', 'total': '0',
                'total_in_words': 'CERO', 'code': conformity.code,
                'supporting_document': 'DOC', 'date': '01/01/2024'}

        response = self.client.post(reverse('purchases:service_conformity_update',
                                            args=[conformity.pk]), data)

        self.assertEqual(302, response.status_code)
        conformity.refresh_from_db()
        self.assertEqual('DOC', conformity.supporting_document)

    def test_order_excel_reports_by_date(self):
        import datetime

        supplier = baker.make(Supplier)
        baker.make(PurchaseOrder, supplier=supplier, date=datetime.date(2024, 1, 15))
        baker.make(ServiceOrder, supplier=supplier, date=datetime.date(2024, 1, 15))
        data = {'start_date': '01/01/2024', 'end_date': '31/01/2024',
                'month': '01', 'year': '2024'}

        for search_type in ('F', 'M', 'A'):
            for name in ('purchases:purchase_order_excel_report_by_date',
                         'purchases:service_order_excel_report_by_date'):
                with self.subTest(search_type=search_type, name=name):
                    response = self.client.post(reverse(name),
                                                dict(data, search_type=search_type))
                    self.assertEqual(200, response.status_code)

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

    def test_lists_return_htmx_fragment_and_search(self):
        supplier = baker.make(Supplier, business_name='PROVEEDOR UNICO')
        quotation = baker.make(Quotation, supplier=supplier)
        purchase_order = baker.make(PurchaseOrder, quotation=quotation,
                                    supplier=supplier)
        service_order = baker.make(ServiceOrder, quotation=quotation,
                                   supplier=supplier)
        conformity = baker.make('purchases.ServiceConformity',
                                service_order=service_order)
        cases = [
            ('purchases:supplier_list', supplier.business_name),
            ('purchases:quotation_list', quotation.code),
            ('purchases:purchase_order_list', purchase_order.code),
            ('purchases:service_order_list', service_order.code),
            ('purchases:service_conformity_list', conformity.code),
        ]

        for name, term in cases:
            with self.subTest(name=name):
                fragment = self.client.get(reverse(name), {'q': term},
                                           HTTP_HX_REQUEST='true')
                self.assertEqual(200, fragment.status_code)
                self.assertNotContains(fragment, '<html')
                self.assertContains(fragment, term)


class PurchasesDeleteAndFetchTest(TestCase):
    """Los borrados por AJAX y los fetch que alimentan los formsets."""

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('d', 'd@example.com', 'clave'))
        self.supplier = baker.make(Supplier)

    def test_quotation_delete(self):
        quotation = baker.make(Quotation, supplier=self.supplier)

        response = self.client.post(reverse('purchases:quotation_delete'),
                                    {'code': quotation.code},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(200, response.status_code)
        self.assertEqual('NO', response.json()['orders'])
        quotation.refresh_from_db()
        self.assertEqual(Quotation.STATUS.CANC, quotation.status)

    def test_quotation_delete_with_orders(self):
        quotation = baker.make(Quotation, supplier=self.supplier)
        baker.make(PurchaseOrder, quotation=quotation, supplier=self.supplier)

        response = self.client.post(reverse('purchases:quotation_delete'),
                                    {'code': quotation.code},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(200, response.status_code)
        self.assertEqual('SI', response.json()['orders'])

    def test_purchase_order_delete(self):
        order = baker.make(PurchaseOrder, supplier=self.supplier)

        response = self.client.post(reverse('purchases:purchase_order_delete'),
                                    {'code': order.code},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(200, response.status_code)
        self.assertEqual('NO', response.json()['movements'])
        order.refresh_from_db()
        self.assertEqual(PurchaseOrder.STATUS.CANC, order.status)

    def test_purchase_order_delete_with_movement(self):
        order = baker.make(PurchaseOrder, supplier=self.supplier)
        baker.make('warehouse.Movement', reference=order)

        response = self.client.post(reverse('purchases:purchase_order_delete'),
                                    {'code': order.code},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(200, response.status_code)
        self.assertEqual('SI', response.json()['movements'])

    def test_service_order_delete(self):
        order = baker.make(ServiceOrder, supplier=self.supplier)

        response = self.client.post(reverse('purchases:service_order_delete'),
                                    {'code': order.code},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(200, response.status_code)
        self.assertEqual('NO', response.json()['conformidades'])
        order.refresh_from_db()
        self.assertEqual(ServiceOrder.STATUS.CANC, order.status)

    def test_service_order_delete_with_conformity(self):
        order = baker.make(ServiceOrder, supplier=self.supplier)
        baker.make('purchases.ServiceConformity', service_order=order)

        response = self.client.post(reverse('purchases:service_order_delete'),
                                    {'code': order.code},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(200, response.status_code)
        self.assertEqual('SI', response.json()['conformidades'])

    def test_service_conformity_delete(self):
        conformity = baker.make('purchases.ServiceConformity')

        response = self.client.post(reverse('purchases:service_conformity_delete'),
                                    {'code': conformity.code},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(200, response.status_code)
        conformity.refresh_from_db()
        self.assertFalse(conformity.is_active)

    def test_transfer_lists(self):
        for name in ('purchases:quotation_transfer', 'purchases:purchase_order_transfer',
                     'purchases:service_order_transfer'):
            with self.subTest(name=name):
                self.assertEqual(200, self.client.get(reverse(name)).status_code)

    def test_quotation_detail_fetch(self):
        from purchases.models import QuotationDetail

        requirement = create_requirement()
        product = baker.make('products.Product', is_service=False)
        service = baker.make('products.Product', is_service=True)
        quotation = baker.make(Quotation, supplier=self.supplier, requirement=requirement)
        for number, item in enumerate((product, service), start=1):
            requirement_detail = baker.make('requirements.RequirementDetail',
                                            requirement=requirement, product=item,
                                            quantity=10, purchased_quantity=0)
            baker.make(QuotationDetail, quotation=quotation,
                       requirement_detail=requirement_detail, line_number=number,
                       quantity=5)

        for search_type in ('PRODUCTOS', 'SERVICIOS'):
            with self.subTest(search_type=search_type):
                response = self.client.get(reverse('purchases:quotation_detail_fetch'),
                                           {'quotation': quotation.code,
                                            'search_type': search_type},
                                           HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                self.assertEqual(200, response.status_code)

    def test_purchase_order_detail_fetch(self):
        from purchases.models import PurchaseOrderDetail

        order = baker.make(PurchaseOrder, supplier=self.supplier,
                           in_dollars=False, with_tax=False)
        baker.make(PurchaseOrderDetail, order=order,
                   product=baker.make('products.Product'), line_number=1,
                   quantity=5, status=PurchaseOrderDetail.STATUS.PEND)

        response = self.client.get(reverse('purchases:purchase_order_detail_fetch'),
                                   {'purchase_order': order.code, 'date': '01/01/2024'},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(200, response.status_code)

    def test_service_order_detail_fetch(self):
        from purchases.models import ServiceOrderDetail

        order = baker.make(ServiceOrder, supplier=self.supplier)
        baker.make(ServiceOrderDetail, order=order,
                   product=baker.make('products.Product'), line_number=1,
                   quantity=2, price=10, status=ServiceOrderDetail.STATUS.PEND)

        response = self.client.get(reverse('purchases:service_order_detail_fetch'),
                                   {'service_order': order.code},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(200, response.status_code)
