all : clean group4 contributions

clean :
	rm -f *.pdf *.qry *.log *.blg *.bbl *.aux *.bcf *-blx.bib *.run.xml

group4 : group4.tex
	pdflatex group4
	biber group4
	pdflatex group4
	pdflatex group4

contributions : 
	pdflatex contribution_group4.tex
