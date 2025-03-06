<script setup>

import axios from "axios";
import {computed, onMounted, ref} from "vue";

import {BDropdownDivider, BDropdownItem} from "bootstrap-vue-next";

import DataTable from 'datatables.net-vue3';
import DataTablesLib from 'datatables.net-bs5';

DataTable.use(DataTablesLib);

import {formatExponential} from "topobank/utils/formatting";

import AnalysisCard from "topobank/analysis/AnalysisCard.vue";
import {subjectsToBase64} from "topobank/utils/api";

const props = defineProps({
    apiUrl: {
        type: String,
        default: '/plugins/statistics/card/roughness-parameters'
    },
    detailUrl: {
        type: String,
        default: '/ui/analysis-detail/'
    },
    functionId: {
        type: Number,
        required: true
    },
    functionName: {
        type: String,
        required: true
    },
    subjects: {
        type: Object,
        required: true
    },
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
    {
        data: 'symbol',
        title: '<span title="Symbol according to ASME B46.1">Sym. 🛈</span>'
    },
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
const _title = "Roughness parameters";

onMounted(() => {
    updateCard();
});

const analysisIds = computed(() => {
    return _analyses.value.map(a => a.id).join();
});

function updateCard() {
    /* Fetch JSON describing the card */
    axios.get(`${props.apiUrl}/${props.functionId}?subjects=${subjectsToBase64(props.subjects)}`).then(response => {
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

</script>

<template>
    <AnalysisCard v-model:analyses="_analyses"
                  :detailUrl="detailUrl"
                  :dois="_dois"
                  :enlarged="enlarged"
                  :messages="_messages"
                  :functionId="functionId"
                  :subjects="subjects"
                  :showLoadingSpinner="_nbPendingAjaxRequests > 0"
                  :title="_title"
                  @allTasksFinished="updateCard"
                  @someTasksFinished="updateCard"
                  @refreshButtonClicked="updateCard">
        <template #dropdowns>
            <BDropdownDivider
                v-if="_analyses != null && _analyses.length > 0"></BDropdownDivider>
            <BDropdownItem v-for="analysis in _analyses"
                           :href="`/analysis/download/${analysisIds}/csv`">
                Download CSV
            </BDropdownItem>
            <BDropdownItem v-for="analysis in _analyses"
                           :href="`/analysis/download/${analysisIds}/xlsx`">
                Download XLSX
            </BDropdownItem>
        </template>
        <DataTable class="table table-striped table-bordered"
                   :column-defs="_columnDefs"
                   :columns="_columns"
                   :data="_data"
                   responsive="yes"
                   scroll-x="yes">
        </DataTable>
    </AnalysisCard>
</template>
