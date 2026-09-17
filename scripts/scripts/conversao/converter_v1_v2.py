import argparse
import csv
import os
import re
import sys
from collections import defaultdict

import pandas as pd

COLUNAS_PADRAO = ["ID", "FORM", "LEMMA", "UPOS", "XPOS", "FEATS",
                  "HEAD", "DEPREL", "DEPS", "MISC"]
RE_ARGN = re.compile(r'^(Arg|A)\d+', re.IGNORECASE)
RE_ARGM = re.compile(r'^ArgM-', re.IGNORECASE)
MARCAR_TODOS_DO_SPAN = True

def parse_conllu(caminho):
    with open(caminho, encoding='utf-8') as f:
        linhas = f.read().splitlines()
    sentencas, cabecalho, colunas, sent_atual = [], [], None, None
    for linha in linhas:
        if linha.startswith('# global.columns'):
            colunas = linha.split('=', 1)[1].strip().split()
            cabecalho.append(linha)
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
    return sentencas, colunas, cabecalho

def serializar(sentenca, colunas):
    return ['\t'.join(tok.get(c, '_') for c in colunas) for tok in sentenca['tokens']]

def escrever_v2(caminho, sentencas, colunas, cabecalho):
    with open(caminho, 'w', encoding='utf-8') as f:
        for l in cabecalho:
            f.write(l + '\n')
        for s in sentencas:
            for c in s['comentarios']:
                f.write(c + '\n')
            for l in serializar(s, colunas):
                f.write(l + '\n')
            f.write('\n')

def detectar_coluna_semantica(sentencas, colunas):
    if not colunas:
        return None
    extras = [c for c in colunas if c not in COLUNAS_PADRAO]
    for c in extras:
        for s in sentencas:
            for tok in s['tokens']:
                v = tok.get(c, '_')
                if v != '_' and (RE_ARGM.search(v) or RE_ARGN.search(v)):
                    return c
    for c in extras:
        if 'ARG' in c.upper() and 'ROLESET' not in c.upper():
            return c
    return extras[0] if extras else None

def reconstruir_texto(tokens):
    partes, spans, pos = [], [], 0
    for tok in tokens:
        forma = tok.get('FORM', '_')
        if forma == '_':
            forma = ''
        forma = forma.lower()
        partes.append(forma)
        spans.append((pos, pos + len(forma)))
        pos += len(forma)
        if 'SpaceAfter=No' not in tok.get('MISC', ''):
            partes.append(' ')
            pos += 1
    return ''.join(partes), spans

def normalizar(s):
    if s is None:
        return ''
    return re.sub(r'\s+', ' ', str(s).lower()).strip()

def achar_trecho(tokens, trecho):
    texto, spans = reconstruir_texto(tokens)
    trecho_n = normalizar(trecho)
    if not trecho_n:
        return []
    res, start = [], 0
    while True:
        idx = texto.find(trecho_n, start)
        if idx == -1:
            break
        fim = idx + len(trecho_n)
        toks = [i for i, (a, b) in enumerate(spans) if not (b <= idx or a >= fim)]
        if toks:
            res.append([toks[0], toks[-1]])
        start = idx + 1
    return res

def achar_predicador(tokens, pred):
    p = normalizar(pred)
    if not p:
        return []
    return [i for i, t in enumerate(tokens)
            if normalizar(t.get('FORM', '')) == p or normalizar(t.get('LEMMA', '')) == p]

def achar_sentenca(todas, tweet):
    tweet_n = normalizar(tweet)
    if not tweet_n:
        return []
    res = []
    for arq, s in todas:
        texto, _ = reconstruir_texto(s['tokens'])
        texto_n = normalizar(texto)
        if tweet_n in texto_n or texto_n in tweet_n:
            res.append((arq, s))
    return res

def parse_argm(celula):
    if not celula:
        return '', ''
    if ':' in celula:
        e, t = celula.split(':', 1)
        return e.strip(), t.strip()
    return celula.strip(), celula.strip()

def aplicar_etiqueta(sentenca, span, etiqueta, sem_col, pred_idx):
    conflitos = []
    inicio, fim = span
    for i in range(inicio, fim + 1):
        tok = sentenca['tokens'][i]
        atual = tok.get(sem_col, '_')
        if i in pred_idx:
            conflitos.append((i, atual, 'token é o predicador'))
            continue
        if atual != '_' and RE_ARGN.search(atual):
            conflitos.append((i, atual, 'token já é ArgN'))
            continue
        if MARCAR_TODOS_DO_SPAN:
            tok[sem_col] = etiqueta
        elif i == inicio:
            tok[sem_col] = etiqueta
    return conflitos

def registrar(rel, tipo, arq, tweet, pred, argm, ud, v1, v2, det=''):
    rel.append({'tipo': tipo, 'arquivo': arq, 'tweet': tweet, 'predicador': pred,
                'argm': argm, 'etiqueta_ud': ud, 'v1': v1, 'v2': v2, 'detalhe': det})

def processar_planilha(df, todas, colunas, sem_col, rel):
    cont = defaultdict(int)
    for _, linha in df.iterrows():
        pred = str(linha.get('predicador', '')).strip()
        tweet = str(linha.get('tweet', '')).strip()
        argm_cel = str(linha.get('argm', '')).strip()
        ud = str(linha.get('etiqueta_ud', '')).strip()
        etiqueta, trecho = parse_argm(argm_cel)

        if not pred:
            registrar(rel, 'SEM_PREDICADOR', '', tweet, pred, argm_cel, ud, '', '', 'Predicador vazio')
            cont['SEM_PREDICADOR'] += 1
            continue

        achados = achar_sentenca(todas, tweet)
        if not achados:
            registrar(rel, 'NAO_ENCONTRADO', '', tweet, pred, argm_cel, ud, '', '', 'Tweet não encontrado')
            cont['NAO_ENCONTRADO'] += 1
            continue
        if len(achados) > 1:
            registrar(rel, 'AMBIGUO', '', tweet, pred, argm_cel, ud, '', '',
                      f'Tweet casa com {len(achados)} sentenças')
            cont['AMBIGUO'] += 1
            continue

        arq, sentenca = achados[0]
        pred_idx = achar_predicador(sentenca['tokens'], pred)
        if not pred_idx:
            registrar(rel, 'NAO_ENCONTRADO', arq, tweet, pred, argm_cel, ud, '', '',
                      'Predicador não encontrado')
            cont['NAO_ENCONTRADO'] += 1
            continue
        if len(pred_idx) > 1:
            registrar(rel, 'AMBIGUO', arq, tweet, pred, argm_cel, ud, '', '',
                      f'Predicador {pred} aparece {len(pred_idx)}x')
            cont['AMBIGUO'] += 1
            continue

        spans = achar_trecho(sentenca['tokens'], trecho)
        if not spans:
            registrar(rel, 'NAO_ENCONTRADO', arq, tweet, pred, argm_cel, ud, '', '',
                      f'Trecho "{trecho}" não encontrado')
            cont['NAO_ENCONTRADO'] += 1
            continue
        if len(spans) > 1:
            registrar(rel, 'AMBIGUO', arq, tweet, pred, argm_cel, ud, '', '',
                      f'Trecho "{trecho}" aparece {len(spans)}x')
            cont['AMBIGUO'] += 1
            continue

        span = spans[0]
        atual = sentenca['tokens'][span[0]].get(sem_col, '_')

        if atual == etiqueta:
            registrar(rel, 'MANTIDO', arq, tweet, pred, argm_cel, ud, atual, etiqueta, 'Já correto')
            cont['MANTIDO'] += 1
        elif atual == '_':
            confl = aplicar_etiqueta(sentenca, span, etiqueta, sem_col, pred_idx)
            if confl:
                for i, v, m in confl:
                    registrar(rel, 'CONFLITO', arq, tweet, pred, argm_cel, ud, v, etiqueta,
                              f'Token {i+1}: {m}')
                    cont['CONFLITO'] += 1
            else:
                registrar(rel, 'ADICIONADO', arq, tweet, pred, argm_cel, ud, '_', etiqueta, 'Novo ArgM')
                cont['ADICIONADO'] += 1
        elif RE_ARGN.search(atual):
            registrar(rel, 'CONFLITO', arq, tweet, pred, argm_cel, ud, atual, etiqueta,
                      'Token já é ArgN')
            cont['CONFLITO'] += 1
        else:
            confl = aplicar_etiqueta(sentenca, span, etiqueta, sem_col, pred_idx)
            if confl:
                for i, v, m in confl:
                    registrar(rel, 'CONFLITO', arq, tweet, pred, argm_cel, ud, v, etiqueta,
                              f'Token {i+1}: {m}')
                    cont['CONFLITO'] += 1
            else:
                registrar(rel, 'CORRIGIDO', arq, tweet, pred, argm_cel, ud, atual, etiqueta,
                          'Etiqueta alterada')
                cont['CORRIGIDO'] += 1
    return cont

def detectar_remocoes(todas, df, sem_col, rel, auto_remover):
    trechos_planilha = set()
    for _, l in df.iterrows():
        _, trecho = parse_argm(str(l.get('argm', '')))
        if trecho:
            trechos_planilha.add(normalizar(trecho))

    cand = []
    for arq, s in todas:
        for i, tok in enumerate(s['tokens']):
            v = tok.get(sem_col, '_')
            if v == '_' or not RE_ARGM.search(v):
                continue
            forma = normalizar(tok.get('FORM', ''))
            if forma and not any(forma in t for t in trechos_planilha):
                cand.append((arq, s, i, v))

    if auto_remover:
        for arq, s, i, v in cand:
            s['tokens'][i][sem_col] = '_'
            registrar(rel, 'REMOVIDO', arq, '', '', '', '', v, '_', 'Remoção automática')
    else:
        for arq, s, i, v in cand:
            registrar(rel, 'CANDIDATO_REMOCAO', arq, '', '', '', '', v, '_', 'Revisar manualmente')
    return len(cand)

def validar_argn_argm(todas, colunas, sem_col):
    conflitos = []
    extras = [c for c in colunas if c not in COLUNAS_PADRAO] if colunas else [sem_col]
    for arq, s in todas:
        for i, tok in enumerate(s['tokens']):
            for c in extras:
                v = tok.get(c, '_')
                if v == '_':
                    continue
                if RE_ARGN.search(v) and RE_ARGM.search(v):
                    conflitos.append((arq, s, i, c, v))
    return conflitos

def validar_preservacao(v1, v2, colunas, sem_col):
    problemas = []
    for s1, s2 in zip(v1, v2):
        if len(s1['tokens']) != len(s2['tokens']):
            problemas.append(('N_TOKENS', s1, s2, '', '', ''))
            continue
        for t1, t2 in zip(s1['tokens'], s2['tokens']):
            for c in colunas:
                if c == sem_col:
                    continue
                if t1.get(c) != t2.get(c):
                    problemas.append((c, s1, t1, t2, t1.get(c), t2.get(c)))
    return problemas

def escrever_relatorio(rel, cont, conflitos, problemas, csv_path, resumo_path):
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        campos = ['tipo', 'arquivo', 'tweet', 'predicador', 'argm',
                  'etiqueta_ud', 'v1', 'v2', 'detalhe']
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for r in rel:
            w.writerow(r)

    with open(resumo_path, 'w', encoding='utf-8') as f:
        f.write("RESUMO V2\n" + "=" * 40 + "\n")
        for k, v in sorted(cont.items()):
            f.write(f"{k}: {v}\n")
        f.write("\nVALIDAÇÃO ArgN x ArgM\n" + "=" * 40 + "\n")
        if conflitos:
            f.write(f"ERRO/CONFLITO: {len(conflitos)}. V2 NÃO validada.\n")
            for arq, s, i, c, v in conflitos:
                f.write(f"  {arq} | Tweet {s['comentarios']} | Token {i+1} "
                        f"({s['tokens'][i].get('FORM')}) | {c} | {v}\n")
        else:
            f.write("Nenhum conflito ArgN x ArgM. OK.\n")
        f.write("\nPRESERVAÇÃO V1 x V2\n" + "=" * 40 + "\n")
        if problemas:
            f.write(f"{len(problemas)} diferença(s) fora da coluna semântica. REVISAR.\n")
            for c, s1, t1, t2, v1, v2 in problemas[:50]:
                f.write(f"  {c}: V1='{v1}' -> V2='{v2}'\n")
        else:
            f.write("Nenhuma alteração fora da coluna semântica. OK.\n")

def ler_planilha(caminho):
    if caminho.lower().endswith(('.xlsx', '.xls')):
        df_raw = pd.read_excel(caminho, header=None)
    else:
        df_raw = pd.read_csv(caminho, header=None)

    header_row = 0
    for i in range(min(5, len(df_raw))):
        linha = [str(x).strip().lower() for x in df_raw.iloc[i].tolist()]
        if any('predicador' in x for x in linha):
            header_row = i
            break

    if caminho.lower().endswith(('.xlsx', '.xls')):
        df = pd.read_excel(caminho, header=header_row)
    else:
        df = pd.read_csv(caminho, header=header_row)

    df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
    return df

def main():
    parser = argparse.ArgumentParser(
        description="Converte CoNLL-U Plus DANTES original -> atualizado (V2)."
    )
    parser.add_argument('--originais', default='./V1',
                        help='Pasta com os .conllu originais (padrão: ./V1)')
    parser.add_argument('--correcoes', required=True,
                        help='Caminho da planilha de correções (.xlsx/.csv)')
    parser.add_argument('--saida', default='./V2',
                        help='Pasta de saída dos V2 (padrão: ./V2)')
    parser.add_argument('--logs', default='./logs',
                        help='Pasta dos relatórios (padrão: ./logs)')
    parser.add_argument('--auto-remover', action='store_true',
                        help='Remove automaticamente os candidatos a remoção')
    args = parser.parse_args()

    if not os.path.isdir(args.originais):
        print(f"ERRO: pasta de originais não encontrada: {args.originais}")
        sys.exit(1)
    conllu = sorted(f for f in os.listdir(args.originais)
                    if f.lower().endswith(('.conllu', '.conlluplus', '.conll')))
    if not conllu:
        print(f"ERRO: nenhum arquivo .conllu encontrado em {args.originais}")
        sys.exit(1)

    if not os.path.exists(args.correcoes):
        print(f"ERRO: planilha de correções não encontrada: {args.correcoes}")
        sys.exit(1)
    df = ler_planilha(args.correcoes)
    print(f"Planilha: {len(df)} linhas | Colunas: {list(df.columns)}")

    sentencas_por_arq, colunas, cab_por_arq, todas = {}, None, {}, []
    for n in conllu:
        s, col, cab = parse_conllu(os.path.join(args.originais, n))
        sentencas_por_arq[n] = s
        colunas = col
        cab_por_arq[n] = cab
        for x in s:
            todas.append((n, x))

    sem_col = detectar_coluna_semantica([s for _, s in todas], colunas)
    if sem_col is None:
        print("ERRO: não foi possível detectar a coluna semântica.")
        sys.exit(1)
    print(f"Colunas: {colunas}")
    print(f"Coluna semântica: {sem_col}")
    print(f"Sentenças: {len(todas)}")

    rel = []
    cont = processar_planilha(df, todas, colunas, sem_col, rel)
    cont['CANDIDATOS_REMOCAO'] = detectar_remocoes(todas, df, sem_col, rel, args.auto_remover)

    os.makedirs(args.saida, exist_ok=True)
    for n in conllu:
        escrever_v2(os.path.join(args.saida, n), sentencas_por_arq[n], colunas, cab_por_arq[n])
    print(f"\nV2 gerada em '{args.saida}/' ({len(conllu)} arquivo(s)).")

    conflitos = validar_argn_argm(todas, colunas, sem_col)
    problemas = []
    for n in conllu:
        v1, _, _ = parse_conllu(os.path.join(args.originais, n))
        v2, _, _ = parse_conllu(os.path.join(args.saida, n))
        problemas += validar_preservacao(v1, v2, colunas, sem_col)

    os.makedirs(args.logs, exist_ok=True)
    escrever_relatorio(rel, cont, conflitos, problemas,
                       os.path.join(args.logs, 'alteracoes_v2.csv'),
                       os.path.join(args.logs, 'resumo_v2.txt'))

    print("\n" + "=" * 50)
    for k, v in sorted(cont.items()):
        print(f"  {k}: {v}")
    print("-" * 50)
    if conflitos:
        print(f"  ERRO/CONFLITO ArgN x ArgM: {len(conflitos)}. V2 NÃO validada.")
    else:
        print("  Validação ArgN x ArgM: OK.")
    if problemas:
        print(f"  {len(problemas)} diferença(s) fora da coluna semântica. Ver relatório.")
    else:
        print("  Preservação V1 x V2: OK.")
    print("=" * 50)
    print(f"Relatório: {args.logs}/alteracoes_v2.csv")
    print(f"Resumo   : {args.logs}/resumo_v2.txt")

if __name__ == '__main__':
    main()
