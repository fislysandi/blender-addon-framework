(ns bdocgen.cli-test
  (:require [bdocgen.cli :as cli]
            [clojure.data.json :as json]
            [clojure.java.io :as io]
            [clojure.test :refer [deftest is]]))

(defn- temp-dir
  []
  (-> (java.nio.file.Files/createTempDirectory "bdocgen-test-" (make-array java.nio.file.attribute.FileAttribute 0))
      (.toFile)))

(deftest run-builds-openable-site-and-manifest
  (let [root (temp-dir)
        docs-file (io/file root "bdocgen/docs/architecture.md")
        guide-file (io/file root "bdocgen/docs/getting-started.md")]
    (io/make-parents docs-file)
    (spit docs-file "# Architecture\n\nHello docs.")
    (spit guide-file "# Getting Started\n\nRun this.")
    (let [result (cli/run {:project-root (.getPath root) :scope :self})
          index-path (get-in result [:output :index-path])
          page-paths (get-in result [:output :page-paths])
          manifest-path (get-in result [:output :manifest-path])
          html (slurp index-path)
          manifest (json/read-str (slurp manifest-path))]
      (is (= true (:ok result)))
      (is (.exists (io/file index-path)))
      (is (= 2 (count page-paths)))
      (is (.exists (io/file manifest-path)))
      (is (.contains html "<!doctype html>"))
      (is (.contains html "Generated pages"))
      (is (= "ok" (get manifest "status")))
      (is (= "self" (get manifest "scope")))
      (is (= [] (get manifest "errors")))
      (is (= 2 (get manifest "page_count"))))))
