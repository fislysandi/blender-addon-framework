(in-package :bdocgen)

(defparameter *bdocgen-server* nil)

(defparameter *homepage-redirect-paths* '("/" "" "/core" "/core/"))

(defclass bdocgen-acceptor (hunchentoot:easy-acceptor) ())

(defun redirect-to-homepage-p (request)
  (member (hunchentoot:script-name request)
          *homepage-redirect-paths*
          :test #'string=))

(defmethod hunchentoot:acceptor-dispatch-request ((acceptor bdocgen-acceptor) request)
  (declare (ignore acceptor))
  (if (redirect-to-homepage-p request)
      (hunchentoot:redirect "/index.html")
      (call-next-method)))

(defun output-dir-pathname (project-root output-dir)
  (resolve-directory-path output-dir (resolve-directory-path project-root (uiop:getcwd))))

(defun stop-server ()
  (when *bdocgen-server*
    (ignore-errors (hunchentoot:stop *bdocgen-server*))
    (setf *bdocgen-server* nil))
  :stopped)

(defun start-or-restart-server (&key (address "127.0.0.1") (port 8093) project-root output-dir)
  (let ((doc-root (output-dir-pathname project-root output-dir)))
    (stop-server)
    (setf *bdocgen-server*
          (hunchentoot:start
           (make-instance 'bdocgen-acceptor
                           :address address
                           :port port
                           :document-root doc-root)))
    (list :status :ok
          :url (format nil "http://~a:~a/index.html" address port)
          :document-root (uiop:native-namestring doc-root))))

(defun rebuild-and-restart-server
    (&key (scope "project") project-root docs-root output-dir addon-name
          (address "127.0.0.1") (port 8093))
  (build-site (list :scope scope
                    :project-root project-root
                    :docs-root docs-root
                    :output-dir output-dir
                    :addon-name addon-name))
  (start-or-restart-server
   :address address
   :port port
   :project-root project-root
   :output-dir output-dir))
