# This file is part of HappySchool.
#
# HappySchool is the legal property of its developers, whose names
# can be found in the AUTHORS file distributed with this source
# distribution.
#
# HappySchool is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# HappySchool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with HappySchool.  If not, see <http://www.gnu.org/licenses/>.

import json

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import ObjectDoesNotExist, QuerySet
from django.views.generic import TemplateView

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import DjangoModelPermissions

from django_filters import FilterSet
from django_filters.rest_framework.backends import DjangoFilterBackend

from core.models import ResponsibleModel
from core.utilities import get_menu
from core.views import LargePageSizePagination

from meal_reservation.models import MealModel, ReservationModel
from meal_reservation.serializers import MealSerializer, ReservationSerializer


def get_menu_entry(active_app: str, request) -> dict:
    if not request.user.has_perm("meal_reservation.view_mealmodel"):
        return {}
    menu_entry = {
        "app": "meal_reservation",
        "display": "Repas",
        "url": "/meal_reservation",
        "active": active_app == "meal_reservation",
    }

    return menu_entry


class MealReservationView(PermissionRequiredMixin, TemplateView):
    template_name = "meal_reservation/meal_reservation.html"
    permission_required = ("meal_reservation.view_mealmodel",)
    filters = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["menu"] = json.dumps(get_menu(self.request, "meal_reservation"))
        return context


class MealViewset(ModelViewSet):
    queryset = MealModel.objects.all()
    serializer_class = MealSerializer

    permission_classes = [DjangoModelPermissions]


class ReservationFilterset(FilterSet):

    class Meta:
        model = ReservationModel
        fields = {"date": ["exact", "gte"]}


class ReservationViewset(ModelViewSet):
    queryset = ReservationModel.objects.all()
    serializer_class = ReservationSerializer

    permission_classes = [DjangoModelPermissions]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ReservationFilterset
    pagination_class = LargePageSizePagination

    def get_queryset(self) -> QuerySet[ReservationModel]:
        queryset = super().get_queryset()
        try:
            resp = ResponsibleModel.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            return queryset.none()

        queryset.filter(responsible=resp)

        return queryset

    def perform_create(self, serializer: ReservationSerializer) -> None:
        try:
            resp = ResponsibleModel.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            raise

        serializer.save(responsible=resp)
