<!--  Copyright 2021. Corning Incorporated. All rights reserved.-->

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
    <div class="container-fluid">
      <div>
        <div>
          <component :is="selectedComponent" :simId="currSimId"></component>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import SimulationMaps from "./SimulationMaps.vue";
import DataVisualization from "./DataVisualizations.vue";

export default {
  name: "Simulations",
  components: { SimulationMaps, DataVisualization },
  props: {
    overviewSimObj: Object,
  },

  watch: {
    overviewSimObj(simObj) {
      this.currSimId = simObj.runId;
    },
  },

  data() {
    return {
      selectedComponent: "simulation-maps",
      policyData: {},
      currSimId: "",
    };
  },

  created() {
    this.currSimId = this.overviewSimObj.runId;
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
  background-color: #ebeff2 !important;
  margin: 0 0 100px -15px;
  height: 100%;
}
#simLayout .container-fluid {
  padding: 0px !important;
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
