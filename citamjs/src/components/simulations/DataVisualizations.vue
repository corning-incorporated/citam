<!--  Copyright 2020. Corning Incorporated. All rights reserved.-->

<!--  This software may only be used in accordance with the licenses granted by-->
<!--  Corning Incorporated. All other uses as well as any copying, modification or-->
<!--  reverse engineering of the software is strictly prohibited.-->

<!--  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR-->
<!--  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,-->
<!--  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL-->
<!--  CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN-->
<!--  ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION-->
<!--  WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.-->
<!--  ==============================================================================-->
<template>
  <div id="vizLayout">
    <div class="card-body">
      <span v-if="chartData && chartData.length > 0">
        <scatterplot :pair-data="chartData"></scatterplot>
      </span>
    </div>
    <div class="card-body">
      <span v-if="totalContactsPerAgentHistogram && totalContactsPerAgentHistogram.length > 0 ">
        <histogram
          :pair-data="totalContactsPerAgentHistogram"
          :options="totalContactsHistogramOption"
        />
      </span>
    </div>
    <div class="card-body">
      <span
        v-if="avgContactDurationPerAgentHistogram && avgContactDurationPerAgentHistogram.length > 0">
        <histogram
          :pair-data="avgContactDurationPerAgentHistogram"
          :options="avgContactDurationHistogramOption"
        />
      </span>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import Scatterplot from "@/components/run/dataplots/Scatterplot";
import Histogram from "@/components/run/dataplots/Histogram";
import { library } from "@fortawesome/fontawesome-svg-core";
import {
  faChartBar,
  faChartArea,
  faTable,
  faArrowAltCircleLeft,
  faSort,
  faMap,
} from "@fortawesome/free-solid-svg-icons";
import _ from "lodash";

library.add(
  faChartBar,
  faChartArea,
  faTable,
  faArrowAltCircleLeft,
  faSort,
  faMap
);

export default {
  name: "DataVisualization",
  components: { Scatterplot, Histogram },
  props: {
    simId: String,
    selectedFacility: String,
  },
  watch: {
    simId(selectedSimId) {
      this.simId = selectedSimId;
      this.getPairContacts(this.simId);
    },
  },

  data() {
    return {
      policyData: {},
      simRuns: [],
      chartData: [],
      currSimId: '',
      totalContactsPerAgentHistogram: [],
      avgContactDurationPerAgentHistogram: [],
      totalContactsHistogramOption: {},
      avgContactDurationHistogramOption: {},
    };
  },

  created() {
    this.currSimId = this.simId;
    this.getPairContacts(this.currSimId);
  },

  methods: {
    getSimMap(simId) {
      this.currSimId = simId;
      this.getPairContacts(this.currSimId);
    },

    /**
     * Get Contacts data between two agents
     * @param simId
     * @param cb
     */
    getPairContacts(simId, cb) {
      axios
        .get(`/${simId}/pair`)
        .then((response) => {
          this.chartData = _.map(
            _.union(
              _.map(response.data, "Agent1"),
              _.map(response.data, "Agent2")
            ),
            (agent) => {
              let agentGrp = _.filter(response.data, (f) => {
                return f.Agent1 === agent || f.Agent2 === agent;
              });
              let totalContactsPerAgent = _.sumBy(agentGrp, "N_Contacts");
              let avgContactDurationPerAgent = (
                _.sumBy(agentGrp, (o) => {
                  return parseFloat(o.TotalContactDuration);
                }) / totalContactsPerAgent
              ).toPrecision(2);
              return {
                a: agent,
                x: totalContactsPerAgent,
                y: avgContactDurationPerAgent,
              };
            }
          );

          this.totalContactsPerAgentHistogram = _.map(this.chartData, "x");
          this.totalContactsHistogramOption = {
            chartTitle: "Total Contact per Agent",
            chartCol: "#5290f1",
          };
          this.avgContactDurationPerAgentHistogram = _.map(this.chartData, "y");
          this.avgContactDurationHistogramOption = {
            chartTitle: "Average Contact Duration (minutes)",
            chartCol: "#5fd0c7",
          };
          cb();
        })
        .catch(function(error) {
          console.log(error);
        });
    },
  },
};
</script>

<style scoped>
#vizLayout {
  text-align: left !important;
  padding-top: 25px;
  background-color: white;
}
</style>
