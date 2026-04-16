<!-- This file is part of Happyschool. -->
<!--  -->
<!-- Happyschool is the legal property of its developers, whose names -->
<!-- can be found in the AUTHORS file distributed with this source -->
<!-- distribution. -->
<!--  -->
<!-- Happyschool is free software: you can redistribute it and/or modify -->
<!-- it under the terms of the GNU Affero General Public License as published by -->
<!-- the Free Software Foundation, either version 3 of the License, or -->
<!-- (at your option) any later version. -->
<!--  -->
<!-- Happyschool is distributed in the hope that it will be useful, -->
<!-- but WITHOUT ANY WARRANTY; without even the implied warranty of -->
<!-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the -->
<!-- GNU Affero General Public License for more details. -->
<!--  -->
<!-- You should have received a copy of the GNU Affero General Public License -->
<!-- along with Happyschool.  If not, see <http://www.gnu.org/licenses/>. -->

<template>
    <BContainer>
        <BRow class="mt-1">
            <BCol>
                <BButton
                    variant="success"
                    @click="formVisible=true"
                >
                    <IBiPlus />
                    Ajouter
                </BButton>
            </BCol>
            <BCol
                cols="8"
                v-if="nextMeal"
                class="text-end text-secondary"
            >
                Prochain repas : <strong>{{ nextMeal.meal }}</strong> le <strong>{{ nextMeal.date }}</strong>
            </BCol>
        </BRow>
        <BCollapse
            id="meal-form"
            v-model="formVisible"
        >
            <BRow>
                <BCol>
                    <MealForm
                        v-model:dates="selectedDates"
                        v-model:reservations="reservations"
                        :meals="meals"
                        @close-form="formVisible = false"
                    />
                </BCol>
            </BRow>
        </BCollapse>
        <BRow class="mt-2">
            <BCol>
                <FullCalendar
                    ref="fullCalendar"
                    :options="calendarOptions"
                >
                    <template #eventContent="data">
                        <div>
                            <span
                                class="mealRes"
                                v-if="'meal' in data.event.extendedProps"
                            >
                                <span
                                    class="text-center"
                                    style="flex-grow: 2"
                                >
                                    {{ data.event.extendedProps.meal }}
                                </span>
                                <BButton
                                    size="sm"
                                    variant="danger"
                                >
                                    <IBiTrash @click="removeEvent(data.event)" />
                                </BButton>
                            </span>
                            <span
                                v-else
                            >
                                {{ data.event.extendedProps.name }}
                            </span>
                        </div>
                    </template>
                </FullCalendar>
            </BCol>
        </BRow>
    </BContainer>
</template>

<script>
import axios from "axios";
import { DateTime, Interval } from "luxon";

import FullCalendar from "@fullcalendar/vue3";
import dayGridPlugin from "@fullcalendar/daygrid";
import interactionPlugin from "@fullcalendar/interaction";
import frLocale from "@fullcalendar/core/locales/fr";

import { useModalController, useToastController } from "bootstrap-vue-next";

import MealForm from "./MealForm.vue";

const token = { xsrfCookieName: "csrftoken", xsrfHeaderName: "X-CSRFToken" };

export default {
    setup: function () {
        const { show } = useToastController();
        const { create } = useModalController();
        return { show, create };
    },
    data: function () {
        return {
            meals: [],
            firstAvailableDate: null,
            formVisible: false,
            reservations: [],
            selectedDates: [],
            unselectableDates: [],
            calendarOptions: {
                plugins: [dayGridPlugin, interactionPlugin],
                locale: frLocale,
                initialView: "dayGridMonth",
                // eventClick: this.handleDateClick,
                // dateClick: info => console.log(info),
                select: this.parseSelection,
                selectable: true,
                holidays: [],
                selectAllow: this.canBeSelectable,
                weekends: false,
                hiddenDays: [3],
                events: [],
            },
        };
    },
    watch: {
        reservations: {
            handler(newVal, oldVal) {
                if (JSON.stringify(oldVal) === "[]" && JSON.stringify(newVal) === "[]") {
                    return;
                }

                this.updateCalendar();
            },
            immediate: false,
        },
    },
    computed: {
        nextMeal: function () {
            if (this.reservations.length === 0) {
                return null;
            }

            return this.reservations.reduce((pV, nV) => {
                if (nV.date < DateTime.now().toISODate()) {
                    return pV;
                }
                return pV.date < nV.date ? pV : nV;
            });
        },
    },
    methods: {
        updateCalendar: function () {
            this.calendarOptions.eventSources[0] = {
                events: this.reservations.map((evt) => {
                    if (typeof (evt.meal) === "number") {
                        evt.meal = this.meals.find(mO => mO.id === evt.meal).name;
                    }
                    return evt;
                }),
                color: "blue",
            };
        },
        removeEvent: function (evt) {
            this.create({
                body: `Êtes-vous sûr de vouloir supprimer le repas «${evt.extendedProps.meal}» du ${evt.extendedProps.dateObject.toLocaleString()} ?`,
                okTitle: "Oui",
                cancelTitle: "Annuler",
                okVariant: "danger",
            })
                .then((remove) => {
                    if (!remove.ok) return;

                    axios.delete(`/meal_reservation/api/reservation/${evt.extendedProps.pk}/`, token)
                        .then(() => {
                            console.log(this.reservations.findIndex(r => r.id === evt.extendedProps.pk));
                            this.reservations.splice(this.reservations.findIndex(r => r.id === evt.extendedProps.pk), 1);
                            this.updateCalendar();
                        });
                });
        },
        parseSelection: function (selection) {
            this.formVisible = true;

            this.selectedDates = [];
            const begin = DateTime.fromJSDate(selection.start);
            const end = DateTime.fromJSDate(selection.end);

            const daysInterval = end.diff(begin, "days").days;

            for (let d = 0; d < daysInterval; d++) {
                const day = begin.plus({ days: d });
                // Don't select wednesday, saturday and sunday.
                if ([3, 6, 7].find(wD => wD === day.weekday)) {
                    continue;
                }
                this.selectedDates.push(day.toISODate());
            }
        },
        canBeSelectable: function (info) {
            const start = DateTime.fromJSDate(info.start);
            const end = DateTime.fromJSDate(info.end);

            if (end <= this.firstAvailableDate) {
                return false;
            }

            return this.unselectableDates.filter(inter => inter.overlaps(Interval.fromDateTimes(start, end))).length === 0;
        },
    },
    components: {
        FullCalendar,
        MealForm,
    },
    mounted: function () {
        Promise.all([
            axios.get("/meal_reservation/api/reservation/"),
            axios.get("/meal_reservation/api/meal/"),
            axios.get("/core/api/calendar/"),
        ])
            .then((resps) => {
                this.meals = resps[1].data.results;
                this.firstAvailableDate = DateTime.fromISO(this.meals
                    .reduce((prevVal, curVal) => prevVal.first_available_date < curVal.first_available_date ? prevVal : curVal)
                    .first_available_date);

                this.calendarOptions.eventSources = [
                    {
                        events: resps[0].data.results.map((evt) => {
                            evt.meal = this.meals.find(mO => mO.id === evt.meal).name;
                            evt.pk = evt.id;
                            evt.dateObject = DateTime.fromISO(evt.date);
                            return evt;
                        }),
                        color: "blue",
                        className: "mealEvents",
                    },
                    {
                        color: "lightgrey",
                        textColor: "black",
                        events: resps[2].data.results.filter(evt => evt.calendar === "Secondaire").map((evt) => {
                            evt.date = DateTime.fromFormat(evt.begin.slice(0, 11), "dd/MM/yyyy").toISODate();
                            return evt;
                        }),
                        className: "otherEvents",
                    },
                    {
                        color: "red",
                        textColor: "black",
                        events: resps[2].data.results.filter(evt => evt.calendar === "Congés").map((evt) => {
                            evt.start = DateTime.fromFormat(evt.begin.slice(0, 11), "dd/MM/yyyy").toISODate();
                            evt.end = DateTime.fromFormat(evt.end.slice(0, 11), "dd/MM/yyyy").plus({ days: 1 }).toISODate();
                            evt.selectable = false;
                            return evt;
                        }),
                        className: "blockingEvents",
                    },
                ];

                resps[2].data.results.filter(evt => evt.calendar === "Congés").forEach((evt) => {
                    const begin = DateTime.fromFormat(evt.begin.slice(0, 11), "dd/MM/yyyy");
                    const end = DateTime.fromISO(evt.end);

                    this.unselectableDates.push(Interval.fromDateTimes(begin, end));
                }),

                this.reservations = resps[0].data.results;
            });
    },
};
</script>

<style>
    .otherEvents {
        overflow: hidden;
        opacity: 60%;
        text-align: center;
    }

    .blockingEvents {
        text-align: center;
    }

    .mealRes {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .mealRes {
        text-wrap: auto;
    }

    .mealRes button {
        --bs-btn-padding-x: 0rem;
        --bs-btn-padding-y: 0.15rem;
    }
</style>
