# ODEVI Numbers — piloto Portugal

**Atualizado:** 9 novembro 2026  
**Estado:** validação documental; não aprovado para venda nem provisionamento.

## Decisão de trabalho

Portugal é o primeiro mercado-piloto. O fornecedor com melhor evidência pública de adequação funcional encontrada até agora é a **Zadarma**, mas apenas como candidato para prova técnica e negociação comercial. Não está aprovado como fornecedor de produção.

Não comprar números nem abrir pagamentos antes de obter confirmação escrita de que a Zadarma aceita o modelo de marca branca/revenda B2C da ODEVI e de resolver a elegibilidade regulatória portuguesa.

## Descoberta principal: Zadarma

A página oficial do produto Zadarma apresenta um número móvel português +351 9 com:
- chamadas recebidas pela aplicação/softphone;
- SMS recebidos;
- SMS recebidos sem custo adicional;
- ativação de SMS apenas ao prolongar o número por um mínimo de 3 meses;
- necessidade de documento de identificação e endereço atual em Portugal;
- atribuição aleatória: a página informa que atualmente não é possível escolher o número português;
- preço público apresentado de €9 para a ligação do número (sem IVA), com custo mensal/renovação a confirmar no checkout e na proposta comercial.

Fonte: https://zadarma.com/pt/tariffs/numbers/portugal/mobile/

A FAQ oficial informa:
- receção de SMS só em números móveis;
- documento de identificação exigido;
- máximo de 10 números virtuais com SMS por conta;
- não garante SMS de serviços de terceiros ou de números de outros países;
- número deve estar ligado por pelo menos 3 meses para ativar SMS.

Fonte: https://zadarma.com/pt/support/faq/sms/how-to-receive-sms/

### API e revenda — sinal positivo, mas não é aprovação contratual

A API oficial Zadarma documenta:
- consulta de números disponíveis: `GET /v1/direct_numbers/available/{DIRECTION_ID}/`;
- compra/ordem de número: `POST /v1/direct_numbers/order/`;
- ativação de SMS: `PUT /v1/direct_numbers/receive_sms/`;
- prolongamento de número: `POST /v1/direct_numbers/prolong/`;
- parâmetro `user_id` nos métodos de encomenda/prolongamento, explicitamente disponível para parceiros ou utilizadores criados por estes;
- registo de utilizadores de revendedor e gestão de saldo por API;
- documentação sobre telefonia white-label.

Fonte: https://zadarma.com/pt/support/api/

Isto mostra que existe uma infraestrutura API de parceiros. Não demonstra, por si só, que:
1. o programa de parceiro permite atribuir números móveis portugueses a clientes finais da ODEVI;
2. os clientes podem ser utilizadores individuais de uma app de consumo;
3. a Zadarma permite que a ODEVI cobre a sua própria assinatura e créditos;
4. o limite público de 10 números com SMS pode ser ultrapassado num contrato de parceiro;
5. a API permite selecionar números portugueses específicos, apesar de a página pública dizer que a seleção não está atualmente disponível;
6. é permitido usar os números para OTP/2FA de Facebook, TikTok, bancos ou outros serviços.

## Comparação dos fornecedores para Portugal

| Fornecedor | Evidência para Portugal | Avaliação |
|---|---|---|
| Zadarma | Número móvel +351 9, chamadas recebidas e SMS recebidos; API com recursos de parceiro. | Melhor candidato funcional; depende de autorização de revenda B2C, limite de escala, seleção de número e preço grossista. |
| DIDWW | Página pública de Portugal lista +351 (30) e +351 (707), com chamadas recebidas, mas SMS não suportados. A lista de Mobile DIDs publicada não inclui Portugal. | Não cumpre o requisito principal de número móvel + SMS em Portugal segundo a evidência pública atual. |
| Telnyx | Requisitos publicados para números locais portugueses exigem uso empresarial e proíbem uso privado. Os nacionais têm documentação pessoal/empresarial, mas não foi provado SMS móvel + voz no mesmo SKU nem revenda B2C. | Não selecionar sem confirmação de produto e aprovação escrita. |

Fontes:
- Zadarma Portugal mobile: https://zadarma.com/pt/tariffs/numbers/portugal/mobile/
- Zadarma API: https://zadarma.com/pt/support/api/
- DIDWW Portugal: https://www.didww.com/phone-numbers/all-phone-numbers/Portugal/National
- DIDWW mobile coverage: https://www.didww.com/phone-numbers/mobile-numbers
- Telnyx Portugal requirements: https://support-v2.telnyx.com/en/articles/5466980-portugal-did-requirements

## Enquadramento ANACOM — bloqueio a resolver antes de comercializar

A ANACOM esclarece que as empresas que pretendem oferecer serviços de comunicações eletrónicas acessíveis ao público em Portugal devem comunicar previamente o início da atividade. A página oficial classifica, entre outros, serviços de voz com base em números fixos, móveis e nómadas, e serviços de SMS/MMS com base em números.

Fonte: https://digital.anacom.pt/pt-PT/Servicos/Comunica%C3%A7%C3%B5es-Eletr%C3%B3nicas/inicio-atividade/

O Regulamento n.º 1028/2021 regula a subatribuição de números E.164 e foi posteriormente alterado, incluindo pelo Regulamento n.º 38/2025. O modelo prevê contrato entre titular e beneficiário e comunicação à ANACOM pelo titular e pelo beneficiário antes da subatribuição. O beneficiário só pode fazer atribuição secundária aos utilizadores finais da sua própria oferta retalhista; não pode voltar a subatribuir a outras empresas. O regime aplica-se às gamas nele indicadas, incluindo números móveis 91, 92, 93 e 96, números fixos, nómadas e algumas gamas não geográficas.

Fontes:
- ANACOM — Regulamento e atualizações: https://www.anacom.pt/render.jsp?contentId=1713169
- Diário da República: https://diariodarepublica.pt/dr/detalhe/regulamento/1028-2021-176724098
- ANACOM — início da atividade: https://digital.anacom.pt/pt-PT/Servicos/Comunica%C3%A7%C3%B5es-Eletr%C3%B3nicas/inicio-atividade/

**Ação jurídica necessária:** pedir confirmação à ANACOM/advogado especializado sobre a classificação exata da oferta ODEVI, a comunicação de início de atividade, o papel da ODEVI como beneficiário/operador retalhista, elegibilidade da gama +351 9 e o contrato de subatribuição. Não presumir que o fornecedor faz automaticamente a comunicação regulatória pela ODEVI.

## RFI — email para Zadarma (não enviado)

**Subject:** Portugal mobile numbers — API reseller / white-label consumer service partnership

Hello Zadarma Partnerships Team,

We are evaluating Zadarma as the telecom infrastructure provider for ODEVI Numbers, a mobile application for customers who need a dedicated Portuguese phone number managed inside our app.

We found your Portugal +351 9 mobile number product and your API documentation, including reseller user management and the direct-number order/prolongation methods.

Before any purchase or integration, could you please confirm in writing:

1. Can ODEVI operate as an authorised reseller/white-label partner and assign one Portuguese mobile number to each individual consumer account?
2. Does the partner agreement explicitly permit B2C resale/sub-allocation of Portuguese mobile numbers to our own end users?
3. Can each end user be provisioned as a Zadarma reseller sub-user via API, with the Portuguese number attached to that user?
4. Can the ODEVI platform select a specific available +351 9 number? Your public page currently says Portugal numbers are assigned randomly. Is number selection available through the partner API or at higher volume?
5. Is the 10-number limit for SMS-enabled numbers per account also applicable to reseller accounts/sub-users? Can it be raised contractually?
6. Can the same Portuguese mobile number receive PSTN calls and inbound SMS, and can the user make outbound calls from the ODEVI app using that caller ID?
7. Is outbound SMS from the Portuguese mobile number supported? If so, what are the restrictions and wholesale rates?
8. What are the activation, monthly/quarterly number rental, SMS, inbound/outbound call, and API costs? Is there a minimum monthly commitment or prepaid balance?
9. Is the 3-month minimum prepayment for SMS activation mandatory for reseller accounts?
10. What end-user KYC, Portuguese address/residency, business documentation, and data retention requirements apply?
11. Are SMS verification messages from third-party platforms permitted? Please specify any restrictions for OTP, 2FA, short codes, Facebook, TikTok, WhatsApp and financial services. We will not advertise guaranteed OTP compatibility.
12. Can inbound SMS and call events be delivered to our backend through signed webhooks, and can calls be handled through SIP/WebRTC in a white-label mobile app?
13. What is the number quarantine/recycling policy after cancellation, and can a customer port the number out?
14. Can you provide a draft partner agreement and a written confirmation of the permitted Portuguese numbering range and resale model?

We intend to start with a small closed pilot and scale only after regulatory and technical validation.

Kind regards,  
ODEVI Numbers Team

## RFI — questões para a ANACOM (não enviado)

Solicitar orientação formal, descrevendo a operação real e pedindo resposta sobre:
- se a ODEVI, enquanto entidade que comercializa a aplicação e atribui números aos seus próprios clientes finais, deve comunicar início de atividade ao abrigo do regime de autorização geral;
- se a estrutura de subatribuição do Regulamento n.º 1028/2021 é aplicável quando o fornecedor grossista é titular dos direitos de utilização e a ODEVI recebe números para atribuição secundária a clientes finais;
- que requisitos de comunicação, contrato, gamas móveis e responsabilidades se aplicam;
- como se aplicam portabilidade, reclamações, emergência, identificação de assinantes e proteção de dados ao serviço proposto.

## Plano de piloto proposto

### Fase A — validação comercial e regulatória (sem custo de inventário)
- Enviar RFI à Zadarma.
- Pedir proposta de parceiro e minuta contratual.
- Pedir confirmação escrita da permissão B2C e limite de números.
- Consultar ANACOM/assessor jurídico sobre comunicação de início de atividade e subatribuição.
- Não pedir credenciais API nem comprar número antes destas respostas.

### Fase B — prova técnica controlada (só após aprovação)
- Uma conta/parceiro de teste e 1 número de teste.
- Verificar chamadas recebidas e efetuadas, SMS recebidos, caller ID e entrega de webhooks.
- Testar um SMS normal de pessoa para pessoa e mensagens de serviços terceiros apenas com autorização do fornecedor.
- Medir latência, falhas, reconexão, custos e comportamento em cancelamento.
- Não depender de OTP para o caso de uso principal.

### Fase C — MVP comercial
- Só depois de contrato, obrigações regulatórias e custos validados.
- Catálogo real via API; nunca números inventados.
- Provisionamento idempotente, KYC, assinatura e ledger de créditos.
- Limite de utilizadores compatível com o inventário contratado.
- Aviso claro sobre serviços terceiros que podem bloquear números VoIP.

## Go / No-Go

**GO condicional para continuar a negociação com Zadarma.**  
**NO-GO para compras, revenda, checkout e promessa de números escolhíveis enquanto não existir resposta escrita.**

Critérios mínimos para aprovar:
- autorização B2C/white-label e subatribuição;
- pelo menos 20–50 números no piloto ou um limite suficiente acordado;
- API de seleção/provisionamento utilizável;
- custos grossistas que permitam margem positiva;
- SMS e voz na mesma linha com testes reais;
- requisitos ANACOM cumpridos;
- política de número e dados adequada à continuidade e privacidade do cliente.
