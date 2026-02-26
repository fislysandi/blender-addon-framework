(ns bdocgen.cli-test
  (:require [bdocgen.cli :as cli]
            [clojure.java.io :as io]
            [clojure.test :refer [deftest is]]))

(defn- temp-dir
  []
  (-> (java.nio.file.Files/createTempDirectory "bdocgen-test-" (make-array java.nio.file.attribute.FileAttribute 0))
      (.toFile)))

(deftest run-builds-openable-index
  (let [root (temp-dir)
        docs-file (io/file root "bdocgen/docs/architecture.md")]
    (io/make-parents docs-file)
    (spit docs-file "# Architecture")
    (let [result (cli/run {:project-root (.getPath root) :scope :self})
          index-path (get-in result [:output :index-path])
          html (slurp index-path)]
      (is (= true (:ok result)))
      (is (.exists (io/file index-path)))
      (is (.contains html "<!doctype html>"))
      (is (.contains html "Discovered Sources")))))
