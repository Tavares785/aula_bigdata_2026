# Regras da camada silver — MercadoFácil

O CSV bruto é preservado integralmente no prefixo raw. A unidade é um item de pedido. A saída silver contém itens válidos em Parquet; a quarentena contém registros rejeitados com o motivo, sem identificadores pessoais diretos.

- Espaços e marcadores de ausência: trim e conversão de vazio, null, none, n/a, nan e na para nulo.
- Identificadores: padronização em maiúsculas; pedido ou item ausente vai para quarentena.
- Códigos e categorias: UF/SKU em maiúsculas, categorias, canais e status em minúsculas com espaços normalizados; UF fora da lista brasileira vai para quarentena.
- Datas: conversão explícita dos formatos ISO, brasileiro e ano/mês/dia; data de pedido inválida vai para quarentena; datas opcionais inválidas tornam-se nulas.
- Valores: normalização dos separadores decimais e conversão para decimal; preço e valor total ausentes, inválidos ou negativos e quantidade não positiva ou não inteira vão para quarentena.
- Logística: prazos negativos vão para quarentena; atraso é recalculado com os dois prazos disponíveis e fica nulo quando não é mensurável. Não confundir prazo desconhecido com entrega pontual.
- Avaliações: notas fora de 1 a 5 vão para quarentena; ausência não é substituída por nota artificial.
- Duplicidade: chave pedido/item; cópias idênticas ficam na quarentena, preservando uma em silver. Chaves com payload divergente são integralmente encaminhadas à quarentena.
- Atributos categóricos ausentes: categoria, canal e status recebem desconhecido na silver; não imputar valores de negócio.
- LGPD: nome, e-mail, CPF, identificador do cliente e comentário livre não chegam à silver ou quarentena. O raw permanece privado. Identificadores operacionais de pedido e item são mantidos para conciliação, não expostos na gold.
- Conciliação: linhas raw = silver + quarentena, sem descarte silencioso. A execução falha se não houver linhas válidas.

Gold: atrasos por UF, com denominador de pedidos com prazo conhecido e média de avaliação; agregação comercial por mês e categoria, separando valor bruto do valor sem status explícito de cancelamento/devolução. Não constitui receita contábil líquida. Pedidos com UF divergente podem aparecer em mais de uma UF; pedidos com várias categorias podem aparecer em mais de uma categoria.

## Perfil observado

A contagem real de ausências e chaves repetidas está em `evidencias/perfil-raw.txt`. As regras acima também cobrem validações preventivas, mesmo quando não houver ocorrências.
