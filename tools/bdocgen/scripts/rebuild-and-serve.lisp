(require :asdf)

(defun parse-args (argv)
  (labels ((next-value (items key)
             (if (null items)
                 (error "Missing value for ~a" key)
                 (values (first items) (rest items)))))
    (let ((scope "project")
          (project-root ".")
          (docs-root "bdocgen/docs")
          (output-dir "bdocgen/docs/_build_lisp")
          (addon-name "bdocgen")
          (address "127.0.0.1")
          (port 8093))
      (loop while argv
            do (let ((key (first argv)))
                 (setf argv (rest argv))
                 (cond
                   ((string= key "--scope")
                    (multiple-value-setq (scope argv) (next-value argv key)))
                   ((string= key "--project-root")
                    (multiple-value-setq (project-root argv) (next-value argv key)))
                   ((string= key "--docs-root")
                    (multiple-value-setq (docs-root argv) (next-value argv key)))
                   ((string= key "--output-dir")
                    (multiple-value-setq (output-dir argv) (next-value argv key)))
                   ((string= key "--addon-name")
                    (multiple-value-setq (addon-name argv) (next-value argv key)))
                   ((string= key "--address")
                    (multiple-value-setq (address argv) (next-value argv key)))
                   ((string= key "--port")
                    (multiple-value-bind (value rest) (next-value argv key)
                      (setf port (parse-integer value)
                            argv rest)))
                   (t (error "Unknown argument: ~a" key)))))
      (list :scope scope
            :project-root project-root
            :docs-root docs-root
            :output-dir output-dir
            :addon-name addon-name
            :address address
            :port port))))

(let* ((script-path *load-truename*)
       (script-dir (uiop:pathname-directory-pathname script-path))
       (tool-root (uiop:pathname-parent-directory-pathname script-dir))
       (asd-path (merge-pathnames #P"bdocgen.asd" tool-root))
       (args (parse-args (uiop:command-line-arguments))))
  (asdf:load-asd asd-path)
  (asdf:load-system "bdocgen/server")
  (let ((result (apply (find-symbol "REBUILD-AND-RESTART-SERVER" :bdocgen) args)))
    (format t "BDocGen server URL: ~a~%" (getf result :url))
    (uiop:quit 0)))
