!pip install -q pandas openpyxl

import os, re
import pandas as pd

COLUNAS_PADRAO = ["ID", "FORM", "LEMMA", "UPOS", "XPOS", "FEATS",
                  "HEAD", "DEPREL", "DEPS", "MISC"]

def normalizar_etiqueta(v):
    if v is None or v == '_' or str(v).strip() == '':
        return v
    partes = str(v).split('|')
    novos = []
    for p in partes:
        p = p.strip()
        sufixo = ''
        if ':' in p:
            p, sufixo = p.split(':', 1)
            sufixo = ':' + sufixo
        if p.lower().startswith('argm-'):
            p = 'ARGM-' + p[5:].upper()
        novos.append(p + sufixo)
    return '|'.join(novos)

def normalizar_etiqueta_planilha(v):
    if ':' in v:
        etiqueta, texto = v.split(':', 1)
        return normalizar_etiqueta(etiqueta.strip()) + ':' + texto
    return normalizar_etiqueta(v)

def parse_conllu(caminho):
    with open(caminho, encoding='utf-8') as f:
        linhas = f.read().splitlines()
    sentencas, colunas, sent_atual = [], None, None
    for linha in linhas:
        if linha.startswith('# global.columns'):
            colunas = linha.split('=', 1)[1].strip().split()
        elif linha.startswith('#'):
            if sent_atual is None:
                sent_atual = {'comentarios': [], 'tokens': []}
            sent_atual['comentarios'].append(linha)
        elif linha.strip() == '':
            if sent_atual is not None:
                sentencas.append(sent_atual)
                sent_atual = None
        else:
            if sent_atual is None:
                sent_atual = {'comentarios': [], 'tokens': []}
            campos = linha.split('\t')
            if colunas is None:
                colunas = COLUNAS_PADRAO + [f'EXTRA{i}' for i in range(len(campos) - len(COLUNAS_PADRAO))]
            tok = {}
            for i, n in enumerate(colunas):
                tok[n] = campos[i] if i < len(campos) else '_'
            sent_atual['tokens'].append(tok)
    if sent_atual is not None:
        sentencas.append(sent_atual)
    return sentencas, colunas

def detectar_semantica(sentencas, colunas):
    extras = [c for c in colunas if c not in COLUNAS_PADRAO] if colunas else []
    for c in extras:
        for s in sentencas:
            for t in s['tokens']:
                v = t.get(c, '_')
                if v != '_' and (v.lower().startswith('argm') or re.match(r'^arg\d', v, re.I)):
                    return c
    for c in extras:
        if 'ARG' in c.upper() and 'ROLESET' not in c.upper():
            return c
    return extras[0] if extras else None

def serializar(sentenca, colunas):
    return ['\t'.join(tok.get(c, '_') for c in colunas) for tok in sentenca['tokens']]

def escrever_conllu(caminho, sentencas, colunas):
    with open(caminho, 'w', encoding='utf-8') as f:
        for s in sentencas:
            for c in s['comentarios']:
                f.write(c + '\n')
            for l in serializar(s, colunas):
                f.write(l + '\n')
            f.write('\n')

import os

# Verifica se as pastas existem
if not os.path.isdir(PASTA_V1):
    print(f"ERRO: pasta V1 não encontrada: {PASTA_V1}")
    raise SystemExit
if not os.path.isdir(PASTA_V2):
    print(f"ERRO: pasta V2 não encontrada: {PASTA_V2}")
    raise SystemExit

# Lista os arquivos de cada pasta
v1_arquivos = sorted(f for f in os.listdir(PASTA_V1) if f.lower().endswith(('.conllu', '.conll')))
v2_arquivos = sorted(f for f in os.listdir(PASTA_V2) if f.lower().endswith(('.conllu', '.conll')))

print("Arquivos em V1:")
for f in v1_arquivos:
    print(f"  - {f}")
print("Arquivos em V2:")
for f in v2_arquivos:
    print(f"  - {f}")

if not v1_arquivos:
    print("ERRO: nenhum arquivo .conllu em V1.")
    raise SystemExit
if not v2_arquivos:
    print("ERRO: nenhum arquivo .conllu em V2.")
    raise SystemExit

def contar_semantica(sentencas, sem_col):
    """Conta apenas os MODIFICADORES (ArgM-*), ignorando argumentos (arg0, arg1...)."""
    cont = Counter()
    for s in sentencas:
        for t in s['tokens']:
            v = t.get(sem_col, '_')
            if v == '_':
                continue
            # Pega só a parte antes do ':' e do '|' para classificar
            primeira = v.split('|')[0].split(':')[0]
            if primeira.lower().startswith('argm'):
                cont[v] += 1
    return cont

def parse_conllu(caminho):
    with open(caminho, encoding='utf-8') as f:
        linhas = f.read().splitlines()
    sentencas, colunas, sent_atual = [], None, None
    for linha in linhas:
        if linha.startswith('# global.columns'):
            colunas = linha.split('=', 1)[1].strip().split()
        elif linha.startswith('#'):
            if sent_atual is None:
                sent_atual = {'comentarios': [], 'tokens': []}
            sent_atual['comentarios'].append(linha)
        elif linha.strip() == '':
            if sent_atual is not None:
                sentencas.append(sent_atual)
                sent_atual = None
        else:
            if sent_atual is None:
                sent_atual = {'comentarios': [], 'tokens': []}
            campos = linha.split('\t')
            if colunas is None:
                colunas = COLUNAS_PADRAO + [f'EXTRA{i}' for i in range(len(campos) - len(COLUNAS_PADRAO))]
            tok = {}
            for i, n in enumerate(colunas):
                tok[n] = campos[i] if i < len(campos) else '_'
            sent_atual['tokens'].append(tok)
    if sent_atual is not None:
        sentencas.append(sent_atual)
    return sentencas, colunas

def detectar_semantica(sentencas, colunas):
    extras = [c for c in colunas if c not in COLUNAS_PADRAO] if colunas else []
    for c in extras:
        for s in sentencas:
            for t in s['tokens']:
                v = t.get(c, '_')
                if v != '_' and (v.startswith('ArgM') or (v[:3].lower() in ('arg', 'a') and v[3:4].isdigit())):
                    return c
    for c in extras:
        if 'ARG' in c.upper() and 'ROLESET' not in c.upper():
            return c
    return extras[0] if extras else None

def comparar(v1, v2, sem_col):
    mudancas = []
    for s1, s2 in zip(v1, v2):
        if len(s1['tokens']) != len(s2['tokens']):
            mudancas.append(('N_TOKENS', s1, s2, '', '', ''))
            continue
        for t1, t2 in zip(s1['tokens'], s2['tokens']):
            for c in s1['tokens'][0].keys():
                if c == sem_col:
                    continue
                if t1.get(c) != t2.get(c):
                    mudancas.append((c, s1, t1, t2, t1.get(c), t2.get(c)))
    return mudancas

def contar_semantica(sentencas, sem_col):
    cont = Counter()
    for s in sentencas:
        for t in s['tokens']:
            v = t.get(sem_col, '_')
            if v != '_':
                cont[v] += 1
    return cont

os.makedirs(PASTA_SAIDA, exist_ok=True)
rel = []
rel.append("RELATÓRIO DA PADRONIZAÇÃO DE CAIXA (argm- -> ARGM-)")
rel.append("=" * 50)

# --- 1) CoNLL-U ---
arquivos = sorted(f for f in os.listdir(PASTA_ENTRADA) if f.lower().endswith(('.conllu', '.conll')))
total_conllu = 0
for nome in arquivos:
    sentencas, colunas = parse_conllu(os.path.join(PASTA_ENTRADA, nome))
    sem = detectar_semantica(sentencas, colunas)
    if sem is None:
        rel.append(f"\n[{nome}] coluna semântica não detectada. Ignorado.")
        continue
    mudou = 0
    for s in sentencas:
        for t in s['tokens']:
            v = t.get(sem, '_')
            novo = normalizar_etiqueta(v)
            if novo != v:
                t[sem] = novo
                mudou += 1
    escrever_conllu(os.path.join(PASTA_SAIDA, nome), sentencas, colunas)
    total_conllu += mudou
    rel.append(f"\n[{nome}] {mudou} etiqueta(s) corrigida(s) na coluna {sem}")

# --- 2) Planilha ---
total_pl = 0
if PLANILHA and os.path.exists(PLANILHA):
    df_raw = pd.read_excel(PLANILHA, header=None)
    header_row = 0
    for i in range(min(5, len(df_raw))):
        linha = [str(x).strip().lower() for x in df_raw.iloc[i].tolist()]
        if any('argm' in x or 'arg' in x for x in linha):
            header_row = i
            break
    df = pd.read_excel(PLANILHA, header=header_row)
    df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
    col_argm = next((c for c in df.columns if 'argm' in c), None)
    if col_argm:
        mudou = 0
        for i, v in df[col_argm].items():
            if pd.isna(v):
                continue
            novo = normalizar_etiqueta_planilha(str(v))
            if novo != str(v):
                df.at[i, col_argm] = novo
                mudou += 1
        df.to_excel(os.path.join(PASTA_SAIDA, "correcoes_padronizada.xlsx"), index=False)
        total_pl = mudou
        rel.append(f"\nPlanilha: {mudou} célula(s) corrigida(s) na coluna {col_argm}")
    else:
        rel.append("\nPlanilha: coluna argM não encontrada.")

rel.append("\n" + "=" * 50)
rel.append(f"TOTAL corrigido: {total_conllu} no CoNLL-U + {total_pl} na planilha")

# --- 3) Salva e mostra o relatório ---
caminho_rel = os.path.join(PASTA_SAIDA, "relatorio_padronizacao.txt")
with open(caminho_rel, 'w', encoding='utf-8') as f:
    f.write("\n".join(rel) + "\n")
print("\n".join(rel))
print(f"\nRelatório salvo em: {caminho_rel}")

# --- 4) Baixa tudo ---
for nome in os.listdir(PASTA_SAIDA):
    files.download(os.path.join(PASTA_SAIDA, nome))

import re

def nome_base(nome):
    """Extrai o nome base do arquivo (ex.: DANTESdev) ignorando sufixos."""
    # Remove extensão
    base = re.sub(r'\.conllu.*$', '', nome, flags=re.IGNORECASE)
    # Remove sufixos de versão/atualização
    base = re.sub(r'_ATUALIZADO.*$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'_CORRIGIDO.*$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'_V2.*$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'\(.*?\)', '', base)          # remove "(conllu plus)"
    base = re.sub(r'\s+', '', base)              # remove espaços
    return base.strip()

# Verifica as pastas
if not os.path.isdir(PASTA_V1):
    print(f"ERRO: pasta V1 não encontrada: {PASTA_V1}")
    raise SystemExit
if not os.path.isdir(PASTA_V2):
    print(f"ERRO: pasta V2 não encontrada: {PASTA_V2}")
    raise SystemExit

# Lista os arquivos de cada pasta
v1_arquivos = sorted(f for f in os.listdir(PASTA_V1) if f.lower().endswith(('.conllu', '.conll')))
v2_arquivos = sorted(f for f in os.listdir(PASTA_V2) if f.lower().endswith(('.conllu', '.conll')))

if not v1_arquivos:
    print("ERRO: nenhum arquivo .conllu em V1.")
    raise SystemExit
if not v2_arquivos:
    print("ERRO: nenhum arquivo .conllu em V2.")
    raise SystemExit

# Cria um mapa: nome_base -> caminho do arquivo V2
mapa_v2 = {nome_base(n): os.path.join(PASTA_V2, n) for n in v2_arquivos}

os.makedirs(PASTA_SAIDA, exist_ok=True)
caminho_rel = os.path.join(PASTA_SAIDA, 'relatorio_v2.txt')
linhas = []
linhas.append("RELATÓRIO DA ATUALIZAÇÃO V1 -> V2")
linhas.append("=" * 50)

total_mudancas = 0
pareados = 0
for nome in v1_arquivos:
    p1 = os.path.join(PASTA_V1, nome)
    base = nome_base(nome)
    p2 = mapa_v2.get(base)

    if p2 is None:
        linhas.append(f"\n[{nome}] SEM V2 correspondente (base '{base}' não achada em V2).")
        linhas.append(f"    V2 disponíveis: {[nome_base(n) for n in v2_arquivos]}")
        continue

    v1, col1 = parse_conllu(p1)
    v2, col2 = parse_conllu(p2)
    sem = detectar_semantica(v1, col1)
    mudancas = comparar(v1, v2, sem)
    total_mudancas += len(mudancas)
    pareados += 1

    linhas.append(f"\n--- {nome}  <->  {os.path.basename(p2)} ---")
    linhas.append(f"  Sentenças V1: {len(v1)} | V2: {len(v2)}")
    linhas.append(f"  Coluna semântica: {sem}")
    linhas.append(f"  Diferenças fora da coluna semântica: {len(mudancas)}")
    if mudancas:
        for c, s1, t1, t2, a, b in mudancas[:20]:
            linhas.append(f"    {c}: V1='{a}' -> V2='{b}'")
        if len(mudancas) > 20:
            linhas.append(f"    ... e mais {len(mudancas) - 20}.")
    else:
        linhas.append("    OK: nenhuma alteração fora da coluna semântica.")

    linhas.append(f"  Distribuição ArgM/ArgN na V2:")
    for k, v in sorted(contar_semantica(v2, sem).items()):
        linhas.append(f"    {k}: {v}")

linhas.append("\n" + "=" * 50)
linhas.append(f"Arquivos pareados: {pareados}/{len(v1_arquivos)}")
linhas.append(f"TOTAL de diferenças fora da coluna semântica: {total_mudancas}")
if total_mudancas == 0:
    linhas.append("RESULTADO: V2 preserva integralmente a V1 fora da coluna semântica. OK.")

with open(caminho_rel, 'w', encoding='utf-8') as f:
    f.write("\n".join(linhas) + "\n")

print("\n".join(linhas))
print(f"\nRelatório salvo em: {caminho_rel}")

from collections import Counter
import re

def nome_base(nome):
    """Extrai o nome base (ex.: DANTESdev) ignorando sufixos e extensão."""
    base = re.sub(r'\.conllu.*$', '', nome, flags=re.IGNORECASE)
    base = re.sub(r'_ATUALIZADO.*$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'_CORRIGIDO.*$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'_V2.*$', '', base, flags=re.IGNORECASE)
    base = re.sub(r'\(.*?\)', '', base)   # remove "(conllu plus)"
    base = re.sub(r'\s+', '', base)       # remove espaços
    return base.strip()

def partes_modificadores(valor):
    """Extrai os tipos ArgM de uma célula NBDS:ARG.
    Ex.: 'argm-adv:3|ARGM-ADV:7' -> ['ADV', 'ADV'] | 'arg1:3' -> []
    """
    tipos = []
    if not valor or valor == '_':
        return tipos
    for parte in str(valor).split('|'):
        p = parte.strip()
        if not p:
            continue
        nome = p.split(':')[0]      # remove o índice do token
        if nome.lower().startswith('argm-'):
            tipos.append(nome[5:].upper())  # ex.: TMP, ADV, LOC, NEG
    return tipos

# --- Lista os arquivos de cada pasta ---
v1_arquivos = sorted(f for f in os.listdir(PASTA_V1) if f.lower().endswith(('.conllu', '.conll')))
v2_arquivos = sorted(f for f in os.listdir(PASTA_V2) if f.lower().endswith(('.conllu', '.conll')))

# --- Mapa: nome_base -> caminho do V2 ---
mapa_v2 = {nome_base(n): os.path.join(PASTA_V2, n) for n in v2_arquivos}

linhas = []
linhas.append("RELATÓRIO V1 -> V2 — SOMENTE MODIFICADORES (ArgM-*)")
linhas.append("=" * 56)

pareados = 0
for nome in v1_arquivos:
    p1 = os.path.join(PASTA_V1, nome)
    base = nome_base(nome)
    p2 = mapa_v2.get(base)

    if p2 is None:
        linhas.append(f"[{nome}] SEM V2 correspondente (base '{base}').")
        continue

    v1, col1 = parse_conllu(p1)
    v2, col2 = parse_conllu(p2)
    sem = detectar_semantica(v1, col1)
    mudancas = comparar(v1, v2, sem)
    pareados += 1

    c1, c2 = Counter(), Counter()
    for s in v1:
        for t in s['tokens']:
            for tp in partes_modificadores(t.get(sem, '_')):
                c1[tp] += 1
    for s in v2:
        for t in s['tokens']:
            for tp in partes_modificadores(t.get(sem, '_')):
                c2[tp] += 1

    linhas.append(f"\n--- {nome} <-> {os.path.basename(p2)} ---")
    linhas.append(f"  Sentenças V1: {len(v1)} | V2: {len(v2)}")
    linhas.append(f"  Modificadores V1: {sum(c1.values())} | V2: {sum(c2.values())}")
    linhas.append(f"  Diferenças fora da coluna semântica: {len(mudancas)}")

    tipos_ord = sorted(set(c1) | set(c2))
    if not tipos_ord:
        linhas.append("  Nenhum modificador ArgM encontrado.")
        continue
    linhas.append("  Tipos de modificador (V1 -> V2):")
    for tp in tipos_ord:
        linhas.append(f"    ARGM-{tp:<6} {c1.get(tp, 0):>4} -> {c2.get(tp, 0):>4}")

linhas.append("\n" + "=" * 56)
linhas.append(f"Arquivos pareados: {pareados}/{len(v1_arquivos)}")

caminho_mod = os.path.join(PASTA_SAIDA, 'relatorio_modificadores.txt')
with open(caminho_mod, 'w', encoding='utf-8') as f:
    f.write("\n".join(linhas) + "\n")

print("\n".join(linhas))
print(f"\nRelatório salvo em: {caminho_mod}")
