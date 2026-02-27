(ns bdocgen.core-test
  (:require [bdocgen.core :as core]
            [clojure.test :refer [deftest is]]))

(deftest plan-build-valid-request
  (let [candidates ["bdocgen/docs/architecture.md"
                    "docs/index.md"
                    "README.md"]
        result (core/plan-build {:docs-root "docs" :output-dir "docs/_build"}
                                candidates)]
    (is (= true (:ok result)))
    (is (= [:scan-docs :convert-markdown :build-navigation :write-site]
           (get-in result [:plan :steps])))
    (is (= :self (get-in result [:plan :scope])))
    (is (= ["bdocgen/docs"] (get-in result [:plan :source-roots])))
    (is (= ["bdocgen/docs/architecture.md"]
           (get-in result [:plan :doc-paths])))
    (is (= [{:source-path "bdocgen/docs/architecture.md"
             :route-base "architecture"
             :output-path "architecture/index.html"
             :url "/architecture/"}]
           (get-in result [:plan :pages])))))

(deftest plan-build-project-scope
  (let [candidates ["bdocgen/docs/architecture.md"
                    "docs/index.md"
                    "docs/reference/usage.md"]
        result (core/plan-build {:docs-root "docs"
                                 :output-dir "docs/_build"
                                 :scope :project}
                                candidates)]
    (is (= true (:ok result)))
    (is (= :project (get-in result [:plan :scope])))
    (is (= ["bdocgen/docs/architecture.md"
            "docs/index.md"
            "docs/reference/usage.md"]
           (get-in result [:plan :doc-paths])))
    (is (= ["bdocgen/architecture/index.html"
            "index.html"
           "reference/usage/index.html"]
           (mapv :output-path (get-in result [:plan :pages]))))))

(deftest plan-build-project-custom-root
  (let [candidates ["addons/demo/docs/index.md"
                    "addons/demo/docs/guide/usage.md"
                    "docs/index.md"]
        result (core/plan-build {:docs-root "addons/demo/docs"
                                 :output-dir "addons/demo/docs/_build"
                                 :scope :project
                                 :source-roots ["addons/demo/docs"]}
                                candidates)]
    (is (= true (:ok result)))
    (is (= ["addons/demo/docs"] (get-in result [:plan :source-roots])))
    (is (= ["guide/usage/index.html" "index.html"]
           (mapv :output-path (get-in result [:plan :pages]))))))

(deftest plan-build-invalid-request
  (let [result (core/plan-build {:docs-root "docs"})]
    (is (= false (:ok result)))
    (is (= :invalid-request (get-in result [:error :type])))))
