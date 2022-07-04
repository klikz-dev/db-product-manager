from rest_framework import viewsets
from rest_framework.response import Response

from misc.models import Config
from misc.serializers import ConfigListSerializer


class ConfigViewSet(viewsets.ModelViewSet):

    queryset = Config.objects.all()
    serializer_class = ConfigListSerializer

    def list(self, request):
        configs = Config.objects.all()

        page = self.paginate_queryset(configs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(configs, many=True)
        return Response(serializer.data)
