from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response

from mysql.models import Manufacturer, PORecord, PendingUpdatePublish
from shopify.models import Address, Customer, Line_Item, Order, Product, ProductImage, Tracking, Variant
from shopify.serializers import AddressDetailSerializer, AddressListSerializer, CustomerDetailSerializer, CustomerListSerializer, ImageDetailSerializer, ImageListSerializer, LineItemDetailSerializer, LineItemListSerializer, OrderDetailSerializer, OrderListSerializer, OrderTrackingSerializer, OrderUpdateSerializer, ProductDetailSerializer, ProductListSerializer, ProductUpdateSerializer, VariantDetailSerializer, VariantListSerializer, VariantUpdateSerializer

from datetime import datetime, timedelta
from django.db.models import Q

import pymysql
from library import common, shopify, debug

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))


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
            orders = orders.filter(referenceNumber__icontains=ref)

        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        orderRes = shopify.getOrderById(pk)

        if orderRes.get('order'):
            try:
                common.importOrder(orderRes['order'])
            except Exception as e:
                debug.debug("Order", 1, str(e))

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

            updatedOrder = get_object_or_404(orders, pk=pk)
            shopify.updateOrderById(order.shopifyOrderId, updatedOrder)

            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class LineItemViewSet(viewsets.ModelViewSet):

    queryset = Line_Item.objects.all()
    serializer_class = LineItemListSerializer

    def list(self, request):
        lineItems = Line_Item.objects.all().order_by('-createdAt')

        # Filter by Brand Name
        brand = self.request.query_params.get('brand')
        manufacturers = []
        for m in Manufacturer.objects.filter(brand=brand):
            manufacturers.append(m)

        if brand is not None and len(manufacturers) > 0:
            lineItems = lineItems.filter(
                orderedProductManufacturer__in=manufacturers)
        ######################

        # Filter by Processor Type
        type = self.request.query_params.get('type')
        if type == 's':
            lineItems = lineItems.filter(
                orderedProductVariantTitle__icontains='Sample -')
        if type == 'o':
            lineItems = lineItems.exclude(
                orderedProductVariantTitle__icontains='Sample -')
        ###########################

        # Filter by Status
        lineItems = lineItems.exclude(
            Q(order__status__icontains='Processed') |
            Q(order__status__icontains='Cancel') |
            Q(order__status__icontains='Hold') |
            Q(order__status__icontains='Call') |
            Q(order__status__icontains='Return') |
            Q(order__status__icontains='Discontinued') |
            Q(order__status__icontains='Back') |
            Q(order__status__icontains='B/O') |
            Q(order__status__icontains='Manually') |
            Q(order__status__icontains='CFA')
        )

        # Filter by Last Processed Order/Sample Ids
        poRecord = PORecord.objects.values()
        lastPO = None

        brandName = brand.replace(' ', '').replace('/', '').replace('&', '')
        if type == "o":
            typeName = "Order"
        else:
            typeName = "Sample"

        if brandName != "":
            lastPO = (poRecord[0]['{}{}'.format(brandName, typeName)])

        if lastPO is not None:
            lastPO = int(lastPO) + 1
            lineItems = lineItems.filter(order__orderNumber__gte=lastPO)
        ############################################

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
        sku = self.request.query_params.get('sku')
        pattern = self.request.query_params.get('pattern')
        color = self.request.query_params.get('color')
        type = self.request.query_params.get('type')
        vendor = self.request.query_params.get('vendor')

        if productId:
            products = products.filter(productId=productId)

        if sku:
            products = products.filter(sku=sku)

        if pattern:
            products = products.filter(pattern=pattern)

        if color:
            products = products.filter(color=color)

        if type:
            products = products.filter(productTypeId=type)

        if vendor:
            products = products.filter(vendor=vendor)

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

    def update(self, request, pk=None):
        products = Product.objects.all()
        product = get_object_or_404(products, productId=pk)
        serializer = ProductUpdateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.update(
                instance=product, validated_data=serializer.validated_data)

            updateProduct = get_object_or_404(products, productId=pk)
            try:
                PendingUpdatePublish.objects.get(
                    productId=updateProduct.productId)
            except PendingUpdatePublish.DoesNotExist:
                PendingUpdatePublish.objects.create(
                    productId=updateProduct.productId)

            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class VariantViewSet(viewsets.ModelViewSet):

    queryset = Variant.objects.all()
    serializer_class = VariantListSerializer

    def list(self, request):
        variants = Variant.objects.all()

        variantID = self.request.query_params.get('id')
        productId = self.request.query_params.get('productid')

        if variantID:
            variants = variants.filter(VariantID=variantID)

        if productId:
            variants = variants.filter(productId=productId)

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


class PORecordViewSet(viewsets.ModelViewSet):

    queryset = PORecord.objects.all()

    def update(self, request, pk=None):

        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        if request.data.get('field') != None and request.data.get('lastPO') != None:
            csr.execute(
                "UPDATE PORecord SET {} = {}".format(request.data['field'], request.data['lastPO']))
            con.commit()

        return Response(status=status.HTTP_200_OK)


class TrakcingViewSet(viewsets.ModelViewSet):

    queryset = Tracking.objects.all()
    serializer_class = OrderTrackingSerializer

    def list(self, request):
        trackings = Tracking.objects.all()

        orderNumber = self.request.query_params.get('po')
        if orderNumber is not None:
            trackings = trackings.filter(orderNumber=orderNumber)

        page = self.paginate_queryset(trackings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(trackings, many=True)
        return Response(serializer.data)
