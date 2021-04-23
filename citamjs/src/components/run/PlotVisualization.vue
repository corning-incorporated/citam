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
import { getBaseMap, getTrajectory, getSummary } from "@/script/data_service";

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
  watch: {
    simId(selectedSimId) {
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
    this.mapInstance.destroy();
    this.gui.destroy();
  },
  created() {
    this.showSimulationMap();
  },

  methods: {
    getSimulationData() {
      getSummary(this.simId).then((response) => {
        this.floorOptions = response.data.floors.map((x) => x.name);
        this.nAgents = response.data.NumberOfAgents;
        this.$store.commit("setNumberOfAgents", this.nAgents);
        this.totalSteps = response.data.TotalTimesteps;
        this.$store.commit("setTotalSteps", this.totalSteps);
        this.scaleMultiplier = response.data.scaleMultiplier;
        this.$store.commit("setScaleMultiplier", this.scaleMultiplier);
        getBaseMap(this.simId, this.floor).then((map) => {
          this.mapData = map;
          this.$store.commit("setMapData", map);
        });
        this.getTrajectoryData();
      });
    },

    async getTrajectoryData() {
      this.trajectories = [];
      let max_chunk_size = Math.ceil(1e8 / this.nAgents);
      let request_arr = [],
        first_timestep = 0,
        max_contacts = 0;

      while (first_timestep < this.totalSteps) {
        request_arr.push(
          getTrajectory(this.simId, this.floor, first_timestep, max_chunk_size)
        );
        first_timestep += max_chunk_size;
      }
      await Promise.all(request_arr).then((response) => {
        if (response !== undefined) {
          response.forEach((chunk) => {
            this.trajectories = this.trajectories.concat(chunk.data.data);
            max_contacts = Math.max(max_contacts, chunk.data.max_count);
          });
          this.$store.commit("setTrajectoryData", this.trajectories);
          this.createMapInstance();
          this.$store.commit("setIsLoadingData", false);
        }
      });
      this.totalSteps = this.trajectories.length;
      this.$store.commit("setTrajectoryData", this.trajectories);
    },

    showSimulationMap() {
      if (
        this.$store.state.trajectoryData === null &&
        !this.$store.state.isLoadingData
      ) {
        this.$store.commit("setIsLoadingData", true);
        this.getSimulationData();
      } else if (this.$store.state.trajectoryData !== null) {
        this.createMapInstance();
      }
    },

    createMapInstance() {
      let animationParams = {};
      let GUI, timestepSlider;
      let mapRoot = this.$refs.mapRoot;
      let mapInstance = (this.mapInstance = new Map2D(
        mapRoot,
        this.$store.state.mapData,
        this.$store.state.nAgents,
        this.$store.state.totalSteps,
        this.$store.state.trajectoryData
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

      animationParams.floorOptions = this.floorOptions;
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
