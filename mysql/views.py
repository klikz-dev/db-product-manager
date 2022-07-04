from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response

from mysql.models import Address, Customer, ProductImage
from mysql.serializeres import AddressDetailSerializer, AddressListSerializer, CustomerDetailSerializer, CustomerListSerializer, ImageDetailSerializer, ImageListSerializer


class CustomerViewSet(viewsets.ModelViewSet):

    queryset = Customer.objects.all()
    serializer_class = CustomerListSerializer

    def list(self, request):
        customers = Customer.objects.all().order_by('-firstName')

        page = self.paginate_queryset(customers)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(customers, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        customers = Customer.objects.all()
        customer = get_object_or_404(customers, pk=pk)
        serializer = CustomerDetailSerializer(
            instance=customer, context={'request': request})
        return Response(serializer.data)


class AddressViewSet(viewsets.ModelViewSet):

    queryset = Address.objects.all()
    serializer_class = AddressListSerializer

    def list(self, request):
        addresses = Address.objects.all().order_by('-updatedAt')

        customer = self.request.query_params.get('customer')
        if customer is not None:
            addresses = addresses.filter(customerId=customer)

        page = self.paginate_queryset(addresses)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(addresses, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        addresses = Address.objects.all()
        address = get_object_or_404(addresses, pk=pk)
        serializer = AddressDetailSerializer(
            instance=address, context={'request': request})
        return Response(serializer.data)


class ImageViewSet(viewsets.ModelViewSet):

    queryset = ProductImage.objects.all()
    serializer_class = ImageListSerializer

    def list(self, request):
        images = ProductImage.objects.all()

        productId = self.request.query_params.get('product')
        if productId is not None:
            images = images.filter(productId=productId, imageIndex=1)

        page = self.paginate_queryset(images)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(images, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        images = ProductImage.objects.all()
        image = get_object_or_404(images, pk=pk)
        serializer = ImageDetailSerializer(
            instance=image, context={'request': request})
        return Response(serializer.data)
