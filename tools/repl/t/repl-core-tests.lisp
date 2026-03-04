(in-package :generic-repl-tests)

(def-suite :generic-repl-tests)
(in-suite :generic-repl-tests)

(test parse-form-valid
  (is (equal '(ping 1) (parse-form "(ping 1)"))))

(test parse-form-invalid
  (is (eql :invalid (parse-form "(ping 1"))))

(test dispatch-registered-command
  (let ((registry (make-registry)))
    (register-command registry 'ping (lambda (value) (list :ok value)))
    (is (equal '(:ok 42) (eval-form registry '(ping 42))))))

(test dispatch-missing-command
  (let ((registry (make-registry)))
    (is (equal '(:error :unknown-command :name ping)
               (eval-form registry '(ping))))))

(test install-commands-binds-handlers
  (let ((registry (make-registry)))
    (install-commands
     registry
     (list (cons 'hello (lambda (name) (list :hello name)))))
    (is (equal '(:hello "world")
               (dispatch-command registry 'hello "world")))))

(test load-command-bindings-loads-examples
  (let ((registry (make-registry)))
    (install-commands registry (load-command-bindings '(:examples)))
    (is (equal '(:ok :pong)
               (eval-form registry '(ping))))
    (is (equal '(:ok 7)
               (eval-form registry '(ping 7))))))

(test load-framework-bindings-loads-multiple-frameworks
  (let ((registry (make-registry)))
    (install-commands registry (load-framework-bindings '(:blender :krita)))
    (is (equal '(:framework :blender :adapter :loaded)
               (eval-form registry '(blender-ping))))
    (is (equal '(:framework :krita :adapter :loaded)
               (eval-form registry '(krita-ping))))))

(test blender-mesh-cube-command-returns-normalized-call-spec
  (let ((registry (make-registry)))
    (install-commands registry (load-framework-bindings '(:blender)))
    (is (equal '(:framework :blender
                 :target "bpy.ops.mesh.primitive_cube_add"
                 :kwargs (:size 2.0 :location (0 0 0) :align "WORLD"))
               (eval-form registry '(mesh-cube))))
    (is (equal '(:framework :blender
                 :target "bpy.ops.mesh.primitive_cube_add"
                 :kwargs (:size 4 :location (1 2 3) :align "VIEW"))
               (eval-form registry '(mesh-cube :size 4 :location (1 2 3) :align "VIEW"))))))

(test krita-new-document-command-returns-normalized-call-spec
  (let ((registry (make-registry)))
    (install-commands registry (load-framework-bindings '(:krita)))
    (is (equal '(:framework :krita
                 :target "Krita.instance().createDocument"
                 :kwargs (:width 1920
                          :height 1080
                          :name "Untitled"
                          :color-model "RGBA"
                          :color-depth "U8"
                          :profile "sRGB-elle-V2-srgbtrc.icc"))
               (eval-form registry '(new-document))))
    (is (equal '(:framework :krita
                 :target "Krita.instance().createDocument"
                 :kwargs (:width 512
                          :height 512
                          :name "Icon"
                          :color-model "RGBA"
                          :color-depth "F16"
                          :profile "Linear"))
               (eval-form registry
                          '(new-document :width 512 :height 512 :name "Icon"
                                         :color-depth "F16" :profile "Linear"))))))

(test python-dict-literal-renders-stable-dict
  (is (equal "{'size': 2, 'align': 'WORLD', 'location': [0, 0, 0]}"
             (python-dict-literal
              '(:size 2 :align "WORLD" :location (0 0 0))))))

(test python-call-expression-renders-target-and-kwargs
  (is (equal "bpy.ops.mesh.primitive_cube_add(**{'size': 2, 'align': 'WORLD'})"
             (python-call-expression
              "bpy.ops.mesh.primitive_cube_add"
              '(:size 2 :align "WORLD")))))

(test execute-flag-toggles
  (set-execute-enabled nil)
  (is (not (execute-enabled-p)))
  (set-execute-enabled t)
  (is (execute-enabled-p))
  (set-execute-enabled nil)
  (is (not (execute-enabled-p))))

(test execute-mode-blocked-by-default-for-adapter-commands
  (set-execute-enabled nil)
  (let ((registry (make-registry)))
    (install-commands registry (load-framework-bindings '(:blender :krita)))
    (is (equal '(:error :execute-mode-disabled :reason :set-allow-execute-true)
               (eval-form registry '(mesh-cube :mode :execute))))
    (is (equal '(:error :execute-mode-disabled :reason :set-allow-execute-true)
               (eval-form registry '(new-document :mode :execute))))))

(test set-execute-form-toggles-runtime-flag
  (set-execute-enabled nil)
  (let ((registry (make-registry)))
    (is (equal '(:ok :execute-enabled t)
               (eval-form registry '(set-execute! true))))
    (is (equal '(:ok :execute-enabled t)
               (eval-form registry '(execute-enabled?))))
    (is (equal '(:ok :execute-enabled nil)
               (eval-form registry '(set-execute! false))))
    (is (equal '(:ok :execute-enabled nil)
               (eval-form registry '(execute-enabled?))))))

(test set-execute-form-validates-boolean-input
  (let ((registry (make-registry)))
    (is (equal '(:error :invalid-boolean :value maybe)
               (eval-form registry '(set-execute! maybe))))))

(test active-frameworks-form-reports-current-frameworks
  (set-active-frameworks '(:blender))
  (let ((registry (make-registry)))
    (is (equal '(:ok :frameworks (:blender))
               (eval-form registry '(active-frameworks?))))))

(test set-frameworks-form-switches-framework-bindings
  (set-active-frameworks '())
  (let ((registry (make-registry)))
    (install-commands registry (load-framework-bindings '(:blender)))
    (set-active-frameworks '(:blender))
    (is (equal '(:framework :blender :adapter :loaded)
               (eval-form registry '(blender-ping))))
    (is (equal '(:ok :frameworks (:krita))
               (eval-form registry '(set-frameworks! (:krita)))))
    (is (equal '(:error :unknown-command :name blender-ping)
               (eval-form registry '(blender-ping))))
    (is (equal '(:framework :krita :adapter :loaded)
               (eval-form registry '(krita-ping))))))
