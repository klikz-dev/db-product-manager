from rest_framework import serializers
from mysql.serializeres import CustomerDetailSerializer

from shopify.models import Line_Item, Order, Product, Variant


# Product
class ProductDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


# Product Variant
class VariantDetailSerializer(serializers.ModelSerializer):
    product = ProductDetailSerializer()

    class Meta:
        model = Variant
        fields = '__all__'


class VariantListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variant
        fields = '__all__'


class VariantUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variant
        fields = ['backOrderDate', 'boDateStatus']


# Line Items
class LineItemDetailSerializer(serializers.ModelSerializer):
    variant = VariantDetailSerializer()

    class Meta:
        model = Line_Item
        fields = '__all__'


class LineItemListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Line_Item
        fields = '__all__'


# Orders
class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['shopifyOrderId', 'orderNumber', 'email', 'shippingFirstName', 'shippingLastName', 'shippingAddress1',
                  'shippingAddress2', 'shippingCity', 'shippingState', 'shippingZip', 'shippingCountry', 'shippingPhone', 
                  'status', 'orderType', 'orderTotal', 'manufacturerList', 'referenceNumber', 'orderDate', 'note', 'specialShipping']


class OrderDetailSerializer(serializers.ModelSerializer):
    line_items = LineItemDetailSerializer(many=True, read_only=True)
    customer = CustomerDetailSerializer()

    class Meta:
        model = Order
        fields = ['shopifyOrderId', 'orderNumber', 'email', 'phone', 'customer', 'billingLastName', 'billingFirstName',
                  'billingCompany', 'billingAddress1', 'billingAddress2', 'billingCity', 'billingState', 'billingZip',
                  'billingCountry', 'billingPhone', 'shippingLastName', 'shippingFirstName', 'shippingCompany', 'shippingAddress1',
                  'shippingAddress2', 'shippingCity', 'shippingState', 'shippingZip', 'shippingCountry', 'shippingPhone',
                  'shippingMethod', 'orderNote', 'totalItems', 'totalDiscounts', 'orderSubtotal', 'orderTax', 'orderShippingCost',
                  'orderTotal', 'weight', 'orderDate', 'initials', 'status', 'orderType', 'manufacturerList', 'referenceNumber',
                  'customerEmailed', 'customerCalled', 'customerChatted', 'specialShipping', 'customerOrderStatus', 'note', 'oldPO',
                  'isFraud', 'line_items']


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['shippingFirstName', 'shippingLastName', 'shippingCompany', 'shippingAddress1', 'shippingAddress2',
                  'shippingCity', 'shippingState', 'shippingZip', 'shippingCountry', 'shippingPhone', 'shippingMethod',
                  'orderTotal', 'orderNote', 'status', 'manufacturerList', 'referenceNumber', 'customerEmailed', 'customerCalled',
                  'customerChatted', 'specialShipping', 'customerOrderStatus', 'note', 'isFraud']
