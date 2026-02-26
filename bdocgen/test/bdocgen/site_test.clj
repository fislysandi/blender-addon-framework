(ns bdocgen.site-test
  (:require [bdocgen.site :as site]
            [clojure.test :refer [deftest is]]))

(deftest render-index-html-includes-plan-data
  (let [html (site/render-index-html {:scope :self
                                      :doc-count 2
                                      :doc-paths ["bdocgen/docs/architecture.md"
                                                  "bdocgen/docs/guide.md"]})]
    (is (string? html))
    (is (.contains html "BDocGen Self Documentation"))
    (is (.contains html "bdocgen/docs/architecture.md"))
    (is (.contains html "Discovered markdown files: <strong>2</strong>"))))
