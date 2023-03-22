<script>

import {v4 as uuid4} from 'uuid';

import DataTable from 'datatables.net-vue3';
import DataTablesLib from 'datatables.net-bs4';

DataTable.use(DataTablesLib);

import BibliographyModal from 'topobank/analysis/BibliographyModal.vue';
import TasksButton from 'topobank/analysis/TasksButton.vue';

export default {
  name: 'roughness-parameters-card',
  components: {
    BibliographyModal,
    DataTable,
    TasksButton
  },
  props: {
    apiUrl: String,
    csrfToken: String,
    detailUrl: String,
    enlarged: {
      type: Boolean,
      default: false
    },
    functionId: Number,
    functionName: String,
    subjects: Object,
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
            return format_exponential(x, 5);
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
  methods: {
    updateCard() {
      /* Fetch JSON describing the card */
      fetch(this.apiUrl, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'X-CSRFToken': this.csrfToken
        },
        body: JSON.stringify({
          function_id: this.functionId,
          subjects: this.subjects
        })
      })
          .then(response => response.json())
          .then(data => {
            console.log(data);
            this.analyses = data.analyses;
            /** replace null in value with NaN
             * This is needed because we cannot pass NaN through JSON without
             * extra libraries, so it is passed as null (workaround) */
            this.data = data.tableData.map(x => {
              if (x['value'] === null) {
                console.log("replaced null");
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
        <div v-if="!enlarged" class="btn-group btn-group-sm float-right">
          <a :href="detailUrl" class="btn btn-default float-right">
            <i class="fa fa-expand"></i>
          </a>
        </div>
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
    <div :id="`sidebar-${uid}`" class="col-1 col-sm-6 p-0 collapse sidebar position-absolute h-100">
      <!-- card-header sets the margins identical to the card so the title appears at the same position -->
      <nav class="card-header navbar navbar-toggleable-xl bg-light flex-column align-items-start h-100">
        <ul class="flex-column navbar-nav">
          <a class="text-dark" href="#" data-toggle="collapse" :data-target="`#sidebar-${uid}`">
            <h5><i class="fa fa-bars"></i> {{ title }}</h5>
          </a>
          <li class="nav-item">
            Download
            <a :href="txtDownloadUrl">
              TXT
            </a>
            <a :href="xlsxDownloadUrl">
              XLSX
            </a>
            <a v-on:click="$refs.plot.download()">
              SVG
            </a>
          </li>
          <li class="nav-item">
            <a href="#" data-toggle="modal" :data-target="`#bibliography-modal-${uid}`">
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
