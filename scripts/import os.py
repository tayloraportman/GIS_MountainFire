import os
import qgis.core as qgc
from qgis.core import QgsProject, QgsPrintLayout, QgsLayoutItemMap, QgsLayoutExporter, QgsRectangle
from qgis.PyQt.QtCore import QSizeF
import jenkspy

# Assuming this directory structure, adjust as necessary
output_dir = os.path.join(QgsProject.instance().homePath(), 'figures')
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def calculate_jenks_breaks(values, num_classes):
    breaks = jenkspy.jenks_breaks(values, nb_class=num_classes)
    return breaks

def apply_graduated_symbology_and_export(layer, field_name):
    # Calculating breaks and applying symbology
    values = [feature[field_name] for feature in layer.getFeatures()]
    num_classes = 5  # Example: aiming for 5 classes
    breaks = calculate_jenks_breaks(values, num_classes)

    # Create a graduated symbol renderer
    renderer = qgc.QgsGraduatedSymbolRenderer()
    renderer.setClassAttribute(field_name)
    
    # Define the color ramp
    color_ramp = qgc.QgsStyle().defaultStyle().colorRamp('Magma')
    
    # Create classification ranges
    ranges = []
    for i in range(1, len(breaks)):
        symbol = qgc.QgsSymbol.defaultSymbol(layer.geometryType())
        symbol.setColor(color_ramp.color(float(i) / (len(breaks) - 1)))
        rng = qgc.QgsRendererRange(breaks[i-1], breaks[i], symbol, f"{breaks[i-1]} - {breaks[i]}")
        ranges.append(rng)
    
    # Apply the renderer to the layer
    renderer.setRanges(ranges)
    layer.setRenderer(renderer)
    layer.triggerRepaint()
    # After applying symbology:
    
    project = QgsProject.instance()
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(f"Layout_{field_name}")
    
    # Create a map item in the layout
    map = QgsLayoutItemMap(layout)
    map.setRect(20, 20, 20, 20)  # Adjust dimensions as needed
    
    # Set the map extent to the layer's extent
    map.setExtent(layer.extent())
    layout.addLayoutItem(map)
    
    map.attemptMove(QgsLayoutItem.MapPos0)
    map.attemptResize(QSizeF(200, 200))  # Adjust size as needed

    # Export the layout
    exporter = QgsLayoutExporter(layout)
    output_file = os.path.join(output_dir, f"{field_name}.png")
    exporter.exportToImage(output_file, QgsLayoutExporter.ImageExportSettings())
    
    # Optionally, remove the layout after export to avoid cluttering the project
    project.layoutManager().removeLayout(layout)

# Main logic to apply symbology and export maps
layer = iface.activeLayer()  # Assuming layer is active, or set it programmatically
exclude_columns = ['GPSLon', 'GPSLat', 'GPSAlt']

for field in layer.fields():
    if field.name().lower() not in exclude_columns:
        apply_graduated_symbology_and_export(layer, field.name())
