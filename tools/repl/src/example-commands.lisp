(in-package :generic-repl)

(defun make-example-command-bindings ()
  "Return default example command bindings for the generic skeleton."
  (list
   (cons 'ping (lambda (&optional (value :pong)) (list :ok value)))))
