import os
import numpy as np
from qgis.core import (
    QgsProject, QgsPrintLayout, QgsLayoutItemMap, QgsLayoutExporter,
    QgsStyle, QgsClassificationJenks, QgsGraduatedSymbolRenderer,
    QgsSymbol, QgsRendererRange, QgsLayoutItemLabel, QgsLayoutItemLegend,
    QgsMapLayerLegendUtils, QgsRectangle
)
from qgis.PyQt.QtCore import QRectF
from qgis.PyQt.QtGui import QFont
import jenkspy

layer.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))  # Example: Reproject to WGS 84

# Setup the output directory
output_dir = os.path.join(QgsProject.instance().homePath(), 'figures')
if not os.path.exists(output_dir):
    os.makedirs(output_dir)


def calculate_points_extent(layer):
    # Initialize an empty QgsRectangle
    extent = QgsRectangle()
    extent.setMinimal()
    
    # Iterate over all features in the layer to expand the extent
    for feature in layer.getFeatures():
        extent.combineExtentWith(feature.geometry().boundingBox())
    
    return extent
def calculate_jenks_breaks(values, num_classes):
    numeric_values = [np.nan if not isinstance(value, (int, float)) else value for value in values]
    values_array = np.array(numeric_values, dtype=float)
    finite_values = values_array[np.isfinite(values_array)]
    
    if len(finite_values) > 1:
        return jenkspy.jenks_breaks(finite_values, n_classes=num_classes)
    else:
        return []

def apply_graduated_symbology_and_export(layer, field_name, num_classes=5):
    values = [feature[field_name] for feature in layer.getFeatures() if feature[field_name] is not None]
    breaks = calculate_jenks_breaks(values, num_classes)
    
    if len(breaks) > 1:
        color_ramp = QgsStyle().defaultStyle().colorRamp('Magma')
        ranges = []
        
        for i in range(1, len(breaks)):
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            color = color_ramp.color(float(i-1) / (len(breaks)-2))
            symbol.setColor(color)
            renderer_range = QgsRendererRange(breaks[i-1], breaks[i], symbol, f"{breaks[i-1]} - {breaks[i]}")
            ranges.append(renderer_range)
        
        renderer = QgsGraduatedSymbolRenderer(field_name, ranges)
        layer.setRenderer(renderer)
        layer.triggerRepaint()

    prepare_layout(layer, field_name)

def prepare_layout(layer, field_name):
    project = QgsProject.instance()
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(f"Layout_{field_name}")
    
    # Calculate the extent of the GPS points
    points_extent = calculate_points_extent(layer)
    aspect_ratio = (points_extent.width() / points_extent.height())

    # Example dimensions for A4 size in millimeters
    layout_width_mm = 297  # A4 width
    layout_height_mm = 210  # A4 height

    # Calculate aspect ratio of the points' extent
    aspect_ratio = points_extent.width() / points_extent.height()

    # Start by setting a maximum width and calculating height based on aspect ratio
    max_width_mm = layout_width_mm - 20  # Assuming a 10mm margin on each side
    calculated_height_mm = max_width_mm / aspect_ratio
    
    # If the calculated height is too tall for the page, adjust the width instead
    if calculated_height_mm > (layout_height_mm - 20):  # Assuming a 10mm margin top & bottom
        calculated_height_mm = layout_height_mm - 20  # Adjust height to fit within margins
        max_width_mm = calculated_height_mm * aspect_ratio  # Recalculate width based on adjusted height

    # Map item
    map = QgsLayoutItemMap(layout)
    map_rect = QRectF(0, 0, max_width_mm, calculated_height_mm)  # Set the map rectangle size
    map.setRect(map_rect)
    map.setExtent(points_extent)  # Ensure the map view focuses on your points
    layout.addLayoutItem(map)

    # Title item
    title = QgsLayoutItemLabel(layout)
    title.setText(f"Map of {field_name}")
    title.setFont(QFont("Arial", 16, QFont.Bold))
    title_rect = QRectF(10, 10, 277, 30)  # Adjust width as needed, leaving space for margins
    title.setRect(title_rect)
    layout.addLayoutItem(title)

    export_layout(layout, field_name)

def export_layout(layout, field_name):
    exporter = QgsLayoutExporter(layout)
    output_file = os.path.join(output_dir, f"{field_name}.png")
    exporter.exportToImage(output_file, QgsLayoutExporter.ImageExportSettings())

# Main execution
layer = iface.activeLayer()
exclude_columns = ['GPSLon', 'GPSLat', 'GPSAlt']

for field in layer.fields():
    if field.name().lower() not in exclude_columns:
        apply_graduated_symbology_and_export(layer, field.name())