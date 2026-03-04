(in-package :generic-repl)

(defun load-config (&optional (path "tools/repl/config.lisp"))
  "Load REPL config data from PATH and return a property list."
  (with-open-file (stream path :direction :input)
    (read stream nil '())))
