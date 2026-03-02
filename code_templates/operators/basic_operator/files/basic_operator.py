import bpy


class {{addon_name}}OT_basic_operator(bpy.types.Operator):
    bl_idname = "{{addon_name}}.basic_operator"
    bl_label = "{{addon_name}} Basic Operator"
    bl_description = "Reusable operator scaffold"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context is not None

    def execute(self, context):
        try:
            self.report({"INFO"}, "Operator executed")
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"}, f"Operation failed: {error}")
            return {"CANCELLED"}
