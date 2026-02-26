(ns bdocgen.specs
  (:require [clojure.spec.alpha :as s]))

(s/def ::docs-root string?)
(s/def ::output-dir string?)
(s/def ::addon-name string?)
(s/def ::scope #{:self :project})

(s/def ::request
  (s/keys :req-un [::docs-root ::output-dir]
          :opt-un [::addon-name ::scope]))

(defn request-valid?
  [request]
  (s/valid? ::request request))

(defn explain-request
  [request]
  (s/explain-data ::request request))
