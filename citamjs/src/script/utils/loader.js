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

import '../../css/_loader.scss';

export class Loader {
  constructor() {
    // Add Loader elements
    let loader = document.createElement('div');
    document.body.prepend(loader);
    loader.outerHTML = `
      <div id="loader-root">
        <div class="simulation-loader-overlay"></div>
        <div class="simulation-loader">
          <div class="loader-title">Loading...</div>
          <div class="loader-wrapper">
            <div id="trajectory-loader" class="loader"></div>
            <span class="loader-label">Trajectory File</span>
           </div>
          <div class="loader-wrapper">
            <div id="contact-loader" class="loader"></div>
            <span class="loader-label">Contacts File</span>
          </div>
          <div class="loader-wrapper">
            <div id="map-loader" class="loader"></div>
            <span class="loader-label">Map File</span>
          </div>
          <div class="loader-wrapper">
            <div id="distribution-loader" class="loader"></div>
            <span class="loader-label">Contact Distribution Files</span>
          </div>
        </div>
      </div>
    `;

    this.loaderRoot = document.getElementById('loader-root');
    this._trajectoryElem = document.getElementById('trajectory-loader');
    this._contactElem = document.getElementById('contact-loader');
    this._mapElem = document.getElementById('map-loader');
    this._distributionsElem = document.getElementById('distribution-loader');
  }

  /** Show the loader element */
  show() {
    this.loaderRoot.style.display = 'block';
    this._reset();
  }

  /** Hide the loader element */
  hide() {
    this.loaderRoot.style.display = 'none';
  }

  /** Set the trajectory spinner to the loaded state */
  trajectoryLoaded() {
    this._setComplete(this._trajectoryElem);
  }

  /** Set the contact spinner to the loaded state */
  contactLoaded() {
    this._setComplete(this._contactElem);
  }

  /** Set the map spinner to the loaded state */
  mapLoaded() {
    this._setComplete(this._mapElem);
  }

  /** Set the heatmap spinner to the loaded state */
  distributionsLoaded() {
    this._setComplete(this._distributionsElem);
  }

  /**
   * Remove this element from the dom
   */
  destroy() {
    this.loaderRoot.parentElement.removeChild(this.loaderRoot)
  }

  /**
   * Set a spinner to the loaded state
   *
   * @param {HTMLElement} node
   * @private
   */
  _setComplete(node) {
    node.classList.remove('loader');
    node.classList.add('loaded');
  }

  /**
   * Reset all spinners to the unloaded state
   *
   * @private
   */
  _reset() {
    [this._trajectoryElem, this._mapElem, this._contactElem, this._distributionsElem].forEach(
      (elem) => {
        elem.classList.remove('loaded');
        elem.classList.add('loader');
      });
  }
}
