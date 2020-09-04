  // Copyright 2020. Corning Incorporated. All rights reserved.
  //
  // This software may only be used in accordance with the licenses granted by
  // Corning Incorporated. All other uses as well as any copying, modification or
  // reverse engineering of the software is strictly prohibited.
  //
  // THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  // IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  // FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
  // CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
  // ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
  // WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
  // ==============================================================================

import axios from 'axios';
import Map2D from './basic_map';
import * as dat from 'dat.gui';
import {getSummary} from './data_service';

/**
 * Base URL for the CITAM Results API
 * TODO: Update this when the API is deployed
 *
 * @type {string}
 */
axios.defaults.baseURL = '/v1';

const HTML_ROOT = `
  <div id="app" style="position: relative">
    <div id="map"></div>
  </div>
`;

// Create a document element for the map
const domRoot = document.createElement('div');
document.body.append(domRoot);
domRoot.outerHTML = HTML_ROOT;

const mapRoot = document.getElementById('map');

let simulation_ids = [];
let animationParams = {};
let GUI, timestepSlider;

function init() {
  /** Create map instance */
  let mapInstance = new Map2D(mapRoot);

  axios.get('/list')
    .then(response => simulation_ids = response.data)
    .then(() => {
      /** Control Panel Parameters */
      animationParams = {
        simulation: simulation_ids[0],
        startAnimation: () => mapInstance.startAnimation(),
        stopAnimation: () => mapInstance.stopAnimation(),
        animationSpeed: 10,
        floorOptions: ["1"],
        floor: "1",
      };
      /** Create Control Panel */
      GUI = new dat.GUI();
      GUI.add(animationParams, 'simulation', simulation_ids)
        .name('Simulation')
        .onChange(value => {
          getSummary(value).then((response) => {
            animationParams.floorOptions = response.data.floors.map(x => x.name);
            animationParams.floor = animationParams.floorOptions[0];
            guiFloorWidget = guiFloorWidget.options(animationParams.floorOptions)
              .name('Floor')
              .onChange(value => mapInstance.setFloor(value));
            mapInstance.scaleFactor = response.data.scaleMultiplier || 1;
            console.log('scale_multiplier', response.data.scaleMultiplier);
            console.log('scaleFactor', mapInstance.scaleFactor);
            mapInstance.setSimulation(value).then(() => {
              timestepSlider.min(0);
              timestepSlider.max(mapInstance.totalSteps);
            });
          });
        });

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

      /** Load floor list */
      getSummary(animationParams.simulation)
        .then((response) => {
          animationParams.floorOptions = response.data.floors.map(x => x.name);
          animationParams.floor = animationParams.floorOptions[0];
          guiFloorWidget = guiFloorWidget.options(animationParams.floorOptions)
            .name('Floor')
            .onChange(value => mapInstance.setFloor(value));

          mapInstance.scaleFactor = response.data.scaleMultiplier || 1;
          /** Load first simulation */
          mapInstance.setSimulation(animationParams.simulation).then(() => {
            timestepSlider.min(0);
            timestepSlider.max(mapInstance.totalSteps);
          });
        });
    });
}

/** Call init when page has loaded */
window.onload = init;
