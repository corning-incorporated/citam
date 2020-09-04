
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

from matplotlib import cm, colors
import xml.etree.ElementTree as ET
import logging

from citam.engine.point import Point
from svgpathtools import wsvg, Arc, Line, parse_path

ET.register_namespace('', "http://www.w3.org/2000/svg")
ET.register_namespace('xlink', "http://www.w3.org/1999/xlink")

X_MARKER = 1
LINE_MARKER = 2
PLUS_MARKER = 3


def export_possible_oneway_aisles_to_svg(walls, oneway_network, svgfile):

    texts = []
    text_paths = []
    radius = complex(3, 3)
    small_radius = complex(1.0, 1.0)
    paths = [wall for wall in walls]
    attributes = [{'fill': 'white',
                   'stroke': 'black',
                   'stroke-width': 0.5
                   }
                  for p in paths
                  ]

    for e in list(oneway_network.edges(data=True)):
        color = 'red'
        p = Line(start=complex(e[0][0], e[0][1]),
                 end=complex(e[1][0], e[1][1])
                 )
        paths.append(p)
        attributes.append({'fill': color,
                           'stroke': color,
                           'stroke-width': 0.1
                           })
        midx, midy = p.point(0.5).real, p.point(0.5).imag
        t_path = parse_path('M ' + str(midx) + ',' + str(midy) + ' L ' +
                            str(midx+60) + ',' + str(midy)
                            )

        texts.append(str(e[2]['id']))
        text_paths.append(t_path)

        for coord in (e[0], e[1]):
            x, y = coord
            start = Point(x=x - radius.real, y=y)
            end = Point(x=x + radius.real, y=y)
            agent_top = Arc(start=start.complex_coords,
                            radius=radius,
                            rotation=0,
                            large_arc=1,
                            sweep=1,
                            end=end.complex_coords
                            )
            attributes.append({'fill': color,
                               'stroke': color,
                               'stroke-width': 0.1
                               })
            paths.append(agent_top)
            agent_bottom = agent_top.rotated(180)
            attributes.append({'fill': color,
                               'stroke': color,
                               'stroke-width': 0.1
                               })
            paths.append(agent_bottom)

        for coord in e[2]['inter_points']:
            x, y = coord
            start = Point(x=x - small_radius.real, y=y)
            end = Point(x=x + small_radius.real, y=y)
            agent_top = Arc(start=start.complex_coords,
                            radius=small_radius,
                            rotation=0,
                            large_arc=1,
                            sweep=1,
                            end=end.complex_coords
                            )
            attributes.append({'fill': color,
                               'stroke': color,
                               'stroke-width': 0.1
                               })
            paths.append(agent_top)
            agent_bottom = agent_top.rotated(180)
            attributes.append({'fill': color,
                               'stroke': color,
                               'stroke-width': 0.1
                               })
            paths.append(agent_bottom)

    wsvg(paths,
         attributes=attributes,
         text=texts,
         text_path=text_paths,
         font_size=10,
         filename=svgfile
         )

    return


def create_arrow_svg_paths(arrow):

    paths = []
    attributes = []

    radius = complex(0.5, 0.5)

    x_start, y_start = arrow[0]
    x_end, y_end = arrow[1]

    start = Point(x=x_start, y=y_start)
    end = Point(x=x_end, y=y_end)
    line1 = Line(start=start.complex_coords, end=end.complex_coords)
    attributes.append({'stroke': 'green', 'stroke-width': 0.5})
    paths.append(line1)

    start = Point(x=x_end - radius.real, y=y_end)
    end = Point(x=x_end + radius.real, y=y_end)
    agent_top = Arc(start=start.complex_coords,
                    radius=radius,
                    rotation=0,
                    large_arc=1,
                    sweep=1,
                    end=end.complex_coords
                    )
    attributes.append({'fill': 'green',
                       'stroke': 'green',
                       'stroke-width': 0.1
                       })
    paths.append(agent_top)
    agent_bottom = agent_top.rotated(180)
    attributes.append({'fill': 'green',
                       'stroke': 'green',
                       'stroke-width': 0.1
                       })
    paths.append(agent_bottom)

    return paths, attributes


def create_markers_svg_paths(x, y, marker_type):

    paths = []
    attributes = []

    if marker_type == PLUS_MARKER or marker_type is None:

        half_length = 0.5
        start = Point(x=x - half_length, y=y)
        end = Point(x=x + half_length, y=y)
        line1 = Line(start=start.complex_coords, end=end.complex_coords)
        start = Point(x=x, y=y - half_length)
        end = Point(x=x, y=y + half_length)
        line2 = Line(start=start.complex_coords, end=end.complex_coords)

        attributes.append({'stroke': 'red', 'stroke-width': 0.5})
        paths.append(line1)
        attributes.append({'stroke': 'red', 'stroke-width': 0.5})
        paths.append(line2)

    elif marker_type == LINE_MARKER:

        half_length = 0.4
        start = Point(x=x - half_length, y=y)
        end = Point(x=x + half_length, y=y)
        line1 = Line(start=start.complex_coords, end=end.complex_coords)
        attributes.append({'stroke': 'red', 'stroke-width': 0.5})
        paths.append(line1)

    else:
        logging.info('ERROR: unsupported marker type ', marker_type)

    return paths, attributes


def export_nav_network_to_svg(walls,
                              nav_paths,
                              nav_nodes,
                              filename,
                              marker_type=X_MARKER,
                              color='blue'
                              ):

    radius = complex(2, 2)
    paths = [wall for wall in walls]
    attributes = [{'fill': 'white',
                   'stroke': 'black',
                   'stroke-width': 0.5
                   }
                  for p in paths
                  ]

    for nn in nav_nodes:
        x, y = nn
        start = Point(x=x - radius.real, y=y)
        end = Point(x=x + radius.real, y=y)
        agent_top = Arc(start=start.complex_coords,
                        radius=radius,
                        rotation=0,
                        large_arc=1,
                        sweep=1,
                        end=end.complex_coords
                        )
        attributes.append({'fill': color,
                           'stroke': color,
                           'stroke-width': 0.1
                           })
        paths.append(agent_top)
        agent_bottom = agent_top.rotated(180)
        attributes.append({'fill': color,
                           'stroke': color,
                           'stroke-width': 0.1
                           })
        paths.append(agent_bottom)

    for np in nav_paths:
        paths.append(np)
        attributes.append({'fill': color,
                           'stroke': color,
                           'stroke-width': 0.1
                           })

    wsvg(paths, attributes=attributes, filename=filename)

    return


def export_world_to_svg(walls,
                        agent_positions_and_contacts,
                        svg_file,
                        marker_locations=[],
                        marker_type=None,
                        arrows=[],
                        doors=[],
                        max_contacts=100,
                        current_time=None,
                        show_colobar=False,
                        viewbox=None
                        ):

    if viewbox is not None:
        xmax = viewbox[2]
        multiplier = round(xmax/1500, 1)
    else:
        multiplier = 1.0

    radius = complex(2, 2)
    paths = [wall for wall in walls]
    attributes = [{'fill': 'white',
                   'stroke': 'black',
                   'stroke-width': 0.5*multiplier
                   }
                  for p in paths
                  ]

    color_scale = cm.get_cmap('RdYlGn')

    for x, y, n_contacts in agent_positions_and_contacts:
        color = color_scale(1.0 - n_contacts*1.0/max_contacts)
        start = Point(x=x - radius.real, y=y)
        end = Point(x=x + radius.real, y=y)
        agent_top = Arc(start=start.complex_coords,
                        radius=radius,
                        rotation=0,
                        large_arc=1,
                        sweep=1,
                        end=end.complex_coords)
        attributes.append({'fill': colors.to_hex(color),
                           'stroke': 'blue',
                           'stroke-width': 0.1*multiplier
                           })
        paths.append(agent_top)
        agent_bottom = agent_top.rotated(180)
        attributes.append({'fill': colors.to_hex(color),
                           'stroke': 'blue',
                           'stroke-width': 0.1*multiplier
                           })
        paths.append(agent_bottom)

    for x, y, n_contacts in marker_locations:

        marker_paths, marker_attr = create_markers_svg_paths(x, y, marker_type)
        paths += marker_paths
        attributes += marker_attr

    for arrow in arrows:
        arrow_path, arrow_attr = create_arrow_svg_paths(arrow)
        paths += arrow_path
        attributes += arrow_attr

    for door in doors:
        paths.append(door.path)
        attributes.append({'stroke': 'red', 'stroke-width': 3.0*multiplier})

    t_path = parse_path('M 0,0 L 250,0')

    if viewbox is not None:
        xmin, ymin, xmax, ymax = viewbox
        viewbox_str = str(xmin) + " " + str(ymin) + " " + str(xmax) + " " + \
            str(ymax)
        svg_attributes = {'width': '100%',
                          'height': '100%',
                          'debug': False,
                          'viewBox': viewbox_str
                          }
    else:
        svg_attributes = None

    wsvg(paths,
         attributes=attributes,
         text=current_time,
         text_path=t_path,
         filename=svg_file,
         svg_attributes=svg_attributes
         )
    add_root_layer_to_svg(svg_file, svg_file)

    return


def add_root_layer_to_svg(original_svg_filename, updated_filename):

    tree = ET.parse(original_svg_filename)

    root = tree.getroot()

    new_root = ET.Element('g')
    new_root.set('id', 'root')

    for path_elem in root:
        new_root.append(path_elem)

    while len(root) > 0:
        root.remove(root[0])

    root.append(new_root)

    tree.write(updated_filename)

    return
