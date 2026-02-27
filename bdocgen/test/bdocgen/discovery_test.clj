(ns bdocgen.discovery-test
  (:require [bdocgen.discovery :as discovery]
            [clojure.test :refer [deftest is testing]]))

(deftest scope-roots
  (testing "self scope only includes bdocgen docs"
    (is (= ["bdocgen/docs"]
           (discovery/scope->roots :self))))
  (testing "project scope includes root docs and bdocgen docs"
    (is (= ["docs" "bdocgen/docs"]
           (discovery/scope->roots :project)))))

(deftest select-doc-paths-self-scope
  (let [candidates ["docs/index.md"
                    "bdocgen/docs/architecture.md"
                    "bdocgen/docs/_build/index.md"
                    "bdocgen/docs/guide.markdown"
                    "bdocgen/src/bdocgen/core.clj"
                    "./bdocgen/docs/getting-started.md"
                    "bdocgen/docs/.drafts/private.md"
                    "bdocgen\\docs\\windows-path.md"]]
    (is (= ["bdocgen/docs/architecture.md"
            "bdocgen/docs/getting-started.md"
            "bdocgen/docs/guide.markdown"
            "bdocgen/docs/windows-path.md"]
           (discovery/select-doc-paths :self nil candidates)))))

(deftest select-doc-paths-project-scope
  (let [candidates ["docs/overview.md"
                    "docs/reference/api.md"
                    "docs/_build/index.md"
                    ".tmp/external-context/clojure/bdocgen.md"
                    "bdocgen/docs/architecture.md"
                    "target/site/index.md"
                    "README.md"]]
    (is (= ["bdocgen/docs/architecture.md"
            "docs/overview.md"
            "docs/reference/api.md"]
           (discovery/select-doc-paths :project nil candidates)))))

(deftest select-doc-paths-custom-root
  (let [candidates ["addons/demo/docs/index.md"
                    "addons/demo/docs/guide/usage.md"
                    "docs/index.md"]]
    (is (= ["addons/demo/docs/guide/usage.md"
            "addons/demo/docs/index.md"]
           (discovery/select-doc-paths :project ["addons/demo/docs"] candidates)))))

(deftest build-discovery-plan-shape
  (let [plan (discovery/build-discovery-plan :project nil)]
    (is (= :project (:scope plan)))
    (is (= ["docs" "bdocgen/docs"] (:roots plan)))
    (is (= [".md" ".markdown"] (:accepted-extensions plan)))
    (is (some #(= "_build" %) (:ignored-dir-segments plan)))))
