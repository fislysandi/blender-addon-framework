(in-package :generic-repl)

(defparameter *execute-enabled* nil
  "When NIL, adapter :mode :execute calls are blocked.")

(defun set-execute-enabled (enabled)
  "Set execute safety flag to ENABLED and return resulting state."
  (setf *execute-enabled* (not (null enabled))))

(defun execute-enabled-p ()
  "Return T when execute mode is enabled."
  *execute-enabled*)

(defun python-option-value (options key default)
  "Read KEY from OPTIONS plist and return DEFAULT when missing."
  (let ((value (getf options key :missing)))
    (if (eq value :missing) default value)))

(defun python-identifier (value)
  "Convert VALUE to a Python identifier fragment."
  (if (keywordp value)
      (string-downcase (substitute #\_ #\- (symbol-name value)))
      (princ-to-string value)))

(defun python-string-literal (value)
  "Convert VALUE to a quoted Python string literal."
  (with-output-to-string (stream)
    (write-char #\' stream)
    (loop for char across value
          do (when (or (char= char #\\) (char= char #\'))
               (write-char #\\ stream))
             (write-char char stream))
    (write-char #\' stream)))

(defun python-literal (value)
  "Render VALUE as a Python literal expression."
  (cond
    ((null value) "None")
    ((eq value t) "True")
    ((stringp value) (python-string-literal value))
    ((numberp value) (princ-to-string value))
    ((keywordp value) (python-string-literal (python-identifier value)))
    ((listp value)
     (format nil "[~{~a~^, ~}]" (mapcar #'python-literal value)))
    (t (python-string-literal (princ-to-string value)))))

(defun python-dict-literal (plist)
  "Render PLIST as a Python dictionary literal expression."
  (let ((pairs
          (loop for (key value) on plist by #'cddr
                collect (format nil "~a: ~a"
                                (python-string-literal (python-identifier key))
                                (python-literal value)))))
    (format nil "{~{~a~^, ~}}" pairs)))

(defun python-call-expression (target kwargs)
  "Build a Python expression for TARGET and KWARGS execution."
  (format nil "~a(**~a)" target (python-dict-literal kwargs)))

(defun call-py4cl2 (function-name &rest args)
  "Call py4cl2-cffi FUNCTION-NAME with ARGS or return a structured error."
  (let ((py-package (find-package :py4cl2-cffi)))
    (if (null py-package)
        (list :error :python-bridge-unavailable :library :py4cl2-cffi)
        (let ((fn-symbol (find-symbol function-name py-package)))
          (if (or (null fn-symbol) (not (fboundp fn-symbol)))
              (list :error :bridge-function-missing :function function-name)
              (handler-case
                  (apply (symbol-function fn-symbol) args)
                (error (condition)
                  (list :error :python-call-failed :message (princ-to-string condition)))))))))

(defun python-start-if-needed ()
  "Start Python bridge if available and return startup status."
  (call-py4cl2 "PYTHON-START-IF-NOT-ALIVE"))

(defun python-call (target &rest args)
  "Call Python TARGET with ARGS through py4cl2-cffi pycall."
  (python-start-if-needed)
  (apply #'call-py4cl2 "PYCALL" target args))

(defun python-execute-call-spec (call-spec)
  "Execute CALL-SPEC (:target string :kwargs plist) via py4cl2-cffi."
  (if (not (execute-enabled-p))
      (list :error :execute-mode-disabled :reason :set-allow-execute-true)
      (let ((target (python-option-value call-spec :target ""))
            (kwargs (python-option-value call-spec :kwargs '())))
        (if (string= target "")
            (list :error :invalid-call-spec :reason :missing-target)
            (let ((startup (python-start-if-needed)))
              (if (and (listp startup)
                       (eq (getf startup :error) :python-bridge-unavailable))
                  startup
                  (call-py4cl2 "RAW-PYEVAL" (python-call-expression target kwargs))))))))
