#!/usr/bin/env python3
"""Generate original PT-BR short-form editorial script drafts from approved news.
No third-party footage is downloaded. A human must verify facts and approve copy.
"""
import argparse, json, re
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="Exact source URL in the news queue")
    args=ap.parse_args()
    db=json.loads(Path("data/inreais-delivery-news.json").read_text(encoding="utf-8"))
    item=next((x for x in db.get("items",[]) if x.get("url")==args.url),None)
    if not item: raise SystemExit("URL not found in the current news queue")
    title=item.get("title","")
    source=item.get("source","Fonte a confirmar")
    published=item.get("published_at","Data a confirmar")
    # Editorial template, deliberately not an AI-generated factual assertion.
    safe_title=re.sub(r"\\s+"," ",title).strip()
    slug=re.sub(r"[^a-z0-9]+","-",safe_title.lower()).strip("-")[:55] or "noticia"
    out=Path("drafts")/f"{slug}.md"
    out.parent.mkdir(exist_ok=True)
    body=f"""# Rascunho INREAIS — revisão obrigatória

**Manchete encontrada:** {safe_title}
**Fonte indicada pelo feed:** {source}
**Data indicada:** {published}
**Link:** {args.url}

## Antes de gravar
- [ ] Abrir a fonte original e confirmar que o artigo existe.
- [ ] Confirmar data, país, plataforma e nomes.
- [ ] Encontrar uma segunda fonte independente para alegações importantes.
- [ ] Distinguir factos, acusações, opinião e rumores.
- [ ] Se envolver imigração, não generalizar nem expor dados pessoais.
- [ ] Confirmar autorização/licença antes de usar qualquer vídeo de terceiros.

## Direção editorial aplicada\n- Idioma/voz: português brasileiro (PT-BR), natural e direto.\n- Estilo: viral e provocador, sem sensacionalismo enganoso.\n- Gancho: abrir com consequência concreta, pergunta forte ou contraste — nunca inventar impacto.\n- Responsabilidade: separar fato confirmado, alegação, opinião e ponto ainda não confirmado.\n\n## Guião vertical (máximo 60 segundos; alvo 45–55 segundos)

**Gancho (0–4s):**
"Entregador, presta atenção: isso pode mexer com o seu dinheiro e com o seu trabalho."

**Contexto (4–18s):**
"[Explicar o que aconteceu, onde e quando — preencher apenas após verificação.]"

**O que sabemos (18–35s):**
"[Apresentar os factos confirmados e atribuir cada declaração à respetiva fonte.]"

**O que ainda falta confirmar (35–45s):**
"[Indicar claramente dúvidas, versões em conflito ou informação não confirmada.]"

**Fecho (45–55s):**
"Isso pode afetar quem trabalha com entregas? Conta a tua experiência nos comentários."

## Pacote TikTok
**Título/capa:** {safe_title[:65]}
**Legenda:** "Notícia para quem trabalha com entregas. Contexto, fonte e atualização no vídeo. Informação sujeita a verificação."
**Hashtags:** #Entregadores #Delivery #BrasileirosNoExterior #UberEats #Deliveroo #JustEat

## Pacote YouTube Shorts
**Título:** {safe_title[:85]} | Entregadores
**Descrição:** "Resumo jornalístico em elaboração. Consulte a fonte original: {args.url}"
**Hashtags:** #Shorts #Delivery #Entregadores

## Narração e edição
- Formato: 9:16, 1080x1920, legendas grandes e alto contraste.
- Voz: PT-BR natural; ler apenas o texto final aprovado.
- B-roll: imagens próprias, licenciadas ou autorizadas; não reutilizar cortes sem permissão.
- Música: áudio original ou biblioteca licenciada para uso comercial.
- Não publicar até todas as caixas acima estarem verificadas.
"""
    out.write_text(body,encoding="utf-8")
    print(out)

if __name__=="__main__": main()
