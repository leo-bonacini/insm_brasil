# The Brazil that preserved and the Brazil that was deforested: a story told by data

> "Which Brazilian municipalities can most efficiently balance economic development, environmental preservation, and quality of life?"

That question sounds simple. The answer required cross-referencing more than **2.3 million land-use records**, economic data from all 5,572 Brazilian municipalities, and decades of satellite monitoring. The result is the **INSM** (National Municipal Sustainability Index), built entirely from public data and reproducible scientific methods.

---

## What the INSM is

The INSM is not a grade. It is a balance thermometer.

It measures how well each municipality simultaneously preserves what nature it still has, uses land responsibly, and generates wealth without destroying the environment that sustains it.

The index runs from **0 to 100**. Higher means more sustainable. But what goes into the calculation?

| Indicator | Weight | Direction |
|-----------|--------|-----------|
| Forest cover (MapBiomas) | 18.9% | More forest: better |
| Total native vegetation (MapBiomas) | 19.2% | More nature: better |
| Agricultural area (MapBiomas) | 20.4% | More pasture and cropland: worse |
| Combined environmental pressure | 12.0% | More pressure: worse |
| Urban area (MapBiomas) | 9.9% | More urbanization: worse |
| Population density | 9.4% | Denser: worse |
| Change in native vegetation (2015 to 2021) | 8.9% | Gained green: better |
| GDP per capita | 1.2% | More wealth: better |

The weights **were not set by human judgment**. They emerge from two statistical methods applied in sequence: PCA (Principal Component Analysis, which captures the latent structure of the data) and the Entropy Weight Method (which gives more weight to indicators with higher informational variation across municipalities). The final result is the average of both, normalized to sum to 100%.

---

## Where the data comes from

All public. All verifiable. All open-licensed.

**MapBiomas Collection 9** is the project's environmental backbone. It is 39 years of satellite imagery classified pixel by pixel across all of Brazil, from 1985 to 2023. For every municipality, we know exactly how many hectares are forest, pasture, soy cropland, urban area, mining, or mangrove. That is **2,322,780 records** processed in this project.

**IBGE** provided the economic and demographic skeleton: municipal GDP from 2018 to 2021, population estimates, agricultural production (PAM) and livestock (PPM) via the SIDRA API, and the shapefile with the precise boundaries of all 5,572 Brazilian municipalities.

**INPE** monitors deforestation via PRODES and heat spots via the Queimadas program. Both are fed by satellites that have been operating for decades.

---

## What the data reveals

### The Brazil up north is not the same as the Brazil down south

The first major surprise from the INSM is geographic. The country's most sustainable states are not its wealthiest.

| State | Average INSM |
|-------|-------------|
| Amazonas (AM) | 93.7 |
| Amapá (AP) | 88.9 |
| Piauí (PI) | 84.5 |
| Roraima (RR) | 84.4 |
| Ceará (CE) | 76.2 |

Amazonas leads by a wide margin. The reason is direct: 93% of the state is still covered by native forest. Agricultural pressure is low. Population density is among the lowest in Brazil. The environmental pressure index is minimal.

São Paulo, the wealthiest state, ranks 25th out of 27, with an average INSM of just 35.5. The equation is reversed: heavy cropland, heavy urban footprint, little remaining vegetation.

By region:

| Region | Average INSM |
|--------|-------------|
| North | 66.1 |
| Northeast | 59.3 |
| South | 46.4 |
| Center-West | 44.4 |
| Southeast | 40.5 |

The North preserves more because it still has something to preserve. The Southeast industrialized, urbanized, and deforested decades ago. That is not a judgment: it is history recorded in satellite imagery.

---

### The number one municipality

**Serra do Navio (AP)** sits at the absolute top with an INSM of 100.

A town of just over 5,000 people in the heart of Amapá. Native vegetation covers virtually the entire territory. No meaningful agricultural pressure. The local economy is modest, which the index captures in the GDP per capita component, but the environmental sustainability more than compensates across every other criterion.

**Guaramiranga (CE)**, second with 99.9, tells a different story. It is a highland municipality in the Chapada do Apodi, with 97% of its native vegetation intact. Small, sparsely populated, and economically humble. But green. Very green.

**Atalaia do Norte (AM)**, third overall, borders Peru. It contains part of the Vale do Javari, the world's largest indigenous reserve by area. Dense forest, environmental pressure close to zero.

---

### The other extreme

**Lajedão (BA)** closes the ranking with an INSM of 0.

A municipality in Bahia with less than 2% native cover, territory almost entirely taken over by pasture and cropland, and accelerating vegetation loss between 2015 and 2021. It is not alone.

**545 municipalities** have less than 10% native cover. **550 municipalities** score below 25 on the INSM. By environmental metrics, these municipalities are in critical degradation.

The other municipalities at the bottom of the ranking are in Espírito Santo, São Paulo, Minas Gerais, and Bahia. The pattern is consistent: high proportion of agricultural area, low remaining vegetation, high pressure index.

---

### GDP and sustainability: the correlation that surprises

The correlation between GDP per capita and the INSM is just **-0.12**.

That means virtually no linear relationship. Wealthy municipalities are not necessarily more sustainable. In fact, the slight negative correlation suggests the opposite: richer municipalities tend to score marginally lower, likely because wealth here tends to come paired with urbanization and intensive land use.

The dominant correlation is with native vegetation: **+0.97**.

It is almost a law: where there is forest, there is sustainability. Where the forest disappeared, the INSM collapsed. Agricultural expansion has a correlation of **-0.90** with the INSM.

**534 municipalities** have more than 80% native cover. These are the municipalities that still hold original Brazil.

---

### 39 years recorded in pixels

The Brazil of 2021 is not the same as the Brazil of 1985. The satellites recorded everything.

In 1985, Brazil had **657.3 million hectares** of native vegetation. By 2021, that figure had fallen to **558.2 million**. The difference: **99 million hectares lost** in 36 years.

For scale: 99 million hectares is an area larger than Venezuela. It is as though an entire country was converted to pasture and cropland over three and a half decades.

On the other side of the ledger, agricultural area nearly doubled:

| Year | Native vegetation | Agricultural area |
|------|------------------|-------------------|
| 1985 | 657.3 M ha | 110.6 M ha |
| 2000 | 603.6 M ha | 185.7 M ha |
| 2010 | 577.4 M ha | 209.7 M ha |
| 2021 | 558.2 M ha | 221.9 M ha |

Each hectare gained by agribusiness during this period corresponds, on average, to one hectare lost of native vegetation. The revised Forest Code of 2012 and strengthened satellite monitoring slowed the process in subsequent years, but did not reverse it.

This data is at the foundation of the INSM. When a municipality appears with a low score, it is because decades of imagery show exactly what happened to its territory.

---

### What machine learning learned

Five machine learning algorithms were trained to predict the INSM from the raw indicators.

The winner was **LightGBM**, with 5-fold cross-validation:

| Model | R² (CV) | RMSE (CV) |
|-------|---------|-----------|
| LightGBM | 0.999 | 0.687 |
| XGBoost | 0.999 | 0.775 |
| Gradient Boosting | 0.998 | 0.853 |
| Random Forest | 0.998 | 0.908 |
| ElasticNet | 0.969 | 3.765 |

An R² of 0.999 means the model explains 99.9% of the variation in the index from its input indicators. This is not overfitting: it reflects that the INSM is a deterministic combination of its components, and the tree-based models captured that structure precisely.

SHAP analysis confirms what the correlations already indicated: **forest cover** and **native vegetation** are the factors with the greatest individual impact on the final score.

---

### The three profiles of municipal Brazil

The K-Means algorithm, after testing k values from 3 to 9 and selecting the one that maximizes the silhouette coefficient, identified **3 clusters**:

| Profile | Municipalities | Description |
|---------|---------------|-------------|
| Municipalities under critical environmental risk | 3,196 | High agricultural area, low native vegetation, low INSM |
| Moderate agricultural municipalities | 2,306 | Average balance between productive use and some preservation |
| Recovering municipalities | 70 | Net gain in native vegetation between 2015 and 2021 |

The most striking figure: **3,196 municipalities** (57% of the total) fall in the critical-risk cluster. These are municipalities where agricultural use dominates the landscape and native vegetation has been largely suppressed.

The **70 recovering municipalities** have an unexpected characteristic: most are not on the Amazonian frontier. They are cities. Ananindeua (PA), Santo André (SP), Maracanaú (CE), Duque de Caxias (RJ), Porto Alegre (RS), and Brasília (DF) lead the cluster.

What these urban municipalities share is that they gained vegetation cover between 2015 and 2021. Not through primary forest restoration, but through regeneration in peri-urban areas, riverside revegetation, and reforestation of previously degraded hillsides. The satellite records all of it as native vegetation gain.

It signals that environmental recovery can happen even in dense urban contexts. It does not resolve the structural problem of the 3,196 municipalities in critical risk, but it demonstrates that the trajectory is not necessarily irreversible.

---

## What makes this project different

Most existing Brazilian municipal sustainability indexes use weights defined by expert committees. That creates a problem: the weight reflects opinion, not data.

The INSM uses two quantitative methods to derive weights from the structure of the data itself:

**PCA** identifies which indicators carry the most independent information about variation across municipalities. Indicators that are highly correlated with each other receive a combined lower weight. This avoids double-counting.

**EWM (Entropy Weight Method)** operates on the principle that an indicator with little variation across municipalities carries less discriminating information. If all municipalities have similar GDP per capita, that indicator does not help distinguish the more from the less sustainable. The EWM penalizes those indicators automatically.

The result is that the weights reflect the actual geometry of the data, not external assumptions.

---

## How to reproduce

Everything is public in the repository. The data can be downloaded directly from their sources with:

```bash
python -m pipeline.download
python -m pipeline.transform
python -m src.models.index_builder
streamlit run src/dashboard/app.py
```

The interactive dashboard lets you explore the choropleth map of Brazil, filter by state, biome, or population range, compare municipalities, and view the detailed profile of each of the 5,572 municipalities analyzed.

---

## What comes next

This first version of the INSM covers the 2021 base year using sources available via open API. The natural next steps are:

- Incorporate PRODES data (annual deforestation by municipality) once the API is stable
- Add IDEB and DATASUS environmental health indicators
- Build a complete time series from 2010 to 2023
- Publish a scientific article describing the full methodology
- Create a public dashboard for municipal managers to track their position over time

Brazil covers 8.5 million km². Knowing where nature still exists to be preserved, where recovery potential remains, and where pressure has already reached its limit is the first step toward better decisions. The data already exists. Now it is organized.

---

## What the index does not capture

Every model is a simplification. The INSM was built with rigor, but there are assumptions that shape the results and limitations the reader needs to know.

**Scores are relative, not absolute.** The 0-to-100 score is computed by anchoring the current worst municipality at 0 and the best at 100. That means every municipality's score depends on the full set of 5,572. If the set changes, scores change. Scores from different years cannot be compared directly without a full recalibration.

**Missing data is filled with the national median.** When an indicator is absent for a municipality — unreported GDP, incomplete MapBiomas coverage — the median value across all other municipalities is imputed. The municipality is not excluded from the analysis, but its score may not reflect the actual situation.

**The index primarily measures environmental sustainability.** GDP per capita carries a weight of just 1.2% in the final composition. This follows directly from the method: the EWM assigns less importance to indicators with low relative variation across municipalities, and GDP varies proportionally less than vegetation when comparing an Amazonian municipality to one in São Paulo. In practice, the INSM is almost entirely an environmental index. Social dimensions such as sanitation, health, and education are not included in this version.

**All agricultural land use receives the same negative weight.** The model does not distinguish between large-scale soy monoculture and diversified family farming. Agroforestry systems and perennial crops receive the same penalty as degraded pasture. This is a limitation of the available data: MapBiomas classifies land use, not the quality or intensity of that use.

**Large municipalities dilute their internal heterogeneity.** Altamira (PA) covers 159,000 km² — larger than Greece. A municipal average hides the difference between intact forest in the west and deforested areas near highways. The larger the municipality, the more the average indicator masks internal variation.

**PRODES deforestation and fire hotspot data were not incorporated.** The INPE APIs did not return complete data at the time of extraction. These indicators appear as listed sources but are not part of the index calculation in this version. Municipalities with a recent history of heavy deforestation may have an overstated score.

**Native vegetation includes varied stages of conservation.** MapBiomas classifies grassland formations, restinga, apicum, and caatinga as native vegetation alongside dense primary forest. A degraded patch of Caatinga contributes positively to the INSM in the same way as an intact Amazonian forest. The ecological quality of the vegetation is not captured by the coverage indicator.

**Weight derivation uses only 3 PCA components.** With 8 available indicators, capping at 3 components means part of the data's variation structure does not influence the final weights. This is a parameterization choice that can be revisited in future versions.

Knowing these assumptions does not invalidate the index — it invalidates a naive reading of the precise number. An INSM of 72.4 is not necessarily "better" than 71.9 in any statistically meaningful way. The large differences are robust: Amazonas versus São Paulo, Serra do Navio versus Lajedão. Marginal differences between nearby municipalities in the ranking require more careful analysis before any use in public policy.

---

## What the data says

The INSM is a diagnosis. Not a verdict.

Brazil lost 99 million hectares of native vegetation between 1985 and 2021. That is in the data, pixel by pixel, image by image. But also in the data: **534 municipalities** still preserve more than 80% native cover. And **70 municipalities** reversed the trend and gained net vegetation in the last six recorded years.

What the index makes visible, above all, is Brazil's heterogeneity. There is no "sustainable Brazil" or "unsustainable Brazil." There are 5,572 different municipal stories, with distinct pressures, distinct institutional capacities, and distinct starting points. Amazonas has an average INSM of 93.7 and São Paulo has 35.5. Both are Brazil.

Knowing where each municipality stands is the first step toward deciding where it wants to go. The INSM exists to make that conversation possible, with data instead of impressions.

---

*Sources: IBGE (GDP, population, PAM, PPM, 2022 shapefile), MapBiomas Collection 9 (land use 1985-2023), INPE (PRODES, Queimadas), SICONFI/National Treasury, INEP. Methodology: PCA + Entropy Weight Method (weights), LightGBM (predictive modeling), K-Means (clustering). Open source: github.com/leo-bonacini/insm_brasil*
