(ns bdocgen.markdown
  (:require [clojure.string :as str])
  (:import (org.commonmark.parser Parser)
           (org.commonmark.renderer.html HtmlRenderer)))

(def ^Parser parser
  (.build (Parser/builder)))

(def ^HtmlRenderer renderer
  (.build (HtmlRenderer/builder)))

(defn- strip-tags
  [html-fragment]
  (-> (or html-fragment "")
      (str/replace #"<[^>]+>" "")
      (str/trim)))

(defn- slugify
  [value]
  (let [normalized (-> value
                       str/lower-case
                       (str/replace #"[^a-z0-9\s-]" "")
                       (str/replace #"\s+" "-")
                       (str/replace #"-+" "-")
                       (str/replace #"^-|-$" ""))]
    (if (str/blank? normalized) "section" normalized)))

(defn- unique-slug
  [slug seen]
  (let [count-so-far (get seen slug 0)]
    (if (zero? count-so-far)
      [slug (assoc seen slug 1)]
      [(str slug "-" count-so-far)
       (assoc seen slug (inc count-so-far))])))

(defn- annotate-headings
  [html]
  (let [pattern #"<h([1-3])>(.*?)</h\1>"
        parts (str/split (or html "") pattern)
        matches (re-seq pattern (or html ""))]
    (loop [result [(first parts)]
           remaining-parts (rest parts)
           remaining-matches matches
           seen {}]
      (if (seq remaining-matches)
        (let [[_ level inner] (first remaining-matches)
              heading-text (strip-tags inner)
              [id next-seen] (unique-slug (slugify heading-text) seen)
              heading (str "<h" level " id=\"" id "\">"
                           inner
                           "<a class=\"heading-citation\" href=\"#" id
                           "\" title=\"Link to this heading\" aria-label=\"Link to this heading\"></a>"
                           "</h" level ">")]
          (recur (conj result heading (first remaining-parts))
                 (rest remaining-parts)
                 (rest remaining-matches)
                 next-seen))
        (apply str result)))))

(defn render-html
  [markdown-text]
  (->> (or markdown-text "")
       (.parse parser)
       (.render renderer)
       annotate-headings))

(defn- basename
  [source-path]
  (-> source-path
      (str/split #"/")
      last
      (str/replace #"\.(md|markdown)$" "")
      (str/replace #"[_-]+" " ")))

(defn- title-case
  [value]
  (->> (str/split value #"\s+")
       (remove str/blank?)
       (map str/capitalize)
       (str/join " ")))

(defn extract-title
  [source-path markdown-text]
  (let [heading (some->> (str/split-lines (or markdown-text ""))
                         (map str/trim)
                         (some (fn [line]
                                 (when (str/starts-with? line "# ")
                                   (subs line 2))))
                         str/trim
                         not-empty)
        fallback (-> source-path basename title-case)]
    (or heading fallback "Untitled")))
