from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response

from .models import ProductInventory
from .serializers import InventorySerializer


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = ProductInventory.objects.all()
    serializer_class = InventorySerializer

    def list(self, request):
        inventories = ProductInventory.objects.all()

        sku = self.request.query_params.get('sku')
        if sku is not None:
            inventories = inventories.filter(sku=sku)

        page = self.paginate_queryset(inventories)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(inventories, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        inventories = ProductInventory.objects.all()
        inventory = get_object_or_404(inventories, pk=pk)
        serializer = InventorySerializer(
            instance=inventory, context={'request': request})
        return Response(serializer.data)
