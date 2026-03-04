(in-package :generic-repl)

(defun parse-form (line)
  "Parse LINE into a Lisp object or return :INVALID for bad input."
  (handler-case
      (read-from-string line)
    (error () :invalid)))

(defun operator-name (op)
  "Convert OP into a normalized command/operator name string."
  (string-downcase
   (if (symbolp op)
       (symbol-name op)
       (princ-to-string op))))

(defun eval-form (registry form)
  "Evaluate FORM through REGISTRY dispatch.
Expected shape: (command arg1 arg2 ...)."
  (if (or (atom form) (null form))
      (list :error :invalid-form :value form)
      (or (handle-runtime-control-form registry form)
          (apply #'dispatch-command registry (first form) (rest form)))))

(defun boolean-literal-value (value)
  "Coerce VALUE to boolean or return :INVALID when unsupported."
  (let ((normalized
          (cond
            ((or (eq value t) (null value)) value)
            ((symbolp value) (string-downcase (symbol-name value)))
            ((stringp value) (string-downcase value))
            (t value))))
    (cond
      ((or (eq normalized t) (equal normalized "true")) t)
      ((or (null normalized) (equal normalized "false")) nil)
      (t :invalid))))

(defun parse-framework-list-argument (arg)
  "Parse ARG as framework list or return :INVALID."
  (if (listp arg)
      (normalize-framework-list arg)
      :invalid))

(defun handle-runtime-control-form (registry form)
  "Handle built-in runtime control forms and return result or NIL."
  (let ((op (operator-name (first form)))
        (args (rest form)))
    (cond
      ((string= op "set-execute!")
       (if (/= (length args) 1)
           (list :error :invalid-form :usage "(set-execute! true|false)")
           (let ((enabled (boolean-literal-value (first args))))
             (if (eq enabled :invalid)
                 (list :error :invalid-boolean :value (first args))
                 (progn
                   (set-execute-enabled enabled)
                   (list :ok :execute-enabled (execute-enabled-p)))))))
      ((string= op "execute-enabled?")
       (if args
           (list :error :invalid-form :usage "(execute-enabled?)")
           (list :ok :execute-enabled (execute-enabled-p))))
      ((string= op "set-frameworks!")
       (if (/= (length args) 1)
           (list :error :invalid-form :usage "(set-frameworks! (:blender :krita))")
           (let ((frameworks (parse-framework-list-argument (first args))))
             (if (eq frameworks :invalid)
                 (list :error :invalid-framework-list :value (first args))
                 (list :ok :frameworks
                       (switch-framework-bindings registry frameworks))))))
      ((string= op "active-frameworks?")
       (if args
           (list :error :invalid-form :usage "(active-frameworks?)")
           (list :ok :frameworks (active-frameworks))))
      (t nil))))

(defun config-value (config key &optional default)
  "Read KEY from CONFIG plist and return DEFAULT when missing."
  (let ((value (getf config key :missing)))
    (if (eq value :missing) default value)))

(defun start-repl
    (&key registry command-bindings prompt (config-path "tools/repl/config.lisp"))
  "Start a minimal interactive REPL loop.
Type (quit) to exit."
  (let* ((config (load-config config-path))
         (configured-frameworks
           (normalize-framework-list (config-value config :frameworks '())))
         (auto-bindings
             (load-command-bindings (config-value config :autoload-commands '())))
         (active-prompt (or prompt (config-value config :prompt "repl> ")))
         (active-registry (or registry (make-registry))))
    (set-execute-enabled (config-value config :allow-execute nil))
    (set-active-frameworks configured-frameworks)
    (install-commands active-registry (load-framework-bindings configured-frameworks))
    (install-commands active-registry auto-bindings)
    (install-commands active-registry command-bindings)
    (loop
      (format t "~a" active-prompt)
      (finish-output)
      (let ((line (read-line *standard-input* nil nil)))
        (when (null line)
          (return :eof))
        (let ((form (parse-form line)))
          (when (equal form '(quit))
            (return :quit))
          (format t "~s~%" (eval-form active-registry form)))))))
