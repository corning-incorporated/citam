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

/**
 * This is built using D3 and should be added directly to the DOM
 *
 * @author Chris Soper
 * @module colorbar
 */
import {
  interpolateSinebow,
  axisLeft,
  scaleSequential,
  select,
  scaleLinear,
} from 'd3';
import {Draggable} from './draggable';

const DEFAULT_PARAMS = {
  min: 0,
  max: 1,
  ticks: 10,
  height: 300,
  width: 80,
  paddingBottom: 20,
  paddingTop: 20,
  scale: scaleSequential,
  palette: interpolateSinebow,
};

/**
 * @see http://bl.ocks.org/chrisbrich/4209888
 */
export class Colorbar {
  constructor(parameters) {
    const params = Object.assign({}, DEFAULT_PARAMS, parameters);
    this._draggable = new Draggable('Colorbar');
    this.domElement = this._draggable.domElement;
    this.domElement.style.position = 'absolute';
    this.domElement.style.top = '25%';
    this.domElement.style.left = '20px';
    this.scaleType = params.scale;
    this.palette = params.palette;

    this._svg = select(this._draggable.contentElement)
      .append('svg')
      .attr('width', params.width)
      .attr('height', params.height + params.paddingBottom + params.paddingTop);

    this._gradient = this._svg.append('linearGradient')
      .attr('id', 'colorbar-gradient')
      .attr('x1', '0%')
      .attr('y1', '100%')
      .attr('x2', '0%')
      .attr('y2', '0%');

    this.steps = [];
    // Good place for lodash, if it was already being used in this project :(
    for (let i = 0; i <= 100; i++) {
      this.steps.push(this._gradient.append('stop').attr('offset', `${i}%`));
    }

    this._svg.append('rect')
      .attr('width', '25px')
      .attr('height', params.height)
      .attr('transform', `translate(${params.width - 25},${params.paddingTop})`)
      .style('fill', 'url(#colorbar-gradient)');

    this.axisScale = scaleLinear()
      .range([0, params.height])
      .domain([params.min, params.max]);

    this._legendAxis = axisLeft(this.axisScale).ticks(10);

    this._axisElem = this._svg.append('g')
      .attr('class', 'color-axis')
      .attr('transform', `translate(${params.width - 25},${params.paddingTop})`)
      .call(this._legendAxis);

    this.update(params.min, params.max);
  }

  show() {
    this.domElement.style.display = 'block';
  }

  hide() {
    this.domElement.style.display = 'none';
  }

  /** Set the domain for the colorbar and update the gradient */
  update(min, max) {
    this._updateColors();
    this._updateValues(min, max);
  }

  /** Set the palette for the colorbar and update the gradient */
  setPalette(palette) {
    this.palette = palette;
  }

  /** Set the Title for the colorbar */
  setTitle(title) {
    this._draggable.updateTitle(title);
  }

  /**
   * Remove this element from the dom
   */
  destroy() {
    this.domElement.parentElement.removeChild(this.domElement)
  }

  /**
   * Update the gradent
   *
   * @private
   */
  _updateColors() {
    let colorScale = this.scaleType(this.palette)
      .domain([0, this.steps.length - 1]);

    for (let i = 0; i < this.steps.length; i++) {
      this.steps[i].attr('stop-color', colorScale(i));
    }
  }

  /**
   * Update the tick marks on the colorbar
   *
   * @param min
   * @param max
   * @private
   */
  _updateValues(min, max) {
    this.axisScale = this.axisScale.domain([max, min]);
    let axisElem = select('.color-axis');
    this._legendAxis.scale(this.axisScale);
    axisElem.call(this._legendAxis);
  }

}
