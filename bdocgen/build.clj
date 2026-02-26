(ns build
  (:require [clojure.tools.build.api :as b]))

(def lib 'bdocgen/bdocgen)
(def class-dir "target/classes")
(def basis (b/create-basis {:project "deps.edn"}))
(def version "0.1.0-SNAPSHOT")
(def jar-file (format "target/%s-%s.jar" (name lib) version))

(defn clean [_]
  (b/delete {:path "target"}))

(defn jar [_]
  (clean nil)
  (b/copy-dir {:src-dirs ["src" "resources"] :target-dir class-dir})
  (b/jar {:class-dir class-dir :jar-file jar-file :basis basis})
  {:jar jar-file})
