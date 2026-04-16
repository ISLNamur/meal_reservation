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
    <BRow class="mt-1 mb-2">
        <BCol>
            <BCard title="Ajout/modification de réservation">
                <BFormGroup label="Date">
                    <div v-if="dates.length > 0">
                        <span
                            v-for="(day, i) in dates"
                            :key="day"
                            class="me-1"
                        >

                            <strong>{{ niceDate(day) }}</strong>
                            <span v-if="i < dates.length - 1">,</span>
                        </span>
                    </div>
                    <span
                        v-else
                        class="text-secondary"
                    >
                        Sélectionner une date en cliquant dessus (ou plusieurs dates en maintenant la pression du curseur).
                    </span>
                </BFormGroup>
                <BFormGroup label="Type de repas">
                    <BFormSelect
                        v-model="meal"
                        :options="availableMeals"
                        text-field="name"
                        value-field="id"
                    >
                        <template #option="data">
                            {{ data.name }} (à partir du {{ niceDate(data.first_available_date) }})
                        </template>
                    </BFormSelect>
                </BFormGroup>
                <BFormGroup class="text-end">
                    <BButton
                        variant="outline-danger"
                        @click="closeForm"
                    >
                        Annuler
                    </BButton>
                    <BButton
                        variant="primary"
                        class="ms-2"
                        @click="submit"
                    >
                        Soumettre
                    </BButton>
                </BFormGroup>
            </BCard>
        </BCol>
    </BRow>
</template>

<script>
import axios from "axios";
import { DateTime } from "luxon";

import { useToastController } from "bootstrap-vue-next";
import { errorMessages } from "vue/compiler-sfc";

const token = { xsrfCookieName: "csrftoken", xsrfHeaderName: "X-CSRFToken" };

export default {
    setup: function () {
        const { show } = useToastController();
        return { show };
    },
    props: {
        dates: {
            type: Array,
            default: () => [],
        },
        reservations: {
            type: Array,
            default: () => [],
        },
        meals: {
            type: Array,
            default: () => [],
        },
    },
    emits: ["update:dates", "update:reservations", "close-form"],
    computed: {
        availableMeals: function () {
            return this.meals.map((m) => {
                m.disabled = false;

                if (this.dates.length === 0) {
                    return m;
                }

                if (m.first_available_date > this.dates[0]) {
                    m.disabled = true;
                    return m;
                }

                return m;
            });
        },
    },
    methods: {
        closeForm: function () {
            this.$emit("update:dates", []);
            this.$emit("close-form");
        },
        niceDate: function (str) {
            return DateTime.fromISO(str).toLocaleString();
        },
        submit: function () {
            const data = this.dates.map((d) => {
                return {
                    meal: this.meal,
                    date: d,
                    responsible: this.responsible,
                };
            });

            const newReserv = data.filter((m) => {
                return !this.reservations.find(r => r.date === m.date);
            }).map(reserv => axios.post("/meal_reservation/api/reservation/", reserv, token));

            const existReserv = data.filter(m => this.reservations.find(r => r.date === m.date))
                .map((reserv) => {
                    return axios.put(
                        `/meal_reservation/api/reservation/${this.reservations.find(r => r.date === reserv.date).id}/`,
                        reserv, token);
                });

            Promise.all(newReserv.concat(existReserv))
                .then((resps) => {
                    let reservations = this.reservations.slice();
                    resps.forEach((resp) => {
                        resp.data.dateObject = DateTime.fromISO(resp.data);
                        resp.data.pk = resp.data.id;
                        if (resp.config.method === "put") {
                            const index = reservations.findIndex(exRes => exRes.date === resp.data.date);
                            reservations.splice(index, 1, resp.data);
                        } else {
                            reservations.push(resp.data);
                        }
                    });
                    this.show({
                        body: "La demande a été enregistrée.",
                        variant: "success",
                    });
                    this.$emit("update:reservations", reservations);
                    this.$emit("close-form");
                })
                .catch((err) => {
                    if ("non_field_errors" in err.response.data) {
                        this.show({
                            body: err.response.data.non_field_errors[0],
                            variant: "danger",
                        });
                    } else {
                        console.log(err.response.data);
                    }
                });
        },
    },
    data: function () {
        return {
            meal: null,
            responsible: null,
        };
    },
    mounted: function () {
        axios.get(`/annuaire/api/responsible/${user_properties.matricule}/`)
            .then((resp) => {
                this.responsible = resp.data.pk;
            });
    },
};
</script>
