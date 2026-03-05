(asdf:defsystem "bdocgen"
  :description "Minimal Common Lisp documentation generator tool"
  :author "blender-addon-framework contributors"
  :license "MIT"
  :serial t
  :components
  ((:file "packages")
   (:file "src/fs")
   (:file "src/core")
   (:file "src/cli"))
  :in-order-to ((test-op (test-op "bdocgen/tests"))))

(asdf:defsystem "bdocgen/server"
  :description "BDocGen rebuild and local server helpers"
  :depends-on ("bdocgen" "hunchentoot")
  :serial t
  :components
  ((:file "src/server")))

(asdf:defsystem "bdocgen/tests"
  :depends-on ("bdocgen" "fiveam")
  :serial t
  :components ((:file "t/packages")
               (:file "t/core-tests"))
  :perform (test-op (o c)
                    (declare (ignore o c))
                    (uiop:symbol-call :fiveam :run! :bdocgen-tests)))
