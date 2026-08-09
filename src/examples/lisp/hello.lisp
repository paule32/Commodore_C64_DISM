; Windows PE32 / PE32+ Beispiel
(setq counter 3)

(defun square (x)
  (* x x))

(defun main ()
  (println "Hallo vom d64_dism LISP-Compiler")
  (println (square 7))
  (while (> counter 0)
    (println counter)
    (setq counter (- counter 1)))
  (println (if (= counter 0) "fertig" "Fehler")))

(start main)
