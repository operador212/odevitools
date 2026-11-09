# ODEVI Numbers — Due diligence inicial de fornecedores

Data da pesquisa: 9 novembro 2026

## Decisão executiva

Ainda não foi identificado um fornecedor único que esteja publicamente comprovado para fornecer números móveis com SMS e voz no mesmo número, nos quatro mercados (Portugal, Espanha, Reino Unido e Brasil), com autorização contratual explícita para a ODEVI revender/subatribuir esses números a consumidores finais.

**Não ativar checkout, não comprar inventário e não anunciar compatibilidade com Facebook/TikTok até obter respostas contratuais por país e tipo de número.**

## Comparação documental

| Fornecedor | Evidência pública | Lacunas / riscos | Estado |
|---|---|---|---|
| Telnyx | API para pesquisar/comprar números; cobertura anunciada inclui PT, ES, UK e BR; inbound voice em 130+ países. | A página global não prova que cada país oferece o mesmo tipo de número, SMS e voz no mesmo número. Necessário confirmar subatribuição B2C, tipos móveis, KYC por utilizador final, OTP/P2P, chamadas de emergência e preços grossistas. | Primeiro candidato a RFI |
| DIDWW | Publica números móveis com voz e SMS em mercados como Brasil e Reino Unido; API, billing e documentação. Publicou aquisição de números nacionais próprios em Espanha. | A lista pública de Mobile DIDs não demonstra Portugal; números nacionais espanhóis não equivalem a números móveis/SMS. Revenda B2C e inventário PT/ES a confirmar. | Segundo candidato a RFI |
| Twilio | API global de números e gestão programática. | Restrições de revenda/subalocação em países específicos; evidência prévia indicou restrições em Portugal e Espanha. Não selecionar sem aprovação contratual escrita para cada mercado. | Não usar como pressuposto de revenda |
| Vonage | Matriz pública SMS+Voice por país: Brasil com mobile SMS/voice indicado; Portugal e Reino Unido aparecem como mobile sem SMS na tabela consultada. | A2P proibido no Brasil; restrições de revenda/subalocação aplicam-se a vários países e devem ser verificadas individualmente. Não cumpre publicamente os quatro países. | Alternativa parcial |

## Fontes públicas

- Telnyx Global Numbers: https://telnyx.com/products/phone-numbers
- Telnyx International Numbers — documentos: https://support.telnyx.com/en/articles/5469551-international-numbers-required-documents
- Telnyx Global Number Types: https://support.telnyx.com/en/articles/1458084-global-number-types
- Telnyx Requirement Groups (Portugal incluído): https://support.telnyx.com/en/articles/9801714-requirement-groups-for-ordering-phone-numbers
- DIDWW Mobile DIDs: https://www.didww.com/phone-numbers/mobile-numbers
- DIDWW Espanha, números nacionais: https://news.didww.com/2025/03/27/didww-acquires-its-own-national-numbers-in-spain-34/
- DIDWW API e documentação: https://doc.didww.com/index.html
- Vonage SMS + Voice por país: https://api.support.vonage.com/hc/en-us/articles/115011612267-SMS-Voice-Numbers-Features-Overview
- Twilio Phone Numbers: https://www.twilio.com/docs/phone-numbers
- Twilio requisitos regulatórios: https://www.twilio.com/en-us/guidelines/regulatory

## RFI — perguntas obrigatórias aos fornecedores

Solicitar resposta escrita, país por país e SKU/tipo de número por tipo de número:

1. A ODEVI pode atribuir/subalocar cada número a um consumidor final que paga uma subscrição semanal/mensal?
2. É permitido comercializar o serviço dentro de uma aplicação móvel/PWA de marca própria?
3. Quais países têm números móveis reais, e quais apenas geográficos/nacionais/VoIP?
4. Para o mesmo número, há SMS inbound e outbound e chamadas inbound e outbound?
5. SMS P2P é permitido? A2P/OTP/short-code é permitido? Quais plataformas ou categorias são bloqueadas?
6. Existem limitações de Facebook, TikTok, WhatsApp, bancos ou códigos de autenticação?
7. Que KYC e documentos são exigidos à ODEVI e ao utilizador final em cada país?
8. Que regras de endereço local, residência, titularidade, portabilidade e retenção se aplicam?
9. Chamadas de emergência: são suportadas? Como se gere localização, callback e obrigações locais? Não anunciar emergência até validação formal.
10. Qual o custo de ativação, mensalidade grossista, SMS recebido/enviado, minuto de voz, impostos, depósitos e compromisso mínimo?
11. Há limites mínimos de compra, volume, crédito pré-pago ou permanência?
12. Que webhooks/API estão disponíveis para inventário, provisionamento, SMS, chamadas, consumo, suspensão, cancelamento e portabilidade?
13. Qual a política de números reciclados, quarentena e proteção de dados do anterior titular?
14. Qual o SLA, suporte, processo de reclamação e exportação/eliminação de dados?

## Modelo económico a validar

Receita por linha = assinatura semanal/mensal + margem nos créditos de uso.

Custos por linha = número grossista + tráfego SMS/voz + taxas de pagamento + impostos + KYC + suporte + fraude/chargebacks + infraestrutura.

Não publicar preços finais antes de conhecer custos reais por país e calcular margem de contribuição após impostos e suporte. O número gratuito deve ser apenas uma opção promocional controlada, com limite de tempo/uso e aviso de expiração; não prometer números gratuitos permanentes.

## MVP recomendado

1. Começar com um único país e um SKU autorizado para revenda B2C.
2. Catálogo só apresenta números cuja disponibilidade e capacidades foram confirmadas em tempo real.
3. Atribuição exclusiva por utilizador, KYC quando exigido, estado de renovação e ledger de créditos.
4. Caixa de entrada SMS e chamadas apenas após integração de webhook/SIP e testes de isolamento entre contas.
5. Checkout Stripe em modo teste até o fornecedor, a legalidade e a economia unitária estarem aprovados.
6. Política clara de cancelamento, grace period, quarentena antes de reciclar números e exportação/apagamento de dados.
7. Piloto fechado; testar receção real de SMS e chamadas em cada rede e plataforma antes de qualquer promessa de OTP.

## Estado

Esta é uma due diligence documental inicial. Não houve contacto comercial com os fornecedores, acesso a inventário autenticado, cotação vinculativa, parecer jurídico, aquisição de números ou teste de tráfego real.
