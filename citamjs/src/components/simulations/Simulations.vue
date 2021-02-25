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
  <div id="simLayout">
    <div id="title">
      <span>Simulations</span>Individual simulation maps per policy, run, and
      floor. Data visualization per simulation run.
    </div>
    <div class="container-fluid">
      <div class="row header">
        <div class="col-sm-2 policy">
          <div class="policyBtn">
            <button type="button" class="btn btn-link">Add Policy</button>
          </div>
          <policy-list
            :policyData="policyData"
            v-model="policyData"
            @getSimMap="getSimMap($event)"
          ></policy-list>
        </div>
        <div class="col-sm-10">
          <ul class="nav nav-tabs">
            <li class="nav-item">
              <a
                class="nav-link simMaps active"
                data-toggle="tab"
                @click="setSelectedComponent('simulation-maps')"
                >Simulation Maps</a
              >
            </li>
            <li class="nav-item">
              <a
                class="nav-link dataViz"
                data-toggle="tab"
                @click="setSelectedComponent('data-visualization')"
                >Data Visualizations</a
              >
            </li>
          </ul>
          <div>
            <component :is="selectedComponent" :simId="currSimId"></component>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import PolicyList from "../PolicyList.vue";
import SimulationMaps from "./SimulationMaps.vue";
import DataVisualization from "./DataVisualizations.vue";
import _ from "lodash";

export default {
  name: "Simulations",
  components: { PolicyList, SimulationMaps, DataVisualization },

  props: {
    selectedFacility: String,
    overviewSimObj: Object,
  },
  data() {
    return {
      selectedComponent: "simulation-maps",
      policyData: {},
      currSimId: "",
      selectedPolicy: "",
      selectedSim: "",
    };
  },
  watch: {
    selectedFacility(newFacility) {
      this.policyData = {
        policies: this.$store.state.facilities.find(
          (item) => item.facilityName == newFacility
        ).policies,
      };
      this.currSimId = this.policyData.policies[0].simulationRuns[0].simName;
    },
  },
  created() {
    this.policyData = {
      policies: this.$store.state.facilities.find(
        (item) => item.facilityName == this.selectedFacility
      ).policies,
    };
    if (_.isEmpty(this.overviewSimObj)) {
      this.currSimId = this.policyData.policies[0].simulationRuns[0].simName;
    } else {
      this.currSimId = this.overviewSimObj.simId;
      this.policyData.selectedPolicy = this.overviewSimObj.policyName;
      this.policyData.selectedSim = this.overviewSimObj.simId;
      this.selectedComponent =
        this.overviewSimObj.type == "simMaps"
          ? "simulation-maps"
          : "data-visualization";
    }
  },
  mounted() {
    // wait till Simulations component is loaded and update the DOM element
    this.$nextTick(function () {
      if (this.overviewSimObj.type == "dataViz") {
        var simTab = document.getElementsByClassName("simMaps");
        simTab[0].className = simTab[0].className.replace("active", "");
        var dataTab = document.getElementsByClassName("dataViz");
        dataTab[0].className += " active";
      }
    });
  },
  methods: {
    setSelectedComponent(cmp) {
      this.selectedComponent = cmp;
    },
    getSimMap(simId) {
      this.currSimId = simId;
    },
  },
};
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@600&display=swap");
#title {
  font-family: Inter;
  text-align: left;
  padding: 10px;
  color: #607080;
}
#title span {
  color: black !important;
  font-family: Inter;
  font-weight: 600;
  font-size: 16px;
  margin: 0px 10px 0px 5px;
  padding: 10px 0 10px 0;
}
#simLayout {
  background-color: #ffff;
  margin-bottom: 100px;
}
.navbar {
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

.navbar-light {
  background-color: #f0f0f0;
}

.nav-tabs {
  border-bottom: none !important;
  background-color: #ebeff2;
}

.nav-tabs .nav-item {
  width: 200px;
  height: 50px;
  background-color: #ebeff2;
}
.nav-tabs .nav-item.policy {
  width: 250px;
  text-align: left;
  height: 50px;
  background-color: #32404d;
}

.nav-tabs .nav-item.policy a {
  font-family: Inter;
  font-style: normal;
  font-weight: 600;
  font-size: 16px;
  color: #ffffff;
  background-color: #32404d;
}

.nav-tabs .nav-link {
  color: #607080;
  font-family: Inter;
  font-style: normal;
  font-weight: 600;
  font-size: 16px;
  border: none;
  cursor: pointer;
}
.nav-tabs .nav-link.active {
  color: #0080ff;
  background-color: #fff;
  font-family: Inter;
  font-style: normal;
  font-weight: 600;
  font-size: 16px;
  height: 45px;
  margin-top: 5px;
}

.nav-tabs .nav-link:hover {
  border: none;
}
.header {
  background: #ebeff2;
}

#simLayout .col-sm-2,
.col-sm-10 {
  text-align: left;
  background-color: white;
  padding-right: 0px !important;
  padding-left: 0px !important;
}

.policyBtn {
  font-family: Inter;
  font-weight: bold;
  color: #0080ff;
  background-color: #ebeff2 !important;
  height: 50px;
}

.btn-link:hover {
  text-decoration: none !important;
  color: #007bff;
}
</style>
