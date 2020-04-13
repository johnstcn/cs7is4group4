all : clean group4.pdf #contribution_group4.pdf merged_group4.pdf

clean :
	rm -f *.pdf *.qry *.log *.blg *.bbl *.aux *.bcf *-blx.bib *.run.xml

group4.pdf :
	pdflatex group4
	biber group4
	pdflatex group4
	pdflatex group4

contribution_group4.pdf : 
	pdflatex contribution_group4.tex

merged_group4.pdf:
	pdflatex merged_group4.tex
