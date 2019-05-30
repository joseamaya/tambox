from django.db import models

class NavegableQuerySet(models.query.QuerySet):
    
    def ultimo(self):
        return self.order_by('pk').last()
    
    def anterior(self, instancia):        
        try:
            return self.filter(pk__lt = instancia.pk).order_by('-pk')[0]
        except:
            return self.order_by('pk').last()            
        
    def siguiente(self, instancia):        
        try:        
            return self.filter(pk__gt = instancia.pk).order_by('pk')[0]
        except:
            return self.order_by('pk').first()    