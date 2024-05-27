import bpy
import math
import mathutils

def update_rotation(self, context):
    armature_obj = context.scene.objects.get(context.scene.selected_armature)
    if not armature_obj or armature_obj.type != 'ARMATURE':
        return
    limb_bone = armature_obj.pose.bones.get(context.scene.selected_bone)
    if not limb_bone:
        return

    rotation_order = context.scene.transformation_order

    if rotation_order == 'XYZ':
        rotation_x_rad = math.radians(context.scene.rotation_x)
        rotation_y_rad = math.radians(context.scene.rotation_y)
        rotation_z_rad = math.radians(context.scene.rotation_z)
    else:
        rotation_z_rad = math.radians(context.scene.rotation_z)
        rotation_y_rad = math.radians(context.scene.rotation_y)
        rotation_x_rad = math.radians(context.scene.rotation_x)

    if rotation_order == 'XYZ':
        limb_bone.rotation_euler = (rotation_x_rad, rotation_y_rad, rotation_z_rad)
    else:
        limb_bone.rotation_euler = (rotation_z_rad, rotation_y_rad, rotation_x_rad)

def update_location_handler(scene):
    armature_obj = bpy.data.objects.get(scene.selected_armature)
    if armature_obj:
        limb_bone = armature_obj.pose.bones.get(scene.selected_bone)
        if limb_bone:
            translation = limb_bone.matrix.to_translation()
            scene.location_x = translation.x
            scene.location_y = translation.y
            scene.location_z = translation.z

class LimbPositionAddonPanel(bpy.types.Panel):
    bl_label = "Limb Position Addon"
    bl_idname = "OBJECT_PT_limb_position_addon"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Limb Position'

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'ARMATURE'

    def draw(self, context):
        layout = self.layout

        layout.label(text="Armature Selection:")
        row = layout.row()
        row.prop_search(context.scene, "selected_armature", bpy.data, "objects", text="")
        row.operator("object.armature_eyedropper", text="", icon='BONE_DATA')

        layout.label(text="Limb Selection:")
        row = layout.row()
        row.prop_search(context.scene, "selected_bone", bpy.context.active_object.data, "bones", text="")
        row.operator("object.select_bone", text="", icon='BONE_DATA')

        layout.label(text="Rotation (degrees):")
        col = layout.column(align=True)
        col.prop(context.scene, "rotation_x", text="X")
        col.prop(context.scene, "rotation_y", text="Y")
        col.prop(context.scene, "rotation_z", text="Z")

        layout.prop(context.scene, "transformation_order", text="Transformation Order")

        layout.operator("object.clear_limb_position", text="Clear")
        layout.operator("object.apply_limb_position")
        layout.operator("object.reset_to_rest_position", text="Reset to Rest Position")
        layout.operator("object.insert_keyframe", text="Insert Keyframe")

class ApplyLimbPositionOperator(bpy.types.Operator):
    bl_label = "Apply Limb Position"
    bl_idname = "object.apply_limb_position"

    transformation_order: bpy.props.EnumProperty(
        items=[('XYZ', "XYZ", "Apply Rotation then Translation"),
               ('ZYX', "ZYX", "Apply Translation then Rotation")],
        default='XYZ',
        name="Transformation Order"
    )

    def execute(self, context):
        armature_obj = context.scene.objects.get(context.scene.selected_armature)
        if not armature_obj or armature_obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Selected object is not an armature")
            return {'CANCELLED'}

        limb_bone = armature_obj.pose.bones.get(context.scene.selected_bone)
        if not limb_bone:
            self.report({'ERROR'}, "Selected bone not found in armature")
            return {'CANCELLED'}

        if self.transformation_order == 'XYZ':
            transformation_matrix = (
                mathutils.Matrix.Translation((context.scene.location_x, context.scene.location_y, context.scene.location_z)) @
                mathutils.Euler((math.radians(context.scene.rotation_x), math.radians(context.scene.rotation_y), math.radians(context.scene.rotation_z)), 'XYZ').to_matrix().to_4x4()
            )
        else:
            transformation_matrix = (
                mathutils.Matrix.Translation((context.scene.location_x, context.scene.location_y, context.scene.location_z)) @
                mathutils.Euler((math.radians(context.scene.rotation_z), math.radians(context.scene.rotation_y), math.radians(context.scene.rotation_x)), 'ZYX').to_matrix().to_4x4()
            )

        limb_bone.matrix = transformation_matrix

        bpy.context.view_layer.update()
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        return {'FINISHED'}

class ClearLimbPositionOperator(bpy.types.Operator):
    bl_label = "Clear Limb Position"
    bl_idname = "object.clear_limb_position"

    def execute(self, context):
        context.scene.rotation_x = 0
        context.scene.rotation_y = 0
        context.scene.rotation_z = 0
        return {'FINISHED'}

class ArmatureEyedropperOperator(bpy.types.Operator):
    bl_label = "Armature Eyedropper"
    bl_idname = "object.armature_eyedropper"

    def modal(self, context, event):
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            bpy.context.scene.selected_armature = bpy.context.active_object.name
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class BoneSelectorOperator(bpy.types.Operator):
    bl_label = "Select Bone"
    bl_idname = "object.select_bone"

    def execute(self, context):
        if context.active_pose_bone:
            bpy.context.scene.selected_bone = bpy.context.active_pose_bone.name

            armature_obj = context.scene.objects.get(context.scene.selected_armature)
            if armature_obj and armature_obj.type == 'ARMATURE':
                limb_bone = armature_obj.pose.bones.get(context.scene.selected_bone)
                if limb_bone:
                    translation = limb_bone.matrix.to_translation()
                    bpy.context.scene.location_x = translation.x
                    bpy.context.scene.location_y = translation.y
                    bpy.context.scene.location_z = translation.z

        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return context.active_pose_bone is not None

class BoneDoubleClickOperator(bpy.types.Operator):
    bl_idname = "object.bone_double_click"
    bl_label = "Bone Double Click"
    
    def modal(self, context, event):
        if event.type == 'LEFTMOUSE' and event.value == 'DOUBLE_CLICK':
            bpy.ops.object.select_bone()
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            return {'CANCELLED'}
        return {'PASS'}
    
    def invoke(self, context, event):
        self.execute(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        return {'FINISHED'}

class ResetToRestPositionOperator(bpy.types.Operator):
    bl_label = "Reset to Rest Position"
    bl_idname = "object.reset_to_rest_position"

    def execute(self, context):
        armature_obj = context.scene.objects.get(context.scene.selected_armature)
        if not armature_obj or armature_obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Selected object is not an armature")
            return {'CANCELLED'}

        for bone in armature_obj.pose.bones:
            bone.matrix_basis.identity()

        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        return {'FINISHED'}

class InsertKeyframeOperator(bpy.types.Operator):
    bl_label = "Insert Keyframe"
    bl_idname = "object.insert_keyframe"

    def execute(self, context):
        armature_obj = context.scene.objects.get(context.scene.selected_armature)
        if not armature_obj or armature_obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Selected object is not an armature")
            return {'CANCELLED'}

        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.anim.keyframe_insert_menu(type='LocRot')

        return {'FINISHED'}

bpy.types.Scene.location_x = bpy.props.FloatProperty(name="Location X")
bpy.types.Scene.location_y = bpy.props.FloatProperty(name="Location Y")
bpy.types.Scene.location_z = bpy.props.FloatProperty(name="Location Z")

def register():
    bpy.utils.register_class(LimbPositionAddonPanel)
    bpy.utils.register_class(ApplyLimbPositionOperator)
    bpy.utils.register_class(ClearLimbPositionOperator)
    bpy.utils.register_class(ArmatureEyedropperOperator)
    bpy.utils.register_class(BoneSelectorOperator)
    bpy.utils.register_class(BoneDoubleClickOperator)
    bpy.utils.register_class(ResetToRestPositionOperator)
    bpy.utils.register_class(InsertKeyframeOperator)
    bpy.types.Scene.selected_armature = bpy.props.StringProperty(name="Selected Armature")
    bpy.types.Scene.selected_bone = bpy.props.StringProperty(name="Selected Bone")
    bpy.types.Scene.rotation_x = bpy.props.FloatProperty(name="Rotation X", update=update_rotation)
    bpy.types.Scene.rotation_y = bpy.props.FloatProperty(name="Rotation Y", update=update_rotation)
    bpy.types.Scene.rotation_z = bpy.props.FloatProperty(name="Rotation Z", update=update_rotation)
    bpy.types.Scene.transformation_order = bpy.props.EnumProperty(
        items=[('XYZ', "XYZ", "Apply Rotation then Translation"),
               ('ZYX', "ZYX", "Apply Translation then Rotation")],
        default='XYZ',
        name="Transformation Order"
    )

    bpy.app.handlers.frame_change_post.append(update_location_handler)

def unregister():
    bpy.utils.unregister_class(LimbPositionAddonPanel)
    bpy.utils.unregister_class(ApplyLimbPositionOperator)
    bpy.utils.unregister_class(ClearLimbPositionOperator)
    bpy.utils.unregister_class(ArmatureEyedropperOperator)
    bpy.utils.unregister_class(BoneSelectorOperator)
    bpy.utils.unregister_class(BoneDoubleClickOperator)
    bpy.utils.unregister_class(ResetToRestPositionOperator)
    bpy.utils.unregister_class(InsertKeyframeOperator)
    del bpy.types.Scene.selected_armature
    del bpy.types.Scene.selected_bone
    del bpy.types.Scene.rotation_x
    del bpy.types.Scene.rotation_y
    del bpy.types.Scene.rotation_z
    del bpy.types.Scene.transformation_order

    bpy.app.handlers.frame_change_post.remove(update_location_handler)

if __name__ == "__main__":
    register()
