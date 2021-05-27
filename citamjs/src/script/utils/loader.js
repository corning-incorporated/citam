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
  constructor(parentElement) {
    // Add Loader elements
    this.loader = document.createElement('div');
    parentElement.append(this.loader);
    // document.body.prepend(loader);
    this.loader.innerHTML = `
      <div id="loader-root">
        <div class="simulation-loader-overlay"></div>
        <div class="simulation-loader">
          <div class="loader-wrapper">
            <div id="trajectory-loader" class="loader"></div>
            <div> 
              <span class="loader-label" id="traj-loader-label">Loading trajectory Data</span>
              <br/>
              <span class="loader-label" id="countdown-root"></span>
            </div>
           </div>
          <div class="loader-wrapper">
            <div id="map-loader" class="loader"></div>
            <span class="loader-label">Map File</span>
          </div>
        </div>
      </div>
    `;

    this.loaderRoot = document.getElementById('loader-root');
    this._trajectoryElem = document.getElementById('trajectory-loader');
    this.trajLoaderLabel = document.getElementById('traj-loader-label');

    // this._contactElem = document.getElementById('contact-loader');
    this._mapElem = document.getElementById('map-loader');
    // this._distributionsElem = document.getElementById('distribution-loader');
    this.countdownRoot = document.getElementById('countdown-root');

  }

  /** Show the loader element */
  show() {
    this.loaderRoot.style.display = 'inline';
    this._reset();
  }

  showError(message) {
    this._setError(this._trajectoryElem);
    // this._setComplete(this._trajectoryElem);
    this.trajLoaderLabel.innerText = "Error loading trajectory"
    if (message !== undefined) {
      this.countdownRoot.innerText = message;
    }

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

  startCountdown(duration) {
    let minutes = Math.floor(duration / 60);
    let seconds = Math.floor(duration % 60);
    this.countdownRoot.innerText = minutes + " min " + seconds + " sec left";
    this.countdown = setInterval(() => {
      if (duration > 0) {
        duration--;
        minutes = Math.floor(duration / 60);
        seconds = Math.floor(duration % 60);
        this.countdownRoot.innerText = minutes + " min " + seconds + " sec left";
      } else {
        this.countdownRoot.innerText = "Finalizing... "
      }
    }, 1000);

  }

  stopCountdown() {
    clearInterval(this.countdown);
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
 * Set a spinner to the loaded state
 *
 * @param {HTMLElement} node
 * @private
 */
  _setError(node) {
    node.classList.remove('loader');
    node.classList.add('loader-error');

  }

  /**
   * Reset all spinners to the unloaded state
   *
   * @private
   */
  _reset() {
    [this._trajectoryElem, this._mapElem].forEach(
      (elem) => {
        elem.classList.remove('loaded');
        elem.classList.remove('error');
        elem.classList.add('loader');
      });
  }
}
