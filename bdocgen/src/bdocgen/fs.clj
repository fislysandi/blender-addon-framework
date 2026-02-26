(ns bdocgen.fs
  (:require [clojure.java.io :as io]
            [clojure.string :as str]))

(defn- normalize-path
  [path]
  (-> path
      (str/replace "\\" "/")
      (str/replace #"^\./" "")))

(defn list-relative-file-paths
  [root-dir]
  (let [root-file (io/file root-dir)
        root-path (.toPath root-file)]
    (if (.exists root-file)
      (->> (file-seq root-file)
           (filter #(.isFile %))
           (map #(.toPath %))
           (map #(.relativize root-path %))
           (map str)
           (map normalize-path)
           vec)
      [])))
