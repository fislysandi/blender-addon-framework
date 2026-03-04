(defpackage :generic-repl
  (:use :cl)
  (:export
   :load-config
   :make-registry
   :install-commands
   :unregister-command
   :load-command-bindings
   :load-framework-bindings
   :switch-framework-bindings
   :active-frameworks
   :set-active-frameworks
   :make-example-command-bindings
   :register-command
   :resolve-command
   :dispatch-command
   :set-execute-enabled
   :execute-enabled-p
   :python-call-expression
   :python-dict-literal
   :parse-form
   :eval-form
   :start-repl))
