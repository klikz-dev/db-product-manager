from rest_framework import viewsets
from rest_framework.response import Response

from .models import ProductInventory, ProductTag
from .serializers import InventorySerializer, ProductTagSerializer
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


class ProductTagViewSet(viewsets.ModelViewSet):
    queryset = ProductTag.objects.all()
    serializer_class = ProductTagSerializer

    def list(self, request):
        # try:
        #     sku = self.request.query_params.get('sku')
        #     stock = inventory.inventory(sku)
        #     return Response(stock)
        # except Exception as e:
        #     return Response({"error": str(e)})

        tags = ProductTag.objects.all()

        sku = self.request.query_params.get('sku')
        if sku is not None:
            tags = tags.filter(sku=sku)

        page = self.paginate_queryset(tags)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)
