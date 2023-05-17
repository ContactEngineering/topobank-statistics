<script>

import {v4 as uuid4} from 'uuid';

import DataTable from 'datatables.net-vue3';
import DataTablesLib from 'datatables.net-bs4';

DataTable.use(DataTablesLib);

import BibliographyModal from 'topobank/analysis/BibliographyModal.vue';
import CardExpandButton from 'topobank/analysis/CardExpandButton.vue';
import TasksButton from 'topobank/analysis/TasksButton.vue';

import {formatExponential} from "topobank/utils/formatting";

export default {
    name: 'roughness-parameters-card',
    components: {
        BibliographyModal,
        CardExpandButton,
        DataTable,
        TasksButton
    },
    props: {
        apiUrl: {
            type: String,
            default: '/plugins/topobank_statistics/card/roughness-parameters'
        },
        csrfToken: String,
        detailUrl: {
            type: String,
            default: '/analysis/html/detail/'
        },
        enlarged: {
            type: Boolean,
            default: false
        },
        functionId: Number,
        functionName: String,
        subjects: String,
        txtDownloadUrl: String,
        uid: {
            type: String,
            default() {
                return uuid4();
            }
        },
        xlsxDownloadUrl: String
    },
    data() {
        return {
            analyses: [],
            analysesAvailable: false,
            columnDefs: [
                // Indicate that first column contains HTML
                // to have HTML tags removed for sorting/filtering
                {targets: 0, type: 'html'}
            ],
            columns: [
                {
                    title: 'Measurement',
                    render: function (data, type, row) {
                        let name = row.topography_name;
                        return `<a target="_blank" title="${name}" href="${row.topography_url}">${name}</a>`;
                    }
                },
                {data: 'quantity', title: 'Quantity'},
                {data: 'from', title: 'From'},
                {data: 'symbol', title: '<span title="Symbol according to ASME B46.1">Sym. 🛈</span>'},
                {data: 'direction', title: 'Direct.'},
                {
                    data: 'value', title: 'Value', render: function (x) {
                        return formatExponential(x, 5);
                    }
                },
                {data: 'unit', title: 'Unit'},
            ],
            dois: [],
            data: [],
            title: "Roughness parameters"
        }
    },
    mounted() {
        this.updateCard();
    },
    computed: {
        analysisIds() {
            return this.analyses.map(a => a.id).join();
        }
    },
    methods: {
        updateCard() {
            /* Fetch JSON describing the card */
            fetch(`${this.apiUrl}/${this.functionId}?subjects=${this.subjects}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-CSRFToken': this.csrfToken
                }
            })
                .then(response => response.json())
                .then(data => {
                    this.analyses = data.analyses;
                    /** replace null in value with NaN
                     * This is needed because we cannot pass NaN through JSON without
                     * extra libraries, so it is passed as null (workaround) */
                    this.data = data.tableData.map(x => {
                        if (x['value'] === null) {
                            x['value'] = NaN;
                        }
                        return x
                    });
                    this.dois = data.dois;
                    this.analysesAvailable = true;
                });
        }
    }
};
</script>

<template>
    <div class="card search-result-card">
        <div class="card-header">
            <div class="btn-group btn-group-sm float-right">
                <tasks-button :analyses="analyses"
                              :csrf-token="csrfToken">
                </tasks-button>
                <button @click="updateCard" class="btn btn-default float-right ml-1">
                    <i class="fa fa-redo"></i>
                </button>
                <card-expand-button v-if="!enlarged"
                                    :detail-url="detailUrl"
                                    :function-id="functionId"
                                    :subjects="subjects"
                                    class="btn-group btn-group-sm float-right">
                </card-expand-button>
            </div>
            <a class="text-dark" href="#" data-toggle="collapse" :data-target="`#sidebar-${uid}`">
                <h5><i class="fa fa-bars"></i> {{ title }}</h5>
            </a>
        </div>
        <div class="card-body">
            <div v-if="!analysesAvailable" class="tab-content">
                <span class="spinner"></span>
                <div>Please wait...</div>
            </div>

            <div v-if="analysesAvailable" class="tab-content">
                <div class="tab-pane show active" role="tabpanel" aria-label="Tab showing a plot">
                    <data-table class="table table-striped table-bordered"
                                :column-defs="columnDefs"
                                :columns="columns"
                                :data="data"
                                responsive="yes"
                                scroll-x="yes">
                    </data-table>
                </div>
            </div>
        </div>
        <div :id="`sidebar-${uid}`" class="collapse position-absolute h-100">
            <!-- card-header sets the margins identical to the card so the title appears at the same position -->
            <nav class="card-header navbar navbar-toggleable-xl bg-light flex-column align-items-start h-100">
                <ul class="flex-column navbar-nav">
                    <a class="text-dark" href="#" data-toggle="collapse" :data-target="`#sidebar-${uid}`">
                        <h5><i class="fa fa-bars"></i> {{ title }}</h5>
                    </a>
                    <li class="nav-item mb-1 mt-1">
                        Download
                        <div class="btn-group ml-1" role="group" aria-label="Download formats">
                            <a :href="`/analysis/download/${analysisIds}/txt`" class="btn btn-default">
                                TXT
                            </a>
                            <a :href="`/analysis/download/${analysisIds}/xlsx`" class="btn btn-default">
                                XLSX
                            </a>
                        </div>
                    </li>
                    <li class="nav-item mb-1 mt-1">
                        <a href="#" data-toggle="modal" :data-target="`#bibliography-modal-${uid}`"
                           class="btn btn-default  w-100">
                            Bibliography
                        </a>
                    </li>
                </ul>
            </nav>
        </div>
    </div>
    <bibliography-modal
            :id="`bibliography-modal-${uid}`"
            :dois="dois">
    </bibliography-modal>
</template>
