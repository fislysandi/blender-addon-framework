(ns bdocgen.interop.python)

(defn call-python-adapter
  [{:keys [module function payload]}]
  {:ok false
   :error {:type :not-implemented
           :message "Python adapter boundary is not implemented yet"
           :context {:module module
                     :function function
                     :payload payload}}})
