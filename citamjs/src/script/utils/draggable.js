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
 * @module draggable
 *
 * Utilities for creating draggable pseudo-windows in the DOM
 */

import interact from 'interactjs';
import {
  library,
  dom,
} from '@fortawesome/fontawesome-svg-core';
import {faGripVertical} from '@fortawesome/free-solid-svg-icons';
import '../../css/_draggable.scss';

// configure the fontawesome icons
library.add(faGripVertical);
dom.watch();

const DRAGGABLE_TEMPLATE = `<div class="drag-title-bar">
  <span class="drag-title">{{title}}</span>
</div>`;


export class Draggable {
  constructor(title) {
    title = title || '';
    this.domElement = document.createElement('div');
    this.domElement.classList.add('drag-window');
    this.domElement.innerHTML = DRAGGABLE_TEMPLATE
      .replace('{{title}}', title);

    this.contentElement = document.createElement('div');
    this.contentElement.setAttribute('class', 'drag-content');
    this.domElement.appendChild(this.contentElement);

    interact(this.domElement).draggable({onmove: onMove});
  }

  updateTitle(title) {
    let elem = this.domElement.querySelector('.drag-title');
    elem.textContent = title;
  }
}

/**
 * Create a draggable pseudo-window element
 *
 * @param title
 * @returns {HTMLDivElement}
 */
export function createDraggableElement(title) {
  title = title || '';
  let wrapper = document.createElement('div');
  wrapper.setAttribute('class', 'drag-window');

  wrapper.innerHTML = DRAGGABLE_TEMPLATE.replace('{{title}}', title);
  interact(wrapper).draggable({onmove: onMove});
  return wrapper;
}


/**
 * Event handler for updating the position of an element being dragged
 *
 * @param event
 */
function onMove(event) {
  let target = event.target;
  let x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
  let y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;
  target.style.transform = 'translate(' + x + 'px, ' + y + 'px)';

  // update the position attributes
  target.setAttribute('data-x', x);
  target.setAttribute('data-y', y);
}
