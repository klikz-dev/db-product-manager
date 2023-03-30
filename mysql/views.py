from rest_framework import viewsets
from rest_framework.response import Response

from .models import ProductInventory
from .serializers import InventorySerializer
from library import inventory


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = ProductInventory.objects.all()
    serializer_class = InventorySerializer

    def list(self, request):
        try:
            sku = self.request.query_params.get('sku')
            stock = inventory.inventory(sku)
            return Response(stock)
        except Exception as e:
            return Response({"error": str(e)})
