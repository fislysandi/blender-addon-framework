(in-package :generic-repl)

(defun command-key (name)
  "Normalize NAME into a registry key string."
  (string-downcase
   (cond
     ((symbolp name) (symbol-name name))
     ((stringp name) name)
     (t (princ-to-string name)))))

(defun make-registry ()
  "Create an empty command registry."
  (make-hash-table :test 'equal))

(defun register-command (registry name fn)
  "Register FN for NAME in REGISTRY and return REGISTRY."
  (setf (gethash (command-key name) registry) fn)
  registry)

(defun unregister-command (registry name)
  "Remove NAME from REGISTRY and return REGISTRY."
  (remhash (command-key name) registry)
  registry)

(defun install-commands (registry command-bindings)
  "Load COMMAND-BINDINGS into REGISTRY and return REGISTRY.
COMMAND-BINDINGS is an alist of (command-symbol . function)."
  (dolist (entry command-bindings registry)
    (register-command registry (car entry) (cdr entry))))

(defun resolve-command (registry name)
  "Resolve NAME in REGISTRY or return NIL when missing."
  (gethash (command-key name) registry))

(defun dispatch-command (registry name &rest args)
  "Call the command mapped by NAME using ARGS."
  (let ((handler (resolve-command registry name)))
    (if handler
        (apply handler args)
        (list :error :unknown-command :name name))))
