(in-package :generic-repl)

(defun blender-ping-handler ()
  "Return adapter status for Blender bindings."
  (list :framework :blender :adapter :loaded))

(defun blender-option-value (options key default)
  "Read KEY from OPTIONS plist and return DEFAULT when missing."
  (let ((value (getf options key :missing)))
    (if (eq value :missing) default value)))

(defun blender-command-mode (options)
  "Read command execution mode from OPTIONS."
  (blender-option-value options :mode :plan))

(defun blender-normalize-cube-options (options)
  "Normalize cube OPTIONS into a stable call contract."
  (list
   :size (blender-option-value options :size 2.0)
   :location (blender-option-value options :location '(0 0 0))
   :align (blender-option-value options :align "WORLD")))

(defun blender-mesh-cube-call-spec (options)
  "Build host-specific call spec for Blender cube creation."
  (list
   :framework :blender
   :target "bpy.ops.mesh.primitive_cube_add"
   :kwargs (blender-normalize-cube-options options)))

(defun blender-mesh-cube-handler (&rest options)
  "Translate mesh-cube command form to plan or execute mode."
  (let ((call-spec (blender-mesh-cube-call-spec options)))
    (if (eq (blender-command-mode options) :execute)
        (python-execute-call-spec call-spec)
        call-spec)))

(defun make-blender-command-bindings ()
  "Return command bindings for Blender adapter."
  (list
   (cons 'blender-ping #'blender-ping-handler)
   (cons 'mesh-cube #'blender-mesh-cube-handler)))
