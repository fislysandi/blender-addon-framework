(in-package :generic-repl)

(defparameter *active-frameworks* '()
  "Active framework keys for current REPL session.")

(defun active-frameworks ()
  "Return active frameworks for current REPL session."
  *active-frameworks*)

(defun set-active-frameworks (frameworks)
  "Set active FRAMEWORKS and return normalized value."
  (setf *active-frameworks* (normalize-framework-list frameworks)))

(defun load-command-bindings (autoload-commands)
  "Load command bindings for AUTOLOAD-COMMANDS module keys."
  (append-bindings
   (mapcar #'command-bindings-for-module autoload-commands)))

(defun load-framework-bindings (frameworks)
  "Load command bindings for framework keys.
FRAMEWORKS is a list such as (:blender :krita)."
  (append-bindings
   (mapcar #'command-bindings-for-framework
           (normalize-framework-list frameworks))))

(defun switch-framework-bindings (registry frameworks)
  "Switch REGISTRY framework bindings to FRAMEWORKS and return active list."
  (let ((previous (active-frameworks))
        (next (normalize-framework-list frameworks)))
    (uninstall-framework-bindings registry previous)
    (install-commands registry (load-framework-bindings next))
    (set-active-frameworks next)))

(defun uninstall-framework-bindings (registry frameworks)
  "Remove all command bindings associated with FRAMEWORKS from REGISTRY."
  (dolist (name (framework-command-names frameworks) registry)
    (unregister-command registry name)))

(defun append-bindings (binding-lists)
  "Flatten BINDING-LISTS into one binding list."
  (apply #'append binding-lists))

(defun framework-command-names (frameworks)
  "Return command names contributed by FRAMEWORKS."
  (mapcar #'car (load-framework-bindings frameworks)))

(defun normalize-framework-key (framework)
  "Normalize FRAMEWORK value into a keyword key."
  (cond
    ((keywordp framework) framework)
    ((symbolp framework) (intern (symbol-name framework) :keyword))
    (t framework)))

(defun normalize-framework-list (frameworks)
  "Normalize FRAMEWORKS into an ordered duplicate-free keyword list."
  (let ((result '()))
    (dolist (framework frameworks (nreverse result))
      (let ((normalized (normalize-framework-key framework)))
        (when (and (keywordp normalized)
                   (not (member normalized result :test #'eq)))
          (push normalized result))))))

(defun command-bindings-for-module (module-key)
  "Return command bindings for MODULE-KEY."
  (case module-key
    (:examples (make-example-command-bindings))
    (otherwise '())))

(defun command-bindings-for-framework (framework-key)
  "Return command bindings for FRAMEWORK-KEY."
  (case framework-key
    (:blender (make-blender-command-bindings))
    (:krita (make-krita-command-bindings))
    (otherwise '())))
