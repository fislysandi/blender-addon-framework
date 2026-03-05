(defpackage :generic-repl-tests
  (:use :cl :rove)
  (:import-from :generic-repl
                :make-registry
                :install-commands
                :unregister-command
                :load-command-bindings
                :load-framework-bindings
                :switch-framework-bindings
                :active-frameworks
                :set-active-frameworks
                :register-command
                :dispatch-command
                :set-execute-enabled
                :execute-enabled-p
                :python-call-expression
                :python-dict-literal
                :parse-form
                :eval-form))
