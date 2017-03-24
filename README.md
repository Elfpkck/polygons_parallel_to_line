# Polygons Parallel to Line
## General description and demonstration

Depending on the settings, the plugin rotates the polygons in such a way that 
they become parallel to the nearest lines.

In the new layer, a "_`rotated`" field is created with a value `1` for each polygon 
that has been rotated. If in the source layer such field already exists, and 
its type is `integer`, then the data of this field remains, but updated in the 
new layer.

* before using the plugin:

![](https://github.com/Elfpkck/pptl_images/blob/master/before.png?raw=true)

* after using the plugin:

![](https://github.com/Elfpkck/pptl_images/blob/master/after.png?raw=true)

## Algorithm

First, the plugin creates a spatial index for the objects of the linear layer.

Within the distance specified in the "Distance from line" field, for each line 
of the layer selected in the "Select line layer", the plugin finds the nearest 
polygon of the layer selected in the "Select polygon layer".

Two edges of the polygon adjoin the node. If the angle between the edge and the 
nearest line segment is no larger than the value specified in the "Angle value" 
field, then the polygon rotates relative to the centroid so that the edge 
becomes parallel to the line segment.

If both the angles between the edges and the line segment are less than the 
"Angle value", then for the rotation is selected the edge, which forms the 
smaller angle if in the settings are not chosen "Rotate by longest edge if both 
angles between polygon edges and line segment <= 'Angle value'".

## Settings
#### Distance from line
If value is 0, plugin will process all polygons.

In the following example, the distance is 50 m.

* before:

![](https://github.com/Elfpkck/pptl_images/blob/master/distance_before.png?raw=true)

* after:

![](https://github.com/Elfpkck/pptl_images/blob/master/distance_after.png?raw=true)

#### Save only selected
If not chosen "Save only selected", to new layer will saved both rotated and 
unrotated polygons. This option makes sense if chosen "Rotate only selected 
polygons".

#### Rotate by longest edge if both angles between polygon edges and line segment <= 'Angle value'
* if not checked:
* if checked:

#### Do not rotate multipolygons

#### Angle value
Min: 0, max 89.9

Copyright (C) 2016-2017 by Andrey Lekarev