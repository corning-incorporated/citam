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
  <div id="app" style="position: relative">
    <div id="controls" ref="controls"></div>
    <div id="map" ref="mapRoot"></div>
  </div>
</template>

<script>
import Map2D from "../../script/basic_map";
import * as dat from "dat.gui";
import { mapState } from "vuex";

export default {
  name: "PlotVisualization",
  props: ["simId"],
  data() {
    return {
      mapInstance: null,
      gui: null,
      newSimId: false,
      trajectories: null,
      nAgents: null,
      totalSteps: null,
      isLoadingData: null,
    };
  },
  computed: mapState(["mapData", "status"]),

  watch: {
    status(newValue, oldValue) {
      if (oldValue === "fetchingData" && newValue === "ready") {
        this.mapInstance.setTrajectoryData(this.$store.state.trajectoryData);
        this.mapInstance.hideLoader();
        this.mapInstance.startAnimation();
      }
    },
    mapData() {
      this.createMapInstance();
      this.mapInstance.loader.show();
      this.mapInstance.loader.mapLoaded();
      let expectedDuration = this.computeEstimatedLoadTime();
      this.mapInstance.loader.startCountdown(expectedDuration);
    },
    simId(selectedSimId) {
      console.log("We have a new simulation ID", selectedSimId);
      this.simId = selectedSimId;
      this.gui = null;
      this.mapInstance = null;
      this.newSimId = true;
      this.mapData = null;
      this.floor = 0;
      this.showSimulationMap();
    },
  },
  beforeDestroy() {
    if (this.mapInstance !== null) {
      if (this.$store.state.trajectoryData !== null) {
        this.$store.commit("setCurrentStep", this.mapInstance.currentStep);
      }
      this.mapInstance.destroy();
    }
    if (this.gui !== null) {
      this.gui.destroy();
    }
  },
  mounted() {
    this.showSimulationMap();
  },

  methods: {
    showSimulationMap() {
      if (
        this.$store.state.trajectoryData === null &&
        (this.$store.state.status === "ready" ||
          this.$store.state.status === null)
      ) {
        this.$store.commit("setSimulationID", this.simId);
        this.$store.dispatch("fetchSimulationData");
      } else if (this.$store.state.trajectoryData !== null) {
        this.createMapInstance();
        this.mapInstance.setTrajectoryData(this.$store.state.trajectoryData);
        this.mapInstance.setCurrentStep(this.$store.state.currentStep);
        this.mapInstance.startAnimation();
      } else if (this.$store.state.status === "fetchingData") {
        if (this.$store.state.mapData !== null) {
          this.createMapInstance();
          this.mapInstance.loader.show();
          this.mapInstance.loader.mapLoaded();
          let expectedDuration = this.computeEstimatedLoadTime();
          let currentTime = new Date().getTime() / 1000;
          let elapsedTime = currentTime - this.$store.state.fetchingStartTime;
          this.mapInstance.loader.startCountdown(
            expectedDuration - elapsedTime
          );
        }
      }
    },

    computeEstimatedLoadTime() {
      // The factor of 160,000 is based on observations and used here for a
      // rough estimate of how long it will take to process the trajectory
      // data based on number of agents and total steps.
      return (
        (this.$store.state.totalSteps * this.$store.state.nAgents) / 160000
      );
    },

    createMapInstance() {
      let animationParams = {};
      let GUI, timestepSlider;
      let mapRoot = this.$refs.mapRoot;
      let mapInstance = (this.mapInstance = new Map2D(
        mapRoot,
        this.$store.state.mapData,
        this.$store.state.nAgents,
        this.$store.state.totalSteps
      ));

      /** Control Panel Parameters */
      animationParams = {
        startAnimation: () => mapInstance.startAnimation(),
        stopAnimation: () => mapInstance.stopAnimation(),
        animationSpeed: 10,
        floorOptions: ["1"],
        floor: "1",
      };
      /** Create Control Panel */
      this.gui = GUI = new dat.GUI({ autoPlace: false });
      if (this.newSimId) {
        while (this.$refs.controls.hasChildNodes()) {
          this.$refs.controls.removeChild(this.$refs.controls.firstChild);
        }
        this.$refs.controls.appendChild(this.gui.domElement);
      } else {
        this.$refs.controls.appendChild(this.gui.domElement);
      }

      let guiFloorWidget = GUI.add(
        animationParams,
        "floor",
        animationParams.floorOptions
      )
        .name("Floor")
        .onChange((value) => {
          mapInstance.setFloor(value);
          this.floor = value;
        });

      GUI.add(animationParams, "animationSpeed", 1, 300)
        .name("Speed (fps)")
        .step(1)
        .onChange((value) => mapInstance.setSpeed(value));

      GUI.add(animationParams, "startAnimation").name("Start");

      GUI.add(animationParams, "stopAnimation").name("Stop");

      timestepSlider = GUI.add(mapInstance, "currentStep")
        .name("Timestep")
        .min(0)
        .max(mapInstance.totalSteps)
        .step(1)
        .onChange(() => mapInstance.update())
        .listen();

      animationParams.floorOptions = this.$store.state.floorOptions;
      animationParams.floor = animationParams.floorOptions[0];
      mapInstance.floor = animationParams.floor;

      guiFloorWidget
        .options(animationParams.floorOptions)
        .name("Floor")
        .onChange((value) => mapInstance.setFloor(value));

      mapInstance.scaleFactor = this.$store.state.scaleMultiplier || 1;
      timestepSlider.max(this.$store.state.totalSteps);
    },
  },
};
</script>

<style scoped>
#controls {
  position: absolute;
  right: 0px;
  top: 0px;
}
#map {
  background-color: white;
}
</style>
