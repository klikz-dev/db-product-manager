from rest_framework import serializers

from .models import Config


# Line Items
class ConfigDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Config
        fields = '__all__'


class ConfigListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Config
        fields = '__all__'
