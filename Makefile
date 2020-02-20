all : clean latex

clean :
	rm -f *.pdf

latex : group4.tex
	pdflatex group4.tex
