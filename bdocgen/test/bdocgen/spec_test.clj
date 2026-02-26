(ns bdocgen.spec-test
  (:require [bdocgen.specs :as specs]
            [clojure.test :refer [deftest is]]))

(deftest request-validation
  (is (true? (specs/request-valid? {:docs-root "docs" :output-dir "docs/_build"})))
  (is (true? (specs/request-valid? {:docs-root "docs" :output-dir "docs/_build" :scope :project})))
  (is (false? (specs/request-valid? {:docs-root "docs"})))
  (is (false? (specs/request-valid? {:docs-root "docs" :output-dir "docs/_build" :scope :all}))))
