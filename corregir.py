from compras.models import OrdenCompra
archivo = open("detalles_ordenes_compra.txt")
for linea in archivo:
	inicio = linea.find("OC")
	codigo = linea[inicio:inicio+12]
	if codigo!="":
		orden = OrdenCompra.objects.get(codigo=codigo)
		cad = linea.replace(codigo,str(orden.pk))
		print cad	
