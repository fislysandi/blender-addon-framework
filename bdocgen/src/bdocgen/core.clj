(ns bdocgen.core
  (:require [bdocgen.discovery :as discovery]
            [bdocgen.specs :as specs]))

(defn plan-build
  ([request]
   (plan-build request []))
  ([request candidate-paths]
  (if (specs/request-valid? request)
    (let [scope (or (:scope request) :self)
          doc-paths (discovery/select-doc-paths scope candidate-paths)]
      {:ok true
       :plan {:docs-root (:docs-root request)
              :output-dir (:output-dir request)
              :addon-name (:addon-name request)
              :scope scope
              :discovery (discovery/build-discovery-plan scope)
              :doc-count (count doc-paths)
              :doc-paths doc-paths
              :steps [:scan-docs :convert-markdown :build-navigation :write-site]}})
    {:ok false
     :error {:type :invalid-request
             :details (specs/explain-request request)}})))
