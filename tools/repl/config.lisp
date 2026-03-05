;; Generic REPL local configuration
;; Keep this file simple and data-only.

(:prompt "repl> "
 :python-bridge :py4cl2-cffi
 :allow-execute nil
 :frameworks (:blender :krita)
 :autoload-commands (:examples :framework))
