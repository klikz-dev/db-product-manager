from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from misc.models import Config

from mysql.models import Manufacturer
from shopify.models import Address, Customer, Line_Item, Order, Product, ProductImage, Variant
from shopify.serializers import AddressDetailSerializer, AddressListSerializer, CustomerDetailSerializer, CustomerListSerializer, ImageDetailSerializer, ImageListSerializer, LineItemDetailSerializer, LineItemListSerializer, OrderDetailSerializer, OrderListSerializer, OrderUpdateSerializer, ProductDetailSerializer, ProductListSerializer, VariantDetailSerializer, VariantListSerializer, VariantUpdateSerializer

from datetime import datetime, timedelta
from django.db.models import Q


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


class OrderViewSet(viewsets.ModelViewSet):

    queryset = Order.objects.all()
    serializer_class = OrderListSerializer

    def list(self, request):
        orders = Order.objects.all().order_by('-orderDate')

        fr = self.request.query_params.get('from')
        to = self.request.query_params.get('to')
        if fr is not None and to is not None:
            orders = orders.filter(orderDate__range=(datetime.strptime(
                fr, '%y-%m-%d'), datetime.strptime(to, '%y-%m-%d') + timedelta(days=1)))

        po = self.request.query_params.get('po')
        if po is not None:
            orders = orders.filter(orderNumber=po)

        customer = self.request.query_params.get('customer')
        if customer is not None:
            orders = orders.filter(Q(shippingFirstName__icontains=customer) | Q(
                shippingLastName__icontains=customer) | Q(email__icontains=customer))

        manufacturer = self.request.query_params.get('manufacturer')
        if manufacturer is not None:
            orders = orders.filter(manufacturerList__icontains=manufacturer)

        ref = self.request.query_params.get('ref')
        if ref is not None:
            orders = orders.filter(referenceNumber=ref)

        brand = self.request.query_params.get('brand')
        type = self.request.query_params.get('type')

        manufacturers = []
        for m in Manufacturer.objects.filter(brand=brand):
            manufacturers.append(m)

        if brand is not None and len(manufacturers) > 0:
            orders = orders.filter(
                line_items__orderedProductManufacturer__in=manufacturers)

        type = self.request.query_params.get('type')
        if type is not None and type == 's':
            orders = orders.filter(
                Q(orderType='Sample') | Q(orderType='Order/Sample'))

        if type is not None and type == 'o':
            lineItems = lineItems.exclude(
                Q(orderType='Order') | Q(orderType='Order/Sample'))

        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        orders = Order.objects.all()
        order = get_object_or_404(orders, pk=pk)
        serializer = OrderDetailSerializer(
            instance=order, context={'request': request})
        return Response(serializer.data)

    def update(self, request, pk=None):
        orders = Order.objects.all()
        order = get_object_or_404(orders, pk=pk)
        serializer = OrderUpdateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.update(
                instance=order, validated_data=serializer.validated_data)
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class LineItemViewSet(viewsets.ModelViewSet):

    queryset = Line_Item.objects.all()
    serializer_class = LineItemListSerializer

    def list(self, request):
        lineItems = Line_Item.objects.all().order_by('-createdAt')

        order = self.request.query_params.get('order')
        if order is not None:
            lineItems = lineItems.filter(order=order)

        brand = self.request.query_params.get('brand')
        manufacturers = []
        for m in Manufacturer.objects.filter(brand=brand):
            manufacturers.append(m)
        if brand is not None and len(manufacturers) > 0:
            lineItems = lineItems.filter(
                orderedProductManufacturer__in=manufacturers)

        config = Config.objects.all()
        last_processed_order = config[0].last_processed_order
        last_processed_sample = config[0].last_processed_sample

        type = self.request.query_params.get('type')
        if type is not None and type == 's':
            lineItems = lineItems.filter(
                orderedProductVariantTitle__icontains='Sample -')
            lineItems = lineItems.filter(order__gte=last_processed_sample)
        if type is not None and type == 'o':
            lineItems = lineItems.exclude(
                orderedProductVariantTitle__icontains='Sample -')
            lineItems = lineItems.filter(order__gte=last_processed_order)

        page = self.paginate_queryset(lineItems)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(lineItems, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        lineItems = Line_Item.objects.all()
        lineItem = get_object_or_404(lineItems, pk=pk)
        serializer = LineItemDetailSerializer(
            instance=lineItem, context={'request': request})
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):

    queryset = Product.objects.all()
    serializer_class = ProductListSerializer

    def list(self, request):
        products = Product.objects.all()

        productId = self.request.query_params.get('id')
        if productId is not None:
            products = products.filter(productId=productId)

        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        products = Product.objects.all()
        product = get_object_or_404(products, pk=pk)
        serializer = ProductDetailSerializer(
            instance=product, context={'request': request})
        return Response(serializer.data)


class VariantViewSet(viewsets.ModelViewSet):

    queryset = Variant.objects.all()
    serializer_class = VariantListSerializer

    def list(self, request):
        variants = Variant.objects.all()

        variantID = self.request.query_params.get('id')
        if variantID is not None:
            variants = variants.filter(VariantID=variantID)

        page = self.paginate_queryset(variants)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(variants, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        variants = Variant.objects.all()
        variant = get_object_or_404(variants, pk=pk)
        serializer = VariantDetailSerializer(
            instance=variant, context={'request': request})
        return Response(serializer.data)

    def update(self, request, pk=None):
        variants = Variant.objects.all()
        variant = get_object_or_404(variants, pk=pk)
        serializer = VariantUpdateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.update(
                instance=variant, validated_data=serializer.validated_data)
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
