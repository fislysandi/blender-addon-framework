(ns bdocgen.cli
  (:require [bdocgen.core :as core]
            [bdocgen.fs :as fs]
            [bdocgen.markdown :as markdown]
            [bdocgen.logging :as logging]
            [bdocgen.site :as site]
            [bdocgen.writer :as writer]
            [clojure.java.io :as io]
            [clojure.string :as str]))

(defn default-docs-root
  [scope]
  (case scope
    :project "docs"
    "bdocgen/docs"))

(defn default-output-dir
  [scope]
  (case scope
    :project "docs/_build"
    "bdocgen/docs/_build"))

(defn site-name
  [{:keys [addon-name scope]}]
  (cond
    (and addon-name (not (str/blank? addon-name))) addon-name
    (= scope :project) "blender-addon-framework"
    :else "bdocgen"))

(defn site-subtitle
  [_request]
  "Reference Manual")

(defn run
  [{:keys [docs-root output-dir addon-name scope project-root] :as _opts}]
  (let [effective-scope (or scope :self)
        request (cond-> {:scope effective-scope
                         :docs-root (or docs-root (default-docs-root effective-scope))
                         :output-dir (or output-dir (default-output-dir effective-scope))}
                  docs-root (assoc :source-roots [docs-root])
                  addon-name (assoc :addon-name addon-name))
        resolved-site-name (site-name request)
        resolved-site-subtitle (site-subtitle request)
        root (or project-root "..")
        candidate-paths (fs/list-relative-file-paths root)
        result (core/plan-build request candidate-paths)]
    (if (:ok result)
      (let [page-models (mapv (fn [page-spec]
                                (let [source-text (slurp (io/file root (:source-path page-spec)))
                                      title (markdown/extract-title (:source-path page-spec) source-text)
                                      body-html (markdown/render-html source-text)]
                                  (assoc page-spec
                                         :title title
                                         :body-html body-html)))
                              (get-in result [:plan :pages]))
            nav-pages (mapv (fn [{:keys [title url]}]
                              {:title title :url url})
                            page-models)
            pages (mapv (fn [page]
                          (let [html (site/render-page-html {:title (:title page)
                                                             :body-html (:body-html page)
                                                             :output-path (:output-path page)
                                                             :pages nav-pages
                                                             :current-url (:url page)
                                                             :site-name resolved-site-name
                                                             :site-subtitle resolved-site-subtitle})]
                            (-> page
                                (dissoc :body-html)
                                (assoc :html html))))
                        page-models)
            index-html (site/render-index-html (assoc (:plan result)
                                                      :site-name resolved-site-name
                                                      :site-subtitle resolved-site-subtitle
                                                      :pages pages))
            output (writer/write-site! {:project-root root
                                        :output-dir (:output-dir request)
                                        :scope (get-in result [:plan :scope])
                                        :index-html index-html
                                        :pages pages
                                        :errors []})]
        (logging/log-event {:phase :built
                            :request request
                            :doc-count (get-in result [:plan :doc-count])
                            :page-count (count pages)
                            :scope (get-in result [:plan :scope])
                            :index-path (:index-path output)})
        (assoc result :output output))
      (do
        (logging/log-error (:error result))
        result))))

(defn -main
  [& _args]
  (let [result (run {})]
    (when-not (:ok result)
      (System/exit 1))))
