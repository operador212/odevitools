# ODEVI Numbers — MVP backlog e contrato de integração

## Objetivo imediato

Construir a experiência do cliente e a integração sem assumir capacidades telecom não confirmadas. A interface atual é um protótipo navegável, não um catálogo real.

## Estado do protótipo web

- [x] Seleção de país: PT, ES, UK e BR.
- [x] Seleção de números mascarados de demonstração.
- [x] Alternância entre plano semanal e mensal.
- [x] Resumo da seleção e mensagem de simulação.
- [x] Layout responsivo e estados acessíveis.
- [x] Sem checkout, reserva ou compra real.
- [x] Aviso explícito de que os números são fictícios.

## Contrato de backend proposto

Todas as rotas devem exigir sessão autenticada quando expuserem dados pessoais, atribuições, mensagens, chamadas ou saldo. A chave/API do fornecedor permanece exclusivamente no servidor.

### Catálogo público

`GET /numbers/markets`

Retorna apenas mercados que tenham sido habilitados pela equipa de operações, com estado de disponibilidade e aviso de elegibilidade. Um mercado em avaliação não deve aparecer como comprável.

`GET /numbers/catalog?country=PT&capabilities=sms_inbound,voice_inbound`

Retorna inventário real sincronizado com fornecedor e normalizado pela ODEVI. Campos mínimos:
- `number_id` (ID interno opaco, nunca usar o número como chave primária)
- `country`, `number_e164`, `number_type`
- `capabilities` (sms_inbound, sms_outbound, voice_inbound, voice_outbound)
- `requirements` (KYC, endereço/residência, documentos)
- `restrictions` (OTP/short codes, A2P/P2P, emergency calling)
- `setup_fee`, `recurring_price`, `currency`, `billing_period`
- `inventory_checked_at`, `availability_expires_at`

Nunca devolver um número como disponível com base em cache vencida ou em exemplos estáticos.

### Reserva e ativação

`POST /numbers/reservations`

- Requer utilizador autenticado, elegibilidade e KYC aprovado quando aplicável.
- Recebe apenas `number_id`, `plan_id` e uma chave de idempotência.
- Cria uma reserva temporária após confirmação do fornecedor.
- Não ativar serviço antes de autorização comercial e pagamento confirmado.
- Se o fornecedor não suportar reserva, fazer revalidação atómica antes da compra.

`POST /numbers/orders/{order_id}/activate`

- Confirma provisionamento do fornecedor.
- Guarda o identificador externo encriptado/isolado.
- Atualiza estados apenas após resposta verificada ou webhook.
- Nunca assumir sucesso apenas porque o pedido foi enviado.

### Conta do cliente

`GET /me/numbers` — linhas do próprio utilizador, estado e renovação.

`GET /me/wallet` — saldo e moeda; não permite alteração direta.

`GET /me/usage` — utilização faturável reconciliada.

`POST /me/credits/checkout` — cria checkout Stripe em modo de teste até aprovação do piloto.

`POST /me/subscriptions/checkout` — cria checkout de plano semanal/mensal.

### Mensagens e chamadas

`GET /me/numbers/{id}/messages` e `GET /me/numbers/{id}/calls` devem filtrar obrigatoriamente pelo proprietário da linha e aplicar paginação.

Webhooks do fornecedor:
- validar assinatura, timestamp e replay window;
- persistir evento antes de responder 2xx;
- idempotência por ID do fornecedor;
- resolver a linha e proprietário no servidor;
- nunca aceitar user_id fornecido pelo payload como autoridade;
- não escrever conteúdo de SMS, números completos ou tokens em logs comuns.

## Modelo de dados mínimo

- `users`
- `provider_accounts` (segredos fora da base de dados ou encriptados por KMS)
- `provider_number_inventory`
- `number_assignments` (owner_id, number_id, status, assigned_at, released_at)
- `plans` e `plan_prices` (por país e tipo de número)
- `subscriptions`
- `wallets` e `wallet_ledger` (ledger imutável; saldo calculado/reconciliado)
- `usage_records`
- `provider_webhook_events` (idempotência)
- `kyc_cases`
- `audit_events`

## Regras comerciais e de segurança

1. A assinatura paga a atribuição/manutenção do número; os créditos cobrem uso tarifado, quando aplicável.
2. Não vender SMS OTP, short codes ou compatibilidade com Facebook/TikTok/WhatsApp/bancos como garantidos.
3. Não lançar números gratuitos permanentes. Promoção gratuita deve ter duração, limite, custo máximo e regra de expiração claros.
4. Antes de reciclar um número, suspender, notificar, aplicar período de quarentena e garantir que dados do cliente anterior foram removidos.
5. Falha de renovação tem período de tolerância comunicado; nunca libertar um número silenciosamente.
6. Números virtuais não devem ser anunciados como substitutos de SIM ou linha de emergência.
7. Ativar países apenas após autorização contratual de revenda/subatribuição, KYC e análise regulatória.
8. O utilizador deve poder cancelar, exportar dados aplicáveis e pedir eliminação nos limites legais.

## Critérios de aceitação do piloto

- Um número real de teste é provisionado e libertado com sucesso pelo fornecedor.
- SMS inbound/outbound e voz inbound/outbound testados no mesmo SKU quando anunciados.
- Eventos de webhooks duplicados, fora de ordem e inválidos são tratados com segurança.
- Dois utilizadores nunca conseguem ver mensagens, chamadas, saldo ou números um do outro.
- Subscrição, créditos, falhas de pagamento, chargebacks e reembolsos são reconciliados.
- Custos reais por país e margem unitária aprovados antes de abrir vendas.
- Teste de cancelamento, quarentena e reciclagem de número concluído.

## Bloqueios externos

- Resposta escrita dos fornecedores sobre revenda B2C e marca branca.
- Inventário autenticado e cotações por país/tipo de número.
- Parecer sobre telecom, privacidade, KYC, emergência, faturação e consumo.
- Decisão do país-piloto e aprovação dos custos pelo responsável do negócio.

## Estado atual

Protótipo de interface apenas. Nenhum endpoint telecom, conta de fornecedor, inventário real, compra, subscrição, crédito ou fluxo KYC foi ativado.
