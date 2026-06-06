from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from qgis.core import (
    Qgis,
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureRequest,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsRectangle,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.gui import QgsMapToolIdentify, QgsMapToolIdentifyFeature, QgsRubberBand
from qgis.PyQt.QtCore import QPoint, Qt  # type: ignore[import-not-found]
from qgis.PyQt.QtGui import QColor  # type: ignore[import-not-found]

from .line import Line, Segment
from .parallelizer import compute_parallel_geometry

if TYPE_CHECKING:
    from qgis.core import QgsCoordinateReferenceSystem
    from qgis.gui import QgisInterface, QgsMapMouseEvent
    from qgis.PyQt.QtGui import QKeyEvent  # type: ignore[import-not-found]

    from .settings import MapToolSettings


def _closest_segment_of(geom: QgsGeometry, point_xy: QgsPointXY) -> Segment:
    feature = QgsFeature()
    feature.setGeometry(geom)
    return Line(feature).get_closest_segment(point_xy)


def _pick_segment_in_rect(geom: QgsGeometry, rect_geom: QgsGeometry, rect_center: QgsPointXY) -> Segment:
    best: Segment | None = None
    best_length = 0.0
    parts = geom.asGeometryCollection() or [geom]
    for part in parts:
        verts = list(part.vertices())
        for i in range(len(verts) - 1):
            seg = Segment(start=verts[i], end=verts[i + 1])
            seg_geom = QgsGeometry.fromPolyline([seg.start, seg.end])
            clipped = seg_geom.intersection(rect_geom)
            if clipped.isNull() or clipped.isEmpty():
                continue
            length = clipped.length()
            if length > best_length or best is None:
                best_length = length
                best = seg
    if best is not None:
        return best
    return _closest_segment_of(geom, rect_center)


Kind = Literal["line", "polygon"]


class ParallelToLineMapTool(QgsMapToolIdentifyFeature):
    REFERENCE_COLOR = QColor(255, 140, 0, 200)
    REFERENCE_WIDTH = 3
    SELECTION_STROKE = QColor(0, 128, 255, 220)
    SELECTION_FILL = QColor(0, 128, 255, 50)
    DRAG_THRESHOLD_PX = 5

    def __init__(self, iface: QgisInterface, settings: MapToolSettings) -> None:
        super().__init__(iface.mapCanvas())
        self.iface = iface
        self.settings = settings
        self.reference_geom: QgsGeometry | None = None
        self.reference_rubber_band: QgsRubberBand | None = None
        self._selection_rubber_band: QgsRubberBand | None = None
        self._drag_start_pos: QPoint | None = None
        self._drag_start_point: QgsPointXY | None = None
        self._is_dragging: bool = False

    def activate(self) -> None:
        super().activate()
        self.setCursor(Qt.CursorShape.CrossCursor)
        self._show_message("Click or drag-rectangle on a line to set the reference.", Qgis.Info)

    def deactivate(self) -> None:
        self._clear_reference()
        self._cancel_drag()
        super().deactivate()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            if self._is_dragging:
                self._cancel_drag()
                return
            if self.reference_geom is not None:
                self._clear_reference()
                self._show_message("Reference cleared. Click a line feature to set a new reference.", Qgis.Info)
            else:
                self.iface.mapCanvas().unsetMapTool(self)
            return
        super().keyPressEvent(event)

    def canvasPressEvent(self, event: QgsMapMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._drag_start_pos = event.pos()
        self._drag_start_point = self.toMapCoordinates(event.pos())

    def canvasMoveEvent(self, event: QgsMapMouseEvent) -> None:
        if self._drag_start_pos is None:
            return
        if not self._is_dragging:
            delta = event.pos() - self._drag_start_pos
            if abs(delta.x()) < self.DRAG_THRESHOLD_PX and abs(delta.y()) < self.DRAG_THRESHOLD_PX:
                return
            self._is_dragging = True
            self._start_selection_band()
        self._update_selection_band(self.toMapCoordinates(event.pos()))

    def canvasReleaseEvent(self, event: QgsMapMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self._cancel_drag()
            self._clear_reference()
            self._show_message("Reference cleared. Click a line feature to set a new reference.", Qgis.Info)
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        was_dragging = self._is_dragging
        drag_start = self._drag_start_point
        self._cancel_drag()

        if was_dragging and drag_start is not None:
            release_point = self.toMapCoordinates(event.pos())
            rect = QgsRectangle(drag_start, release_point)
            if self.reference_geom is None:
                self._set_reference_from_rect(rect)
            else:
                self._rotate_features_in_rect(rect)
            return

        self._handle_single_click(event)

    def _handle_single_click(self, event: QgsMapMouseEvent) -> None:
        results = self.identify(
            event.x(),
            event.y(),
            QgsMapToolIdentify.TopDownAll,  # type: ignore[attr-defined]
            QgsMapToolIdentify.VectorLayer,  # type: ignore[attr-defined]
        )
        if not results:
            return

        map_point = self.toMapCoordinates(event.pos())

        for result in results:
            layer = result.mLayer
            if not isinstance(layer, QgsVectorLayer):
                continue
            feature: QgsFeature = result.mFeature
            geom_type = layer.geometryType()

            if self.reference_geom is None:
                if geom_type != QgsWkbTypes.LineGeometry:
                    continue
                ref_geom = feature.geometry()
                if self.settings.pick_reference_segment:
                    click_layer = self._point_in_layer_crs(map_point, layer)
                    segment = _closest_segment_of(ref_geom, click_layer)
                    ref_geom = QgsGeometry.fromPolylineXY([QgsPointXY(segment.start), QgsPointXY(segment.end)])
                self._set_reference(ref_geom, layer.crs())
                self._show_message(
                    "Reference set. Click or drag-rectangle to rotate line/polygon features.",
                    Qgis.Success,
                )
                return

            if geom_type not in (QgsWkbTypes.LineGeometry, QgsWkbTypes.PolygonGeometry):
                continue
            self._rotate_target(layer, feature, geom_type, map_point)
            return

    def _rotate_target(
        self,
        layer: QgsVectorLayer,
        feature: QgsFeature,
        geom_type: int,
        map_point: QgsPointXY,
    ) -> None:
        if not layer.isEditable():
            self._show_message(
                f"Layer '{layer.name()}' is not in edit mode; toggle editing to rotate features.",
                Qgis.Warning,
            )
            return

        kind: Kind = "line" if geom_type == QgsWkbTypes.LineGeometry else "polygon"
        target_segment: Segment | None = None
        if self.settings.pick_target_segment:
            click_layer = self._point_in_layer_crs(map_point, layer)
            target_segment = _closest_segment_of(feature.geometry(), click_layer)
        rotated = compute_parallel_geometry(
            self._reference_for_layer(layer),
            feature.geometry(),
            kind,
            by_longest=self.settings.by_longest,
            target_segment=target_segment,
        )
        if rotated is None:
            self._show_message("Feature already parallel; no rotation applied.", Qgis.Info)
            return

        layer.beginEditCommand("Parallel to Line")
        ok = layer.changeGeometry(feature.id(), rotated)
        if ok:
            layer.endEditCommand()
            layer.triggerRepaint()
        else:
            layer.destroyEditCommand()
            self._show_message("Failed to update feature geometry.", Qgis.Warning)

    def _set_reference_from_rect(self, map_rect: QgsRectangle) -> None:
        if map_rect.isEmpty():
            return

        canvas = self.iface.mapCanvas()
        found: list[tuple[QgsVectorLayer, QgsFeature]] = []

        for canvas_layer in canvas.layers():
            if not isinstance(canvas_layer, QgsVectorLayer):
                continue
            if canvas_layer.geometryType() != QgsWkbTypes.LineGeometry:
                continue
            layer_rect = self._transform_rect_to_layer(map_rect, canvas_layer)
            rect_geom = QgsGeometry.fromRect(layer_rect)
            request = QgsFeatureRequest().setFilterRect(layer_rect)
            found.extend(
                (canvas_layer, feature)
                for feature in canvas_layer.getFeatures(request)
                if feature.geometry().intersects(rect_geom)
            )

        if not found:
            self._show_message("No line feature in the selection.", Qgis.Info)
            return

        layer, feature = found[0]
        ref_geom = feature.geometry()
        if self.settings.pick_reference_segment:
            layer_rect = self._transform_rect_to_layer(map_rect, layer)
            rect_geom = QgsGeometry.fromRect(layer_rect)
            segment = _pick_segment_in_rect(ref_geom, rect_geom, layer_rect.center())
            ref_geom = QgsGeometry.fromPolylineXY([QgsPointXY(segment.start), QgsPointXY(segment.end)])
        self._set_reference(ref_geom, layer.crs())
        suffix = f" ({len(found)} lines in selection; using topmost)" if len(found) > 1 else ""
        self._show_message(
            f"Reference set{suffix}. Click or drag-rectangle to rotate line/polygon features.",
            Qgis.Success,
        )

    def _rotate_features_in_rect(self, map_rect: QgsRectangle) -> None:
        if map_rect.isEmpty() or self.reference_geom is None:
            return

        canvas = self.iface.mapCanvas()
        rotated_count = 0
        non_editable: list[str] = []

        for canvas_layer in canvas.layers():
            if not isinstance(canvas_layer, QgsVectorLayer):
                continue
            geom_type = canvas_layer.geometryType()
            if geom_type not in (QgsWkbTypes.LineGeometry, QgsWkbTypes.PolygonGeometry):
                continue

            layer_rect = self._transform_rect_to_layer(map_rect, canvas_layer)
            rect_geom = QgsGeometry.fromRect(layer_rect)
            request = QgsFeatureRequest().setFilterRect(layer_rect)
            features = [f for f in canvas_layer.getFeatures(request) if f.geometry().intersects(rect_geom)]
            if not features:
                continue

            if not canvas_layer.isEditable():
                non_editable.append(canvas_layer.name())
                continue

            kind: Kind = "line" if geom_type == QgsWkbTypes.LineGeometry else "polygon"
            layer_rotated = self._rotate_layer_features(canvas_layer, features, kind, layer_rect=layer_rect)
            rotated_count += layer_rotated

        self._report_bulk_result(rotated_count, non_editable)

    def _rotate_layer_features(
        self,
        layer: QgsVectorLayer,
        features: list[QgsFeature],
        kind: Kind,
        *,
        layer_rect: QgsRectangle | None = None,
    ) -> int:
        reference = self._reference_for_layer(layer)
        pick_target = self.settings.pick_target_segment and layer_rect is not None
        rect_geom: QgsGeometry | None = None
        rect_center: QgsPointXY | None = None
        if pick_target and layer_rect is not None:
            rect_geom = QgsGeometry.fromRect(layer_rect)
            rect_center = layer_rect.center()

        layer.beginEditCommand("Parallel to Line (bulk)")
        layer_rotated = 0
        try:
            for feature in features:
                target_segment: Segment | None = None
                if pick_target and rect_geom is not None and rect_center is not None:
                    target_segment = _pick_segment_in_rect(feature.geometry(), rect_geom, rect_center)
                rotated = compute_parallel_geometry(
                    reference,
                    feature.geometry(),
                    kind,
                    by_longest=self.settings.by_longest,
                    target_segment=target_segment,
                )
                if rotated is None:
                    continue
                if layer.changeGeometry(feature.id(), rotated):
                    layer_rotated += 1
        except Exception:
            layer.destroyEditCommand()
            raise

        if layer_rotated:
            layer.endEditCommand()
            layer.triggerRepaint()
        else:
            layer.destroyEditCommand()
        return layer_rotated

    def _report_bulk_result(self, rotated_count: int, non_editable: list[str]) -> None:
        if rotated_count > 0 and non_editable:
            joined = ", ".join(non_editable)
            self._show_message(
                f"Rotated {rotated_count} feature(s). Skipped non-editable layer(s): {joined}.",
                Qgis.Success,
            )
        elif rotated_count > 0:
            self._show_message(f"Rotated {rotated_count} feature(s).", Qgis.Success)
        elif non_editable:
            joined = ", ".join(non_editable)
            self._show_message(
                f"No features rotated. Non-editable layer(s) in selection: {joined}.",
                Qgis.Warning,
            )
        else:
            self._show_message("No features to rotate in the selection.", Qgis.Info)

    def _point_in_layer_crs(self, map_point: QgsPointXY, layer: QgsVectorLayer) -> QgsPointXY:
        map_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        layer_crs = layer.crs()
        if not (map_crs.isValid() and layer_crs.isValid()) or map_crs == layer_crs:
            return map_point
        transform = QgsCoordinateTransform(map_crs, layer_crs, QgsProject.instance())
        return transform.transform(map_point)

    def _transform_rect_to_layer(self, map_rect: QgsRectangle, layer: QgsVectorLayer) -> QgsRectangle:
        map_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        layer_crs = layer.crs()
        if map_crs == layer_crs:
            return map_rect
        transform = QgsCoordinateTransform(map_crs, layer_crs, QgsProject.instance())
        return transform.transformBoundingBox(map_rect)

    def _set_reference(self, geom: QgsGeometry, source_crs: QgsCoordinateReferenceSystem) -> None:
        self._clear_reference()
        reference = QgsGeometry(geom)
        map_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if source_crs.isValid() and map_crs.isValid() and source_crs != map_crs:
            transform = QgsCoordinateTransform(source_crs, map_crs, QgsProject.instance())
            reference.transform(transform)
        self.reference_geom = reference
        rubber_band = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.LineGeometry)
        rubber_band.setColor(self.REFERENCE_COLOR)
        rubber_band.setWidth(self.REFERENCE_WIDTH)
        rubber_band.setToGeometry(self.reference_geom)
        self.reference_rubber_band = rubber_band

    def _reference_for_layer(self, layer: QgsVectorLayer) -> QgsGeometry:
        if self.reference_geom is None:
            msg = "reference must be set before rotation"
            raise RuntimeError(msg)
        map_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        layer_crs = layer.crs()
        if not (map_crs.isValid() and layer_crs.isValid()) or map_crs == layer_crs:
            return self.reference_geom
        transform = QgsCoordinateTransform(map_crs, layer_crs, QgsProject.instance())
        result = QgsGeometry(self.reference_geom)
        result.transform(transform)
        return result

    def _clear_reference(self) -> None:
        self.reference_geom = None
        if self.reference_rubber_band is not None:
            self.iface.mapCanvas().scene().removeItem(self.reference_rubber_band)
            self.reference_rubber_band = None

    def _start_selection_band(self) -> None:
        canvas = self.iface.mapCanvas()
        band = QgsRubberBand(canvas, QgsWkbTypes.PolygonGeometry)
        band.setColor(self.SELECTION_STROKE)
        band.setFillColor(self.SELECTION_FILL)
        band.setWidth(1)
        self._selection_rubber_band = band

    def _update_selection_band(self, current_point: QgsPointXY) -> None:
        if self._selection_rubber_band is None or self._drag_start_point is None:
            return
        rect = QgsRectangle(self._drag_start_point, current_point)
        self._selection_rubber_band.setToGeometry(QgsGeometry.fromRect(rect))

    def _clear_selection_band(self) -> None:
        if self._selection_rubber_band is None:
            return
        self.iface.mapCanvas().scene().removeItem(self._selection_rubber_band)
        self._selection_rubber_band = None

    def _cancel_drag(self) -> None:
        self._clear_selection_band()
        self._drag_start_pos = None
        self._drag_start_point = None
        self._is_dragging = False

    def _show_message(self, text: str, level: Qgis.MessageLevel) -> None:
        self.iface.messageBar().pushMessage("Parallel to Line", text, level=level, duration=10)
