from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class QuotationDetailManager(models.Manager):

    def bulk_create(self, objs, requirement, order):
        if requirement is not None:
            self.save_details_with_reference(objs, requirement, order)
        else:
            self.save_details_without_reference(objs, order)

    def save_detail_service_order(self, order, detail):
        from compras.models import ServiceOrderDetail
        service_order_detail = ServiceOrderDetail(order=order,
                                                        quotation_detail=detail,
                                                        line_number=detail.line_number,
                                                        quantity=detail.quantity,
                                                        price=detail.requirement_detail.product.price)
        return service_order_detail

    def save_details_with_reference(self, objs, requirement, order):
        from compras.models import ServiceOrderDetail
        details = []
        for detail in objs:
            requirement_detail = detail.requirement_detail
            requirement_detail.quoted_quantity = requirement_detail.quoted_quantity + detail.quantity
            requirement_detail.set_status_quoted()
            requirement_detail.save()
            detail.save()
            if order is not None:
                service_order_detail = self.save_detail_service_order(order, detail)
                details.append(service_order_detail)
        requirement.set_status_quoted()
        requirement.save()
        if order is not None:
            ServiceOrderDetail.objects.bulk_create(details, order.quotation)

    def save_details_without_reference(self, objs, order):
        for detail in objs:
            detail.save()
            if order is not None:
                self.save_detail_service_order(order, detail)


class ServiceConformityDetailManager(models.Manager):

    def bulk_create(self, objs, order):
        if order is not None:
            self.save_details_with_reference(objs, order)
        else:
            self.save_details_without_reference(objs)

    def save_details_with_reference(self, objs, order):
        try:
            requirement = order.quotation.requirement
        except ObjectDoesNotExist:
            requirement = None
        for detail in objs:
            order_detail = detail.service_order_detail
            order_detail.conformed_quantity = order_detail.conformed_quantity + detail.quantity
            order_detail.set_status_served()
            order_detail.save()
            try:
                requirement_detail = order_detail.quotation_detail.requirement_detail
            except ObjectDoesNotExist:
                requirement_detail = None
            if requirement_detail is not None:
                requirement_detail.served_quantity = requirement_detail.served_quantity + order_detail.conformed_quantity
                requirement_detail.set_status_served()
                requirement_detail.save()
            detail.save()
        if requirement is not None:
            requirement.set_status_served()
            requirement.save()
        order.set_status()
        order.save()

    def save_details_without_reference(self, objs):
        for detail in objs:
            detail.save()
