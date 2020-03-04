all : clean latex

clean :
	rm -f *.pdf *.qry *.log *.blg *.bbl *.aux *.bcf *-blx.bib *.run.xml

latex : group4.tex
	pdflatex group4
	biber group4
	pdflatex group4
	pdflatex group4
