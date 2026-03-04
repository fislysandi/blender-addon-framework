(in-package :generic-repl)

(defun krita-ping-handler ()
  "Return adapter status for Krita bindings."
  (list :framework :krita :adapter :loaded))

(defun krita-option-value (options key default)
  "Read KEY from OPTIONS plist and return DEFAULT when missing."
  (let ((value (getf options key :missing)))
    (if (eq value :missing) default value)))

(defun krita-command-mode (options)
  "Read command execution mode from OPTIONS."
  (krita-option-value options :mode :plan))

(defun krita-normalize-document-options (options)
  "Normalize document OPTIONS into a stable call contract."
  (list
   :width (krita-option-value options :width 1920)
   :height (krita-option-value options :height 1080)
   :name (krita-option-value options :name "Untitled")
   :color-model (krita-option-value options :color-model "RGBA")
   :color-depth (krita-option-value options :color-depth "U8")
   :profile (krita-option-value options :profile "sRGB-elle-V2-srgbtrc.icc")))

(defun krita-new-document-call-spec (options)
  "Build host-specific call spec for Krita document creation."
  (list
   :framework :krita
   :target "Krita.instance().createDocument"
   :kwargs (krita-normalize-document-options options)))

(defun krita-new-document-handler (&rest options)
  "Translate new-document command form to plan or execute mode."
  (let ((call-spec (krita-new-document-call-spec options)))
    (if (eq (krita-command-mode options) :execute)
        (python-execute-call-spec call-spec)
        call-spec)))

(defun make-krita-command-bindings ()
  "Return command bindings for Krita adapter."
  (list
   (cons 'krita-ping #'krita-ping-handler)
   (cons 'new-document #'krita-new-document-handler)))
