(asdf:defsystem "generic-repl"
  :description "Minimal generic Common Lisp REPL skeleton"
  :author "blender-addon-framework contributors"
  :license "MIT"
  :depends-on ("py4cl2-cffi")
  :serial t
  :components
  ((:file "packages")
   (:file "src/config")
   (:file "src/command-registry")
   (:file "src/example-commands")
   (:file "src/python-bridge")
   (:file "src/framework-commands")
   (:module "blender_adapter"
     :pathname "../adapters/blender_adapter"
     :components ((:file "bindings")))
   (:module "krita_adapter"
    :pathname "../adapters/krita_adapter"
    :components ((:file "bindings")))
   (:file "src/command-loader")
   (:file "src/repl-core"))
  :in-order-to ((test-op (test-op "generic-repl/tests"))))

(asdf:defsystem "generic-repl/tests"
  :depends-on ("generic-repl" "fiveam")
  :serial t
  :components ((:file "t/packages")
               (:file "t/repl-core-tests")
               (:file "t/framework-command-tests"))
  :perform (test-op (o c)
                    (declare (ignore o c))
                    (uiop:symbol-call :fiveam :run! :generic-repl-tests)))
