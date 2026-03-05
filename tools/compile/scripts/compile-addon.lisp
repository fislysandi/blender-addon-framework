(require :asdf)

(defun print-usage ()
  (format t "Usage:~%")
  (format t "  sbcl --script tools/compile/scripts/compile-addon.lisp --addon-name <name> [options]~%~%")
  (format t "Options:~%")
  (format t "  --addon-name <name>       Addon to compile (required)~%")
  (format t "  --project-root <path>     Framework root (default: auto from script path)~%")
  (format t "  --release-dir <path>      Release directory override~%")
  (format t "  --no-zip                  Keep unpacked folder only (no zip artifact)~%")
  (format t "  --extension               Build as extension~%")
  (format t "  --with-version            Append version to artifact name~%")
  (format t "  --no-version              Disable version suffix (default is enabled)~%")
  (format t "  --with-timestamp          Append timestamp to artifact name~%")
  (format t "  --append-date             Append date suffix (YYYY-MM-DD) to zip filename~%")
  (format t "  --append-time             Append time suffix (HH:MM:SS) to zip filename~%")
  (format t "  --append-datetime         Append date and time suffix to zip filename~%")
  (format t "  --with-deps               Force dependency wheel packaging~%")
  (format t "  --no-deps                 Disable dependency wheel packaging~%")
  (format t "  --with-bdocgen            Build docs via tools/bdocgen before compile~%")
  (format t "  --with-docs               Enable compile docs flow (passes --with-docs)~%")
  (format t "  --docs-only               Run docs flow and skip compile step~%")
  (format t "  --print-artifact          Print final artifact path (if zip exists)~%")
  (format t "  --skip-uv-sync            Skip 'uv sync' environment setup step~%")
  (format t "  --dry-run                 Print commands without running them~%")
  (format t "  --help                    Show this help~%"))

(defun parse-args (argv)
  (labels ((next-value (items key)
             (if (null items)
                 (error "Missing value for ~a" key)
                 (values (first items) (rest items)))))
    (let ((addon-name nil)
          (project-root nil)
          (release-dir nil)
          (no-zip nil)
          (extension nil)
          (with-version t)
          (no-version nil)
          (with-timestamp nil)
          (append-date nil)
          (append-time nil)
          (append-datetime nil)
          (with-deps nil)
          (no-deps nil)
          (with-bdocgen nil)
          (with-docs nil)
          (docs-only nil)
          (print-artifact nil)
          (skip-uv-sync nil)
          (dry-run nil)
          (help nil))
      (loop while argv
            do (let ((key (first argv)))
                 (setf argv (rest argv))
                 (cond
                   ((string= key "--addon-name")
                    (multiple-value-setq (addon-name argv) (next-value argv key)))
                   ((string= key "--project-root")
                    (multiple-value-setq (project-root argv) (next-value argv key)))
                   ((string= key "--release-dir")
                    (multiple-value-setq (release-dir argv) (next-value argv key)))
                   ((string= key "--no-zip")
                    (setf no-zip t))
                   ((string= key "--extension")
                    (setf extension t))
                   ((string= key "--with-version")
                    (setf with-version t))
                   ((string= key "--no-version")
                    (setf no-version t
                          with-version nil))
                   ((string= key "--with-timestamp")
                    (setf with-timestamp t))
                   ((string= key "--append-date")
                    (setf append-date t))
                   ((string= key "--append-time")
                    (setf append-time t))
                   ((string= key "--append-datetime")
                    (setf append-datetime t))
                   ((string= key "--with-deps")
                    (setf with-deps t))
                   ((string= key "--no-deps")
                    (setf no-deps t))
                   ((string= key "--with-bdocgen")
                    (setf with-bdocgen t))
                   ((string= key "--with-docs")
                    (setf with-docs t))
                   ((string= key "--docs-only")
                    (setf docs-only t))
                   ((string= key "--print-artifact")
                    (setf print-artifact t))
                   ((string= key "--skip-uv-sync")
                    (setf skip-uv-sync t))
                   ((string= key "--dry-run")
                    (setf dry-run t))
                   ((string= key "--help")
                    (setf help t))
                   (t (error "Unknown argument: ~a" key)))))
      (when (and with-deps no-deps)
        (error "Conflicting options: --with-deps and --no-deps"))
      (when (and docs-only (not with-bdocgen) (not with-docs))
        (error "--docs-only requires --with-bdocgen or --with-docs"))
      (list :addon-name addon-name
            :project-root project-root
            :release-dir release-dir
            :no-zip no-zip
            :extension extension
            :with-version with-version
            :no-version no-version
            :with-timestamp with-timestamp
            :append-date append-date
            :append-time append-time
            :append-datetime append-datetime
            :with-deps with-deps
            :no-deps no-deps
            :with-bdocgen with-bdocgen
            :with-docs with-docs
            :docs-only docs-only
            :print-artifact print-artifact
            :skip-uv-sync skip-uv-sync
            :dry-run dry-run
            :help help))))

(defun default-project-root-from-script ()
  (let* ((script-path *load-truename*)
         (script-dir (uiop:pathname-directory-pathname script-path))
         (compile-root (uiop:pathname-parent-directory-pathname script-dir))
         (tools-root (uiop:pathname-parent-directory-pathname compile-root))
         (project-root (uiop:pathname-parent-directory-pathname tools-root)))
    (uiop:ensure-directory-pathname project-root)))

(defun resolve-project-root (project-root-option)
  (let* ((input-path
           (if project-root-option
               (uiop:parse-native-namestring project-root-option)
               (default-project-root-from-script)))
         (resolved
           (if (uiop:absolute-pathname-p input-path)
               input-path
               (merge-pathnames input-path (uiop:ensure-directory-pathname (uiop:getcwd)))))
         (root (uiop:ensure-directory-pathname resolved))
         (pyproject (merge-pathnames #P"pyproject.toml" root))
         (framework (merge-pathnames #P"src/framework.py" root)))
    (unless (and (probe-file pyproject) (probe-file framework))
      (error "Resolved project root is invalid: ~a" (uiop:native-namestring root)))
    root))

(defun ensure-addon-exists (project-root addon-name)
  (let ((addon-path (merge-pathnames
                     (uiop:parse-native-namestring (format nil "addons/~a/" addon-name))
                     project-root)))
    (unless (probe-file addon-path)
      (error "Addon not found: ~a" (uiop:native-namestring addon-path)))))

(defun ensure-uv-available ()
  (let* ((process (uiop:launch-program
                   '("sh" "-lc" "command -v uv >/dev/null 2>&1")
                   :output :interactive
                   :error-output :interactive))
         (exit-code (uiop:wait-process process)))
    (unless (zerop (or exit-code 1))
      (error "uv executable not found in PATH"))))

(defun python-executable-path (project-root)
  (let ((python-path (merge-pathnames #P".venv/bin/python" project-root)))
    (unless (probe-file python-path)
      (error "Python executable not found: ~a" (uiop:native-namestring python-path)))
    (uiop:native-namestring python-path)))

(defun uv-sync-command ()
  (list "uv" "sync"))

(defun bdocgen-command (project-root addon-name)
  (let* ((script-path (merge-pathnames #P"tools/bdocgen/scripts/run.lisp" project-root))
         (docs-root (format nil "addons/~a/docs" addon-name))
         (output-dir (format nil "addons/~a/docs/_build" addon-name)))
    (unless (probe-file script-path)
      (error "BDocGen script not found: ~a" (uiop:native-namestring script-path)))
    (list "sbcl" "--script" (uiop:native-namestring script-path)
          "--scope" "project"
          "--project-root" (uiop:native-namestring project-root)
          "--docs-root" docs-root
          "--output-dir" output-dir
          "--addon-name" addon-name)))

(defun compile-command (config)
  (let* ((args (list (getf config :python-executable)
                     "-m"
                     "src.commands.compile"
                     (getf config :addon-name)
                     "--framework-root"
                     (getf config :project-root-string))))
    (when (getf config :release-dir)
      (setf args (append args (list "--release-dir" (getf config :release-dir)))))
    (when (getf config :no-zip)
      (setf args (append args (list "--no-zip"))))
    (when (getf config :extension)
      (setf args (append args (list "--extension"))))
    (when (getf config :with-version)
      (setf args (append args (list "--with-version"))))
    (when (getf config :with-timestamp)
      (setf args (append args (list "--with-timestamp"))))
    (when (getf config :with-deps)
      (setf args (append args (list "--with-deps"))))
    (when (getf config :no-deps)
      (setf args (append args (list "--no-deps"))))
    (when (or (getf config :with-bdocgen) (getf config :with-docs))
      (setf args (append args (list "--with-docs"))))
    args))

(defun default-release-dir (project-root)
  (merge-pathnames #P"releases/" project-root))

(defun resolve-release-dir (project-root release-dir-option)
  (let* ((path
           (if release-dir-option
               (uiop:parse-native-namestring release-dir-option)
               (default-release-dir project-root)))
         (resolved
           (if (uiop:absolute-pathname-p path)
               path
               (merge-pathnames path project-root))))
    (uiop:ensure-directory-pathname resolved)))

(defun collect-zip-artifacts (release-dir addon-name)
  (when (probe-file release-dir)
    (remove-if-not
     (lambda (path)
       (and (string= (or (pathname-type path) "") "zip")
            (search addon-name (or (pathname-name path) "") :test #'char-equal)))
     (uiop:directory-files release-dir))))

(defun path-namestrings (paths)
  (mapcar #'uiop:native-namestring paths))

(defun created-artifacts (before after)
  (let ((before-set (path-namestrings before)))
    (remove-if (lambda (path)
                 (member (uiop:native-namestring path) before-set :test #'string=))
               after)))

(defun newest-file (paths)
  (car (sort (copy-list paths) #'> :key #'file-write-date)))

(defun now-date-string ()
  (multiple-value-bind (_sec _min _hour day month year) (decode-universal-time (get-universal-time))
    (declare (ignore _sec _min _hour))
    (format nil "~4,'0d-~2,'0d-~2,'0d" year month day)))

(defun now-time-string ()
  (multiple-value-bind (sec min hour) (decode-universal-time (get-universal-time))
    (format nil "~2,'0d:~2,'0d:~2,'0d" hour min sec)))

(defun artifact-suffix (config)
  (let* ((use-date (or (getf config :append-date) (getf config :append-datetime)))
         (use-time (or (getf config :append-time) (getf config :append-datetime)))
         (parts '()))
    (when use-date
      (push (now-date-string) parts))
    (when use-time
      (push (now-time-string) parts))
    (if parts
        (format nil "~{~a~^_~}" (nreverse parts))
        nil)))

(defun maybe-rename-artifact (artifact-path config)
  (let ((suffix (artifact-suffix config)))
    (if (null suffix)
        artifact-path
        (let* ((new-path
                 (make-pathname :directory (pathname-directory artifact-path)
                                :name (format nil "~a_~a" (pathname-name artifact-path) suffix)
                                :type (pathname-type artifact-path)
                                :defaults artifact-path)))
          (rename-file artifact-path new-path)
          new-path))))

(defun run-command (command cwd)
  (let* ((process
           (uiop:launch-program command
                                :directory cwd
                                :output *standard-output*
                                :error-output *error-output*))
         (exit-code (uiop:wait-process process)))
    (or exit-code 0)))

(defun run-step (label command cwd dry-run)
  (format t "~&[step] ~a~%" label)
  (format t "[cmd]  ~{~a~^ ~}~%" command)
  (if dry-run
      0
      (let ((exit-code (run-command command cwd)))
        (when (/= exit-code 0)
          (error "Step failed (~a), exit code: ~d" label exit-code))
        0)))

(defun main ()
  (handler-case
      (let* ((config (parse-args (uiop:command-line-arguments)))
             (project-root (resolve-project-root (getf config :project-root)))
             (addon-name (getf config :addon-name))
             (dry-run (getf config :dry-run))
             (project-root-string (uiop:native-namestring project-root)))
        (when (getf config :help)
          (print-usage)
          (uiop:quit 0))
        (when (null addon-name)
          (print-usage)
          (format *error-output* "~%Error: --addon-name is required.~%")
          (uiop:quit 1))
        (ensure-addon-exists project-root addon-name)
        (ensure-uv-available)
        (format t "Project root: ~a~%" project-root-string)

        (unless (getf config :skip-uv-sync)
          (run-step "sync environment (uv sync)" (uv-sync-command) project-root dry-run))

        (let* ((python-executable (python-executable-path project-root))
               (release-dir (resolve-release-dir project-root (getf config :release-dir)))
               (artifacts-before (or (collect-zip-artifacts release-dir addon-name) '()))
               (runtime-config (append config
                                        (list :python-executable python-executable
                                              :project-root-string project-root-string))))
          (when (getf config :with-bdocgen)
            (run-step "build docs (bdocgen)"
                      (bdocgen-command project-root addon-name)
                      project-root
                      dry-run))
          (unless (getf config :docs-only)
            (run-step "compile addon"
                      (compile-command runtime-config)
                      project-root
                      dry-run))
          (unless (or dry-run (getf config :no-zip) (getf config :docs-only))
            (let* ((artifacts-after (or (collect-zip-artifacts release-dir addon-name) '()))
                   (new-artifacts (created-artifacts artifacts-before artifacts-after))
                   (selected (or (newest-file new-artifacts)
                                 (newest-file artifacts-after))))
              (when selected
                (let ((final-artifact (maybe-rename-artifact selected config)))
                  (when (getf config :print-artifact)
                    (format t "Final artifact: ~a~%" (uiop:native-namestring final-artifact)))))))
          (format t "Compile orchestration finished successfully.~%")
          (uiop:quit 0)))
    (error (condition)
      (format *error-output* "Compile script error: ~a~%" condition)
      (uiop:quit 1))))

(main)
