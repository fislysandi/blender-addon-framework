(in-package :generic-repl)

(defparameter *framework-command-specs*
  '((create :entrypoint "create")
    (docs :entrypoint "docs")
    (test :entrypoint "test")
    (audit-stale-addons :entrypoint "audit-stale-addons")
    (compile :entrypoint "compile")
    (release :entrypoint "release")
    (addon-deps :entrypoint "addon-deps")
    (test-framework :entrypoint "test-framework")
    (rename-addon :entrypoint "rename-addon")
    (template :entrypoint "template")
    (completion :entrypoint "completion")
    (baf :entrypoint "baf")
    (analyze-eval-timeline :module "analyze_eval_timeline")
    (parse-eval-lisp :module "parse_eval_lisp")
    (context :module "context")
    (repl :module "repl")
    (repl-args :module "repl_args")
    (repl-completion :module "repl_completion")))

(defun option-keyword-p (value)
  (and (keywordp value)
       (> (length (symbol-name value)) 0)))

(defun symbol-token (value)
  (string-downcase (symbol-name value)))

(defun option-flag (keyword)
  (format nil "--~a" (substitute #\- #\_ (symbol-token keyword))))

(defun cli-atom (value)
  (cond
    ((stringp value) value)
    ((symbolp value) (symbol-token value))
    (t (princ-to-string value))))

(defun append-arg-token (tokens value)
  (append tokens (list (cli-atom value))))

(defun maybe-consume-option-value (flag value)
  (cond
    ((eq value t) (list flag))
    ((null value)
     (if (search "--no-" flag)
         (list flag)
         '()))
    (t (list flag (cli-atom value)))))

(defun translate-repl-args-to-cli (args)
  (labels ((walk-args (rest tokens)
             (if (null rest)
                 tokens
                 (let* ((current (first rest))
                        (remaining (rest rest)))
                   (cond
                     ((option-keyword-p current)
                      (let ((flag (option-flag current)))
                        (if (or (null remaining)
                                (option-keyword-p (first remaining)))
                            (walk-args remaining (append tokens (list flag)))
                            (walk-args (rest remaining)
                                       (append tokens
                                               (maybe-consume-option-value
                                                flag
                                                (first remaining)))))))
                     (t
                      (walk-args remaining (append-arg-token tokens current))))))))
    (walk-args args '())))

(defun framework-command-spec (name)
  (assoc name *framework-command-specs* :test #'eq))

(defun command-prefix-from-spec (spec)
  (let ((plist (rest spec)))
    (cond
      ((getf plist :entrypoint)
       (list "uv" "run" (getf plist :entrypoint)))
      ((getf plist :module)
       (list "uv" "run" "python" "-m"
             (format nil "src.commands.~a" (getf plist :module))))
      (t
       (error "Invalid framework command spec: ~a" spec)))))

(defun execute-framework-command (name args)
  (let ((spec (framework-command-spec name)))
    (if (null spec)
        (list :error :unknown-command :name name)
        (let* ((prefix (command-prefix-from-spec spec))
               (argv (append prefix (translate-repl-args-to-cli args)))
               (process (uiop:launch-program argv
                                             :output *standard-output*
                                             :error-output *error-output*))
               (exit-code (or (uiop:wait-process process) 1)))
          (if (zerop exit-code)
              (list :ok t :command name :exit-code exit-code)
              (list :error :command-failed
                    :command name
                    :exit-code exit-code
                    :argv argv))))))

(defun make-framework-command-bindings ()
  (let ((bindings
          (mapcar (lambda (spec)
                    (let ((name (first spec)))
                      (cons name
                            (lambda (&rest args)
                              (execute-framework-command name args)))))
                  *framework-command-specs*)))
    (append bindings
            (list
             (cons 'framework-commands
                   (lambda ()
                     (list :ok
                           (mapcar #'first *framework-command-specs*))))))))
