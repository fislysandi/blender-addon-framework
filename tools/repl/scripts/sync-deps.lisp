(require :asdf)

(defun print-usage ()
  (format t "Usage:~%")
  (format t "  sbcl --script tools/repl/scripts/sync-deps.lisp [options]~%~%")
  (format t "Options:~%")
  (format t "  --project-root <path>   Repository root (default: auto from script path)~%")
  (format t "  --targets <set>         repl | bdocgen | all (default: all)~%")
  (format t "  --skip-uv               Skip uv sync step~%")
  (format t "  --skip-ocicl            Skip OCiCL setup/install steps~%")
  (format t "  --local-only            Set OCICL_LOCAL_ONLY=1~%")
  (format t "  --dry-run               Print commands only~%")
  (format t "  --help                  Show help~%"))

(defun parse-args (argv)
  (labels ((next-value (items key)
             (if (null items)
                 (error "Missing value for ~a" key)
                 (values (first items) (rest items)))))
    (let ((project-root nil)
          (targets "all")
          (skip-uv nil)
          (skip-ocicl nil)
          (local-only nil)
          (dry-run nil)
          (help nil))
      (loop while argv
            do (let ((key (first argv)))
                 (setf argv (rest argv))
                 (cond
                   ((string= key "--project-root")
                    (multiple-value-setq (project-root argv) (next-value argv key)))
                   ((string= key "--targets")
                    (multiple-value-setq (targets argv) (next-value argv key)))
                   ((string= key "--skip-uv")
                    (setf skip-uv t))
                   ((string= key "--skip-ocicl")
                    (setf skip-ocicl t))
                   ((string= key "--local-only")
                    (setf local-only t))
                   ((string= key "--dry-run")
                    (setf dry-run t))
                   ((string= key "--help")
                    (setf help t))
                   (t (error "Unknown argument: ~a" key)))))
      (list :project-root project-root
            :targets (string-downcase targets)
            :skip-uv skip-uv
            :skip-ocicl skip-ocicl
            :local-only local-only
            :dry-run dry-run
            :help help))))

(defun default-project-root-from-script ()
  (let* ((script-path *load-truename*)
         (script-dir (uiop:pathname-directory-pathname script-path))
         (repl-root (uiop:pathname-parent-directory-pathname script-dir))
         (tools-root (uiop:pathname-parent-directory-pathname repl-root))
         (project-root (uiop:pathname-parent-directory-pathname tools-root)))
    (uiop:ensure-directory-pathname project-root)))

(defun resolve-project-root (project-root-option)
  (let* ((path
           (if project-root-option
               (uiop:parse-native-namestring project-root-option)
               (default-project-root-from-script)))
         (resolved
           (if (uiop:absolute-pathname-p path)
               path
               (merge-pathnames path (uiop:ensure-directory-pathname (uiop:getcwd)))))
         (root (uiop:ensure-directory-pathname resolved)))
    (unless (probe-file (merge-pathnames #P"pyproject.toml" root))
      (error "Invalid project root (missing pyproject.toml): ~a"
             (uiop:native-namestring root)))
    root))

(defun ocicl-packages-for-target (target)
  (cond
    ((string= target "repl") '("py4cl2-cffi" "rove"))
    ((string= target "bdocgen") '("py4cl2-cffi" "rove" "hunchentoot"))
    (t (error "Unknown target: ~a" target))))

(defun target-directories (repo-root targets)
  (cond
    ((string= targets "all")
     (list (list :name "repl" :path (merge-pathnames #P"tools/repl/" repo-root))
           (list :name "bdocgen" :path (merge-pathnames #P"tools/bdocgen/" repo-root))))
    ((or (string= targets "repl") (string= targets "bdocgen"))
     (list (list :name targets
                 :path (merge-pathnames (uiop:parse-native-namestring (format nil "tools/~a/" targets)) repo-root))))
    (t (error "Invalid --targets value: ~a" targets))))

(defun run-command (argv directory &key dry-run env)
  (format t "[sync] ~{~a~^ ~} (cwd=~a)~%" argv (uiop:native-namestring directory))
  (when dry-run
    (return-from run-command 0))
  (let* ((process (uiop:launch-program argv
                                       :directory directory
                                       :output *standard-output*
                                       :error-output *error-output*
                                       :env env))
         (exit-code (or (uiop:wait-process process) 1)))
    (unless (zerop exit-code)
      (error "Command failed with exit code ~d: ~{~a~^ ~}" exit-code argv))
    exit-code))

(defun sync-python-deps (repo-root dry-run)
  (run-command '("uv" "sync") repo-root :dry-run dry-run))

(defun sync-ocicl-target (target directory dry-run local-only)
  (let ((env (when local-only '("OCICL_LOCAL_ONLY=1"))))
    (run-command '("ocicl" "setup") directory :dry-run dry-run :env env)
    (run-command (append '("ocicl" "install") (ocicl-packages-for-target target))
                 directory
                 :dry-run dry-run
                 :env env)))

(defun main ()
  (handler-case
      (let* ((config (parse-args (uiop:command-line-arguments)))
             (help (getf config :help))
             (repo-root (resolve-project-root (getf config :project-root)))
             (targets (getf config :targets))
             (skip-uv (getf config :skip-uv))
             (skip-ocicl (getf config :skip-ocicl))
             (dry-run (getf config :dry-run))
             (local-only (getf config :local-only)))
        (when help
          (print-usage)
          (uiop:quit 0))

        (format t "[sync] project root: ~a~%" (uiop:native-namestring repo-root))

        (unless skip-uv
          (sync-python-deps repo-root dry-run))

        (unless skip-ocicl
          (dolist (target (target-directories repo-root targets))
            (sync-ocicl-target
             (getf target :name)
             (getf target :path)
             dry-run
             local-only)))

        (format t "[sync] done~%")
        (uiop:quit 0))
    (error (condition)
      (format *error-output* "sync-deps error: ~a~%" condition)
      (uiop:quit 1))))

(main)
