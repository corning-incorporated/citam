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
  <div id="app" style="position: relative">
    <div id="controls" ref="controls"></div>
    <div id="map" ref="mapRoot"></div>
  </div>
</template>

<script>
import Map2D from '../../script/basic_map';
import * as dat from 'dat.gui';
import {getSummary} from '@/script/data_service';

export default {
  name: "PlotVisualization",
  props: ['simId'],
  data() {
    return {
      mapInstance: null,
      gui: null,
      newSimId: false    
    }
  },
  watch: {
    simId(selectedSimId) {
      this.simId = selectedSimId      
      this.gui = null
      this.mapInstance = null
      this.newSimId = true
      this.showSimulationMap()
    }
  },
  beforeDestroy() {
    this.mapInstance.destroy();
    this.gui.destroy()
  },
  mounted() {
    this.showSimulationMap()
  },

  methods: {
    showSimulationMap() {   
        let animationParams = {};
        let GUI, timestepSlider;
        let mapRoot = this.$refs.mapRoot;
        let mapInstance = this.mapInstance = new Map2D(mapRoot);

    /** Control Panel Parameters */
    animationParams = {
      startAnimation: () => mapInstance.startAnimation(),
      stopAnimation: () => mapInstance.stopAnimation(),
      animationSpeed: 10,
      floorOptions: ["1"],
      floor: "1",
    };
    /** Create Control Panel */
    this.gui = GUI = new dat.GUI({autoPlace: false});
    if(this.newSimId){
      while(this.$refs.controls.hasChildNodes()){
        this.$refs.controls.removeChild(this.$refs.controls.firstChild)
      }
      this.$refs.controls.appendChild(this.gui.domElement);
    }
    else {
      this.$refs.controls.appendChild(this.gui.domElement);
    }    

    let guiFloorWidget = GUI.add(animationParams, 'floor', animationParams.floorOptions)
        .name('Floor')
        .onChange(value => mapInstance.setFloor(value));

    GUI.add(animationParams, 'animationSpeed', 1, 10)
        .name('Speed')
        .step(1)
        .onChange(value => mapInstance.setSpeed(value));

    GUI.add(animationParams, 'startAnimation')
        .name('Start');

    GUI.add(animationParams, 'stopAnimation')
        .name('Stop');

    timestepSlider = GUI.add(mapInstance, 'currentStep')
        .name('Timestep')
        .min(0)
        .max(3600)
        .step(1)
        .onChange(() => mapInstance.update())
        .listen();
      

      getSummary(this.simId).then((response) => {
        animationParams.floorOptions = response.data.floors.map(x => x.name);
        animationParams.floor = animationParams.floorOptions[0];
        mapInstance.floor = animationParams.floor;

        guiFloorWidget = guiFloorWidget.options(animationParams.floorOptions)
            .name('Floor')
            .onChange(value => mapInstance.setFloor(value));

        mapInstance.scaleFactor = response.data.scaleMultiplier || 1;

        mapInstance.setSimulation(this.simId).then(() => {
          timestepSlider.min(0);
          timestepSlider.max(mapInstance.totalSteps);
        });
      });
    }
  }
}
</script>

<style scoped>
#controls {
  position: absolute;
  right: 0px;
  top: 0px;
}

</style>
