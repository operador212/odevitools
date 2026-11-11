# ODEVI+ GTA VI — implementação e automação editorial

## O que foi criado
- Home em dark mode/neon, PT-BR, responsiva e com menu mobile.
- Hero e contador até 19/11/2026, data publicada pela Rockstar; contador usa meia-noite local do visitante.
- Secções Notícias & Rumores, Cortes & Shorts, Catálogo & Guia.
- Área dedicada `assistencia-imigrante.html` com links para ferramentas antigas.
- Feed público em `data/gta-news.json` e `data/gta-shorts.json`.
- A home não inventa vídeos, não republica clipes e não apresenta rumores como factos.

## Fluxo n8n recomendado
1. **Schedule Trigger:** executar a cada 6 horas.
2. **Scout:** RSS oficial Rockstar Newswire e fontes oficiais de plataformas. Reddit `r/GTA6` pode ser usado para descobrir temas, nunca como confirmação única.
3. **Normalize + Deduplicate:** normalizar URL canónica, título, data e hash. Ignorar artigos já publicados.
4. **Source check:** classificar `official`, `rumor` ou `analysis`; guardar fonte e data.
5. **OpenAI:** redigir em PT-BR, título, resumo original, tags e atribuição. Não copiar artigos nem transformar rumor em facto.
6. **Human approval:** obrigatório no piloto. Publicação automática só após período de avaliação e apenas para notícias factuais de fontes oficiais.
7. **GitHub:** atualizar `data/gta-news.json` via GitHub API/Node, usando token armazenado nas credenciais n8n e limitado à branch de conteúdo. Nunca expor token no navegador.
8. **Telegram:** enviar alerta após commit. WhatsApp requer API oficial/provedor e consentimento.
9. **Static site:** o browser faz fetch dos JSON; n8n não precisa editar HTML.

## Contrato de dados — notícias
```json
{"updatedAt":"ISO-8601","items":[{"id":"slug","status":"draft|published","type":"official|rumor|analysis","title":"Título PT-BR","excerpt":"Resumo original","source":"Fonte","date":"YYYY-MM-DD","url":"https://fonte"}]}
```

## Contrato de dados — shorts
```json
{"updatedAt":"ISO-8601","items":[{"id":"slug","status":"published","title":"Título","creator":"Criador","url":"https://original","embedUrl":"https://www.youtube-nocookie.com/embed/ID"}]}
```
Usar vídeos próprios, autorizados ou com incorporação permitida. Não baixar/republicar conteúdo de terceiros sem autorização.

## Credenciais n8n
- OpenAI API key.
- GitHub fine-grained token com Contents: Read/Write apenas no repositório necessário e branch de conteúdo.
- Telegram bot token e chat ID, se usado.
Guardar como credentials/secrets do n8n, nunca em HTML, JSON público ou commits. Configurar limites de custo, retries e logs sem dados pessoais.

## Antes de ativar
- [ ] Definir hospedagem n8n, backups e monitorização.
- [ ] Adicionar feeds RSS oficiais e validar licenças/termos.
- [ ] Configurar credenciais de menor privilégio.
- [ ] Implementar deduplicação, moderação e aprovação humana.
- [ ] Testar feed vazio, fonte fora do ar, duplicados e erros OpenAI/GitHub.
- [ ] Rever direitos de imagem, vídeo, marcas, embeds e SEO.
- [ ] Ativar Cron apenas depois de testes.

## Aviso
ODEVI+ é independente e não afiliado à Rockstar Games. GTA e Grand Theft Auto são marcas dos respetivos titulares. Não apresentar leaks/rumores como comunicados oficiais. Não reproduzir integralmente notícias ou trailers protegidos.
