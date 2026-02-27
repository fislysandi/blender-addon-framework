(ns bdocgen.core
  (:require [bdocgen.discovery :as discovery]
            [bdocgen.pages :as pages]
            [bdocgen.specs :as specs]))

(defn plan-build
  ([request]
   (plan-build request []))
  ([request candidate-paths]
   (if (specs/request-valid? request)
    (let [scope (or (:scope request) :self)
          source-roots (:source-roots request)
          doc-paths (discovery/select-doc-paths scope source-roots candidate-paths)
          page-specs (pages/build-page-specs scope
                                             (discovery/resolve-roots scope source-roots)
                                             doc-paths)]
      {:ok true
       :plan {:docs-root (:docs-root request)
              :output-dir (:output-dir request)
              :addon-name (:addon-name request)
              :scope scope
              :source-roots (discovery/resolve-roots scope source-roots)
              :discovery (discovery/build-discovery-plan scope source-roots)
              :doc-count (count doc-paths)
              :doc-paths doc-paths
              :page-count (count page-specs)
              :pages page-specs
              :steps [:scan-docs :convert-markdown :build-navigation :write-site]}})
    {:ok false
     :error {:type :invalid-request
             :details (specs/explain-request request)}})))
