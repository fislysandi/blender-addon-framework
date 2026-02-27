(ns bdocgen.pages-test
  (:require [bdocgen.pages :as pages]
            [clojure.test :refer [deftest is]]))

(deftest stable-url-mapping
  (is (= {:source-path "docs/foo/bar.md"
          :route-base "foo/bar"
          :output-path "foo/bar/index.html"
          :url "/foo/bar/"}
         (pages/source-path->page :project ["docs" "bdocgen/docs"] "docs/foo/bar.md")))
  (is (= {:source-path "docs/index.md"
          :route-base ""
          :output-path "index.html"
          :url "/"}
         (pages/source-path->page :project ["docs" "bdocgen/docs"] "docs/index.md")))
  (is (= {:source-path "bdocgen/docs/architecture.md"
          :route-base "bdocgen/architecture"
          :output-path "bdocgen/architecture/index.html"
          :url "/bdocgen/architecture/"}
         (pages/source-path->page :project ["docs" "bdocgen/docs"] "bdocgen/docs/architecture.md"))))
