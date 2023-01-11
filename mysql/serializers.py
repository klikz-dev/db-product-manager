from rest_framework import serializers
from .models import ProductInventory


# Address
class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInventory
        fields = '__all__'
