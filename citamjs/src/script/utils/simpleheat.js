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
 * @author mourner
 * @see https://github.com/mourner/simpleheat
 * @module simpleheat
 */

export class SimpleHeat {
  constructor(canvas) {
    this._canvas = canvas = typeof canvas === 'string' ? document.getElementById(canvas) : canvas;
    this._offScreenCanvas = document.createElement('canvas');
    this._offScreenCanvas.width = canvas.width;
    this._offScreenCanvas.height = canvas.height;

    this._ctx = canvas.getContext('2d');
    this._width = canvas.width;
    this._height = canvas.height;
    this._max = 1;
    this._data = {};
    this.defaultRadius = 25;
    this.defaultGradient = {
      0.4: 'blue',
      0.6: 'cyan',
      0.7: 'lime',
      0.8: 'yellow',
      1.0: 'red',
    };
  }

  data(data) {
    this._data = data;
    return this;
  }

  max(max) {
    this._max = max;
    return this;
  }

  add(point) {
    let point_key = `${point[0]}_${point[1]}`;
    this._data[point_key] = this._data[point_key] + 1 || 0;
    return this;
  }

  clear() {
    this._data = [];
    return this;
  }

  radius(r, blur) {
    blur = blur === undefined ? 15 : blur;
    let circle = this._circle = this._createCanvas(),
      ctx = circle.getContext('2d'),
      r2 = this._r = r + blur;
    circle.width = circle.height = r2 * 2;
    ctx.shadowOffsetX = ctx.shadowOffsetY = r2 * 2;
    ctx.shadowBlur = blur;
    ctx.shadowColor = 'black';
    ctx.beginPath();
    ctx.arc(-r2, -r2, r, 0, Math.PI * 2, true);
    ctx.closePath();
    ctx.fill();
    return this;
  }

  resize() {
    this._width = this._canvas.width;
    this._height = this._canvas.height;
  }

  gradient(grad) {
    // create a 256x1 gradient that we'll use to turn a grayscale heatmap into a colored one
    let canvas = this._createCanvas(),
      ctx = canvas.getContext('2d'),
      gradient = ctx.createLinearGradient(0, 0, 0, 256);

    canvas.width = 1;
    canvas.height = 256;

    for (let i in grad) {
      gradient.addColorStop(+i, grad[i]);
    }

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 1, 256);

    this._grad = ctx.getImageData(0, 0, 1, 256).data;

    return this;
  }

  draw(minOpacity) {
    if (!this._circle) this.radius(this.defaultRadius);
    if (!this._grad) this.gradient(this.defaultGradient);

    this._ctx.clearRect(0, 0, this._width, this._height);

    // draw a grayscale heatmap by putting a blurred circle at each data point

    for (let i = 0, len = Object.values(this._data).length, p; i < len; i++) {
      p = Object.values(this._data)[i];
      this._ctx.globalAlpha = Math.min(
        Math.max(
          p[2] / this._max,
          minOpacity === undefined ? 0.05 : minOpacity,
        ),
        1,
      );
      this._ctx.drawImage(this._circle, p[0] - this._r, p[1] - this._r);
    }

    // // colorize the heatmap, using opacity value of each pixel to get the right color from our gradient
    let colored = this._ctx.getImageData(0, 0, this._width, this._height);
    this._colorize(colored.data, this._grad);
    this._ctx.putImageData(colored, 0, 0);

    return this;
  }

  _colorize(pixels, gradient) {
    for (let i = 0, len = pixels.length, j; i < len; i += 4) {
      j = pixels[i + 3] * 4; // get gradient color from opacity value

      if (j) {
        pixels[i] = gradient[j];
        pixels[i + 1] = gradient[j + 1];
        pixels[i + 2] = gradient[j + 2];
      }
    }
  }

  _createCanvas() {
    if (typeof document !== 'undefined') {
      return document.createElement('canvas');
    } else {
      // create a new canvas instance in node.js
      // the canvas class needs to have a default constructor without any parameter
      return new this._canvas.constructor();
    }
  }
}
