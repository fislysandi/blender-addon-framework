(ns bdocgen.logging)

(defn log-event
  [event]
  (binding [*out* *err*]
    (prn {:source :bdocgen
          :event event})))

(defn log-error
  [error-map]
  (binding [*out* *err*]
    (prn {:source :bdocgen
          :level :error
          :error error-map})))
