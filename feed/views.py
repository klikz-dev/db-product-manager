from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response

from .models import Roomvo
from .serializers import RoomvoSerializer

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))


class RoomvoViewSet(viewsets.ModelViewSet):

    queryset = Roomvo.objects.all()
    serializer_class = RoomvoSerializer

    def list(self, request):
        roomvos = Roomvo.objects.all().order_by('-name')

        sku = self.request.query_params.get('sku')
        if sku is not None:
            roomvos = roomvos.filter(sku=sku)

        page = self.paginate_queryset(roomvos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(roomvos, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        roomvos = Roomvo.objects.all()
        roomvo = get_object_or_404(roomvos, pk=pk)
        serializer = RoomvoSerializer(
            instance=roomvo, context={'request': request})
        return Response(serializer.data)
