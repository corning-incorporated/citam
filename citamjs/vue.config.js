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

const FRONTEND_PORT = process.env.VUE_PORT || 8081;
const API_PORT = process.env.DJANGO_PORT || 8000;


module.exports = {
    publicPath: process.env.NODE_ENV === 'production' ? './' : '/',
    configureWebpack: {
        output: {
            libraryExport: 'default'
        }
    },
    devServer: {
        port: FRONTEND_PORT,
        host: '0.0.0.0',
        logLevel: 'info',
        clientLogLevel: 'info',
        hot: true,
        overlay: true,
        watchContentBase: true,
        disableHostCheck: true,
        headers: {'Access-Control-Allow-Origin': '*'},
        proxy: {'/v1': {target: `http://127.0.0.1:${API_PORT}`}},
    },
}
