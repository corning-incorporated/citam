# Copyright 2020. Corning Incorporated. All rights reserved.
#
# This software may only be used in accordance with the licenses granted by
# Corning Incorporated. All other uses as well as any copying, modification or
# reverse engineering of the software is strictly prohibited.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
# ==============================================================================


class Point:
    def __init__(self, x: int, y: int, complex_coords=None):
        super().__init__()
        self.x = x
        self.y = y
        self.complex_coords = complex_coords

        if self.x is None and self.complex_coords is not None:
            self.convert_to_cartesian()

        if self.complex_coords is None and self.x is not None:
            self.convert_to_complex()

        return

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def convert_to_cartesian(self):

        self.x = self.complex_coords.real
        self.y = self.complex_coords.imag

        return

    def convert_to_complex(self):

        self.complex_coords = complex(self.x, self.y)

        return
