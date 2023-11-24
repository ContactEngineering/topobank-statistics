<script setup>

import axios from "axios";
import {v4 as uuid4} from 'uuid';
import {computed, onMounted, ref} from "vue";

import DataTable from 'datatables.net-vue3';
import DataTablesLib from 'datatables.net-bs5';

DataTable.use(DataTablesLib);

import BibliographyModal from 'topobank/analysis/BibliographyModal.vue';
import CardExpandButton from 'topobank/analysis/CardExpandButton.vue';
import TasksButton from 'topobank/analysis/TasksButton.vue';

import {formatExponential} from "topobank/utils/formatting";

const props = defineProps({
    apiUrl: {
        type: String,
        default: '/plugins/topobank_statistics/card/roughness-parameters'
    },
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
});

// Displayed data
const _analyses = ref(null);
const _columnDefs = ref([
    // Indicate that first column contains HTML
    // to have HTML tags removed for sorting/filtering
    {targets: 0, type: 'html'}
]);
const _columns = ref([
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
]);
const _dois = ref([]);
const _data = ref([]);

// GUI logic
const _sidebarVisible = ref(false);
const _title = ref("Roughness parameters");

// Current task status
let _nbRunningOrPending = 0;

onMounted(() => {
    updateCard();
});

const analysisIds = computed(() => {
    return _analyses.value.map(a => a.id).join();
});

function updateCard() {
    /* Fetch JSON describing the card */
    axios.get(`${props.apiUrl}/${props.functionId}?subjects=${props.subjects}`).then(response => {
        _analyses.value = response.data.analyses;
        /** replace null in value with NaN
         * This is needed because we cannot pass NaN through JSON without
         * extra libraries, so it is passed as null (workaround) */
        _data.value = response.data.tableData.map(x => {
            if (x['value'] === null) {
                x['value'] = NaN;
            }
            return x
        });
        _dois.value = response.data.dois;
    });
}

function taskStateChanged(nbRunningOrPending, nbSuccess, nbFailed) {
    if (nbRunningOrPending === 0 && _nbRunningOrPending > 0) {
        // All tasks finished, reload card
        updateCard();
    }
    _nbRunningOrPending = nbRunningOrPending;
}

</script>

<template>
    <div class="card search-result-card">
        <div class="card-header">
            <div class="btn-group btn-group-sm float-end">
                <tasks-button v-if="_analyses !== null && _analyses.length > 0"
                              :analyses="_analyses"
                              @task-state-changed="taskStateChanged">
                </tasks-button>
                <button v-if="_analyses !== null && _analyses.length > 0"
                        @click="updateCard"
                        class="btn btn-default float-end ms-1">
                    <i class="fa fa-redo"></i>
                </button>
                <card-expand-button v-if="!enlarged"
                                    :detail-url="detailUrl"
                                    :function-id="functionId"
                                    :subjects="subjects"
                                    class="btn-group btn-group-sm float-end">
                </card-expand-button>
            </div>
            <h5 v-if="_analyses === null"
                class="text-dark">
                {{ _title }}
            </h5>
            <a v-if="_analyses !== null && _analyses.length > 0"
               class="text-dark"
               href="#"
               @click="_sidebarVisible=true">
                <h5><i class="fa fa-bars"></i> {{ _title }}</h5>
            </a>
        </div>
        <div class="card-body">
            <div v-if="_analyses === null" class="tab-content">
                <span class="spinner"></span>
                <div>Please wait...</div>
            </div>

            <div v-if="_analyses !== null" class="tab-content">
                <div class="tab-pane show active" role="tabpanel" aria-label="Tab showing a plot">
                    <data-table class="table table-striped table-bordered"
                                :column-defs="_columnDefs"
                                :columns="_columns"
                                :data="_data"
                                responsive="yes"
                                scroll-x="yes">
                    </data-table>
                </div>
            </div>
        </div>
        <div v-if="_sidebarVisible"
             class="position-absolute h-100">
            <!-- card-header sets the margins identical to the card so the title appears at the same position -->
            <nav class="card-header navbar navbar-toggleable-xl bg-light flex-column align-items-start h-100">
                <ul class="flex-column navbar-nav">
                    <a class="text-dark"
                       href="#"
                       @click="_sidebarVisible=false">
                        <h5><i class="fa fa-bars"></i> {{ _title }}</h5>
                    </a>
                    <li class="nav-item mb-1 mt-1">
                        Download
                        <div class="btn-group ms-1" role="group" aria-label="Download formats">
                            <a :href="`/analysis/download/${analysisIds}/csv`"
                               class="btn btn-default"
                               @click="_sidebarVisible=false">
                                CSV
                            </a>
                            <a :href="`/analysis/download/${analysisIds}/xlsx`"
                               class="btn btn-default"
                               @click="_sidebarVisible=false">
                                XLSX
                            </a>
                        </div>
                    </li>
                    <li class="nav-item mb-1 mt-1">
                        <a href="#" data
                           data-toggle="modal"
                           :data-target="`#bibliography-modal-${uid}`"
                           class="btn btn-default w-100"
                           @click="_sidebarVisible=false">
                            Bibliography
                        </a>
                    </li>
                </ul>
            </nav>
        </div>
    </div>
    <bibliography-modal
        :id="`bibliography-modal-${uid}`"
        :dois="_dois">
    </bibliography-modal>
</template>
