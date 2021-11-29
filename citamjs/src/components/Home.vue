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
  <div class="container-fluid">
    <div class="row">
      <div class="col-sm-2">
        <ul class="nav nav-tabs" id="my-tab" role="tablist">
          <li class="nav-item facility">
            <select v-model="selectedFacility" class="nav-link">
              <option v-for="(item, id) in facilities" :key="id">
                {{ item }}
              </option>
            </select>
          </li>
        </ul>
      </div>
      <div class="col-sm-10" style="margin-left: -30px">
        <ul class="nav nav-tabs" id="my-tab" role="tablist">
          <li class="nav-item facility">
            <select v-model="selectedFacility" class="nav-link">
              <option v-for="(item, id) in facilities" :key="id">
                {{ item }}
              </option>
            </select>
          </li>
          <li class="nav-item facility">
            <select v-model="selectedFacility" class="nav-link">
              <option v-for="(item, id) in facilities" :key="id">
                {{ item }}
              </option>
            </select>
          </li>
          <li class="nav-item">
            <a
              class="nav-link overviewTab active"
              id="overview-tab"
              data-toggle="tab"
              role="tab"
              aria-controls="profile"
              aria-selected="false"
              @click="setSelectedComponent('overview')"
              >Overview</a
            >
          </li>
          <li class="nav-item">
            <a
              class="nav-link simTab"
              id="sim-tab"
              data-toggle="tab"
              role="tab"
              aria-controls="profile"
              aria-selected="false"
              @click="setSelectedComponent('simulations')"
              >Visualizer</a
            >
          </li>
          <li class="nav-item">
            <a
              class="nav-link policyTab"
              data-toggle="tab"
              role="tab"
              aria-controls="profile"
              aria-selected="false"
              @click="setSelectedComponent('policies')"
              >Simulation Inputs</a
            >
          </li>
        </ul>
      </div>
    </div>
    <div class="row">
      <div class="col-sm-4" v-if="facilities.length > 0">
        <div class="input">Inputs</div>
        <policies :selectedFacility="selectedFacility" :polName="polName">
        </policies>
      </div>
      <div class="col-sm-8">
        <component
          :is="selectedComponent"
          @setFacilities="setFacilities($event)"
          :selectedFacility="selectedFacility"
          @showSims="showSimulations($event)"
          @showPolicy="showPolicyInfo($event)"
          :overviewSimObj="overviewSimObj"
          :polName="polName"
        >
        </component>
      </div>
    </div>
  </div>
</template>

<script>
import Simulations from "./simulations/Simulations.vue";
import Policies from "./Policies.vue";
import FloorPlans from "./FloorPlans.vue";
import Overview from "./Overview.vue";

export default {
  name: "Home",
  components: { Simulations, Policies, FloorPlans, Overview },
  data() {
    return {
      selectedComponent: "overview",
      facilities: [],
      selectedFacility: "",
      overviewSimObj: {},
      polName: "",
    };
  },
  created() {},
  methods: {
    setSelectedComponent(cmp) {
      this.overviewSimObj = {};
      this.polName = "";
      this.selectedComponent = cmp;
    },
    setFacilities(facilities) {
      if (!this.facilities.length > 0) {
        facilities.forEach((element) => {
          this.facilities.push(element.facilityName);
        });
        this.selectedFacility = this.facilities[0];
      }
    },
    showSimulations(simObj) {
      this.selectedComponent = "simulations";
      this.overviewSimObj = simObj;
      var current = document.getElementsByClassName("active");
      current[0].className = current[0].className.replace("active", "");
      var newTab = document.getElementsByClassName("simTab");
      newTab[0].className += " active";
    },
    showPolicyInfo(selectedPolicy) {
      this.selectedComponent = "policies";
      this.polName = selectedPolicy;
      var current = document.getElementsByClassName("active");
      current[0].className = current[0].className.replace("active", "");
      var newTab = document.getElementsByClassName("policyTab");
      newTab[0].className += " active";
    },
  },
};
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@600&display=swap");
.navbar {
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

.navbar-light {
  background-color: #f0f0f0;
}

.nav-tabs .nav-item {
  width: 170px;
  height: 50px;
  border-right: 1px solid black !important;
  background-color: #ebeff2;
}
.nav-tabs .nav-item.facility {
  width: 280px;
  text-align: left;
  height: 50px;
  background-color: #32404d;
}

.nav-tabs .nav-item.facility select {
  width: 130px;
  font-family: Inter;
  font-weight: 600;
  font-size: 16px;
  color: #ffffff;
  background-color: #32404d;
}

.nav-tabs .nav-link {
  color: #607080;
  font-family: Inter;
  font-weight: 600;
  font-size: 16px;
  border: none;
  cursor: pointer;
}
.nav-tabs .nav-link.active {
  color: #0080ff;
  background-color: #fff;
  font-family: Inter;
  font-weight: 600;
  font-size: 16px;
  height: 50px;
}

.nav-tabs .nav-link:hover {
  border: none;
}

*:focus {
  outline: none;
}

.footer {
  position: absolute;
  bottom: 0;
  width: 100%;
  height: 160px;
  line-height: 60px;
  background-color: #f0f0f0;
}

.flex-container {
  display: flex;
}

.flex-container > div {
  background-color: #c4c2c2;
  margin: 10px;
  padding: 20px;
  font-size: 20px;
  cursor: pointer;
}

.input {
  color: #607080;
  background-color: #98a6b3;
  height: 50px;
  padding: 10px;
  text-align: left;
}
</style>
