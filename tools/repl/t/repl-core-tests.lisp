(in-package :generic-repl-tests)

(deftest parse-form-valid
  (ok (equal '(ping 1) (parse-form "(ping 1)"))))

(deftest parse-form-invalid
  (ok (eql :invalid (parse-form "(ping 1"))))

(deftest dispatch-registered-command
  (let ((registry (make-registry)))
    (register-command registry 'ping (lambda (value) (list :ok value)))
    (ok (equal '(:ok 42) (eval-form registry '(ping 42))))))

(deftest dispatch-missing-command
  (let ((registry (make-registry)))
    (ok (equal '(:error :unknown-command :name ping)
               (eval-form registry '(ping))))))

(deftest install-commands-binds-handlers
  (let ((registry (make-registry)))
    (install-commands
     registry
     (list (cons 'hello (lambda (name) (list :hello name)))))
    (ok (equal '(:hello "world")
               (dispatch-command registry 'hello "world")))))

(deftest load-command-bindings-loads-examples
  (let ((registry (make-registry)))
    (install-commands registry (load-command-bindings '(:examples)))
    (ok (equal '(:ok :pong)
               (eval-form registry '(ping))))
    (ok (equal '(:ok 7)
               (eval-form registry '(ping 7))))))

(deftest load-framework-bindings-loads-multiple-frameworks
  (let ((registry (make-registry)))
    (install-commands registry (load-framework-bindings '(:blender :krita)))
    (ok (equal '(:framework :blender :adapter :loaded)
               (eval-form registry '(blender-ping))))
    (ok (equal '(:framework :krita :adapter :loaded)
               (eval-form registry '(krita-ping))))))

(deftest blender-mesh-cube-command-returns-normalized-call-spec
  (let ((registry (make-registry)))
    (install-commands registry (load-framework-bindings '(:blender)))
    (ok (equal '(:framework :blender
                 :target "bpy.ops.mesh.primitive_cube_add"
                 :kwargs (:size 2.0 :location (0 0 0) :align "WORLD"))
               (eval-form registry '(mesh-cube))))
    (ok (equal '(:framework :blender
                 :target "bpy.ops.mesh.primitive_cube_add"
                 :kwargs (:size 4 :location (1 2 3) :align "VIEW"))
               (eval-form registry '(mesh-cube :size 4 :location (1 2 3) :align "VIEW"))))))

(deftest krita-new-document-command-returns-normalized-call-spec
  (let ((registry (make-registry)))
    (install-commands registry (load-framework-bindings '(:krita)))
    (ok (equal '(:framework :krita
                 :target "Krita.instance().createDocument"
                 :kwargs (:width 1920
                          :height 1080
                          :name "Untitled"
                          :color-model "RGBA"
                          :color-depth "U8"
                          :profile "sRGB-elle-V2-srgbtrc.icc"))
               (eval-form registry '(new-document))))
    (ok (equal '(:framework :krita
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

(deftest python-dict-literal-renders-stable-dict
  (ok (equal "{'size': 2, 'align': 'WORLD', 'location': [0, 0, 0]}"
             (python-dict-literal
              '(:size 2 :align "WORLD" :location (0 0 0))))))

(deftest python-call-expression-renders-target-and-kwargs
  (ok (equal "bpy.ops.mesh.primitive_cube_add(**{'size': 2, 'align': 'WORLD'})"
             (python-call-expression
              "bpy.ops.mesh.primitive_cube_add"
              '(:size 2 :align "WORLD")))))

(deftest execute-flag-toggles
  (set-execute-enabled nil)
  (ok (not (execute-enabled-p)))
  (set-execute-enabled t)
  (ok (execute-enabled-p))
  (set-execute-enabled nil)
  (ok (not (execute-enabled-p))))

(deftest execute-mode-blocked-by-default-for-adapter-commands
  (set-execute-enabled nil)
  (let ((registry (make-registry)))
    (install-commands registry (load-framework-bindings '(:blender :krita)))
    (ok (equal '(:error :execute-mode-disabled :reason :set-allow-execute-true)
               (eval-form registry '(mesh-cube :mode :execute))))
    (ok (equal '(:error :execute-mode-disabled :reason :set-allow-execute-true)
               (eval-form registry '(new-document :mode :execute))))))

(deftest set-execute-form-toggles-runtime-flag
  (set-execute-enabled nil)
  (let ((registry (make-registry)))
    (ok (equal '(:ok :execute-enabled t)
               (eval-form registry '(set-execute! true))))
    (ok (equal '(:ok :execute-enabled t)
               (eval-form registry '(execute-enabled?))))
    (ok (equal '(:ok :execute-enabled nil)
               (eval-form registry '(set-execute! false))))
    (ok (equal '(:ok :execute-enabled nil)
               (eval-form registry '(execute-enabled?))))))

(deftest set-execute-form-validates-boolean-input
  (let ((registry (make-registry)))
    (ok (equal '(:error :invalid-boolean :value maybe)
               (eval-form registry '(set-execute! maybe))))))

(deftest active-frameworks-form-reports-current-frameworks
  (set-active-frameworks '(:blender))
  (let ((registry (make-registry)))
    (ok (equal '(:ok :frameworks (:blender))
               (eval-form registry '(active-frameworks?))))))

(deftest set-frameworks-form-switches-framework-bindings
  (set-active-frameworks '())
  (let ((registry (make-registry)))
    (install-commands registry (load-framework-bindings '(:blender)))
    (set-active-frameworks '(:blender))
    (ok (equal '(:framework :blender :adapter :loaded)
               (eval-form registry '(blender-ping))))
    (ok (equal '(:ok :frameworks (:krita))
               (eval-form registry '(set-frameworks! (:krita)))))
    (ok (equal '(:error :unknown-command :name blender-ping)
               (eval-form registry '(blender-ping))))
    (ok (equal '(:framework :krita :adapter :loaded)
               (eval-form registry '(krita-ping))))))
