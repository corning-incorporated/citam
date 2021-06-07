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

/**
 * Timer element
 *
 * @author Chris Soper
 * @module colorbar
 */
import { Draggable } from './draggable';
import '../../css/_timer.scss';

/**
 * @see http://bl.ocks.org/chrisbrich/4209888
 */
export class Timer {
  /**
   *
   * @param {Number} lengthOfStep - The length of time each step represents (in seconds)
   */
  constructor(lengthOfStep) {
    this.lengthOfStep = lengthOfStep;
    this.currentStep = 0;
    this._draggable = new Draggable('Current Time');
    this.domElement = this._draggable.domElement;
    this.domElement.style.position = 'absolute';
    this.domElement.style.top = '0';
    this.domElement.style.left = '0';
    this.startTime = { hour: 8, minute: 0, second: 0 };
    this.startTimeTotSeconds = (
      (this.startTime.hour * 60 * 60) +
      (this.startTime.minute * 60) +
      (this.startTime.second)
    );
    this._draggable.contentElement.append(this._makeTimerElement());
  }

  /**
   * Construct the dom element for the timer
   *
   * @private
   */
  _makeTimerElement() {
    let timerElem = document.createElement('div');
    timerElem.classList.add('timer-element');
    this.hoursElem = document.createElement('span');
    this.hoursElem.innerText = zeroPad(this.startTime.hour);
    this.minutesElem = document.createElement('span');
    this.minutesElem.innerText = zeroPad(this.startTime.minute);
    this.secondsElem = document.createElement('span');
    this.secondsElem.innerText = zeroPad(this.startTime.second);
    this.secondsElem.style.marginRight = '0.25em';
    this.ampmElem = document.createElement('span');
    this.ampmElem.innerText = `${this.startTime.hour < 13 ? 'AM' : 'PM'}`;
    let sep = document.createElement('span');
    sep.innerText = ':';
    timerElem.appendChild(this.hoursElem);
    timerElem.appendChild(sep.cloneNode(true));
    timerElem.appendChild(this.minutesElem);
    timerElem.appendChild(sep.cloneNode(true));
    timerElem.appendChild(this.secondsElem);
    timerElem.appendChild(this.ampmElem);
    return timerElem;
  }

  /** Show the timer */
  show() {
    this.domElement.style.display = 'block';
  }

  /** Hide the timer */
  hide() {
    this.domElement.style.display = 'none';
  }

  /** Set the current timestep */
  setStep(timestep) {
    this.currentStep = timestep;
    this.updateClock();
  }

  updateClock() {
    let timestepSeconds = this.currentStep * this.lengthOfStep;

    let rawSeconds = timestepSeconds + this.startTimeTotSeconds;
    let seconds = rawSeconds % 60;

    let rawMinutes = Math.floor(rawSeconds / 60);
    let minutes = rawMinutes % 60;

    let hours = Math.floor(rawMinutes / 60);
    if (hours >= 13) {
      hours = hours - 13;
      if (this.ampmElem.innerText !== 'PM') {
        this.ampmElem.innerText = 'PM';
      }
    } else {
      if (this.ampmElem.innerText !== 'AM') {
        this.ampmElem.innerText = 'AM';
      }
    }
    this.secondsElem.innerText = zeroPad(seconds);
    this.minutesElem.innerText = zeroPad(minutes);
    this.hoursElem.innerText = zeroPad(hours);
  }

  /**
   * Remove this element from the dom
   */
  destroy() {
    this.domElement.parentElement.removeChild(this.domElement)
  }
}

function zeroPad(number) {
  let strNum = number.toString();
  strNum = '00' + strNum;
  return strNum.slice(strNum.length - 2, strNum.length);
}
