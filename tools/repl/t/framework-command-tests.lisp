(in-package :generic-repl-tests)

(defmacro with-replaced-function ((name replacement) &body body)
  `(let ((original (symbol-function ,name)))
     (unwind-protect
          (progn
            (setf (symbol-function ,name) ,replacement)
            ,@body)
       (setf (symbol-function ,name) original))))

(deftest framework-arg-translation
  (ok (equal '("build")
             (generic-repl::translate-repl-args-to-cli '(build))))
  (ok (equal '("--with-version")
             (generic-repl::translate-repl-args-to-cli '(:with-version t))))
  (ok (equal '("--addon-name" "demo")
             (generic-repl::translate-repl-args-to-cli '(:addon-name "demo"))))
  (ok (equal '("--no-deps")
             (generic-repl::translate-repl-args-to-cli '(:no-deps nil))))
  (ok (equal '("demo" "--with-docs")
             (generic-repl::translate-repl-args-to-cli '(demo :with-docs t)))))

(deftest framework-command-bindings-include-core-commands
  (let* ((registry (make-registry))
         (bindings (load-command-bindings '(:framework))))
    (install-commands registry bindings)
    (let* ((result (eval-form registry '(framework-commands)))
           (names (mapcar #'string-downcase
                          (mapcar #'symbol-name (second result)))))
      (ok (equal :ok (first result)))
      (ok (member "create" names :test #'string=))
      (ok (member "docs" names :test #'string=))
      (ok (member "compile" names :test #'string=))
      (ok (member "analyze-eval-timeline" names :test #'string=))
      (ok (member "repl-completion" names :test #'string=)))))

(deftest framework-command-executes-via-subprocess
  (let ((captured-command nil)
        (captured-output nil)
        (captured-error-output nil)
        (captured-directory nil))
    (with-replaced-function
        ('uiop:launch-program
         (lambda (argv &key directory output error-output &allow-other-keys)
           (setf captured-command argv
                 captured-output output
                 captured-error-output error-output
                 captured-directory directory)
           :fake-process))
      (with-replaced-function
          ('uiop:wait-process
           (lambda (_process)
             0))
        (let ((result (generic-repl::execute-framework-command
                       'generic-repl::compile
                       '(:addon-name "demo" :with-version t))))
          (ok (equal '(:ok t :command generic-repl::compile :exit-code 0) result))
          (ok (equal '("uv" "run" "compile" "--addon-name" "demo" "--with-version")
                     captured-command))
          (ok (eq captured-output *standard-output*))
          (ok (eq captured-error-output *error-output*))
          (ok (null captured-directory)))))))

(deftest framework-command-captures-failure-exit-code
  (with-replaced-function
      ('uiop:launch-program
       (lambda (&rest _args)
         :fake-process))
    (with-replaced-function
        ('uiop:wait-process
         (lambda (_process)
           7))
      (let ((result (generic-repl::execute-framework-command 'generic-repl::docs '("my-addon"))))
        (ok (equal :error (first result)))
        (ok (equal :command-failed (second result)))
        (ok (equal :command (third result)))
        (ok (equal 'generic-repl::docs (fourth result)))
        (ok (equal :exit-code (fifth result)))
        (ok (equal 7 (sixth result)))))))
