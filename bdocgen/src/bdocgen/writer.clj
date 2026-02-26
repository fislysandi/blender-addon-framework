(ns bdocgen.writer
  (:require [clojure.java.io :as io]))

(defn write-index-html!
  [{:keys [project-root output-dir html]}]
  (let [target-file (io/file project-root output-dir "index.html")]
    (io/make-parents target-file)
    (spit target-file html)
    {:index-path (.getPath target-file)}))
