/**
 Copyright 2020. Corning Incorporated. All rights reserved.

 This software may only be used in accordance with the identified license(s).

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
 CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 CONNECTION WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
 ==========================================================================
**/

import * as d3 from 'd3';
import {select, event} from 'd3-selection';
import {zoom} from 'd3-zoom';
import {scaleSequential} from 'd3-scale';
import {Loader} from './utils/loader';
import {
  getBaseMap,
  getContact,
  getTrajectory,
  getContactPositionDist, getSummary,
} from './data_service';
import {Colorbar} from './utils/colorbar';
import {Timer} from './utils/timer';
import '../css/_basic_map.scss';

/**
 * 2D map visualization
 */
export default class Map2D {

  /**
   * @constructor
   * @param {Element} mapRoot - Root HTML Element to use as a container for the map
   */
  constructor(mapRoot) {
    this.mapRoot = mapRoot;


    /** Colorbar **/
    this.colorBar = new Colorbar({palette: d3.interpolateOrRd, scale: scaleSequential});
    this.mapRoot.append(this.colorBar.domElement);
    this.colorBar.hide();

    /** Timer **/
    this.timer = new Timer(1);
    this.mapRoot.append(this.timer.domElement);
    this.timer.hide();

    /** Handle for running animation set by window.setInterval */
    this.animationIntervalID = null;

    /** Actual animation update frequency */
    this.animationInterval = 10;

    /** Current animation frame */
    this.currentStep = 0;

    /** Color scale for contact data */
    // this.colorMap = d3.scaleLinear(d3.interpolateGreys);
    this.colorMap = scaleSequential(d3.interpolateOrRd);

    /** Loader element */
    this.loader = new Loader();

    /** Total Timesteps for the curret Simulation */
    this.totalSteps = 0;

    /** Simulation ID */
    this.simulation = null;

    /** Map Scale Factor - for size of annotations */
    this.scaleFactor = 1;

    /** Marker sizes */
    this.contactSize = 0.5;
    this.agentSize = 1.5;
  }

  /**
   * Change the loaded simulation
   *
   * @param {string} sim_id - Simulation Name
   */
  async setSimulation(sim_id) {
    this.simulation = sim_id;
    return this.reloadSimulation();
  }

  /**
   * Change the floor for the current simulation
   *
   * @param {string} floor - floor id
   */
  async setFloor(floor) {
    this.floor = floor;
    return this.reloadSimulation();
  }


  /**
   * Reload the configured simulation.  this should be done after changing
   * simulation_id or floor
   */
  async reloadSimulation() {
    this.stopAnimation();
    this.colorBar.hide();
    this.timer.hide();
    this.loader.show();

    select('#svg-map').remove();
    select('#svg-map').attr('transform', d3.zoomIdentity);

    /** Current animation frame */
    this.currentStep = 0;

    /* Set timestep length for timer */
    let summaryRequest = getSummary(this.simulation)
      .then(response => {
        this.timer.lengthOfStep = response.data['TimestepInSec'] || 1;
      });

    let contactsRequest = getContact(this.simulation, this.floor)
      .then(response => {
        this.contacts = response.data;
        this.loader.contactLoaded();
      });

    let trajectoriesRequest = getTrajectory(this.simulation, this.floor)
      .then(response => {
        this.trajectories = response.data.data;
        this.totalSteps = this.trajectories.length;
        let contactDomain = [0, response.data['statistics']['max_contacts']];
        this.colorMap.domain(contactDomain);
        this.colorBar.update(...contactDomain);
        this.loader.trajectoryLoaded();
      });

    let mapRequest = getBaseMap(this.simulation, this.floor)
      .then(response => {
        this._init_map(response.data);
        this.loader.mapLoaded();
      });

    let contactDist = getContactPositionDist(this.simulation, this.floor)
      .then(response => {
        this.contactPositionDist = response.data;
        this.loader.distributionsLoaded();
      });

    await Promise.all([
      summaryRequest,
      contactDist,
      contactsRequest,
      trajectoriesRequest,
      mapRequest,
    ]);

    this.loader.hide();
    this.timer.show();
    this.colorBar.show();
    this.startAnimation();
    return this;
  }

  /**
   * Starts the animation if stopped.
   */
  startAnimation() {
    this._resetInterval();
  }

  /**
   * Stops the animation
   */
  stopAnimation() {
    window.clearInterval(this.animationIntervalID);
    this.animationIntervalID = null;
  }

  /**
   * Restart Animation to the first frame
   */
  restartAnimation() {
    this.currentStep = 0;
    select('#svg-map')
      .select('g#contacts')
      .selectAll('circle')
      .remove();
    this.update();
  }

  /**
   * Set the animation speed
   *
   * @param {number} newSpeed
   */
  setSpeed(newSpeed) {
    this.animationInterval = (11 - newSpeed) * 5;
    this._resetInterval();
  }

  /**
   * Update the map with data from the current timestep
   */
  update() {
    this._updateTrajectories();
    this._updateContacts();
    this.timer.setStep(this.currentStep);
  }

  /**
   * Clean up all created and referenced elements and prepare to be deleted
   */
  destroy() {
    window.clearInterval(this.animationIntervalID);
    this.loader.destroy();
    this.timer.destroy();
    this.colorBar.destroy();
    while (this.mapRoot.firstChild) {
      this.mapRoot.removeChild(this.mapRoot.firstChild)
    }
  }

  /**
   * Initialize the map and SVG structure.
   *
   * @param mapData
   * @private
   */
  _init_map(mapData) {
    let domParser = new DOMParser();
    let newMap = domParser.parseFromString(mapData, 'image/svg+xml').firstChild;
    newMap.setAttribute('id', 'svg-map');
    this.mapRoot.insertAdjacentElement('afterbegin', newMap);
    let map = select('#svg-map');
    let drawLayer = map.select('#root');
    drawLayer.append("g").attr('id', 'trajectories');
    drawLayer.append("g").attr('id', 'contacts');
    map.call(zoom().on("zoom", () => this._handleZoom()));
  }

  /**
   * Update the map with current contacts
   * @private
   */
  _updateContacts() {
    // Bind new trajectory data
    let contactLayer = select('#svg-map').select("#root")
      .select('g#contacts');

    this.contacts[this.currentStep].forEach((contact) => {
      contactLayer.append('circle')
        .attr('r', this.contactSize * this.scaleFactor)
        .attr('cx', contact.x)
        .attr('cy', contact.y)
        .style('fill', '#FF0000');
    });
  }

  /**
   * Update the map with current trajectory and contact info
   * @private
   */
  _updateTrajectories() {
    // Bind new trajectory data
    let circle = select('#svg-map').select('#root')
      .select('g#trajectories')
      .selectAll('circle')
      .data(this.trajectories[this.currentStep]);

    // Remove missing trajectories
    circle.exit()
      .remove();

    // Add new trajectories
    circle.enter()
      .append("circle")
      .attr('r', this.agentSize * this.scaleFactor)
      .style('fill', '#000000');

    // update positions
    circle.transition()
      .duration(this.animationInterval)
      .attr('cx', d => d.x)
      .attr('cy', d => d.y)
      .attr('r', this.agentSize * this.scaleFactor)
      .style('stroke', 'black')
      .attr('stroke-width', this.agentSize * this.scaleFactor / 2)
      .style('fill', d => this.colorMap(d.count));
  }

  /**
   * Reinitialize the animation interval with the current settings
   * @private
   */
  _resetInterval() {
    window.clearInterval(this.animationIntervalID);
    this.animationIntervalID = setInterval(() => {
      this.currentStep++;
      if (this.currentStep >= this.trajectories.length) {
        this.restartAnimation();
      }
      this.update();
    }, this.animationInterval);
  }

  /** Handle zooming for synchronization between map and overlays (heatmap) */
  _handleZoom() {
    // Translate map
    select('#svg-map').select('#root').attr('transform', event.transform);
  }
}
