(in-package :bdocgen-tests)

(def-suite :bdocgen-tests)
(in-suite :bdocgen-tests)

(test build-site-writes-contract-files
  (let* ((tmp-root (uiop:ensure-directory-pathname (uiop:temporary-directory)))
         (project-root (merge-pathnames #P"bdocgen-test-project/" tmp-root))
         (docs-root (merge-pathnames #P"docs/" project-root))
         (output-dir (merge-pathnames #P"docs/_build/" project-root))
         (doc-path (merge-pathnames #P"index.md" docs-root)))
    (uiop:ensure-all-directories-exist (list docs-root))
    (with-open-file (stream doc-path
                            :direction :output
                            :if-exists :supersede
                            :if-does-not-exist :create)
      (write-string "# Hello" stream))
    (let ((result (build-site (list :scope "project"
                                    :project-root (uiop:native-namestring project-root)
                                    :docs-root (uiop:native-namestring docs-root)
                                    :output-dir (uiop:native-namestring output-dir)
                                    :addon-name "demo"))))
      (is (eq :ok (getf result :status)))
      (is (probe-file (merge-pathnames #P"index.html" output-dir)))
      (is (probe-file (merge-pathnames #P"manifest.json" output-dir)))
      (is (probe-file (merge-pathnames #P"assets/style.css" output-dir)))
      (is (probe-file (merge-pathnames #P"pages/index.html" output-dir))))))
