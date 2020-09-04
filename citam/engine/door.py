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


class Door:

    def __init__(self,
                 path,
                 space1,
                 space2=None,
                 in_service=True,
                 emergency_only=False,
                 special_access=False
                 ):

        super().__init__()
        self.path = path
        self.space1 = space1
        self.space2 = space2
        self.in_service = in_service
        self.emergency_only = emergency_only
        self.special_access = special_access

    def __str__(self):

        str_repr = '\nPath: ' + str(self.path) + '\n'
        if self.space1 is not None:
            str_repr += 'Space 1: ' + str(self.space1.unique_name) + '\n'
        else:
            str_repr += 'Space 1: None' + '\n'
        if self.space2 is not None:
            str_repr += 'Space 2: ' + str(self.space2.unique_name) + '\n'
        else:
            str_repr += 'Space 2: None' + '\n'

        return str_repr
