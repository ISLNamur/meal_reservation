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
from django.db.models import ObjectDoesNotExist
from django.utils import timezone

from core.email import send_email

from meal_reservation.models import MealModel, ReservationModel


class Command(BaseCommand):
    help = "Send an email with the reservations of the week."

    def add_arguments(self, parser):
        parser.add_argument("--email")
        parser.add_argument("--meal")
        parser.add_argument("--day-interval", default=1, type=int)

    def handle(self, *args, **options):
        recipient = options["email"]
        try:
            meal = MealModel.objects.get(name=options["meal"])
        except ObjectDoesNotExist:
            print("Le repas n'a pas été trouvé")
            return

        from_date = timezone.now()
        to_date = from_date + datetime.timedelta(days=options["day_interval"])

        print(f"Sending reservations to {recipient} between {from_date} and {to_date}")

        reservations = ReservationModel.objects.filter(
            date__gte=from_date,
            date__lt=to_date,
            meal=meal,
        ).order_by("date")

        reservations = [
            {
                "date": res.date,
                "count": reservations.filter(date=res.date).count(),
                "names": ", ".join(
                    [
                        f"{a} {b}"
                        for (a, b) in reservations.filter(date=res.date).values_list(
                            "responsible__last_name", "responsible__first_name"
                        )
                    ]
                ),
            }
            for res in reservations.distinct("date")
        ]

        send_email(
            to=[recipient],
            subject=f"Réservation des repas {meal.name}",
            context={"reservations": reservations, "meal": meal},
            email_template="meal_reservation/reservation_summary.html",
        )
