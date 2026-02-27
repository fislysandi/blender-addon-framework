(ns bdocgen.pages
  (:require [bdocgen.discovery :as discovery]
            [clojure.string :as str]))

(defn- strip-markdown-extension
  [path]
  (str/replace path #"\.(md|markdown)$" ""))

(defn- matching-root
  [roots source-path]
  (let [sorted-roots (->> roots
                    (sort-by count >))]
    (some (fn [root]
            (when (or (= source-path root)
                      (str/starts-with? source-path (str root "/")))
              root))
          sorted-roots)))

(defn- path-relative-to-root
  [source-path root]
  (if (and root (str/starts-with? source-path (str root "/")))
    (subs source-path (inc (count root)))
    source-path))

(defn- route-prefix
  [scope root]
  (case scope
    :project (if (= root "bdocgen/docs") "bdocgen" "")
    ""))

(defn- normalize-route-base
  [route-base]
  (cond
    (= route-base "index") ""
    (str/ends-with? route-base "/index") (subs route-base 0 (- (count route-base) 6))
    :else route-base))

(defn- page-output-path
  [route-base]
  (if (str/blank? route-base)
    "index.html"
    (str route-base "/index.html")))

(defn- page-url
  [route-base]
  (if (str/blank? route-base)
    "/"
    (str "/" route-base "/")))

(defn source-path->page
  [scope roots source-path]
  (let [normalized (discovery/normalize-path source-path)
        root (matching-root roots normalized)
        route-root (route-prefix scope root)
        relative-no-ext (-> normalized
                            (path-relative-to-root root)
                            strip-markdown-extension)
        joined-route (str/join "/" (remove str/blank? [route-root relative-no-ext]))
        route-base (normalize-route-base joined-route)]
    {:source-path normalized
     :route-base route-base
     :output-path (page-output-path route-base)
     :url (page-url route-base)}))

(defn build-page-specs
  [scope roots source-paths]
  (->> source-paths
       (map (fn [path] (source-path->page scope roots path)))
       vec))
