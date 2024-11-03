bl_info = {
    "name": "Export View Layers as PNG Sequence",
    "blender": (3, 0, 0),
    "category": "Render",
}

import bpy
import os

# Global variables to manage render state
render_data = {
    "current_frame": 0,
    "current_layer": 0,
    "total_operations": 0,
    "progress_count": 0,
    "timer_running": False,
}

class RENDER_PT_export_view_layers(bpy.types.Panel):
    """Creates a Panel in the Output Properties for exporting view layers"""
    bl_label = "Export View Layers as PNG Sequence"
    bl_idname = "RENDER_PT_export_view_layers"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        export_props = scene.view_layer_export_props

        layout.prop(export_props, "output_directory")
        layout.prop(export_props, "file_format")
        layout.prop(export_props, "start_frame")
        layout.prop(export_props, "end_frame")
        layout.operator("viewlayer.start_export", text="Export View Layers")
        
        # Display the progress percentage as a slider
        layout.prop(export_props, "progress", slider=True)

class VIEWLAYER_OT_start_export(bpy.types.Operator):
    """Start exporting each view layer as a PNG sequence"""
    bl_label = "Start Export"
    bl_idname = "viewlayer.start_export"

    def execute(self, context):
        scene = context.scene
        export_props = scene.view_layer_export_props

        # Prepare the output directory
        output_dir = bpy.path.abspath(export_props.output_directory)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Set total frame count and initialize global render data
        render_data["current_frame"] = export_props.start_frame
        render_data["current_layer"] = 0
        render_data["total_operations"] = (export_props.end_frame - export_props.start_frame + 1) * len(scene.view_layers)
        render_data["progress_count"] = 0
        render_data["timer_running"] = True

        # Start the timer to handle rendering and updating progress
        bpy.app.timers.register(self.render_step)
        
        return {'FINISHED'}

    def render_step(self):
        """Render one step (one view layer on one frame) and update progress"""
        scene = bpy.context.scene
        export_props = scene.view_layer_export_props

        # Exit timer if rendering is complete
        if not render_data["timer_running"]:
            return None

        # Set current frame and view layer
        frame = render_data["current_frame"]
        scene.frame_set(frame)
        
        view_layer = scene.view_layers[render_data["current_layer"]]
        
        # Temporarily disable all view layers except the current one
        for vl in scene.view_layers:
            vl.use = False
        view_layer.use = True
        bpy.context.window.view_layer = view_layer

        # Set file path and render
        file_path = os.path.join(export_props.output_directory, f"{view_layer.name}_frame{frame:04d}.png")
        scene.render.filepath = file_path
        bpy.ops.render.render(write_still=True)

        # Update progress
        render_data["progress_count"] += 1
        export_props.progress = (render_data["progress_count"] / render_data["total_operations"]) * 100

        # Move to the next view layer or frame
        render_data["current_layer"] += 1
        if render_data["current_layer"] >= len(scene.view_layers):
            render_data["current_layer"] = 0
            render_data["current_frame"] += 1

        # End the process if all frames and layers are done
        if render_data["current_frame"] > export_props.end_frame:
            scene.render.filepath = "//"  # Reset file path
            export_props.progress = 0.0   # Reset progress
            render_data["timer_running"] = False
            self.report({'INFO'}, "All view layers rendered and saved successfully.")
            return None  # Stop the timer

        # Continue the timer for the next render step
        return 0.1  # Run this function again after 0.1 seconds

class ViewLayerExportProperties(bpy.types.PropertyGroup):
    output_directory: bpy.props.StringProperty(
        name="Output Directory",
        description="Directory to save rendered images",
        default="//rendered_layers/",
        subtype='DIR_PATH'
    )
    file_format: bpy.props.EnumProperty(
        name="File Format",
        description="Choose the file format for exported images",
        items=[
            ('PNG', "PNG", ""),
            ('JPEG', "JPEG", ""),
            ('TIFF', "TIFF", ""),
        ],
        default='PNG'
    )
    start_frame: bpy.props.IntProperty(
        name="Start Frame",
        description="Start frame for animation rendering",
        default=1,
        min=1
    )
    end_frame: bpy.props.IntProperty(
        name="End Frame",
        description="End frame for animation rendering",
        default=250,
        min=1
    )
    progress: bpy.props.FloatProperty(
        name="Progress",
        description="Shows the current progress of the export",
        default=0.0,
        min=0.0,
        max=100.0,
        subtype='PERCENTAGE'
    )

def register():
    bpy.utils.register_class(RENDER_PT_export_view_layers)
    bpy.utils.register_class(VIEWLAYER_OT_start_export)
    bpy.utils.register_class(ViewLayerExportProperties)
    bpy.types.Scene.view_layer_export_props = bpy.props.PointerProperty(type=ViewLayerExportProperties)

def unregister():
    bpy.utils.unregister_class(RENDER_PT_export_view_layers)
    bpy.utils.unregister_class(VIEWLAYER_OT_start_export)
    bpy.utils.unregister_class(ViewLayerExportProperties)
    del bpy.types.Scene.view_layer_export_props

if __name__ == "__main__":
    register()
