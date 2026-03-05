(in-package :bdocgen)

(defun parse-cli-args (argv)
  (labels ((next-value (list key)
             (if (null list)
                 (error "Missing value for ~a" key)
                 (values (first list) (rest list)))))
    (let ((scope "project")
          (project-root ".")
          (docs-root "docs")
          (output-dir "docs/_build")
          (addon-name ""))
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
                   (t (error "Unknown argument: ~a" key)))))
      (list :scope scope
            :project-root project-root
            :docs-root docs-root
            :output-dir output-dir
            :addon-name addon-name))))

(defun print-result (result)
  (format t "BDocGen status: ~a~%" (getf result :status))
  (format t "BDocGen scope: ~a~%" (getf result :scope))
  (format t "BDocGen pages: ~a~%" (getf result :page-count))
  (format t "index: ~a~%" (getf result :index-path))
  (format t "manifest: ~a~%" (getf result :manifest-path)))

(defun main ()
  (handler-case
      (let* ((argv (uiop:command-line-arguments))
             (config (parse-cli-args argv))
             (result (build-site config)))
        (print-result result)
        0)
    (error (condition)
      (format *error-output* "BDocGen error: ~a~%" condition)
      1)))
