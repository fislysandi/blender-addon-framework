(in-package :generic-repl-tests)

(defmacro with-replaced-function ((name replacement) &body body)
  `(let ((original (symbol-function ,name)))
     (unwind-protect
          (progn
            (setf (symbol-function ,name) ,replacement)
            ,@body)
       (setf (symbol-function ,name) original))))

(test framework-arg-translation
  (is (equal '("build")
             (generic-repl::translate-repl-args-to-cli '(build))))
  (is (equal '("--with-version")
             (generic-repl::translate-repl-args-to-cli '(:with-version t))))
  (is (equal '("--addon-name" "demo")
             (generic-repl::translate-repl-args-to-cli '(:addon-name "demo"))))
  (is (equal '("--no-deps")
             (generic-repl::translate-repl-args-to-cli '(:no-deps nil))))
  (is (equal '("demo" "--with-docs")
             (generic-repl::translate-repl-args-to-cli '(demo :with-docs t)))))

(test framework-command-bindings-include-core-commands
  (let* ((registry (make-registry))
         (bindings (load-command-bindings '(:framework))))
    (install-commands registry bindings)
    (let* ((result (eval-form registry '(framework-commands)))
           (names (mapcar #'string-downcase
                          (mapcar #'symbol-name (second result)))))
      (is (equal :ok (first result)))
      (is (member "create" names :test #'string=))
      (is (member "docs" names :test #'string=))
      (is (member "compile" names :test #'string=))
      (is (member "analyze-eval-timeline" names :test #'string=))
      (is (member "repl-completion" names :test #'string=)))))

(test framework-command-executes-via-subprocess
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
          (is (equal '(:ok t :command generic-repl::compile :exit-code 0) result))
          (is (equal '("uv" "run" "compile" "--addon-name" "demo" "--with-version")
                     captured-command))
          (is (eq captured-output *standard-output*))
          (is (eq captured-error-output *error-output*))
          (is (null captured-directory)))))))

(test framework-command-captures-failure-exit-code
  (with-replaced-function
      ('uiop:launch-program
       (lambda (&rest _args)
         :fake-process))
    (with-replaced-function
        ('uiop:wait-process
         (lambda (_process)
           7))
      (let ((result (generic-repl::execute-framework-command 'generic-repl::docs '("my-addon"))))
        (is (equal :error (first result)))
        (is (equal :command-failed (second result)))
        (is (equal :command (third result)))
        (is (equal 'generic-repl::docs (fourth result)))
        (is (equal :exit-code (fifth result)))
        (is (equal 7 (sixth result)))))))
