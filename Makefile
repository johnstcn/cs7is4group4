all : clean group4 contributions

clean :
	rm -f *.pdf *.qry *.log *.blg *.bbl *.aux *.bcf *-blx.bib *.run.xml

group4 : group4.tex
	pdflatex group4
	biber group4
	pdflatex group4
	pdflatex group4

contributions : contribution_aishwarya contribution_cian contribution_george contribution_sameer contribution_shravani

contribution_aishwarya:
	pdflatex contribution_aishwarya.tex

contribution_cian:
	pdflatex contribution_cian.tex

contribution_george:
	pdflatex contribution_george.tex

contribution_sameer:
	pdflatex contribution_sameer.tex

contribution_shravani:
	pdflatex contribution_shravani.tex
