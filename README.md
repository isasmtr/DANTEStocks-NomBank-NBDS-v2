# DANTEStocks NomBank NBDS_V2
O [DANTEStocks-NounBank](https://github.com/psilva-99/DANTEStocks-NomBank-NBDS-) **(DSNB)** [(Silva; Di-Felippo, 2026)]([https://github.com/psilva-99/DANTEStocks-NomBank-NBDS-](https://repositorio.usp.br/item/003317708)) é a versão do corpus [DANTEStocks (Di-Felippo; Roman, 2025)](https://sites.google.com/icmc.usp.br/poetisa/porttinari-3-0) que integra, à anotação gramatical segundo o modelo [Universal Dependencies (UD)](https://universaldependencies.org/) [(Nivre et al., 2020, de Marneffe et al. 2021)](https://aclanthology.org/2020.lrec-1.497/), uma camada de anotação de papéis semânticos especificamente voltada às predicações nominais, inspirada no [NomBank](https://nlp.cs.nyu.edu/meyers/nombank/nombank.1.0/) do inglês [(Meyers, 2004, 2007)](http://nlp.cs.nyu.edu/meyers/papers/nombank-pap.pdf). O recurso é disponibilizado no formato [CoNLL-U Plus](https://universaldependencies.org/ext-format.html), com duas colunas adicionais às previstas no tradicional CoNLL-U para o registro da anotação semântica. Em sua primeira versão, o DSNB contém **1.000 predicações nominais**, distribuídas em 822 dos 4.048 tweets do DANTEStocks, anotadas quanto aos argumentos numerados (ArgN0-ArgN5) e modificadores (ArgM). Para compatibilizar as camadas UD e semântica, o DSNB adotou uma representação baseada em dependências, na qual as relações entre o predicador nominal e seus argumentos são estabelecidas entre os heads das expressões correspondentes. Os rolesets e papéis semânticos empregados na anotação são provenientes do repositório lexical [NounBank.DS](https://bryankhelven.github.io/NounBank.DS/index.html) [(Barbosa; Di Felippo, 2025)](https://sol.sbc.org.br/index.php/stil/article/view/37811/37589)
O **DANTEStocks-NounBank v2 (DSNB-v2)** amplia a cobertura da anotação semântica das predicações nominais, passando a registrar o conjunto total de **1.756 instâncias** de nomes predicadores do **NounBank.DS** (distribuídas em **1.218 tweets distintos**), anotadas quanto aos ArgN e ArgM.
O DSNB-v2 é resultado da pesquisa intitulada "Anotação de papéis semânticos no corpus DANTEStocks: os argumentos modificadores em tweets do mercado financeiro ", desenvolvido por Isabella de Souza Monteiro (UFSCar), no âmbito dos projetos [POeTiSA](https://sites.google.com/icmc.usp.br/poetisa/the-project?authuser=0) e [SaPPO](https://arianidifelippo.lovable.app/projects/sappo).


**Agradecimentos**

Este trabalho foi realizado no Centro de Inteligência Artificial da Universidade de São Paulo (C4AI), com apoio da Fundação de Amparo à Pesquisa do Estado de São Paulo (FAPESP, processo nº 2019/07665-4) e da IBM Corporation. O projeto também contou com o apoio do Ministério da Ciência, Tecnologia e Inovações, com recursos da Lei nº 8.248, de 23 de outubro de 1991, no âmbito do PPI-SOFTEX, coordenado pela Softex e publicado como Residência em TIC 13, DOU 01245.010222/2022-44. Agradecemos, ainda, à FAPESP pelo auxílio financeiro específico a este trabalho, concedido por meio de bolsa de iniciação científica (processo nº 2025/07948-7).


**Como Citar**

MONTEIRO, I. de S.; DI-FELIPPO, A. Anotação de papéis semânticos no corpus DANTEStocks: os argumentos modificadores em tweets do mercado financeiro. Relatório Técnico do ICMC 454. São Carlos: Instituto de Ciências Matemáticas e de Computação, Universidade de São Paulo, 2026. 30p. Disponível em: https://repositorio.usp.br/item/003323555

**Estrutura dos conteúdos deste repositório:**

**Data**

Contém:

* O corpus **DANTEStocks-NounBank v2 (DSNB-v2)** (isto é, com anotação semântica codificada nas duas últimas colunas do formato CoNLL-U Plus: NBDS:ROLESET e NBDS:ARG) dividido em treino, desenvolvimento e teste (arquivos .conllup).

**Financiamento**

Essa pesquisa (FAPESP 2025/07974-8) foi financiada pela Fundação de Amparo à Pesquisa do Estado de São Paulo (FAPESP).

