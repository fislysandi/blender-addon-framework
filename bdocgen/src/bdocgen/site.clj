(ns bdocgen.site
  (:require [clojure.string :as str]))

(def theme-css
  "
  :root {
    --content-max: 920px;
    --radius: 4px;
    --font-sans: 'Source Sans Pro', 'Noto Sans', 'DejaVu Sans', sans-serif;
    --font-heading: 'Noto Sans', 'Source Sans Pro', 'DejaVu Sans', sans-serif;
  }

  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }

  body {
    background: #0e1116;
  }

  .theme-root {
    --bg: #f6f7fa;
    --bg-elev: #ffffff;
    --bg-elev-2: #f2f4f8;
    --border: #d9deea;
    --text: #1e2634;
    --text-muted: #5e697b;
    --link: #1f74cf;
    --link-hover: #175da6;
    --accent: #565f0e;
    --brand: #243045;
    --heading-soft: #33435b;
    --code-bg: #eef2f8;
    --hover-bg: #eef3fb;
    --title-bg: #dde39b;
    --title-fg: #223006;
    --sidebar-bg: #ffffff;
    --sidebar-border: #d8deea;
    --sidebar-sep: #d8deea;
    --bg-gradient: var(--bg);

    color: var(--text);
    font-family: var(--font-sans);
    line-height: 1.55;
    min-height: 100vh;
    padding: 1rem;
  }

  @media (prefers-color-scheme: dark) {
    .theme-root {
      --bg: #0f1116;
      --bg-elev: #151a22;
      --bg-elev-2: #141921;
      --border: #2a313d;
      --text: #d8dee8;
      --text-muted: #9aa5b5;
      --link: #5ba8ff;
      --link-hover: #8ac3ff;
      --accent: #aab23b;
      --brand: #e4e9f1;
      --heading-soft: #c5d0df;
      --code-bg: #161c25;
      --hover-bg: #1a212b;
      --title-bg: #565b10;
      --title-fg: #edf2d3;
      --sidebar-bg: #171c23;
      --sidebar-border: #303744;
      --sidebar-sep: #2a313d;
      --bg-gradient: var(--bg);
    }
  }

  .theme-toggle {
    position: absolute;
    opacity: 0;
    pointer-events: none;
  }

  .theme-toggle:checked + .theme-root {
    --bg: #0f1116;
    --bg-elev: #151a22;
    --bg-elev-2: #141921;
    --border: #2a313d;
    --text: #d8dee8;
    --text-muted: #9aa5b5;
    --link: #5ba8ff;
    --link-hover: #8ac3ff;
    --accent: #aab23b;
    --brand: #e4e9f1;
    --heading-soft: #c5d0df;
    --code-bg: #161c25;
    --hover-bg: #1a212b;
    --title-bg: #565b10;
    --title-fg: #edf2d3;
    --sidebar-bg: #171c23;
    --sidebar-border: #303744;
    --sidebar-sep: #2a313d;
    --bg-gradient: var(--bg);
  }

  @media (prefers-color-scheme: dark) {
    .theme-toggle:checked + .theme-root {
      --bg: #f6f7fa;
      --bg-elev: #ffffff;
      --bg-elev-2: #f2f4f8;
      --border: #d9deea;
      --text: #1e2634;
      --text-muted: #5e697b;
      --link: #1f74cf;
      --link-hover: #175da6;
      --accent: #565f0e;
      --brand: #243045;
      --heading-soft: #33435b;
      --code-bg: #eef2f8;
      --hover-bg: #eef3fb;
      --title-bg: #dde39b;
      --title-fg: #223006;
      --sidebar-bg: #ffffff;
      --sidebar-border: #d8deea;
      --sidebar-sep: #d8deea;
      --bg-gradient: var(--bg);
    }
  }

  .theme-root {
    background: var(--bg-gradient);
    padding: 0;
  }

  a { color: var(--link); text-decoration: none; }
  a:hover { color: var(--link-hover); text-decoration: underline; }

  .theme-switch {
    display: inline-block;
    margin: 0.1rem 0 0.7rem;
    padding: 0.16rem 0.5rem;
    border-radius: 999px;
    border: 1px solid var(--border);
    color: var(--text-muted);
    background: transparent;
    cursor: pointer;
    user-select: none;
    font-size: 0.76rem;
    letter-spacing: 0.01em;
  }

  .theme-switch:hover {
    color: var(--text);
  }

  .theme-toggle:focus + .theme-root .theme-switch {
    outline: 2px solid var(--link);
    outline-offset: 2px;
  }

  .layout {
    display: grid;
    grid-template-columns: 620px minmax(0, var(--content-max)) 230px;
    gap: 0;
    align-items: start;
    max-width: none;
    margin: 0;
    min-height: 100vh;
  }

  .panel {
    background: transparent;
    border: none;
    border-radius: 0;
  }

  .left-rail {
    position: sticky;
    top: 0;
    max-height: 100vh;
    min-height: 100vh;
    overflow: auto;
    padding: 0;
    border-radius: 0;
    background: var(--sidebar-bg);
    border: 0;
    border-right: 1px solid var(--sidebar-border);
  }

  .left-rail-inner {
    width: 286px;
    margin-left: auto;
    padding: 1rem 1rem 0.8rem;
  }

  .left-rail::-webkit-scrollbar {
    width: 8px;
  }

  .left-rail::-webkit-scrollbar-thumb {
    background: #394251;
    border-radius: 999px;
  }

  .search-wrap {
    border-top: 1px solid var(--sidebar-sep);
    border-bottom: 1px solid var(--sidebar-sep);
    padding: 0.48rem 0;
    margin: 0.36rem 0 0.86rem;
    position: relative;
  }

  .search-wrap::before {
    content: '⌕';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-52%);
    color: #7f8a9a;
    font-size: 0.92rem;
  }

  .search-field {
    width: 100%;
    border: 0;
    outline: none;
    background: transparent;
    color: var(--text-muted);
    font-size: 0.95rem;
    padding-left: 1.3rem;
  }

  .search-field::placeholder {
    color: #7f8a9a;
  }

  .brand {
    font-family: var(--font-heading);
    font-size: 2.05rem;
    margin: 0;
    color: var(--brand);
    font-weight: 700;
    letter-spacing: -0.01em;
    line-height: 1;
  }

  .brand-lockup {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    margin-bottom: 0.52rem;
    padding: 0.12rem 0;
  }

  .brand-mark {
    display: inline-block;
    width: 1.05rem;
    height: 1.05rem;
    border-radius: 999px;
    border: 2px solid #f28b39;
    box-shadow: inset 0 0 0 3px var(--sidebar-bg);
    background: #f28b39;
    flex: 0 0 auto;
  }

  .brand-sub {
    color: var(--text-muted);
    margin: 0.42rem 0 0.62rem;
    font-size: 1.92rem;
    font-weight: 300;
    line-height: 1.15;
  }

  .content {
    min-height: 100vh;
    padding: 1.05rem 2.35rem 2rem 2.2rem;
  }

  .content h1,
  .content h2,
  .content h3 {
    font-family: var(--font-heading);
    line-height: 1.25;
    margin-top: 1.4rem;
    margin-bottom: 0.7rem;
    scroll-margin-top: 1rem;
  }

  .content h1 { font-size: 2.9rem; margin-top: 0.2rem; margin-bottom: 0.85rem; font-weight: 700; }
  .content h2 { font-size: 2.5rem; }
  .content h3 { font-size: 1.2rem; color: var(--heading-soft); }

  .content h1:first-of-type {
    display: inline;
    background: transparent;
    color: var(--brand);
    border-radius: 0;
    padding: 0;
  }

  .content h1:target,
  .content h2:target,
  .content h3:target {
    display: inline-block;
    background: var(--title-bg);
    color: var(--title-fg);
    border-radius: var(--radius);
    padding: 0.04rem 0.4rem 0.1rem;
  }

  .heading-citation {
    margin-left: 0.38rem;
    color: var(--text-muted);
    text-decoration: none;
    opacity: 0;
    font-size: 0.72em;
    vertical-align: middle;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1em;
  }

  .heading-citation::before {
    content: '⛓';
    font-size: 0.76em;
    line-height: 1;
  }

  .content h1:hover .heading-citation,
  .content h2:hover .heading-citation,
  .content h3:hover .heading-citation,
  .heading-citation:focus {
    opacity: 1;
    color: var(--link);
  }

  .content p,
  .content li { color: var(--text); }

  .content p,
  .content ul,
  .content ol {
    margin-top: 0.55rem;
    margin-bottom: 0.75rem;
    font-size: 1.02rem;
  }

  .content pre,
  .content code {
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 6px;
  }

  .content pre { padding: 0.75rem; overflow: auto; }
  .content code { padding: 0.08rem 0.35rem; }

  .right-rail {
    position: sticky;
    top: 0;
    padding: 1.05rem 0 0.2rem 1.25rem;
    border-left: 1px solid var(--border);
  }

  .rail-title {
    margin: 0 0 0.7rem;
    font-size: 0.85rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
  }

  .nav-list,
  .toc-list {
    margin: 0;
    padding: 0;
    list-style: none;
    display: block;
    gap: 0.45rem;
  }

  .nav-list li,
  .toc-list li {
    border: 0;
    border-radius: 0;
    padding: 0.14rem 0;
  }

  .nav-group-title {
    margin: 1rem 0 0.25rem;
    font-size: 0.72rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--text-muted);
    font-weight: 700;
  }

  .nav-link {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.6rem;
    text-decoration: none;
    font-size: 1.12rem;
    line-height: 1.28;
  }

  .nav-link::after {
    content: '⌄';
    color: #4d82c7;
    font-size: 0.88em;
  }

  .nav-link.current {
    color: #8fc2ff;
    font-weight: 600;
  }

  .sidebar-foot {
    margin-top: 1.2rem;
    padding-top: 0.62rem;
    border-top: 1px solid var(--sidebar-sep);
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.45rem;
  }

  .foot-chip {
    border: 1px solid var(--sidebar-border);
    border-radius: 3px;
    text-align: center;
    font-size: 0.8rem;
    color: var(--link);
    padding: 0.12rem 0;
  }

  .nav-list li:hover,
  .toc-list li:hover {
    background: transparent;
  }

  .nav-list a,
  .toc-list a {
    color: var(--link);
  }

  .nav-list a:hover,
  .toc-list a:hover {
    color: var(--link-hover);
  }

  .meta {
    color: var(--text-muted);
    margin-bottom: 1rem;
    font-size: 0.95rem;
  }

  .back-link {
    display: inline-block;
    margin-bottom: 0.6rem;
    color: var(--text-muted);
    font-weight: 500;
    font-size: 0.82rem;
  }

  @media (max-width: 1180px) {
    .layout {
      grid-template-columns: 300px minmax(0, 1fr);
      gap: 0;
    }
    .right-rail { display: none; }

    .left-rail-inner {
      width: 100%;
    }
  }

  @media (max-width: 860px) {
    .layout {
      grid-template-columns: 1fr;
      padding: 0.6rem;
    }
    .left-rail,
    .content {
      position: static;
      max-height: none;
    }
    .content { min-height: auto; }
  }
  ")

(defn page-title
  [scope]
  (case scope
    :project "BDocGen Project Documentation"
    "BDocGen Self Documentation"))

(defn- escape-html
  [text]
  (-> (or text "")
      (str/replace "&" "&amp;")
      (str/replace "<" "&lt;")
      (str/replace ">" "&gt;")
      (str/replace "\"" "&quot;")))

(defn- strip-tags
  [html-fragment]
  (-> (or html-fragment "")
      (str/replace #"<[^>]+>" "")
      (str/replace "¶" "")
      (str/trim)))

(defn- extract-section-headings
  [body-html]
  (->> (re-seq #"<h2 id=\"([^\"]+)\"[^>]*>(.*?)</h2>" (or body-html ""))
       (map (fn [[_ id label]] {:id id :label (strip-tags label)}))
       (remove (fn [{:keys [label]}] (str/blank? label)))
       vec))

(defn- nav-groups
  [pages]
  (let [pairs (map (fn [page]
                     {:title (:title page)
                      :url (:url page)})
                   pages)
        first-group (vec (take 4 pairs))
        second-group (vec (drop 4 pairs))]
    [{:title "Getting Started" :pages first-group}
     {:title "Sections" :pages second-group}]))

(defn- render-sidebar
  [{:keys [site-name site-subtitle pages current-url index-href]}]
  (let [groups (nav-groups pages)
        nav-html (str/join ""
                           (map (fn [{:keys [title pages]}]
                                  (if (seq pages)
                                    (str "<p class=\"nav-group-title\">" (escape-html title) "</p>"
                                         "<ul class=\"nav-list\">"
                                         (str/join ""
                                                   (map (fn [{:keys [title url]}]
                                                          (str "<li><a class=\"nav-link"
                                                               (when (= current-url url) " current")
                                                               "\" href=\"." url "\">"
                                                               (escape-html title)
                                                               "</a></li>"))
                                                        pages))
                                         "</ul>")
                                    ""))
                                groups))
        back-link (if index-href
                    (str "<a class=\"back-link\" href=\"" index-href "\">Back to docs index</a>")
                    "")]
    (str "  <aside class=\"panel left-rail\">\n"
         "    <div class=\"left-rail-inner\">\n"
         "    <div class=\"brand-lockup\"><span class=\"brand-mark\" aria-hidden=\"true\"></span><h1 class=\"brand\">" (escape-html site-name) "</h1></div>\n"
         "    <p class=\"brand-sub\">" (escape-html site-subtitle) "</p>\n"
         "    <label class=\"theme-switch\" for=\"theme-toggle\">Switch theme</label>\n"
         back-link "\n"
         "    <div class=\"search-wrap\"><input class=\"search-field\" type=\"search\" placeholder=\"Search\" aria-label=\"Search docs\"></div>\n"
         nav-html "\n"
         "    <div class=\"sidebar-foot\"><div class=\"foot-chip\">5.0</div><div class=\"foot-chip\">English</div></div>\n"
         "    </div>\n"
         "  </aside>\n")))

(defn render-index-html
  [plan]
  (let [title (page-title (:scope plan))
        site-name (or (:site-name plan) "bdocgen")
        site-subtitle (or (:site-subtitle plan) "Reference Manual")
        items (if (seq (:pages plan))
                (str/join ""
                          (map (fn [{:keys [title url source-path]}]
                                 (str "<li><a href=\"." url "\">" (escape-html title) "</a>"
                                      " <code>" source-path "</code></li>"))
                               (:pages plan)))
                "<li><em>No markdown docs discovered.</em></li>")
        toc-items (str/join ""
                            ["<li><a href=\"#overview\">Overview</a></li>"
                             "<li><a href=\"#sources\">Discovered Sources</a></li>"])]
    (str "<!doctype html>\n"
         "<html lang=\"en\">\n"
         "<head>\n"
         "  <meta charset=\"utf-8\">\n"
         "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
         "  <title>" title "</title>\n"
         "  <style>" theme-css "</style>\n"
         "</head>\n"
         "<body>\n"
         "<input class=\"theme-toggle\" type=\"checkbox\" id=\"theme-toggle\" aria-label=\"Toggle light and dark mode\">\n"
         "<div class=\"theme-root\">\n"
         "<div class=\"layout\">\n"
         (render-sidebar {:site-name site-name
                          :site-subtitle site-subtitle
                          :pages (:pages plan)
                          :current-url "/"
                          :index-href nil})
         "  <main class=\"panel content\">\n"
         "    <h1 id=\"overview\">" title "</h1>\n"
         "    <p>This is a static HTML/CSS output generated by BDocGen.</p>\n"
         "    <p class=\"meta\">Scope: <strong>" (name (:scope plan)) "</strong> • Generated pages: <strong>" (:page-count plan) "</strong></p>\n"
         "    <h2 id=\"sources\">Discovered Sources</h2>\n"
         "    <ul class=\"nav-list\">" items "</ul>\n"
         "  </main>\n"
         "  <aside class=\"panel right-rail\">\n"
         "    <p class=\"rail-title\">On This Page</p>\n"
         "    <ul class=\"toc-list\">" toc-items "</ul>\n"
         "  </aside>\n"
         "</div>\n"
         "</div>\n"
         "</body>\n"
         "</html>\n")))

(defn render-page-html
  [{:keys [title body-html output-path pages current-url site-name site-subtitle]}]
  (let [segments (str/split output-path #"/")
        nesting (max 0 (dec (count segments)))
        index-href (if (zero? nesting)
                     "index.html"
                     (str (apply str (repeat nesting "../")) "index.html"))
        sections (extract-section-headings body-html)
        section-items (if (seq sections)
                        (str/join ""
                                  (map (fn [{:keys [id label]}]
                                         (str "<li><a href=\"#" (escape-html id) "\">"
                                              (escape-html label)
                                              "</a></li>"))
                                       sections))
                        "<li><em>No section headings</em></li>")]
    (str "<!doctype html>\n"
       "<html lang=\"en\">\n"
       "<head>\n"
       "  <meta charset=\"utf-8\">\n"
       "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
       "  <title>" (escape-html title) "</title>\n"
       "  <style>" theme-css "</style>\n"
       "</head>\n"
       "<body>\n"
       "<input class=\"theme-toggle\" type=\"checkbox\" id=\"theme-toggle\" aria-label=\"Toggle light and dark mode\">\n"
       "<div class=\"theme-root\">\n"
       "<div class=\"layout\">\n"
       (render-sidebar {:site-name (or site-name "bdocgen")
                        :site-subtitle (or site-subtitle "Reference Manual")
                        :pages pages
                        :current-url current-url
                        :index-href index-href})
       "  <main class=\"panel content\">\n"
       body-html
       "  </main>\n"
       "  <aside class=\"panel right-rail\">\n"
       "    <p class=\"rail-title\">On This Page</p>\n"
       "    <ul class=\"toc-list\">" section-items "</ul>\n"
       "  </aside>\n"
       "</div>\n"
       "</div>\n"
       "</body>\n"
       "</html>\n")))
