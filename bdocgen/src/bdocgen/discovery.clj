(ns bdocgen.discovery
  (:require [clojure.string :as str]))

(def ignored-dir-segments
  #{".git" ".tmp" "target" ".venv" "node_modules" ".clj-kondo" ".idea" ".vscode" "_build"})

(defn normalize-path
  [path]
  (-> path
      (str/replace "\\" "/")
      (str/replace #"^\./" "")))

(defn scope->roots
  [scope]
  (case scope
    :self ["bdocgen/docs"]
    :project ["docs" "bdocgen/docs"]
    []))

(defn resolve-roots
  [scope source-roots]
  (if (seq source-roots)
    (->> source-roots
         (map normalize-path)
         vec)
    (scope->roots scope)))

(defn markdown-path?
  [path]
  (or (str/ends-with? path ".md")
      (str/ends-with? path ".markdown")))

(defn hidden-or-ignored-segment?
  [segment]
  (or (contains? ignored-dir-segments segment)
      (and (not= segment "..")
           (str/starts-with? segment "."))))

(defn ignored-path?
  [path]
  (let [segments (str/split path #"/")]
    (some hidden-or-ignored-segment? (butlast segments))))

(defn within-roots?
  [path roots]
  (some (fn [root]
          (or (= path root)
              (str/starts-with? path (str root "/"))))
        roots))

(defn include-path?
  [roots path]
  (let [normalized (normalize-path path)
        resolved-roots (or roots [])]
    (and (within-roots? normalized resolved-roots)
         (markdown-path? normalized)
         (not (ignored-path? normalized)))))

(defn select-doc-paths
  [scope source-roots candidate-paths]
  (let [roots (resolve-roots scope source-roots)]
  (->> candidate-paths
       (map normalize-path)
       (filter (fn [path] (include-path? roots path)))
       distinct
       sort
       vec)))

(defn build-discovery-plan
  [scope source-roots]
  (let [roots (resolve-roots scope source-roots)]
  {:scope scope
   :roots roots
   :accepted-extensions [".md" ".markdown"]
   :ignored-dir-segments (sort ignored-dir-segments)}))
