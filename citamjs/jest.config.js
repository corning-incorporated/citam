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

module.exports = {
    "preset": '@vue/cli-plugin-unit-jest',
    "testMatch": ["**/tests/**/*spec.js"],
    "verbose": true,
    "moduleFileExtensions": [
        "js",
        "json",
        "vue"
    ],
    "transform": {
        ".*\\.(vue)$": "vue-jest"
    },
    "transformIgnorePatterns": ["<rootDir>/node_modules"],
    "testPathIgnorePatterns": ["<rootDir>/node_modules"],
    "collectCoverage": true,
    "collectCoverageFrom": [
        "**/*.{js,vue}",
        "!**/node_modules/**", "!**/build/**", "!**/dist/**", "!<rootDir>/src/script/**", "!<rootDir>/coverage/**"
    ],
    setupFiles: [
        "<rootDir>/tests/jest.stub.js"
    ]
}
