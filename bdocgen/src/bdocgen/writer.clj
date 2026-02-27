(ns bdocgen.writer
  (:require [clojure.data.json :as json]
            [clojure.java.io :as io]))

(defn write-index-html!
  [{:keys [project-root output-dir html]}]
  (let [target-file (io/file project-root output-dir "index.html")]
    (io/make-parents target-file)
    (spit target-file html)
    {:index-path (.getPath target-file)}))

(defn- write-page!
  [{:keys [project-root output-dir page]}]
  (let [target-file (io/file project-root output-dir (:output-path page))]
    (io/make-parents target-file)
    (spit target-file (:html page))
    (.getPath target-file)))

(defn- manifest-json
  [{:keys [scope pages errors]}]
  (json/write-str
   {"status" (if (seq errors) "error" "ok")
    "scope" (name scope)
    "page_count" (count pages)
    "errors" (vec (or errors []))
    "pages" (mapv (fn [page]
                      {"source_path" (:source-path page)
                       "output_path" (:output-path page)
                       "url" (:url page)
                       "title" (:title page)})
                    pages)}))

(defn write-site!
  [{:keys [project-root output-dir scope index-html pages errors]}]
  (let [index-result (write-index-html! {:project-root project-root
                                         :output-dir output-dir
                                         :html index-html})
        page-paths (mapv (fn [page]
                           (write-page! {:project-root project-root
                                         :output-dir output-dir
                                         :page page}))
                         pages)
        manifest-file (io/file project-root output-dir "manifest.json")]
    (spit manifest-file (manifest-json {:scope scope :pages pages :errors errors}))
    {:index-path (:index-path index-result)
     :manifest-path (.getPath manifest-file)
     :page-count (count pages)
     :page-paths page-paths}))
