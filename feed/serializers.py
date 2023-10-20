from rest_framework import serializers
from .models import Roomvo


# Address
class RoomvoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roomvo
        fields = '__all__'
