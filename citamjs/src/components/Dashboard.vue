<!--
 Copyright 2020. Corning Incorporated. All rights reserved.

 This software may only be used in accordance with the identified license(s).

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
 CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 CONNECTION WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
 ==========================================================================
-->


<template>
  <div>
    <nav class="topnav navbar navbar-expand navbar-dark bg-dark">
      <span class="navbar-brand">Dashboard</span>
    </nav>
    <div id="layout-sidenav">
      <div id="layout-sidenav-content">
        <main>
          <div class="container-fluid">
            <div class="row page-heading">
              <div class="col-5">
                <button
                  v-show="showDetails !== 0"
                  class="btn btn-link order-1 order-lg-0"
                  id="back-main"
                  @click="backToMainTable"
                >
                  <font-awesome-icon
                    icon="arrow-alt-circle-left"
                  ></font-awesome-icon>
                  Back
                </button>
              </div>
              <div class="col-auto">
                <div v-if="showDetails === 0">Dashboard</div>
                <div v-else>
                  <ul class="nav nav-tabs" id="my-tab" role="tablist">
                    <li class="nav-item">
                      <a
                        class="nav-link active"
                        id="summary-tab"
                        data-toggle="tab"
                        href=""
                        role="tab"
                        aria-controls="home"
                        aria-selected="true"
                        @click="toVizToggle($event)"
                        >Summary</a
                      >
                    </li>
                    <li class="nav-item">
                      <a
                        class="nav-link"
                        id="viz-tab"
                        data-toggle="tab"
                        role="tab"
                        href=""
                        aria-controls="profile"
                        aria-selected="false"
                        @click="toVizToggle($event)"
                        >Visualization</a
                      >
                    </li>
                  </ul>
                </div>
              </div>
            </div>
            <div class="row" id="main-data-table" v-show="showDetails === 0">
              <div class="card mb-4">
                <div class="card-header">
                  <font-awesome-icon icon="table" />
                  Simulation Table
                </div>
                <div class="card-body">
                  <div class="table-responsive">
                    <table class="table table-bordered" id="data-table">
                      <thead>
                        <tr>
                          <th>Plots</th>
                          <th v-for="att in runAttributes" :key="att">
                            <div class="th-container">
                              {{ att }}
                              <span class="sort-right"
                                ><button
                                  class="btn btn-sm btn-link"
                                  @click="sortTable(att)"
                                >
                                  <font-awesome-icon icon="sort" />
                                </button>
                              </span>
                            </div>
                          </th>
                        </tr>
                      </thead>

                      <tbody>
                        <tr
                          v-for="run in runList"
                          :key="run.sim_id"
                          :id="run.sim_id"
                        >
                          <td>
                            <button
                              type="button"
                              class="btn btn-link"
                              @click="viewPlot(run.sim_id)"
                            >
                              View Details
                            </button>
                          </td>
                          <td
                            v-for="att in runAttributes"
                            :key="run.SimulationName + att"
                            :id="run.SimulationName + att"
                          >
                            {{ run[att] }}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
            <div id="details-view" v-if="showDetails === 1">
              <!--  Summary Cards -->
              <statcards v-if="currSimId" :simid="currSimId"></statcards>
              <div class="row">
                <div class="col-xl-6">
                  <div class="card mb-4">
                    <div class="card-header">
                      <font-awesome-icon icon="chart-area" />
                      Contact Scatterplot
                    </div>
                    <div class="card-body">
                      <span v-if="chartData && chartData.length > 0">
                        <scatterplot :pair-data="chartData"> </scatterplot>
                      </span>
                    </div>
                  </div>
                </div>
                <div class="col-xl-6">
                  <div class="card mb-4">
                    <div class="card-header">
                      <font-awesome-icon icon="chart-bar" />
                      Total Contact Per Agent Histogram
                    </div>
                    <div class="card-body">
                      <span
                        v-if="
                          totalContactsPerAgentHistogram &&
                          totalContactsPerAgentHistogram.length > 0
                        "
                      >
                        <histogram
                          :pair-data="totalContactsPerAgentHistogram"
                          :options="totalContactsHistogramOption"
                        />
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <div class="card mb-4">
                <div class="card-header">
                  <font-awesome-icon icon="chart-bar" />
                  Average Contact Duration Histogram
                </div>
                <div class="card-body">
                  <span
                    v-if="
                      avgContactDurationPerAgentHistogram &&
                      avgContactDurationPerAgentHistogram.length > 0
                    "
                  >
                    <histogram
                      :pair-data="avgContactDurationPerAgentHistogram"
                      :options="avgContactDurationHistogramOption"
                    />
                  </span>
                </div>
              </div>
              <div class="card mb-4">
                <div class="card-header">
                  <font-awesome-icon icon="map" />
                  Heatmap
                </div>
                <div class="card-body">
                  <canvas style="width: 100%" ref="canvas" />
                </div>
              </div>
            </div>
            <div id="viz-view" v-if="showDetails === 2">
              <plot-visualization :simid="currSimId"></plot-visualization>
            </div>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<script>


import axios from 'axios'
import PlotVisualization from '@/components/run/PlotVisualization.vue'
import Scatterplot from '@/components/run/dataplots/Scatterplot';
import Histogram from "@/components/run/dataplots/Histogram";
import Statcards from "@/components/run/dataplots/Statcards";
import {library} from '@fortawesome/fontawesome-svg-core'
import {faChartBar, faChartArea, faTable, faArrowAltCircleLeft, faSort, faMap} from '@fortawesome/free-solid-svg-icons'
import _ from "lodash";

library.add(faChartBar, faChartArea, faTable, faArrowAltCircleLeft, faSort, faMap)

export default {
  name: "Dashboard",
  components: {Scatterplot, Histogram, Statcards, PlotVisualization},
  data() {
    return {
      runList: [],
      listData: [],
      runAttributes: [],
      showDetails: 0,
      showViz: false,
      currSimId: '',
      chartData: [],
      heatmapSrc: '',
      totalContactsPerAgentHistogram: [],
      avgContactDurationPerAgentHistogram: [],
      totalContactsHistogramOption: {},
      avgContactDurationHistogramOption: {},
    }
  },
  created() {
    axios.get('/list')
        .then((response) => {
          return axios.all(response.data.map(x => axios.get(`/${x.sim_id}`)))
        })
        .then((runResponse) => {
          // eslint-disable-next-line no-unused-vars
          this.runList = runResponse.map(run => run.data).map(({floors, timestep, floor_dict, scaleMultiplier, trajectory_file,
                                                                 ...item
                                                               }) => item)
          this.runAttributes = Object.keys(this.runList[0]);
        })
  },
  methods: {

    /**
     * Trigger view details
     * @param simId
     */
    viewPlot(simId) {
      this.currSimId = simId;
      this.getPairContacts(simId, () => {
        this.getHeatmap(simId);
        return this.showDetails = 1
      })
    },

    backToMainTable() {
      this.showDetails = 0;
    },

    sortTable(att) {
      this.runList = _.sortBy(this.runList, [att]);
    },

    toVizToggle(e){
      this.showDetails = e.target.id === 'viz-tab'? 2 : 1;
    },

    /**
     * Get Heatmap data
     * @param simId
     */
    getHeatmap(simId){
      this.heatmapSrc = '';
      axios.get(`/${simId}/heatmap`)
          .then(response=> {
            if(response.data){
              this.heatmapSrc = response.data;
              const canvas = this.$refs.canvas;
              const ctx = canvas.getContext('2d');
              const DOMURL = window.URL || window.webkitURL || window;
              const img = new Image();
              const svgBlob = new Blob([this.heatmapSrc], {type: 'image/svg+xml;charset=utf-8'});
              const url = DOMURL.createObjectURL(svgBlob);
              img.onload = () => {
                ctx.drawImage(img, 0, 0);
              };
              img.src = url;
            }
          }). catch(error => {
            console.error(error)
      })
    },

    /**
     * Get Contacts data between two agents
     * @param simId
     * @param cb
     */
    getPairContacts(simId, cb) {
      axios.get(`/${simId}/pair`)
          .then(response => {
            this.chartData = _.map(_.union(_.map(response.data, 'Agent1'), _.map(response.data, 'Agent2')), (agent) => {
              let agentGrp = _.filter(response.data, (f) => {
                return f.Agent1 === agent || f.Agent2 === agent
              })
              let totalContactsPerAgent = _.sumBy(agentGrp, 'N_Contacts')
              let avgContactDurationPerAgent = (_.sumBy(agentGrp, (o) => {
                return parseFloat(o.TotalContactDuration)
              }) / totalContactsPerAgent).toPrecision(2)
              return {a: agent, x: totalContactsPerAgent, y: avgContactDurationPerAgent}
            })

            this.totalContactsPerAgentHistogram = _.map(this.chartData, 'x')
            this.totalContactsHistogramOption = {chartTitle: "Total Contact per Agent", chartCol: "#5290f1"}
            this.avgContactDurationPerAgentHistogram = _.map(this.chartData, 'y')
            this.avgContactDurationHistogramOption = {
              chartTitle: "Average Contact Duration (minutes)",
              chartCol: "#5fd0c7"
            }
            cb();
          })
    },
  },
}
</script>

<style scoped>
.page-heading {
  font-size: x-large;
  font-weight: bold;
  text-align: left;
  margin: 0.4rem 0;
}

.th-container {
  height: 100%;
  vertical-align: middle;
  text-align: center;
  display: flex;
  align-items: center;
}

.sort-right {
  display: flex;
  flex-direction: column;
  justify-content: center;
}
</style>
