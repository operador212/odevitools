# ODEVI+ — Reestruturação da plataforma

## Visão do produto

ODEVI+ passa a ser uma plataforma mobile-first para apoiar pessoas que vivem, trabalham ou se deslocam entre países, com dois pilares:

1. **ODEVI Assist** — ferramentas e orientação para imigração, documentos, emprego/CV, finanças, impostos e serviços úteis.
2. **ODEVI Numbers** — serviço premium de números telefónicos internacionais, com SMS e voz quando a operadora e a regulamentação local o permitirem.

O produto deve manter as ferramentas atuais durante a transição. Não remover nem quebrar downloader, CV, conversor, Tax Assistant, guias ou páginas legais.

## ODEVI Numbers: promessa e limites

A experiência deve parecer uma linha telefónica pessoal gerida no telemóvel, e não um serviço de SMS descartável. O cliente poderá pesquisar números, consultar capacidades, adquirir, renovar, gerir saldo/plano e utilizar uma caixa de entrada de SMS e interface de chamadas.

**Não prometer equivalência universal a um SIM móvel.** Um número virtual pode não oferecer dados móveis, roaming, chamadas de emergência, portabilidade, receção de OTP/short codes ou compatibilidade com determinados bancos e plataformas. A disponibilidade de SMS e voz varia por país, tipo de número, operador e requisitos regulatórios.

Cada número anunciado deve mostrar capacidades verificadas individualmente:
- Receber SMS / enviar SMS (se permitido)
- Receber chamadas / efetuar chamadas
- Tipo do número (móvel, geográfico, nacional, etc.)
- Requisitos de identidade/residência e documentos
- Compatibilidade conhecida com short codes/OTP, sem prometer aceitação por terceiros
- Preço de ativação, preço semanal/mensal, renovação, tarifas de uso e limites
- Política de retenção, cancelamento e eventual perda/reciclagem do número

## Monetização

Suportar dois modelos, escolhidos por país e tipo de número:
- **Planos recorrentes**: semanal ou mensal, com renovação e cancelamento claros.
- **Créditos pré-pagos**: saldo para utilização tarifada (SMS/chamadas), com preço por evento apresentado antes da utilização.

A subscrição do número e os créditos de utilização são conceitos separados. Não lançar preços fictícios: catálogo e preços devem vir do fornecedor e de regras comerciais configuráveis. Pagamentos só depois de confirmação explícita de custos, taxas, impostos e modelo de cobrança. Stripe pode ser usado para checkout/assinaturas quando o fluxo de telecom estiver validado; não ativar cobranças reais durante desenvolvimento.

## Arquitetura proposta

- **Web app/PWA primeiro**: instalar no ecrã inicial de iOS/Android, navegação mobile-first, manifest, ícones, service worker e experiência autenticada. PWA não substitui uma app nativa em todas as funções; validar chamadas/áudio e notificações em dispositivos reais.
- **Aplicação nativa depois**: avaliar Capacitor ou React Native quando o produto e a API estiverem estáveis, reutilizando backend e design system.
- **Backend ODEVI**: API própria para contas, catálogo, encomendas, subscrições, créditos, webhooks, mensagens, chamadas e auditoria.
- **Adaptador de fornecedor**: começar com uma interface independente do fornecedor. Telnyx e Twilio são candidatos para avaliação; não assumir que a cobertura é igual em todos os países.
- **Persistência**: base de dados PostgreSQL para utilizadores, números atribuídos, estado de subscrição, ledger de créditos, consentimentos, mensagens/metadados, eventos e auditoria.
- **Segurança**: autenticação forte, segregação por utilizador, segredos só no servidor, proteção contra abuso/spam/fraude, limites de utilização, rate limiting, validação de webhooks e políticas de retenção/eliminações.
- **Privacidade**: mensagens e registos de chamadas são dados sensíveis; minimizar conteúdo armazenado, encriptar dados, definir retenção curta e fornecer eliminação/exportação quando aplicável.

## Regras de compliance e segurança

Antes de vender números em cada país, confirmar com o fornecedor e assessoria especializada:
- autorização/licença e modelo de revenda ou subalocação;
- requisitos locais de KYC, endereço, residência e documentos;
- regras de identificação do chamador, chamadas de emergência e localização;
- regras de SMS A2P/P2P, short codes, consentimento e prevenção de spam;
- GDPR/UK GDPR, transferências internacionais, retenção e direitos dos titulares;
- impostos, faturação, renovação automática, reembolsos e cancelamento.

Não permitir contas anónimas para abuso, fraude, bypass de autenticação, criação em massa de contas ou receção de códigos de terceiros com finalidade ilícita. Publicar política de uso aceitável e processo de resposta a abuso.

## Estrutura de navegação proposta

- Início
- ODEVI Numbers (produto em destaque)
- ODEVI Assist
  - Documentos e IA
  - Imigração e residência
  - Trabalho e CV
  - Finanças e impostos
  - Guias por país
  - Ferramentas gratuitas
- Preços
- Como funciona
- Ajuda / FAQ
- Conta / painel

## Fases de implementação

### Fase 0 — Descoberta e prova comercial
- Confirmar acesso e condições comerciais de 2 fornecedores.
- Comparar inventário real por país, capacidades SMS+voz no mesmo número, KYC, preços e restrições.
- Selecionar um país-piloto e um tipo de número.
- Definir margem, preço final, cancelamento e suporte.
- Não assumir que "número móvel" ou "número premium" é sinónimo de SMS+voz; verificar cada SKU.

### Fase 1 — Fundamentos de produto
- Design system e navegação responsiva comum.
- Landing page nova com ODEVI Numbers em destaque.
- PWA instalável com manifesto, ícones, offline fallback e rotas principais.
- Manter todas as páginas e ferramentas atuais acessíveis.
- Painel autenticado inicial e estados de produto ainda não disponível.

### Fase 2 — Integração telecom em sandbox
- Adaptador de fornecedor e sincronização de catálogo.
- Pesquisa de números disponíveis com capacidades verificadas.
- Provisionamento em sandbox/teste, webhooks assinados e eventos.
- Caixa de entrada SMS e registo de chamadas de teste.
- Testes de ciclo de vida: comprar, ativar, renovar, suspender, cancelar e libertar.

### Fase 3 — Pagamentos e lançamento limitado
- Stripe em modo de teste; checkout, subscrição, créditos e ledger idempotente.
- Reconciliação de custos e uso com o fornecedor.
- KYC e regras de país implementados.
- Piloto fechado; sem venda pública até passar testes legais, segurança e telecom.

### Fase 4 — Aplicações nativas e expansão
- Decidir Capacitor/React Native com base nas necessidades de chamadas, notificações e áudio.
- Publicar nas lojas após políticas e revisão.
- Expandir países somente após certificação do fornecedor e testes locais.

## Critérios de aceitação do primeiro lançamento

- Cliente vê apenas números realmente disponíveis para o seu país/eligibilidade.
- Capacidades e todos os custos são exibidos antes do pagamento.
- Nenhum número é ativado sem confirmação do fornecedor e pagamento válido.
- Webhooks e pagamentos são idempotentes.
- SMS e chamadas recebidas são entregues à conta correta, sem cruzamento entre utilizadores.
- Cancelamento, renovação, falhas de pagamento e expiração têm estados claros.
- Limites de abuso, auditoria, retenção e eliminação foram testados.
- Site atual continua funcional e não perde ferramentas existentes.
- PWA instala e funciona em iOS e Android; limitações documentadas.

## Decisões ainda em aberto

- Países-piloto: sugeridos Portugal e Reino Unido, sujeitos a inventário e elegibilidade reais.
- Fornecedor principal e fornecedor de contingência.
- Planos semanal/mensal e pacotes de créditos.
- Marca visual final e idioma padrão.
- PWA inicial versus app nativa após validação.
- Política de suporte, reembolsos e números perdidos por falha de renovação.

## Estado

Documento de produto e arquitetura. Ainda não é uma implementação de telecomunicações, não compra números, não cria cobranças e não autoriza deploy de produção.
