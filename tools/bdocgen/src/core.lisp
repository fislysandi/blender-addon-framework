(in-package :bdocgen)

(defun plist-value (plist key default)
  (let ((value (getf plist key :missing)))
    (if (eq value :missing) default value)))

(defun resolve-directory-path (value base)
  (let* ((path (uiop:parse-native-namestring value))
         (resolved (if (uiop:absolute-pathname-p path)
                       path
                       (merge-pathnames path base))))
    (uiop:ensure-directory-pathname resolved)))

(defun json-escape (text)
  (with-output-to-string (stream)
    (loop for char across text
          do (case char
               (#\" (write-string "\\\"" stream))
               (#\\ (write-string "\\\\" stream))
               (#\Newline (write-string "\\n" stream))
               (#\Return (write-string "\\r" stream))
               (#\Tab (write-string "\\t" stream))
               (otherwise (write-char char stream))))))

(defun json-string (text)
  (format nil "\"~a\"" (json-escape text)))

(defun json-array-of-strings (values)
  (format nil "[~{~a~^,~}]" (mapcar #'json-string values)))

(defun normalize-pages-target (value)
  (let ((normalized (string-downcase (or value "github"))))
    (unless (member normalized '("github" "gitlab") :test #'string=)
      (error "Unsupported pages target: ~a (expected github|gitlab)" value))
    normalized))

(defun default-output-dir-for-pages-target (pages-target)
  (if (string= (normalize-pages-target pages-target) "gitlab")
      "public"
      "docs/_build"))

(defun write-nojekyll-p (pages-target)
  (string= (normalize-pages-target pages-target) "github"))

(defparameter *default-style-css*
  ":root {
  --bwa-color-bg: #0d1117;
  --bwa-color-fg: #e6edf3;
  --bwa-color-accent: #f18f3b;
  --bwa-color-link: #65aef8;
  --bwa-color-border: #2d3643;
  --bwa-spacer: 1rem;
  --bwa-border-radius: 0.35rem;
  --bg: #0e1116;
  --panel: #161b23;
  --panel-soft: #121720;
  --panel-elev: #1d2430;
  --border: #2d3643;
  --text: #e1e8f2;
  --text-muted: #a6b3c5;
  --link: #65aef8;
  --link-hover: #8ec5ff;
  --focus: #e0f266;
  --accent: #f18f3b;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font-family: 'Noto Sans', 'DejaVu Sans', sans-serif; font-size: 15px; line-height: 1.6; }
a { color: var(--link); text-decoration: none; }
a:hover { color: var(--link-hover); text-decoration: underline; }
.skip-link {
  position: absolute;
  left: -9999px;
  top: 0;
  background: var(--focus);
  color: #111;
  padding: 0.4rem 0.7rem;
  border-radius: 0 0 0.4rem 0.4rem;
  font-weight: 700;
}
.skip-link:focus-visible {
  left: 0.6rem;
  z-index: 10;
}
.site-shell { min-height: 100vh; }
.nav-global {
  background-color: #161b23;
  color: #c8d0dc;
  position: sticky;
  top: 0;
  z-index: 30;
  border-bottom: 1px solid var(--bwa-border-color);
}
.nav-global .nav-global-container {
  max-width: 1360px;
  margin: 0 auto;
}
.nav-global nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 54px;
  line-height: 14px;
  font-size: 14px;
  padding: 0 var(--bwa-spacer);
}
.nav-global .nav-global-logo {
  color: #f2f5fa;
  margin-right: var(--bwa-spacer);
}
.nav-global .nav-global-logo strong { font-weight: 700; font-size: 18px; }
.nav-global ul { list-style: none; margin: 0; padding: 0; display: inline-flex; align-items: center; }
.nav-global .nav-global-nav-links { flex-grow: 1; overflow: hidden; }
.nav-global .nav-global-nav-links li a {
  display: inline-flex;
  align-items: center;
  padding: 8px 10px;
  border-radius: var(--bwa-border-radius);
  color: #c8d0dc;
}
.nav-global .nav-global-links-right li a {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: var(--bwa-border-radius);
  color: #dbe4ef;
  border: 1px solid transparent;
}
.nav-global .nav-global-nav-links li a:hover,
.nav-global .nav-global-links-right li a:hover {
  background-color: #2a303b;
  color: #fff;
  text-decoration: none;
}
.nav-global .nav-global-nav-links li a.is-active {
  color: #fff;
  font-weight: 700;
}
.md-tabs {
  border-bottom: 1px solid var(--bwa-border-color);
  background: #141922;
}
.md-tabs .md-grid { max-width: 1360px; margin: 0 auto; }
.md-tabs__list { list-style: none; margin: 0; padding: 0 0.7rem; display: flex; gap: 0.15rem; overflow-x: auto; }
.md-tabs__item { display: inline-flex; }
.md-tabs__link {
  display: inline-flex;
  align-items: center;
  padding: 0.58rem 0.7rem;
  border-bottom: 2px solid transparent;
  color: #bdc8d8;
  white-space: nowrap;
}
.md-tabs__link:hover { color: #e7eef9; text-decoration: none; }
.md-tabs__link--active { color: #fff; border-bottom-color: var(--bwa-color-accent); }
.md-container { min-height: calc(100vh - 96px); }
.md-main__inner.md-grid { max-width: 1360px; margin: 0 auto; }
.md-sidebar--secondary { align-self: stretch; }
.left-rail { padding-top: 1.2rem; }
.content { padding-top: 1.35rem; }
.content h1 { font-size: 2.1rem; }
.content p code { font-size: 0.88em; }
.content pre code { border: 0; padding: 0; }
.content .rail-title { font-size: 0.75rem; letter-spacing: 0.08em; }
.content .admonition-title { font-weight: 700; margin-bottom: 0.35rem; }
.content .note .admonition-title { color: #84beff; }
.content .warning .admonition-title { color: #f3bf75; }
.content .tip .admonition-title { color: #90ce77; }
.content figure { margin: 1rem auto; text-align: center; }
.content figcaption { color: var(--text-muted); font-size: 0.9rem; }
.md-content { min-width: 0; }
@media (max-width: 1320px) {
  .nav-global nav { padding-left: 0.6rem; padding-right: 0.6rem; }
  .md-tabs__list { padding-left: 0.45rem; padding-right: 0.45rem; }
}
.layout { display: grid; grid-template-columns: 300px minmax(0, 1fr) 240px; min-height: calc(100vh - 50px); }
.left-rail { border-right: 1px solid var(--border); background: linear-gradient(180deg, var(--panel) 0%, var(--panel-soft) 100%); padding: 1rem; }
.content { padding: 1.5rem 2.25rem; max-width: 1040px; }
.right-rail { border-left: 1px solid var(--border); padding: 1rem; background: #0c1016; }
.nav-list, .toc-list { list-style: none; margin: 0; padding: 0; }
.nav-list li, .toc-list li { margin: 0.3rem 0; }
.brand { margin: 0; font-size: 1.38rem; letter-spacing: 0.01em; }
.brand-sub { margin: 0.2rem 0 1rem; color: var(--text-muted); }
.meta, .rail-title { color: var(--text-muted); }
.rail-title { text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.06em; }
.back-link { display: inline-block; margin-bottom: 0.75rem; color: var(--text-muted); }
.nav-list a { display: block; padding: 0.25rem 0.4rem; border-radius: 0.32rem; }
.nav-list a:hover { background: var(--panel-elev); text-decoration: none; }
.nav-list a.current { background: #1f2a39; color: #cbe3ff; font-weight: 600; }
.toc-list a { color: var(--text-muted); }
.toc-list a:hover { color: var(--link-hover); }
.nav-mobile-toggle {
  display: none;
  margin: 0 0 0.9rem;
  padding: 0.5rem 0.65rem;
  border: 1px solid var(--border);
  border-radius: 0.35rem;
  background: var(--panel-soft);
}
.nav-mobile-toggle > summary {
  cursor: pointer;
  color: var(--text);
}
.nojs-hint {
  margin: 0.8rem 0;
  padding: 0.55rem 0.65rem;
  border: 1px solid var(--border);
  border-radius: 0.35rem;
  background: var(--panel-soft);
  color: var(--text-muted);
  font-size: 0.9rem;
}
.content section + section {
  margin-top: 1.4rem;
}
.content h1,.content h2,.content h3 { line-height: 1.25; }
.content h1 { font-size: 2rem; margin: 0 0 0.9rem; border-bottom: 1px solid var(--border); padding-bottom: 0.65rem; }
.content h2 { font-size: 1.35rem; margin-top: 1.45rem; }
.content h3 { font-size: 1.1rem; margin-top: 1.1rem; color: #d6deea; }
.content p { line-height: 1.65; color: #d5ddeb; }
.content pre,.content code { background: #161c25; border: 1px solid var(--border); border-radius: 6px; }
.content pre { padding: 0.75rem; overflow: auto; }
.content code { padding: 0.08rem 0.35rem; }
.content blockquote { margin: 1rem 0; padding: 0.65rem 0.85rem; border-left: 4px solid var(--accent); background: #131a24; color: #cdd6e5; }
.content table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
.content th,.content td { border: 1px solid var(--border); padding: 0.5rem 0.65rem; text-align: left; }
.content th { background: #17212d; }
.content .admonition,
.content .note,
.content .warning,
.content .tip {
  margin: 1rem 0;
  padding: 0.7rem 0.85rem;
  border-radius: 0.4rem;
  border: 1px solid var(--border);
  background: #131a24;
}
.content .warning { border-left: 4px solid #d7923b; }
.content .tip { border-left: 4px solid #6aa84f; }
.content .note { border-left: 4px solid #5fa8f2; }
.content img.diagram { max-width: 100%; height: auto; border: 1px solid var(--border); border-radius: 6px; background: #fff; padding: 0.35rem; }
.heading-citation { margin-left: 0.4rem; opacity: 0; }
.content h1:hover .heading-citation,.content h2:hover .heading-citation,.content h3:hover .heading-citation { opacity: 1; }
a:focus-visible,
summary:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 2px;
  border-radius: 0.2rem;
}
@media (max-width: 1024px) {
  .layout { grid-template-columns: 290px minmax(0, 1fr); }
  .right-rail { display: none; }
}
@media (max-width: 780px) {
  .nav-global .nav-global-nav-links { display: none; }
  .nav-global nav { min-height: 50px; }
  .md-tabs__link { padding: 0.52rem 0.62rem; }
  .layout { grid-template-columns: 1fr; }
  .left-rail { border-right: 0; border-bottom: 1px solid var(--border); }
  .nav-mobile-toggle { display: block; }
  .left-rail .nav-list { display: none; }
  .nav-mobile-toggle[open] .nav-list { display: block; margin-top: 0.6rem; }
}")

(defun html-escape (text)
  (with-output-to-string (stream)
    (loop for char across text
          do (case char
               (#\& (write-string "&amp;" stream))
               (#\< (write-string "&lt;" stream))
               (#\> (write-string "&gt;" stream))
               (#\" (write-string "&quot;" stream))
               (otherwise (write-char char stream))))))

(defun trim-line (line)
  (string-trim '(#\Space #\Tab #\Return #\Newline) line))

(defun starts-with (text prefix)
  (let ((n (length prefix)))
    (and (>= (length text) n)
         (string= text prefix :end1 n :end2 n))))

(defun slugify (text)
  (let ((normalized
          (string-downcase
           (with-output-to-string (stream)
             (loop for char across text
                   do (if (or (alphanumericp char) (char= char #\Space) (char= char #\-))
                          (write-char char stream)
                          (write-char #\Space stream)))))))
    (let ((parts (remove "" (uiop:split-string normalized :separator " ") :test #'string=)))
      (if parts
          (format nil "~{~a~^-~}" parts)
          "section"))))

(defun page-title-for-scope (scope)
  (if (string= scope "project")
      "BDocGen Project Documentation"
      "BDocGen Self Documentation"))

(defun site-name-for-config (scope addon-name)
  (if (> (length addon-name) 0)
      addon-name
      (if (string= scope "project")
          "blender-addon-framework"
          "bdocgen")))

(defun markdown-relative-to-page-entry (markdown-relative)
  (let* ((html-relative (markdown-path-to-html-relative markdown-relative))
         (title (or (pathname-name (uiop:parse-native-namestring markdown-relative)) "Untitled")))
    (list :title title
          :source-path markdown-relative
          :html-relative html-relative
          :url (format nil "/~a" html-relative))))

(defun markdown-title-from-content (markdown-content fallback-title)
  (let ((lines (split-lines markdown-content)))
    (or (loop for raw-line in lines
              for line = (trim-line raw-line)
              when (starts-with line "# ")
                do (return (subseq line 2)))
        fallback-title)))

(defun enrich-page-entries-with-titles (docs-root page-entries)
  (mapcar
   (lambda (entry)
     (let* ((source-path
              (merge-pathnames
               (uiop:parse-native-namestring (getf entry :source-path))
               docs-root))
            (content (read-text-file source-path))
            (resolved-title
              (markdown-title-from-content content (getf entry :title "Untitled"))))
       (list :title resolved-title
             :source-path (getf entry :source-path)
             :html-relative (getf entry :html-relative)
             :url (getf entry :url))))
   page-entries))

(defun nav-base-href (index-href)
  (if (null index-href)
      "./"
      (let* ((suffix "index.html")
             (n (length index-href))
             (m (length suffix)))
        (if (and (>= n m)
                 (string= index-href suffix :start1 (- n m) :end1 n :start2 0 :end2 m))
            (let ((base (subseq index-href 0 (- n m))))
              (if (string= base "") "./" base))
            index-href))))

(defun depth-prefix (nesting)
  (with-output-to-string (stream)
    (dotimes (_ nesting)
      (declare (ignore _))
      (write-string "../" stream))))

(defun nav-href (url index-href)
  (format nil "~a~a" (nav-base-href index-href) (string-left-trim "/" url)))

(defun render-global-header (site-name index-href)
  (let ((home-href (or index-href "./index.html")))
    (with-output-to-string (stream)
      (format stream "<header class=\"md-header nav-global\" data-md-component=\"header\">")
      (format stream "<div class=\"nav-global-container\"><nav>")
      (format stream "<a class=\"nav-global-logo\" href=\"~a\"><strong>~a</strong></a>"
              (html-escape home-href)
              (html-escape site-name))
      (format stream "<ul class=\"nav-global-nav-links\">")
      (format stream "<li><a class=\"is-active\" href=\"~a\">Docs</a></li>" (html-escape home-href))
      (format stream "<li><a href=\"https://projects.blender.org\">Projects</a></li>")
      (format stream "<li><a href=\"https://code.blender.org\">Blog</a></li>")
      (format stream "</ul>")
      (format stream "<ul class=\"nav-global-links-right\"><li><a class=\"nav-global-btn\" href=\"~a\">Home</a></li></ul>"
              (html-escape home-href))
      (format stream "</nav></div></header>"))))

(defun render-top-tabs (page-entries index-href current-url)
  (let ((max-tabs 8)
        (count 0))
    (with-output-to-string (stream)
      (format stream "<nav class=\"md-tabs\" aria-label=\"Tabs\"><div class=\"md-grid\"><ul class=\"md-tabs__list\">")
      (format stream "<li class=\"md-tabs__item\"><a class=\"md-tabs__link~a\" href=\"~a\">Home</a></li>"
              (if (string= current-url "/") " md-tabs__link--active" "")
              (html-escape (or index-href "./index.html")))
      (dolist (entry page-entries)
        (when (< count max-tabs)
          (incf count)
          (let* ((url (getf entry :url "/"))
                 (href (nav-href url index-href))
                 (title (html-escape (getf entry :title "Untitled"))))
            (format stream "<li class=\"md-tabs__item\"><a class=\"md-tabs__link~a\" href=\"~a\">~a</a></li>"
                    (if (string= url current-url) " md-tabs__link--active" "")
                    (html-escape href)
                    title))))
      (format stream "</ul></div></nav>"))))

(defun render-sidebar (site-name site-subtitle page-entries current-url index-href)
  (let ((nav-items
          (with-output-to-string (stream)
            (dolist (entry page-entries)
              (let* ((url (getf entry :url))
                     (href (nav-href url index-href))
                     (title (html-escape (getf entry :title "Untitled")))
                     (class-attr (if (string= url current-url) " class=\"current\"" "")))
                (format stream "<li><a~a href=\"~a\">~a</a></li>" class-attr (html-escape href) title))))))
    (with-output-to-string (stream)
      (format stream "<aside class=\"left-rail\" aria-label=\"Documentation navigation\">")
      (format stream "<h1 class=\"brand\">~a</h1>" (html-escape site-name))
      (format stream "<p class=\"brand-sub\">~a</p>" (html-escape site-subtitle))
      (when index-href
        (format stream "<a class=\"back-link\" href=\"~a\">Back to docs index</a>" (html-escape index-href)))
      (format stream "<p class=\"nojs-hint\">No JavaScript required. Use this navigation and your browser find shortcut (Ctrl+F).</p>")
      (format stream "<details class=\"nav-mobile-toggle\"><summary>Browse Pages</summary><ul class=\"nav-list\">~a</ul></details>" nav-items)
      (format stream "<ul class=\"nav-list\">~a</ul>" nav-items)
      (format stream "</aside>"))))

(defun join-lines (lines)
  (with-output-to-string (stream)
    (loop for line in lines
          for index from 0
          do (when (> index 0) (terpri stream))
             (write-string line stream))))

(defun split-lines (text)
  (loop with start = 0
        for end = (position #\Newline text :start start)
        collect (if end
                    (subseq text start end)
                    (subseq text start))
        while end
        do (setf start (1+ end))))

(defun mermaid-fence-start-p (line)
  (or (string= line "```mermaid")
      (starts-with line "```mermaid ")))

(defun hash-fnv1a-32 (text)
  (let ((hash 2166136261))
    (loop for ch across text
          do (setf hash (logand #xffffffff (* (logxor hash (char-code ch)) 16777619))))
    hash))

(defun hash-hex (value)
  (format nil "~8,'0x" value))

(defun mermaid-asset-paths (output-dir diagram-text)
  (let* ((diagram-id (hash-hex (hash-fnv1a-32 diagram-text)))
         (assets-dir (merge-pathnames #P"_assets/mermaid/" output-dir))
         (mmd-path (merge-pathnames (uiop:parse-native-namestring (format nil "~a.mmd" diagram-id)) assets-dir))
         (svg-path (merge-pathnames (uiop:parse-native-namestring (format nil "~a.svg" diagram-id)) assets-dir)))
    (ensure-directory assets-dir)
    (list :mmd-path mmd-path :svg-path svg-path :diagram-id diagram-id)))

(defun run-command-ok-p (command)
  (let* ((process (uiop:launch-program command
                                       :output *standard-output*
                                       :error-output *error-output*))
         (exit-code (or (uiop:wait-process process) 1)))
    (zerop exit-code)))

(defun render-mermaid-svg (output-dir diagram-text)
  (let* ((paths (mermaid-asset-paths output-dir diagram-text))
         (mmd-path (getf paths :mmd-path))
         (svg-path (getf paths :svg-path))
         (mmd-native (uiop:native-namestring mmd-path))
         (svg-native (uiop:native-namestring svg-path))
         (commands
           (list
            (list "mmdc" "-i" mmd-native "-o" svg-native)
            (list "npx" "--yes" "@mermaid-js/mermaid-cli" "-i" mmd-native "-o" svg-native))))
    (write-text-file mmd-path diagram-text)
    (unwind-protect
         (unless (or (probe-file svg-path)
                     (some #'run-command-ok-p commands))
           (error "Failed to render Mermaid diagram. Install mmdc or Node+npx @mermaid-js/mermaid-cli."))
      (ignore-errors (delete-file mmd-path)))
    svg-path))

(defun transform-mermaid-blocks (lines output-dir html-relative render-mermaid-images)
  (let ((in-mermaid nil)
        (mermaid-lines '())
        (result '())
        (prefix (depth-prefix (count #\/ html-relative))))
    (labels ((flush-mermaid ()
               (let* ((diagram-text (join-lines (nreverse mermaid-lines)))
                      (svg-path (if render-mermaid-images
                                    (render-mermaid-svg output-dir diagram-text)
                                    nil))
                      (svg-name (and svg-path (file-namestring svg-path)))
                      (img-href (and svg-name (format nil "~a_assets/mermaid/~a" prefix svg-name))))
                 (setf mermaid-lines '())
                 (if img-href
                     (push (format nil "<p><img class=\"diagram diagram-mermaid\" src=\"~a\" alt=\"Mermaid diagram\"></p>" img-href)
                           result)
                     (progn
                       (push "```mermaid" result)
                       (dolist (line (split-lines diagram-text))
                         (push line result))
                       (push "```" result))))))
      (dolist (raw-line lines)
        (let ((line (trim-line raw-line)))
          (cond
            ((and (not in-mermaid) (mermaid-fence-start-p line))
             (setf in-mermaid t
                   mermaid-lines '()))
            (in-mermaid
             (if (starts-with line "```")
                 (progn
                   (setf in-mermaid nil)
                   (flush-mermaid))
                 (push raw-line mermaid-lines)))
            (t
             (push raw-line result)))))
      (when in-mermaid
        (setf in-mermaid nil)
        (flush-mermaid))
      (nreverse result))))

(defun markdown-lines-to-html (lines)
  (with-output-to-string (stream)
    (let ((in-list nil)
          (in-code nil)
          (paragraph-lines '()))
      (labels ((flush-paragraph ()
                 (when paragraph-lines
                   (format stream "<p>~a</p>~%"
                           (html-escape (join-lines (nreverse paragraph-lines))))
                   (setf paragraph-lines '())))
               (close-list ()
                 (when in-list
                   (format stream "</ul>~%")
                   (setf in-list nil))))
        (dolist (raw-line lines)
          (let ((line (trim-line raw-line)))
            (cond
              ((starts-with line "```")
               (flush-paragraph)
               (close-list)
               (if in-code
                   (progn
                     (format stream "</code></pre>~%")
                     (setf in-code nil))
                   (progn
                     (write-string "<pre><code>" stream)
                     (setf in-code t))))
               (in-code
                (write-string (html-escape raw-line) stream)
                (terpri stream))
               ((or (starts-with line "<p><img ")
                    (starts-with line "<img "))
                (flush-paragraph)
                (close-list)
                (write-string raw-line stream)
                (terpri stream))
               ((string= line "")
                (flush-paragraph)
                (close-list))
              ((starts-with line "### ")
                (flush-paragraph)
                (close-list)
                (let ((label (subseq line 4)))
                  (format stream "<h3 id=\"~a\">~a</h3>~%" (slugify label) (html-escape label))))
              ((starts-with line "## ")
                (flush-paragraph)
                (close-list)
                (let ((label (subseq line 3)))
                  (format stream "<h2 id=\"~a\">~a</h2>~%" (slugify label) (html-escape label))))
              ((starts-with line "# ")
                (flush-paragraph)
                (close-list)
                (let ((label (subseq line 2)))
                  (format stream "<h1 id=\"~a\">~a</h1>~%" (slugify label) (html-escape label))))
              ((starts-with line "- ")
               (flush-paragraph)
               (unless in-list
                 (format stream "<ul>~%")
                 (setf in-list t))
               (format stream "<li>~a</li>~%" (html-escape (subseq line 2))))
              (t
                (push line paragraph-lines)))))
        (flush-paragraph)
        (close-list)
        (when in-code
          (format stream "</code></pre>~%"))))))

(defun strip-html-tags (text)
  (with-output-to-string (stream)
    (let ((in-tag nil))
      (loop for char across text
            do (cond
                 ((char= char #\<) (setf in-tag t))
                 ((char= char #\>) (setf in-tag nil))
                 ((not in-tag) (write-char char stream)))))))

(defun extract-section-headings (body-html)
  (let ((headings '())
        (start 0)
        (html (or body-html "")))
    (loop
      for open = (search "<h2 id=\"" html :start2 start)
      while open
      do (let* ((id-start (+ open (length "<h2 id=\"")))
                (id-end (position #\" html :start id-start))
                (label-start (and id-end (position #\> html :start id-end)))
                (close (and label-start (search "</h2>" html :start2 (1+ label-start)))))
            (if (or (null id-end) (null label-start) (null close))
                (setf start (+ open 1))
                (let* ((id (subseq html id-start id-end))
                       (raw-label (subseq html (1+ label-start) close))
                       (label (string-trim '(#\Space #\Tab #\Newline #\Return #\¶)
                                           (strip-html-tags raw-label))))
                  (when (> (length label) 0)
                    (push (list :id id :label label) headings))
                  (setf start (+ close (length "</h2>")))))))
    (nreverse headings)))

(defun render-section-items (sections)
  (if sections
      (with-output-to-string (stream)
        (dolist (section sections)
          (format stream "<li><a href=\"#~a\">~a</a></li>"
                  (html-escape (getf section :id ""))
                  (html-escape (getf section :label "")))))
      "<li><em>No section headings</em></li>"))

(defun markdown-to-html-page
    (title markdown-content page-entries current-url html-relative site-name site-subtitle output-dir render-mermaid-images)
  (with-output-to-string (stream)
    (let* ((nesting (count #\/ html-relative))
           (prefix (depth-prefix nesting))
             (index-href (format nil "~aindex.html" prefix))
             (css-href (format nil "~a_assets/theme.css" prefix))
             (global-header (render-global-header site-name index-href))
             (top-tabs (render-top-tabs page-entries index-href current-url))
             (sidebar (render-sidebar site-name site-subtitle page-entries current-url index-href))
            (body-html (markdown-lines-to-html
                        (transform-mermaid-blocks
                         (split-lines markdown-content)
                         output-dir
                         html-relative
                         render-mermaid-images)))
            (section-items (render-section-items (extract-section-headings body-html))))
    (format stream "<!doctype html>~%")
    (format stream "<html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>~a</title><link rel=\"stylesheet\" href=\"~a\"></head><body>~%"
            (html-escape title)
            (html-escape css-href))
    (format stream "<a class=\"skip-link\" href=\"#main-content\">Skip to content</a><div class=\"site-shell\">~a~a<div class=\"md-container\" data-md-component=\"container\"><main class=\"md-main\" data-md-component=\"main\"><div class=\"md-main__inner md-grid layout\">~a"
            global-header
            top-tabs
            sidebar)
    (format stream "<main class=\"content md-content\" id=\"main-content\">~a</main>" body-html)
    (format stream "<aside class=\"right-rail md-sidebar md-sidebar--secondary\"><p class=\"rail-title\">On This Page</p><ul class=\"toc-list\">~a</ul></aside>" section-items)
    (format stream "</div></main></div></div></body></html>~%"))))

(defun markdown-path-to-html-relative (markdown-relative)
  (let* ((pathname (uiop:parse-native-namestring markdown-relative))
         (name (pathname-name pathname))
         (dir (or (pathname-directory pathname) '(:relative)))
         (subdir (if (and dir (eq (first dir) :relative)) (rest dir) dir))
         (html-path (make-pathname :directory (append '(:relative "pages") subdir)
                                   :name name
                                   :type "html")))
    (uiop:native-namestring html-path)))

(defun compile-markdown-page (docs-root output-dir page-entry page-entries site-name site-subtitle render-mermaid-images)
  (let* ((markdown-relative (getf page-entry :source-path))
         (html-relative (getf page-entry :html-relative))
         (current-url (getf page-entry :url))
         (source-path (merge-pathnames (uiop:parse-native-namestring markdown-relative) docs-root))
         (target-path (merge-pathnames (uiop:parse-native-namestring html-relative) output-dir))
         (markdown-content (read-text-file source-path))
         (page-title (getf page-entry :title "Untitled"))
         (html-content (markdown-to-html-page page-title markdown-content page-entries current-url html-relative site-name site-subtitle output-dir render-mermaid-images)))
    (write-text-file target-path html-content)
    html-relative))

(defun compile-markdown-pages (docs-root output-dir page-entries site-name site-subtitle render-mermaid-images)
  (mapcar (lambda (entry)
            (compile-markdown-page docs-root output-dir entry page-entries site-name site-subtitle render-mermaid-images))
          page-entries))

(defun write-style-sheet (output-dir)
  (let ((style-path (merge-pathnames #P"_assets/theme.css" output-dir)))
    (write-text-file style-path *default-style-css*)
    "_assets/theme.css"))

(defun build-index-html (scope site-name site-subtitle page-entries)
  (with-output-to-string (stream)
    (let ((title (page-title-for-scope scope))
           (global-header (render-global-header site-name "./index.html"))
          (top-tabs (render-top-tabs page-entries "./index.html" "/"))
          (items
            (if page-entries
                (with-output-to-string (items-stream)
                  (dolist (entry page-entries)
                    (format items-stream "<li><a href=\".~a\">~a</a> <code>~a</code></li>"
                            (html-escape (getf entry :url "/"))
                            (html-escape (getf entry :title "Untitled"))
                            (html-escape (getf entry :source-path ""))))
                  )
                "<li><em>No markdown docs discovered.</em></li>"))
          (toc-items "<li><a href=\"#overview\">Overview</a></li><li><a href=\"#what\">What</a></li><li><a href=\"#why\">Why</a></li><li><a href=\"#how\">How</a></li><li><a href=\"#sources\">Discovered Sources</a></li>"))
    (format stream "<!doctype html>~%")
    (format stream "<html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>~a</title><link rel=\"stylesheet\" href=\"./_assets/theme.css\"></head><body>"
            (html-escape title))
    (format stream "<a class=\"skip-link\" href=\"#main-content\">Skip to content</a><div class=\"site-shell\">~a~a<div class=\"md-container\" data-md-component=\"container\"><main class=\"md-main\" data-md-component=\"main\"><div class=\"md-main__inner md-grid layout\">~a"
            global-header
            top-tabs
            (render-sidebar site-name site-subtitle page-entries "/" nil))
    (format stream "<main class=\"content\" id=\"main-content\">")
    (format stream "<h1 id=\"overview\">~a</h1>" (html-escape title))
    (format stream "<p class=\"meta\">Scope: <strong>~a</strong> • Generated pages: <strong>~d</strong></p>" (html-escape scope) (length page-entries))
    (format stream "<section id=\"what\"><h2>What</h2><p>This is a static docs site generated from markdown sources.</p></section>")
    (format stream "<section id=\"why\"><h2>Why</h2><p>It is optimized for offline readability, keyboard navigation, and predictable output.</p></section>")
    (format stream "<section id=\"how\"><h2>How</h2><p>Use the left navigation to open pages, then jump within sections from the right rail.</p></section>")
    (format stream "<section id=\"sources\"><h2>Discovered Sources</h2><ul class=\"nav-list\">~a</ul></section>" items)
    (format stream "</main><aside class=\"right-rail md-sidebar md-sidebar--secondary\"><p class=\"rail-title\">On This Page</p><ul class=\"toc-list\">~a</ul></aside></div></main></div></div></body></html>" toc-items))))

(defun build-manifest-json (scope page-entries style-relative-path pages-target)
  (let* ((html-relative-paths (mapcar (lambda (entry) (getf entry :html-relative)) page-entries))
         (pages-json (json-array-of-strings html-relative-paths))
         (page-count (length html-relative-paths)))
    (format nil
            "{~%  \"status\": \"ok\",~%  \"scope\": ~a,~%  \"pages_target\": ~a,~%  \"page_count\": ~d,~%  \"errors\": [],~%  \"pages\": ~a,~%  \"assets\": ~a~%}~%"
            (json-string scope)
            (json-string pages-target)
            page-count
            pages-json
            (json-array-of-strings (list style-relative-path)))))

(defun maybe-write-nojekyll (output-dir pages-target)
  (when (write-nojekyll-p pages-target)
    (write-text-file (merge-pathnames #P".nojekyll" output-dir) "")))

(defun build-site (config)
  (let* ((scope (plist-value config :scope "project"))
         (addon-name (plist-value config :addon-name ""))
         (pages-target (normalize-pages-target (plist-value config :pages-target "github")))
         (site-name (plist-value config :site-name (site-name-for-config scope addon-name)))
         (site-subtitle (plist-value config :site-subtitle "Reference Manual"))
         (render-mermaid-images (plist-value config :render-mermaid-images t))
         (cwd (uiop:getcwd))
         (project-root (resolve-directory-path (plist-value config :project-root ".") cwd))
         (docs-root (resolve-directory-path (plist-value config :docs-root "docs/") project-root))
         (output-dir (resolve-directory-path (plist-value config :output-dir "docs/_build/") project-root))
         (markdown-files (collect-markdown-files docs-root))
         (markdown-relative-paths (mapcar (lambda (path) (path-relative-to path docs-root)) markdown-files))
          (page-entries
            (enrich-page-entries-with-titles
             docs-root
             (mapcar #'markdown-relative-to-page-entry markdown-relative-paths)))
         (_compiled-pages (compile-markdown-pages docs-root output-dir page-entries site-name site-subtitle render-mermaid-images))
          (style-relative-path (write-style-sheet output-dir))
          (index-path (merge-pathnames #P"index.html" output-dir))
          (manifest-path (merge-pathnames #P"manifest.json" output-dir))
          (index-html (build-index-html scope site-name site-subtitle page-entries))
          (manifest-json (build-manifest-json scope page-entries style-relative-path pages-target)))
     (ensure-directory output-dir)
     (write-text-file index-path index-html)
     (write-text-file manifest-path manifest-json)
     (maybe-write-nojekyll output-dir pages-target)
     (list :status :ok
           :scope scope
           :pages-target pages-target
           :page-count (length markdown-relative-paths)
           :index-path (uiop:native-namestring index-path)
           :manifest-path (uiop:native-namestring manifest-path))))
