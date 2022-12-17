#!/usr/bin/env python

import os
import sys

if len(sys.argv)!=2:
	print(f"Usage: {sys.argv[0]} [pdf_previewer]")

pdf_previewer=sys.argv[1]

preamble="""# generated by ./scripts/gen-makefile.py
ifndef optimize
	optimize=yes
endif

ifndef pdfpreviewer
	pdfpreviewer={default_previewer}
endif

OBJ_DIR=./obj
OUT_DIR=./out

LATEX=latexmk -pdf -quiet
LATEX_WATCH=latexmk -pvc -pdf -e '$$pdf_previewer=q[$(pdfpreviewer)];'

ifeq ($(optimize), yes)
	SIZEOPT=pdfsizeopt --do-require-image-optimizers=no --quiet
else
	SIZEOPT=cp
endif

default: all

.PHONY: clean
clean:
	rm -rf obj out

.PHONY: reload
reload:
	python ./scripts/gen-makefile.py "{default_previewer}"
""".format(default_previewer=pdf_previewer)

texfile_target="""
$(OUT_DIR)/{0}/{1}.pdf: ./src/{0}/{1}.tex
	@echo "\\e[32m--- Building {0}-{1} ---\\e[0m"
	$(LATEX) -outdir=$(OBJ_DIR)/{0}/{1} ./src/{0}/{1}.tex
	mkdir -p $(OUT_DIR)/{0}
	$(SIZEOPT) $(OBJ_DIR)/{0}/{1}/{1}.pdf $(OUT_DIR)/{0}/{1}.pdf

.PHONY: {0}-{1}-watch
{0}-{1}-watch:
	$(LATEX_WATCH) -outdir=$(OBJ_DIR)/{0}/{1} ./src/{0}/{1}.tex
"""

subject_all_target="""
{subject}-all: {ticket_list} $(OUT_DIR)/{subject}/book.pdf
"""

book_target="""
$(OUT_DIR)/{subject}/book.pdf: src/book.tex $(OBJ_DIR)/{subject}/book-list.tex
	@echo "\\e[32m--- Building {subject}-book ---\\e[0m"
	cp $(OBJ_DIR)/{subject}/book-list.tex $(OBJ_DIR)/book-list.tex
	$(LATEX) -outdir=$(OBJ_DIR)/{subject}/book ./src/book.tex
	mkdir -p $(OUT_DIR)/{subject}
	$(SIZEOPT) $(OBJ_DIR)/{subject}/book/book.pdf $(OUT_DIR)/{subject}/book.pdf
	rm -rf $(OBJ_DIR)/book-list.tex

.PHONY: {subject}-book-watch
{subject}-book-watch: $(OBJ_DIR)/{subject}/book-list.tex
	cp $(OBJ_DIR)/{subject}/book-list.tex $(OBJ_DIR)/book-list.tex
	$(LATEX_WATCH) -outdir=$(OBJ_DIR)/{subject}/book ./src/book.tex
	rm -rf $(OBJ_DIR)/book-list.tex

$(OBJ_DIR)/{subject}/book-list.tex: {ticket_list}
	mkdir -p $(OBJ_DIR)/{subject}
	python ./scripts/gen-book-list.py {subject} $(OBJ_DIR)/{subject}/book-list.tex
"""

subject_target=subject_all_target+book_target

all_all="""
all: {0}
"""

texfiles = {"analysis":[], "geometry":[], "algebra":[]}

for subject in texfiles.keys():
    for file in os.listdir(os.path.join("./src", subject)):
        ticket_number=file[:-4]
        if ticket_number.isnumeric():
            texfiles[subject].append(int(ticket_number))
    texfiles[subject].sort()

makefile=""

#  print(texfiles)

#  defining variables
makefile += preamble

#  file targets 
for subject in texfiles.keys():
    for file in texfiles[subject]:
        makefile += texfile_target.format(subject, file)

# subject targets
for subject in texfiles.keys():
    makefile +=subject_target.format(subject=subject, ticket_list=" ".join(map(lambda ticket:f"$(OUT_DIR)/{subject}/{ticket}.pdf",texfiles[subject])))

makefile += all_all.format(" ".join(map(lambda subject: f"{subject}-all", texfiles.keys())))

makefile_file = open("Makefile", "w")
makefile_file.write(makefile)
makefile_file.close()
