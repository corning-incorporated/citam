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

import axios from 'axios';

axios.defaults.timeout = 20000 * 60;
/**
 * Create a promise which resolves immediately contianing data
 *
 * @param {*} data
 * @return {Promise<Object>}
 */
function makePromise(data) {
  return new Promise((resolve) => resolve(data));
}

/**
 * Retrieve the base map as an SVG document
 *
 * @param {string} simulation - Simulation id
 * @param {string} floor - floor
 * @returns {XMLDocument} Base Map as SVG
 */
export function getBaseMap(simulation, floor) {
  return axios.get(`${simulation}/map`, { params: { floor: floor } });
}


/**
 * Retrieve the the Contact Distribution per Position
 *
 * @param {string} simulation - Simulation id
 * @param {string} floor - floor
 * @returns {XMLDocument} Base Map as SVG
 */
export function getContactPositionDist(simulation, floor) {
  return axios.get(`${simulation}/distribution/coordinate`, { params: { floor: floor } });
}

/**
 * Get the contact data for a given simulation
 *
 * @param {string} simulation - Simulation id
 * @param {string} floor - floor
 * @return {Promise<AxiosResponse>} contact data
 */
export function getContact(simulation, floor) {
  return axios.get(`${simulation}/contact`, { params: { floor: floor } });
}

/**
 * Get the total number of steps for a given simulation
 *
 * @param {string} simulation - Simulation id
 * @return {Promise<AxiosResponse>} contact data
 */
export function getTotalTimesteps(simulation) {
  return axios.get(`${simulation}/total_timesteps`);
}

/**
 * Get the trajectory data for a given simulation
 *
 * @param {string} simulation - Simulation id
 * @param {string} floor - floor
 * @param {number} offset - offset
 * * @param {number} first_timestep - first_timestep
 * * @param {number} max_steps - max_steps
 * @return {Promise<AxiosResponse>} trajectory data
 */
export function getTrajectory(simulation, floor, first_timestep, max_steps) {
  return axios.get(`${simulation}/trajectory`, {
    params:
      { floor: floor, first_timestep: first_timestep, max_steps: max_steps }
  });
}

/**
 *
 * @param simulation
 * @param floor
 * @returns {Promise<AxiosResponse<any>>}
 */
export function getTrajectoryLines(simulation, floor) {
  return axios.get(`${simulation}/trajectory_lines`, { params: { floor: floor } });
}

/** Cache summary responses **/
const _SUMMARY_CACHE = new Map();

/**
 * Get summary data for a given simulation
 *
 * @param {string} simulation - Simulation id
 * @return {Promise<AxiosResponse|Object>} trajectory data
 */
export function getSummary(simulation) {
  if (_SUMMARY_CACHE.has(simulation)) {
    return makePromise(_SUMMARY_CACHE.get(simulation));
  }
  return axios.get(`${simulation}`).then(response => {
    _SUMMARY_CACHE.set(simulation, response);
    return response;
  });
}
