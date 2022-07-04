from rest_framework import serializers

from .models import Address, Customer, ProductImage


# Address
class AddressDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'


class AddressListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'


# Customer
class CustomerDetailSerializer(serializers.ModelSerializer):
    addresses = AddressListSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = '__all__'


class CustomerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


# Product Image
class ImageDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'


class ImageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'
