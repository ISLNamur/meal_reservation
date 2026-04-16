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

import datetime
from django.utils import timezone

from django.db import models

from core.models import ResponsibleModel


class MealModel(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    time_limit = models.TimeField()
    weekday_limit = models.PositiveSmallIntegerField(null=True, blank=True)
    weekday_service = models.CharField(max_length=15, blank=True)

    def __str__(self) -> str:
        return self.name

    @property
    def first_available_date(self) -> datetime.date:
        today = timezone.now()
        today_limit = today.replace(
            hour=self.time_limit.hour,
            minute=self.time_limit.minute,
            second=self.time_limit.second,
            tzinfo=timezone.get_default_timezone(),
        )

        # If no weekday limit, only check time limit.
        if self.weekday_limit is None:
            if today > today_limit:
                return (today_limit + datetime.timedelta(days=1)).date()
            else:
                return today_limit.date()

        # If weekday limit and today is weekday limit, check time limit.
        if today.weekday() == self.weekday_limit:
            if today > today_limit:
                return (today_limit + datetime.timedelta(days=7)).date()
            else:
                return today_limit.date()

        # Finally compute next limit only by weekday.
        delta_days: int = (7 - (today.weekday() - self.weekday_limit)) % 7
        return (today_limit + datetime.timedelta(days=delta_days)).date()


class ReservationModel(models.Model):
    date = models.DateField()
    responsible = models.ForeignKey(ResponsibleModel, on_delete=models.CASCADE)
    meal = models.ForeignKey(MealModel, on_delete=models.CASCADE)

    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["date", "responsible"], name="meal_by_day_by_person")
        ]
        indexes = [models.Index(fields=["date"])]

    def __str__(self) -> str:
        return f"{self.date} : {self.meal.name} ({self.responsible.fullname})"
