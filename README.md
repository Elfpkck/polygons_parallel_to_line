[![PR Validation](https://github.com/Elfpkck/polygons_parallel_to_line/actions/workflows/test.yaml/badge.svg?event=pull_request
)](https://github.com/Elfpkck/polygons_parallel_to_line/actions/workflows/test.yaml)
# Polygons Parallel to Line
## General description and demonstration
Depending on the settings, the plugin rotates the polygons in such a way that
they become parallel to the nearest lines.

In the new layer, a "`_rotated`" field is created with a value `1` for each
polygon that has been rotated. If in the source layer such field already
exists, and its type is `integer`, then the data of this field remains, but
updated in the new layer.

* before using the plugin:

![][before]

* after using the plugin:

![][after]

## Work preparation
The provider needs to be activated in the `Processing` options which are
accessible from QGIS main menu (`Processing -> Options -> Providers`). Check
`Activate` like shown below.

![][processing_options]

## Algorithm
First, the plugin creates a spatial index for the objects of the linear layer.

Within the distance specified in the "Distance from line" field, for each line
of the layer selected in the "Select line layer", the plugin finds the nearest
polygon of the layer selected in the "Select polygon layer".

If the line is the multipolyline, then each line of the multipolyline is
processed as a separate.

Two edges of the polygon adjoin the node. If the angle between the edge and the
nearest line segment is no larger than the value specified in the "Angle value"
field, then the polygon rotates relative to the centroid so that the edge
becomes parallel to the line segment.

Multipolygons are rotated by the same principle with using the nearest node
and the centroid of the multipolygon.

If both the angles between the edges and the line segment are less than the
"Angle value", then for the rotation is selected the edge, which forms the
smaller angle if in the settings are not chosen "Rotate by longest edge if both
angles between polygon edges and line segment <= 'Angle value'".

If the layer objects have geometry errors, rotation may not occur.

## Settings
![][pptl]

I think `Rotate only selected polygons` and `Do not rotate multipolygons`
options are not needed in explanations.

### Distance from line
If value is 0, plugin will process all polygons. In the following example, the
distance is 50 m (showed by grey).

* before:

![][distance_before]

* after:

![][distance_after]

### Angle value
Value, degrees:
* min: 0
* max 89.9

The following example shows the angle between one edge of the polygon and the
nearest line segment. The angle for the second side is similar. The plugin
compares these angles with the values from the settings.

![][angle]

### Save only selected
If not chosen "Save only selected", to new layer will saved both rotated and
unrotated polygons. This option makes sense if chosen "Rotate only selected
polygons".

### Rotate by longest edge if both angles between polygon edges and line segment <= 'Angle value'
* before:

![][long_before]

* if not checked (angle near the short edge less than the long edge):

![][long_without]

* if checked:

![][long_with]

Copyright (C) 2016-2023 by Andrii Liekariev

[before]: https://github.com/Elfpkck/pptl_images/blob/master/before.png?raw=true
[after]: https://github.com/Elfpkck/pptl_images/blob/master/after.png?raw=true
[processing_options]: https://github.com/Elfpkck/pptl_images/blob/master/processing_options.png?raw=true
[pptl]: https://github.com/Elfpkck/pptl_images/blob/master/pptl.png?raw=true
[distance_before]: https://github.com/Elfpkck/pptl_images/blob/master/distance_before.png?raw=true
[distance_after]: https://github.com/Elfpkck/pptl_images/blob/master/distance_after.png?raw=true
[angle]: https://github.com/Elfpkck/pptl_images/blob/master/angle.png?raw=true
[long_before]: https://github.com/Elfpkck/pptl_images/blob/master/long_before.png?raw=true
[long_without]: https://github.com/Elfpkck/pptl_images/blob/master/long_without.png?raw=true
[long_with]: https://github.com/Elfpkck/pptl_images/blob/master/long_with.png?raw=true
