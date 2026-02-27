(ns bdocgen.site-test
  (:require [bdocgen.site :as site]
            [clojure.test :refer [deftest is]]))

(deftest render-index-html-includes-plan-data
  (let [html (site/render-index-html {:scope :self
                                      :doc-count 2
                                      :page-count 2
                                      :pages [{:title "Architecture"
                                               :url "/architecture/"
                                               :source-path "bdocgen/docs/architecture.md"}
                                              {:title "Guide"
                                               :url "/guide/"
                                               :source-path "bdocgen/docs/guide.md"}]})]
    (is (string? html))
    (is (.contains html "BDocGen Self Documentation"))
    (is (.contains html "bdocgen/docs/architecture.md"))
    (is (.contains html "Generated pages: <strong>2</strong>"))))

(deftest render-page-html-includes-content
  (let [html (site/render-page-html {:title "Architecture"
                                     :output-path "reference/intro/index.html"
                                     :body-html "<h1>Architecture</h1>"})]
    (is (.contains html "Back to docs index"))
    (is (.contains html "../../index.html"))
    (is (.contains html "<h1>Architecture</h1>"))))
