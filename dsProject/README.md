# Temporal Analysis of Art Criticism

This project explores **how the language and thematic focus of arts criticism evolve over time**, using a large historical corpus of OCR-scanned arts reviews.

---

## Objectives

Temporal Analysis: To explore how the language and
focus of criticism may have evolved(e vow d) over time (if date information is
available).

---

## Dataset

- **Source**: Gale arts review archives  
- **Domains**: Art Exhibitions, Books, Concerts, Dance, Operas, Poetry, Theater  
- **Time span**: 18th–21st century  
- **Key challenge**: OCR noise and heterogeneous document formats  

---

## Project Structure



.

├── data/

│   ├── raw/            # Original OCR-scanned texts

│   ├── cleaned/        # Cleaned and normalized texts

│   └── merged_data.csv        # Merged corpus with temporal metadata

│

├── aesthetic/

│   ├── notebook/

│                ├── BERTopic.ipynb            #intermediate files for testing)

│                ├── data_analysis.ipynb            #intermediate files for testing)

│                ├── TemporalAnalysis.ipynb            #final file)

│   ├── src/

│                ├── data_cleaning.py            #data preprocessing

│                ├── data_merging.py            #data preprocessing

│

└── README.md





**For details, please see TemporalAnalysis.ipynb.**

---

## Author

**Xinyu Meng**  

XinyuM1998@gmail.com
MSc Data Science, Uppsala University
