(in-package :bdocgen)

(defun ensure-directory (path)
  (let ((directory (uiop:ensure-directory-pathname path)))
    (uiop:ensure-all-directories-exist (list directory))
    directory))

(defun write-text-file (path content)
  (uiop:ensure-all-directories-exist
   (list (uiop:pathname-directory-pathname path)))
  (with-open-file (stream path
                          :direction :output
                          :if-exists :supersede
                          :if-does-not-exist :create)
    (write-string content stream))
  path)

(defun read-text-file (path)
  (with-open-file (stream path :direction :input)
    (let ((content (make-string (file-length stream))))
      (read-sequence content stream)
      content)))

(defun path-relative-to (path root)
  (uiop:native-namestring (uiop:enough-pathname path root)))

(defun markdown-file-p (path)
  (string-equal (pathname-type path) "md"))

(defun collect-markdown-files (root)
  (labels ((walk (dir)
             (let ((files (uiop:directory-files dir))
                   (subdirs (uiop:subdirectories dir)))
               (append
                (remove-if-not #'markdown-file-p files)
                (mapcan #'walk subdirs)))))
    (if (uiop:directory-exists-p root)
        (sort (walk root) #'string< :key #'uiop:native-namestring)
        '())))
