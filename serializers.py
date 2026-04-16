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

from django.utils import timezone

from rest_framework import serializers

from meal_reservation.models import MealModel, ReservationModel


class MealSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealModel
        fields = ["id", "name", "description", "weekday_service", "first_available_date"]


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservationModel
        fields = "__all__"

    def validate(self, attrs):
        data = super().validate(attrs)

        res_date = data["date"]
        meal = data["meal"]

        first_date = meal.first_available_date

        if first_date > res_date:
            raise serializers.ValidationError("Il n'est plus possible de réserver pour cette date")

        return data
