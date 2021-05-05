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

import { SimpleHeat } from '../utils/simpleheat';
import { getContactPositionDist } from '../data_service';

export class Heatmap {
  /**
   *
   * @param {Object} params
   * @param {HTMLElement} params.domRoot - Root element
   * @param {String} params.width - Width of canvas
   * @param {String} params.height - Width of canvas
   */
  constructor(params) {
    this.domElement = document.createElement('canvas');
    params.domRoot.append(this.domElement);
    this._heat = new SimpleHeat(this.domElement);
  }

  setSimulation(sim_id) {
    this.simulation = sim_id;
    getContactPositionDist(sim_id).then(response => {
      this.setData(response.data);
    });
    let img = new Image();
    img.onload = () => this.domElement.getContext('2d').drawImage(img, 0, 0);
    img.src = `/v1/${sim_id}/map`;
  }

  /**
   * Remove all drawn content from the canvas.
   *
   * note: this does not remove data
   */
  clear() {
    let ctx = this.domElement.getContext('2d');
    // Store the current transformation matrix
    ctx.save();
    // Use the identity matrix while clearing the canvas
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, this.domElement.width, this.domElement.height);
    // Restore the transform
    ctx.restore();
  }

  /**
   * Set trajectory or contact data to highlight
   * @param {Array} data - Heatmap data
   */
  setData(data) {
    this.data = data;
    this.redraw();
  }

  /**
   * Redraw data to the canvas
   */
  redraw() {
    // First, clear out all old heatmap data
    this.clear();
    // Redraw the map
    let img = new Image();
    img.onload = () => {
      // TODO: Only works in chrome?
      this.domElement.getContext('2d').drawImage(img, 0, 0);
    };
    img.src = `/v1/${this.simulation}/map`;
    // draw into canvas, with minimum opacity threshold
    this._heat.draw();
  }
}
