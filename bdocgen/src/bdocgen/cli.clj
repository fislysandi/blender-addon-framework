(ns bdocgen.cli
  (:require [bdocgen.core :as core]
            [bdocgen.fs :as fs]
            [bdocgen.logging :as logging]
            [bdocgen.site :as site]
            [bdocgen.writer :as writer]))

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

(defn run
  [{:keys [docs-root output-dir addon-name scope project-root] :as _opts}]
  (let [effective-scope (or scope :self)
        request (cond-> {:scope effective-scope
                         :docs-root (or docs-root (default-docs-root effective-scope))
                         :output-dir (or output-dir (default-output-dir effective-scope))}
                  addon-name (assoc :addon-name addon-name))
        root (or project-root "..")
        candidate-paths (fs/list-relative-file-paths root)
        result (core/plan-build request candidate-paths)]
    (if (:ok result)
      (let [html (site/render-index-html (:plan result))
            output (writer/write-index-html! {:project-root root
                                              :output-dir (:output-dir request)
                                              :html html})]
        (logging/log-event {:phase :built
                            :request request
                            :doc-count (get-in result [:plan :doc-count])
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
