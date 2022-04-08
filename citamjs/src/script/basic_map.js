/**
 Copyright 2021. Corning Incorporated. All rights reserved.

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
import { select, event } from 'd3-selection';
import { zoom } from 'd3-zoom';
import { scaleSequential } from 'd3-scale';
import { Loader } from './utils/loader';
import { Timer } from './utils/timer';
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

        /** Loader Element */
        this.loader = new Loader(this.mapRoot);
        this.loader.hide();

        /** Color scale for contact data */
        this.colorMap = scaleSequential(d3.interpolateOrRd);

        /** Simulation Details */
        this.simulation = null;

        /** Map Scale Factor - for size of annotations */
        this.scaleFactor = 1;

        /** Marker sizes */
        this.contactSize = 0.5;
        this.agentSize = 1.5;

    }

    setTotalSteps(totalSteps) {
        /** Total Timesteps for the current Simulation */
        this.totalSteps = totalSteps;
    }

    setNumberOfAgents(nAgents) {
        /** Number of agents in current simulation */
        this.nAgents = nAgents;
    }

    setMapData(mapData) {
        this._init_map(mapData);
    }

    setTrajectoryData(trajData) {
        this.trajectories = trajData;
    }

    showError(message) {
        this.loader.showError(message);
    }

    showLoader() {
        this.loader.show();

    }

    hideLoader() {
        this.loader.hide()
    }

    showTimer() {
        this.timer.show()
    }

    hideTimer() {
        this.timer.hide()
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
        select('#svg-map').remove();
        select('#svg-map').attr('transform', d3.zoomIdentity);

        /** Current animation frame */
        this.currentStep = 0;
        return this;
    }

    /**
     * Starts the animation if stopped.
     */
    startAnimation() {
        this._resetInterval();
    }

    setCurrentStep(step) {
        this.currentStep = step;
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
        // 1000 ms divided by the number of frames per second to get duration
        // per frame in seconds (or how often to update the animation).
        this.animationInterval = 1000 / newSpeed;
        this._resetInterval();
    }

    /**
     * Update the map with data from the current timestep
     */
    update() {
        this._updateTrajectories();
        this.timer.setStep(this.currentStep);
    }

    /**
     * Clean up all created and referenced elements and prepare to be deleted
     */
    destroy() {
        window.clearInterval(this.animationIntervalID);
        this.loader.destroy();
        this.timer.destroy();
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
        newMap.style.display = "flex";
        newMap.style.flex = " 1 1 auto";
        newMap.style.height = "420px";
        this.mapRoot.insertAdjacentElement('afterbegin', newMap);
        let map = select('#svg-map');
        let drawLayer = map.select('#root');
        drawLayer.append("g").attr('id', 'trajectories');
        drawLayer.append("g").attr('id', 'contacts');
        map.call(zoom().on("zoom", () => this._handleZoom()));
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

        // Add new trajectories
        circle.enter()
            .append("circle")
            .attr('r', this.agentSize * this.scaleFactor)
            .style('fill', '#000000');

        // update positions
        circle.transition()
            .duration(this.animationInterval)
            .attr('cx', d => d[0])
            .attr('cy', d => d[1])
            .attr('r', this.agentSize * this.scaleFactor)
            .style('stroke', 'black')
            .attr('stroke-width', this.agentSize * this.scaleFactor / 2);
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
