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

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.email import send_email

from meal_reservation.models import MealModel, ReservationModel


class Command(BaseCommand):
    help = "Send an email with the reservations of the week."

    def add_arguments(self, parser):
        parser.add_argument("email")

    def handle(self, *args, **options):
        recipient = options["email"]
        from_date = timezone.now()
        to_date = from_date + datetime.timedelta(days=6)

        print(f"Sending reservations to {recipient} between {from_date} and {to_date}")

        reservations = ReservationModel.objects.filter(
            date__gte=from_date,
            date__lt=to_date,
        ).order_by("date")

        meals = {}
        for r in reservations.values(
            "meal", "date", "responsible__last_name", "responsible__first_name"
        ):
            if r["meal"] not in meals:
                meals[r["meal"]] = {
                    "name": MealModel.objects.get(id=r["meal"]).name,
                    "count": 1,
                    "reservations": [
                        {
                            "responsible": f"{r['responsible__last_name']} {r['responsible__first_name']}",
                            "date": r["date"],
                        }
                    ],
                }
            else:
                meals[r["meal"]]["count"] += 1
                meals[r["meal"]]["reservations"].append(
                    {
                        "responsible": f"{r['responsible__last_name']} {r['responsible__first_name']}",
                        "date": r["date"],
                    }
                )

        print(meals)
        meals = [v for (k, v) in meals.items()]
        send_email(
            to=[recipient],
            subject="Réservation des repas",
            context={"meals": meals},
            email_template="meal_reservation/reservation_summary.html",
            from_email="robot@isln.be",
        )
