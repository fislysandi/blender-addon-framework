(require :asdf)

(defparameter *script-entry-commands*
  '("create"
    "docs"
    "test"
    "audit-stale-addons"
    "compile"
    "release"
    "addon-deps"
    "test-framework"
    "rename-addon"
    "template"
    "completion"
    "baf"))

(defun print-usage ()
  (format t "Usage:~%")
  (format t "  sbcl --script tools/repl/scripts/commands.lisp --list [--project-root <path>]~%")
  (format t "  sbcl --script tools/repl/scripts/commands.lisp <command> [args...] [--project-root <path>] [--dry-run]~%~%")
  (format t "Examples:~%")
  (format t "  sbcl --script tools/repl/scripts/commands.lisp --list~%")
  (format t "  sbcl --script tools/repl/scripts/commands.lisp create my_addon~%")
  (format t "  sbcl --script tools/repl/scripts/commands.lisp rename-addon old new~%")
  (format t "  sbcl --script tools/repl/scripts/commands.lisp analyze-eval-timeline .tmp/debugger.log~%"))

(defun split-options-and-command (argv)
  (let ((project-root nil)
        (dry-run nil)
        (list-only nil)
        (command nil)
        (command-args '()))
    (labels ((next-value (items key)
               (if (null items)
                   (error "Missing value for ~a" key)
                   (values (first items) (rest items)))))
      (loop while argv
            do (let ((arg (first argv)))
                 (setf argv (rest argv))
                 (cond
                   ((string= arg "--project-root")
                    (multiple-value-setq (project-root argv) (next-value argv arg)))
                   ((string= arg "--dry-run")
                    (setf dry-run t))
                   ((string= arg "--list")
                    (setf list-only t))
                   ((string= arg "--help")
                    (print-usage)
                    (uiop:quit 0))
                   ((null command)
                    (setf command arg))
                   (t
                    (push arg command-args))))))
    (list :project-root project-root
          :dry-run dry-run
          :list-only list-only
          :command command
          :command-args (nreverse command-args))))

(defun default-project-root-from-script ()
  (let* ((script-path *load-truename*)
         (script-dir (uiop:pathname-directory-pathname script-path))
         (repl-root (uiop:pathname-parent-directory-pathname script-dir))
         (tools-root (uiop:pathname-parent-directory-pathname repl-root))
         (project-root (uiop:pathname-parent-directory-pathname tools-root)))
    (uiop:ensure-directory-pathname project-root)))

(defun resolve-project-root (project-root-option)
  (let* ((candidate
           (if project-root-option
               (uiop:parse-native-namestring project-root-option)
               (default-project-root-from-script)))
         (resolved
           (if (uiop:absolute-pathname-p candidate)
               candidate
               (merge-pathnames candidate (uiop:ensure-directory-pathname (uiop:getcwd)))))
         (root (uiop:ensure-directory-pathname resolved))
         (commands-path (merge-pathnames #P"src/commands/" root)))
    (unless (and (probe-file (merge-pathnames #P"pyproject.toml" root))
                 (probe-file commands-path))
      (error "Invalid project root: ~a" (uiop:native-namestring root)))
    root))

(defun python-command-module-files (project-root)
  (let ((commands-root (merge-pathnames #P"src/commands/" project-root)))
    (remove-if
     (lambda (path)
       (or (not (string-equal (or (pathname-type path) "") "py"))
           (string= (or (pathname-name path) "") "__init__")))
     (uiop:directory-files commands-root))))

(defun module-name-from-path (path)
  (string-downcase (or (pathname-name path) "")))

(defun module-display-name (module-name)
  (substitute #\- #\_ module-name))

(defun list-mirrored-commands (project-root)
  (let* ((modules (mapcar #'module-name-from-path (python-command-module-files project-root)))
         (sorted-modules (sort modules #'string<)))
    (format t "Mirrored command files in src/commands/:~%")
    (dolist (module sorted-modules)
      (format t "  - ~a~%" (module-display-name module)))
    (format t "~%Project script entrypoints (uv run <name>):~%")
    (dolist (name *script-entry-commands*)
      (format t "  - ~a~%" name))))

(defun module-name-from-command (command)
  (string-downcase (substitute #\_ #\- command)))

(defun command-module-exists-p (project-root module-name)
  (let ((module-path
         (merge-pathnames
          (uiop:parse-native-namestring (format nil "src/commands/~a.py" module-name))
          project-root)))
    (probe-file module-path)))

(defun launch-command (argv directory dry-run)
  (format t "[mirror] ~{~a~^ ~} (cwd=~a)~%" argv (uiop:native-namestring directory))
  (when dry-run
    (return-from launch-command 0))
  (let* ((process (uiop:launch-program argv
                                       :directory directory
                                       :output *standard-output*
                                       :error-output *error-output*))
         (exit-code (or (uiop:wait-process process) 1)))
    (uiop:quit exit-code)))

(defun execute-mirrored-command (project-root command command-args dry-run)
  (let ((normalized (string-downcase command)))
    (cond
      ((member normalized *script-entry-commands* :test #'string=)
       (launch-command (append (list "uv" "run" normalized) command-args)
                       project-root
                       dry-run))
      (t
       (let ((module-name (module-name-from-command normalized)))
         (if (command-module-exists-p project-root module-name)
             (launch-command (append (list "uv" "run" "python" "-m"
                                           (format nil "src.commands.~a" module-name))
                                     command-args)
                             project-root
                             dry-run)
             (progn
               (format *error-output* "Unknown command: ~a~%" command)
               (format *error-output* "Use --list to inspect mirrored commands.~%")
               (uiop:quit 2))))))))

(defun main ()
  (handler-case
      (let* ((config (split-options-and-command (uiop:command-line-arguments)))
             (project-root (resolve-project-root (getf config :project-root)))
             (list-only (getf config :list-only))
             (command (getf config :command))
             (command-args (getf config :command-args))
             (dry-run (getf config :dry-run)))
        (when list-only
          (list-mirrored-commands project-root)
          (uiop:quit 0))
        (when (null command)
          (print-usage)
          (uiop:quit 1))
        (execute-mirrored-command project-root command command-args dry-run))
    (error (condition)
      (format *error-output* "command mirror error: ~a~%" condition)
      (uiop:quit 1))))

(main)
