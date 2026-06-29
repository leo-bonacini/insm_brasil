# O Brasil que preserva e o Brasil que desmatou: uma história contada pelos dados

> "Quais municípios brasileiros conseguem conciliar desenvolvimento econômico, preservação ambiental e qualidade de vida de forma mais eficiente?"

Essa pergunta parece simples. A resposta exigiu cruzar mais de **2,3 milhões de registros** de uso do solo, dados econômicos de todos os 5.572 municípios brasileiros e décadas de monitoramento por satélite. O resultado é o **INSM** (Índice Nacional de Sustentabilidade Municipal), construído inteiramente com dados públicos e métodos científicos reproduzíveis.

---

## O que é o INSM

O INSM não é uma nota escolar. É um termômetro de equilíbrio.

Ele mede o quanto cada município consegue, ao mesmo tempo, preservar o que ainda tem de natureza, usar o solo com responsabilidade e gerar riqueza sem destruir o ambiente que sustenta essa riqueza.

O índice varia de **0 a 100**. Quanto maior, mais sustentável. Mas o que entra nessa conta?

| Indicador | Peso | Leitura |
|-----------|------|---------|
| Cobertura florestal (MapBiomas) | 18,9% | Mais floresta: melhor |
| Vegetação nativa total (MapBiomas) | 19,2% | Mais natureza: melhor |
| Área agropecuária (MapBiomas) | 20,4% | Mais pasto e lavoura: pior |
| Pressão ambiental combinada | 12,0% | Mais pressão: pior |
| Área urbana (MapBiomas) | 9,9% | Mais urbanização: pior |
| Densidade demográfica | 9,4% | Mais densa: pior |
| Variação da vegetação nativa (2015,2021) | 8,9% | Ganhou verde: melhor |
| PIB per capita | 1,2% | Mais riqueza: melhor |

Os pesos **não foram definidos por julgamento humano**. Eles emergem de dois métodos estatísticos aplicados em sequência: PCA (Análise de Componentes Principais, que captura a estrutura latente dos dados) e o Entropy Weight Method (que dá mais peso aos indicadores com maior variação informativa entre municípios). O resultado final é a média dos dois, normalizada para somar 100%.

---

## De onde vêm os dados

Tudo público. Tudo verificável. Tudo com licença de uso aberto.

**MapBiomas Coleção 9** é a espinha dorsal ambiental do projeto. São 39 anos de imagens de satélite classificadas pixel a pixel para todo o Brasil, de 1985 a 2023. Para cada município, sabemos exatamente quantos hectares são floresta, pastagem, lavoura de soja, área urbana, mineração, manguezal. São **2.322.780 registros** processados neste projeto.

**IBGE** forneceu o esqueleto econômico e demográfico: PIB municipal de 2018 a 2021, estimativas populacionais, produção agrícola (PAM) e pecuária (PPM) via API SIDRA, e o shapefile com os limites precisos dos 5.572 municípios brasileiros.

**INPE** monitora o desmatamento via PRODES e os focos de calor via Programa Queimadas. Ambos são alimentados por satélites operando há décadas.

---

## O que os dados revelam

### O Brasil de cima é diferente do Brasil de baixo

A primeira grande surpresa do INSM é geográfica. Os estados mais sustentáveis do país não são os mais ricos.

| Estado | INSM médio |
|--------|-----------|
| Amazonas (AM) | 93,7 |
| Amapá (AP) | 88,9 |
| Piauí (PI) | 84,5 |
| Roraima (RR) | 84,4 |
| Ceará (CE) | 76,2 |

O Amazonas lidera com folga. A razão é direta: 93% do estado ainda é coberto por floresta nativa. A pressão agropecuária é baixa. A densidade populacional é das menores do Brasil. O índice de pressão ambiental é mínimo.

São Paulo, o estado mais rico, ocupa a 25ª posição entre 27, com INSM médio de apenas 35,5. A equação é inversa: muita lavoura, muita área urbana, pouca vegetação remanescente.

Por região:

| Região | INSM médio |
|--------|-----------|
| Norte | 66,1 |
| Nordeste | 59,3 |
| Sul | 46,4 |
| Centro-Oeste | 44,4 |
| Sudeste | 40,5 |

O Norte preserva mais porque ainda tem o que preservar. O Sudeste industrializou, urbanizou e desmatou há décadas. Isso não é julgamento: é história registrada em imagem de satélite.

---

### O município número 1

**Serra do Navio (AP)** ocupa o topo absoluto com INSM 100.

Uma cidade de pouco mais de 5.000 habitantes no coração do Amapá. Vegetação nativa cobrindo praticamente toda a extensão territorial. Sem pressão agropecuária relevante. A economia local é modesta, o que o índice captura no componente de PIB per capita, mas a sustentabilidade ambiental compensa com folga em todos os outros critérios.

**Guaramiranga (CE)**, segunda colocada com 99,9, conta uma história diferente. É um município serrano na Chapada do Apodi, com 97% de cobertura de vegetação nativa preservada. É pequeno, pouco denso e economicamente humilde. Mas verde. Muito verde.

**Atalaia do Norte (AM)**, terceira colocada, faz fronteira com o Peru. Abriga parte do Vale do Javari, a maior reserva indígena do mundo em extensão. Floresta densa, pressão ambiental próxima de zero.

---

### O outro extremo

**Lajedão (BA)** fecha o ranking com INSM 0.

Município baiano com cobertura nativa inferior a 2%, área quase inteiramente tomada por pastagem e lavoura, e acelerada perda de vegetação entre 2015 e 2021. Não é o único nessa situação.

**545 municípios** têm menos de 10% de cobertura nativa. **550 municípios** pontuam abaixo de 25 no INSM. São municípios que, pela métrica ambiental, estão em estado crítico de degradação.

Os outros municípios no fundo do ranking incluem municípios do Espírito Santo, São Paulo, Minas Gerais e Bahia. O padrão é consistente: alta proporção de área agropecuária, baixa vegetação remanescente, alto índice de pressão.

---

### PIB e sustentabilidade: a correlação que surpreende

A correlação entre PIB per capita e INSM é de apenas **-0,12**.

Isso significa praticamente nenhuma relação linear. Municípios ricos não são necessariamente mais sustentáveis. Na verdade, a leve correlação negativa sugere o contrário: municípios mais ricos tendem a ter scores ligeiramente menores, provavelmente porque riqueza aqui costuma vir acompanhada de urbanização e uso intensivo do solo.

A correlação que domina é com vegetação nativa: **+0,97**.

É quase uma lei: onde há floresta, há sustentabilidade. Onde a floresta sumiu, o INSM despencou. A expansão agropecuária tem correlação de **-0,90** com o INSM.

**534 municípios** têm mais de 80% de cobertura nativa. São os municípios que ainda guardam o Brasil original.

---

### 39 anos registrados em pixel

O Brasil de 2021 não é o mesmo de 1985. Os satélites registraram tudo.

Em 1985, o Brasil tinha **657,3 milhões de hectares** de vegetação nativa. Em 2021, esse número havia caído para **558,2 milhões**. A diferença: **99 milhões de hectares perdidos** em 36 anos.

Para ter escala: 99 milhões de hectares equivalem a uma área maior que a Venezuela. É como se um país inteiro tivesse sido convertido em pasto e lavoura ao longo de três décadas e meia.

Do outro lado da balança, a área agropecuária quase dobrou:

| Ano | Vegetação nativa | Área agropecuária |
|-----|-----------------|-------------------|
| 1985 | 657,3 M ha | 110,6 M ha |
| 2000 | 603,6 M ha | 185,7 M ha |
| 2010 | 577,4 M ha | 209,7 M ha |
| 2021 | 558,2 M ha | 221,9 M ha |

Cada hectare ganho pelo agronegócio nesse período corresponde, em média, a um hectare perdido de vegetação nativa. O Código Florestal revisado em 2012 e o fortalecimento do monitoramento por satélite desaceleraram o processo nas décadas seguintes, mas não o reverteram.

Esses dados estão na fundação do INSM. Quando um município aparece com nota baixa, é porque décadas de imagens mostram com exatidão o que aconteceu com o território.

---

### O que a inteligência artificial aprendeu

Cinco algoritmos de machine learning foram treinados para prever o INSM a partir dos indicadores brutos.

O vencedor foi o **LightGBM**, com validação cruzada de 5 folds:

| Modelo | R² (CV) | RMSE (CV) |
|--------|---------|-----------|
| LightGBM | 0,999 | 0,687 |
| XGBoost | 0,999 | 0,775 |
| Gradient Boosting | 0,998 | 0,853 |
| Random Forest | 0,998 | 0,908 |
| ElasticNet | 0,969 | 3,765 |

R² de 0,999 indica que o modelo explica 99,9% da variação do índice a partir dos indicadores de entrada. Isso não é overfitting: é reflexo de que o INSM é uma combinação determinística de seus componentes, e os modelos de árvore capturaram essa estrutura com precisão.

A análise SHAP confirma o que a correlação já indicava: **cobertura florestal** e **vegetação nativa** são os fatores com maior impacto individual na nota final.

---

### Os três perfis do Brasil municipal

O algoritmo K-Means, após testar valores de k de 3 a 9 e escolher o que maximiza o coeficiente de silhueta, identificou **3 clusters**:

| Perfil | Municípios | Descrição |
|--------|-----------|-----------|
| Municípios sob risco ambiental crítico | 3.196 | Alta área agropecuária, baixa vegetação nativa, INSM baixo |
| Municípios agrícolas moderados | 2.306 | Equilíbrio médio entre uso produtivo e alguma preservação |
| Municípios em recuperação | 70 | Ganho líquido de vegetação nativa entre 2015 e 2021 |

O dado mais impactante: **3.196 municípios** (57% do total) estão no cluster de risco crítico. São municípios onde o uso agropecuário domina a paisagem e a vegetação nativa foi amplamente suprimida.

Os **70 municípios em recuperação** têm uma característica inesperada: a maioria não está na fronteira amazônica. São cidades. Ananindeua (PA), Santo André (SP), Maracanaú (CE), Duque de Caxias (RJ), Porto Alegre (RS), Brasília (DF) lideram o cluster.

O que esses municípios urbanos têm em comum é que ganharam cobertura vegetal entre 2015 e 2021. Não por restauração de floresta primária, mas por regeneração em áreas periurbanas, arborização de margens de rios e reflorestamento de encostas antes degradadas. O satélite registra tudo isso como ganho de vegetação nativa.

É um sinal de que a recuperação ambiental pode acontecer mesmo em contextos urbanos densos. Não resolve o problema estrutural dos 3.196 municípios em risco crítico, mas demonstra que a trajetória não é necessariamente irreversível.

---

## O que torna este projeto diferente

A maioria dos índices de sustentabilidade municipais brasileiros existentes usa pesos definidos por comitês de especialistas. Isso tem um problema: o peso reflete opinião, não dados.

O INSM usa dois métodos quantitativos para derivar os pesos a partir da estrutura dos próprios dados:

**PCA** identifica quais indicadores carregam mais informação independente sobre a variação entre municípios. Indicadores altamente correlacionados entre si recebem peso combinado menor. Isso evita dupla contagem.

**EWM (Entropy Weight Method)** parte do princípio de que um indicador com pouca variação entre municípios carrega menos informação discriminante. Se todos os municípios têm PIB per capita parecido, esse indicador não ajuda a distinguir os mais dos menos sustentáveis. O EWM penaliza esses indicadores automaticamente.

O resultado é que os pesos refletem a geometria real dos dados, não pressupostos externos.

---

## Como reproduzir

Tudo está público no repositório. Os dados podem ser baixados diretamente das fontes com:

```bash
python -m pipeline.download
python -m pipeline.transform
python -m src.models.index_builder
streamlit run src/dashboard/app.py
```

O dashboard interativo permite explorar o mapa coropleto do Brasil, filtrar por estado, bioma ou faixa de população, comparar municípios e ver o perfil detalhado de cada um dos 5.572 municípios analisados.

---

## O que vem a seguir

Esta primeira versão do INSM cobre o ano base de 2021 com as fontes disponíveis via API aberta. As próximas etapas naturais são:

- Incorporar dados do PRODES (desmatamento anual por município) quando a API estiver estável
- Adicionar o IDEB e indicadores de saúde ambiental do DATASUS
- Construir uma série temporal completa de 2010 a 2023
- Publicar o artigo científico descrevendo a metodologia completa
- Criar um painel público para gestores municipais monitorarem sua posição ao longo do tempo

O Brasil tem 8,5 milhões de km². Saber onde ainda existe natureza para preservar, onde existe potencial de recuperação e onde a pressão já atingiu o limite é o primeiro passo para tomar decisões melhores. Os dados já existem. Agora estão organizados.

---

## O que o índice não captura

Todo modelo é uma simplificação. O INSM foi construído com rigor, mas há premissas que moldam os resultados e limitações que o leitor precisa conhecer.

**As notas são relativas, não absolutas.** O score de 0 a 100 é calculado ancorando o pior município atual em 0 e o melhor em 100. Isso significa que a nota de cada município depende do conjunto inteiro dos 5.572. Se o conjunto mudar, as notas mudam. Scores de anos diferentes não podem ser comparados diretamente sem recalibração completa.

**Dados ausentes são preenchidos com a mediana nacional.** Quando um indicador está ausente para um município — PIB não reportado, cobertura MapBiomas incompleta — o valor da mediana de todos os outros municípios é imputado. O município não é excluído da análise, mas sua nota pode não refletir a situação real.

**O índice mede principalmente sustentabilidade ambiental.** O PIB per capita tem peso de apenas 1,2% na composição final. Isso é consequência direta do método: o EWM dá menos importância a indicadores com baixa variação relativa entre municípios, e o PIB varia proporcionalmente menos do que a vegetação ao comparar um município amazônico com um paulista. Na prática, o INSM é quase inteiramente um índice ambiental. Dimensões sociais como saneamento, saúde e educação não estão incluídas nesta versão.

**Todo uso agropecuário recebe o mesmo peso negativo.** O modelo não distingue entre monocultura de soja em escala industrial e agricultura familiar diversificada. Sistemas agroflorestais e cultivos perenes recebem a mesma penalização que pastagem degradada. Isso é uma limitação do dado disponível: o MapBiomas classifica o uso do solo, não a qualidade ou intensidade do uso.

**Municípios grandes diluem sua heterogeneidade interna.** Altamira (PA) cobre 159.000 km² — maior que a Grécia. Uma média municipal esconde a diferença entre floresta preservada no oeste e áreas desmatadas próximas a rodovias. Quanto maior o município, mais o indicador médio mascara a variação interna.

**Os dados de desmatamento do PRODES e de focos de calor do Queimadas não foram incorporados.** As APIs do INPE não retornaram dados completos no momento da extração. Esses indicadores aparecem como fontes listadas, mas não integram o cálculo nesta versão. Municípios com histórico recente de desmatamento intenso podem ter a nota superestimada.

**A vegetação nativa inclui estágios variados de conservação.** O MapBiomas classifica formações campestres, restingas, apicuns e caatinga como vegetação nativa, ao lado de floresta primária densa. Uma área de Caatinga degradada contribui positivamente para o INSM da mesma forma que uma floresta amazônica intacta. A qualidade ecológica da vegetação não é capturada pelo indicador de cobertura.

**A derivação de pesos usa apenas 3 componentes do PCA.** Com 8 indicadores disponíveis, a restrição a 3 componentes significa que parte da estrutura de variação dos dados não influencia os pesos finais. Essa é uma escolha de parametrização que pode ser revisada em versões futuras.

Conhecer essas premissas não invalida o índice — invalida a leitura ingênua do número preciso. Um INSM de 72,4 não é necessariamente "melhor" do que 71,9 de forma estatisticamente significativa. As grandes diferenças são robustas: Amazonas versus São Paulo, Serra do Navio versus Lajedão. As diferenças marginais entre municípios próximos no ranking exigem análise mais cuidadosa antes de qualquer uso em política pública.

---

## O que os dados dizem

O INSM é um diagnóstico. Não é sentença.

O Brasil perdeu 99 milhões de hectares de vegetação nativa entre 1985 e 2021. Isso está nos dados, pixel por pixel, imagem por imagem. Mas também está nos dados que **534 municípios** ainda preservam mais de 80% de cobertura nativa. E que **70 municípios** reverteram a tendência e ganharam vegetação líquida nos últimos seis anos registrados.

O que o índice torna visível, acima de tudo, é a heterogeneidade do Brasil. Não existe "o Brasil sustentável" ou "o Brasil insustentável". Existem 5.572 histórias municipais diferentes, com pressões distintas, capacidades institucionais distintas e pontos de partida distintos. O Amazonas tem 93,7 de INSM médio e São Paulo tem 35,5. Os dois são Brasil.

Saber onde cada município está é o primeiro passo para decidir para onde quer ir. O INSM existe para tornar essa conversa possível, com dados em vez de impressões.

---

*Fontes: IBGE (PIB, população, PAM, PPM, shapefile 2022), MapBiomas Coleção 9 (uso do solo 1985-2023), INPE (PRODES, Queimadas), SICONFI/Tesouro Nacional, INEP. Metodologia: PCA + Entropy Weight Method (pesos), LightGBM (modelagem preditiva), K-Means (clustering). Código aberto: github.com/leo-bonacini/insm_brasil*
