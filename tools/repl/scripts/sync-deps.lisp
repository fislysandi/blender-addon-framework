(require :asdf)

(defun run-command (argv directory)
  (uiop:run-program argv :directory directory :output t :error-output t))

(defun ensure-python-deps (repo-root)
  (format t "[sync] uv sync in ~a~%" repo-root)
  (run-command '("uv" "sync") repo-root))

(defun ensure-lisp-deps (repl-root)
  (format t "[sync] ocicl install py4cl2-cffi fiveam in ~a~%" repl-root)
  (run-command '("ocicl" "install" "py4cl2-cffi" "fiveam") repl-root))

(defun main ()
  (let* ((script-path *load-truename*)
         (script-dir (uiop:pathname-directory-pathname script-path))
         (repl-root (uiop:pathname-parent-directory-pathname script-dir))
         (tools-root (uiop:pathname-parent-directory-pathname repl-root))
         (repo-root (uiop:pathname-parent-directory-pathname tools-root)))
    (ensure-python-deps repo-root)
    (ensure-lisp-deps repl-root)
    (format t "[sync] done~%")))

(main)
