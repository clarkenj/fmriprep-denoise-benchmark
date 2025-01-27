---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.1
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Results

```{code-cell}
:tags: [hide-input, remove-output]

import warnings

warnings.filterwarnings('ignore')
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fmriprep_denoise.visualization import figures, tables, utils
from myst_nb import glue


path_root = utils.get_data_root()
```

## Level of motion in samples quitified by mean framewise displacement

```{code-cell}
:tags: [hide-input, remove-output]

from statsmodels.stats.weightstats import ttest_ind

for_plotting = {}

datasets = ['ds000228', 'ds000030']
baseline_groups = ['adult', 'CONTROL']
for dataset, baseline_group in zip(datasets, baseline_groups):
    _, data, groups = tables.get_descriptive_data(dataset, path_root)
    baseline = data[data['groups'] == baseline_group]
    for group in groups:
        compare = data[data['groups'] == group]
        glue(
            f'{dataset}_{group}_mean',
            compare['mean_framewise_displacement'].mean(),
        )
        glue(
            f'{dataset}_{group}_sd',
            compare['mean_framewise_displacement'].std(),
        )
        glue(
            f'{dataset}_{group}_n',
            compare.shape[0],
        )
        if group != baseline_group:
            t_stats, pval, df = ttest_ind(
                baseline['mean_framewise_displacement'],
                compare['mean_framewise_displacement'],
                usevar='unequal',
            )
            glue(f'{dataset}_t_{group}', t_stats)
            glue(f'{dataset}_p_{group}', pval)
            glue(f'{dataset}_df_{group}', df)
    for_plotting.update({dataset: data})
```

We will firstly characterise motion through the mean framewise displacement of each sample and the sub-groups.
This report will serve as a reference point for understanding the remainder of the results.
In `ds000228`, there was a significant difference in motion during the scan captured by mean framewise displacement 
between the child 
(M = {glue:text}`ds000228_child_mean:.2f`, SD = {glue:text}`ds000228_child_sd:.2f`, n = {glue:text}`ds000228_child_n:i`)
and adult sample
(M = {glue:text}`ds000228_adult_mean:.2f`, SD = {glue:text}`ds000228_adult_sd:.2f`, n = {glue:text}`ds000228_adult_n:i`,
t({glue:text}`ds000228_df_child:.2f`) = {glue:text}`ds000228_t_child:.2f`, p = {glue:text}`ds000228_p_child:.3f`,
This is consistent with the existing literature.
In `ds000030`, the only patient group shows a difference comparing to the
control 
(M = {glue:text}`ds000030_CONTROL_mean:.2f`, SD = {glue:text}`ds000030_CONTROL_sd:.2f`, n = {glue:text}`ds000030_CONTROL_n:i`)
is the schizophrania group 
(M = {glue:text}`ds000030_SCHZ_mean:.2f`, SD = {glue:text}`ds000030_SCHZ_sd:.2f`, n = {glue:text}`ds000030_SCHZ_n:i`;
t({glue:text}`ds000030_df_SCHZ:.2f`) = {glue:text}`ds000030_t_SCHZ:.2f`, p = {glue:text}`ds000030_p_SCHZ:.3f`).
There was no difference between the control and ADHD group
(M = {glue:text}`ds000030_ADHD_mean:.2f`, SD = {glue:text}`ds000030_ADHD_sd:.2f`, n = {glue:text}`ds000030_ADHD_n:i`;
t({glue:text}`ds000030_df_ADHD:.2f`) = {glue:text}`ds000030_t_ADHD:.2f`, p = {glue:text}`ds000030_p_ADHD:.3f`),
or the bipolar group 
(M = {glue:text}`ds000030_BIPOLAR_mean:.2f`, SD = {glue:text}`ds000030_BIPOLAR_sd:.2f`, n = {glue:text}`ds000030_BIPOLAR_n:i`;
t({glue:text}`ds000030_df_BIPOLAR:.2f`) = {glue:text}`ds000030_t_BIPOLAR:.2f`, p = {glue:text}`ds000030_p_BIPOLAR:.3f`).
In conclusion, adult samples has lower mean framewise displacement than a youth sample.

```{code-cell}
:tags: [hide-input, remove-output]

fig = plt.figure(figsize=(7, 5))
axs = fig.subplots(1, 2, sharey=True)
for dataset, ax in zip(for_plotting, axs):
    df = for_plotting[dataset]
    mean_fd = df['mean_framewise_displacement'].mean()
    sd_fd = df['mean_framewise_displacement'].std()
    df = df.rename(
        columns={
            'mean_framewise_displacement': 'Mean Framewise Displacement (mm)',
            'groups': 'Groups'
        }
    )
    sns.boxplot(
        y='Mean Framewise Displacement (mm)', x='Groups', data=df, ax=ax
    )
    ax.set_title(
        f'{dataset}\nMean\u00B1SD={mean_fd:.2f}\u00B1{sd_fd:.2f}\n$N={df.shape[0]}$'
    )
# fig.suptitle("Mean framewise displacement per sub-sample")

glue('meanFD-fig', fig, display=False)
```

```{glue:figure} meanFD-fig
:figwidth: 800px
:name: "tbl:meanFD-fig"

Mean framewise displacement of each dataset.
We found young subjects has higher motion comparing to adults,
which is consistent with the pattern described in the literature.
Amongst psychiatric conditiontions, only the schizophrania group shows difference to the control group.
```

## The loss in temporal degrees of freedom in different strategies

The common analysis and denoising methods are based on linear reagression.
Using more nuisance regressors can capture additional sources of noise-related variance in the data and thus improve denoising.
However, this comes at the expense of a loss of temporal degrees of freedom for statistical inference in further analysis.
This is an important point to consider along side the denoising performance.

In fMRIPrep, high-pass filtering is done through discrete cosine-basis regressors, 
labled as `cosine_*` in fMRIPrep confounds output.
In the following section, the number of discrete cosine-basis regressor will be denoted as $c$. 
Depending on the length of the scan, the number of discrete cosine-basis regressors can differ ($c_{ds000228}=4$, $c_{ds000030}=3$). 
The `simple` and `srubbing`-based strategy are the strategy with a fixed number of degree of freedom loss.
`compcor` and `aroma`-based strategies shows variability depending on the number of noise compoenets detected.
In theory, `compcor6` should also report a fixed number of degree of freedom loss.
However, fMRIPrep outputs the compcor compoenents based on the 50% variance cut-off.
For some subjects the number of components could be lower than 6, hence the variability.

In {cite:t}`ciric_benchmarking_2017`, the equivalent `aroma` and `aroma+gsr` strategies were reported with 
a lower magnitude of loss in temporal degrees of freedom than `scrubbing` or `simple` strategies.
However, we did not observe this advantage is limited to sample with relatively low motion (i.e. adults).
When selecting denoising strategy, 
The two datasets used in the current benchmark both contained subjects with behaviours deviating from the healthy controls.
`ds000228` is comprised of adult healthy controls and children.
`ds000030` includes healthy controls and subjects with three different psychiatric conditions.
the loss in degrees of freedom `simple` ($26 + c$) and `simple+gsr` ($27 + c$) used the least amount of regressors in the general population.
Certain sub-sample uses less regressors with the `aroma` and `aroma+gsr` strategies.
The reason potentially lies in the implementation of ICA-AROMA. 
ICA-AROMA uses pretrained model on healthy subjects to select noise components {cite:p}`aroma`.

```{code-cell}
:tags: [hide-input, remove-output]
fig, ds_groups = figures.plot_dof_dataset(path_root)
glue(f'dof-fig', fig, display=False)
for ds, group in ds_groups:
    glue(f'group-order_{ds}', group, display=False)
```

```{glue:figure} dof-fig
:figwidth: 800px
:name: "tbl:dof-fig"

Loss in temporal degrees of freedom break down by groups.
`compcor` and `aroma`-based strategies shows variability depending on the number of noise compoenets detected.
The variability is broken down by groups.
From the lightest hue to the darkes, the order of the group in `ds000228` is:
{glue:}`group-order_ds000228`
From the lightest hue to the darkes, the order of the group in `ds000030` is:
{glue:}`group-order_ds000030`
```

To compare the loss in number of volumes from scrubbing base strategy across datasets,
we calculate the proportion of volume loss to number of volumes in a full scan.
`ds000228` includes child subjects and shows higher loss in volumes comparing to `ds000030` with adult subjects only.
This is consistent with the trend in the difference in mean framewise displacement,
and it fits the observation shown in literature {cite:p}`satterthwaite_impact_2012`.
In `ds000030`, we see the similar trend mirroring the mean framewise displacemnt results.
The schizophrania group shows the highest amount of volumes scrubbed,
followed by the bipolar group, and comparable results between the control group and ADHD group.
With a stringent 0.2 mm threshold, groups with high motion will loose on average close to half of the volumes. 

```{code-cell}
:tags: [hide-input, remove-output]
fig = figures.plot_vol_scrubbed_dataset(path_root)
glue(f'scrubbing-fig', fig, display=False)
```

```{glue:figure} scrubbing-fig
:figwidth: 800px
:name: "tbl:scrubbing-fig"

Loss in number of volumes in proportion to the full length of the scan, break down by groups in each dataset.
We can see the trend is similar to mean framewise displacement result. 

```

## Comparisons on the impacts of strategies on connectomes
<!-- Please advice on the threshold here -->
<!-- stiengent -->
```{code-cell}
:tags: [hide-input, remove-output]
from fmriprep_denoise.features.derivatives import get_qc_criteria

stringent = get_qc_criteria('stringent')
glue('gross_fd', stringent['gross_fd'])
glue('fd_thresh', stringent['fd_thresh'])
glue('proportion_thresh', stringent['proportion_thresh'] * 100)
```

To evaluate the impact of denoising strategy on connectomes, 
we will exclude subjects with high motion , 
defined by the following criteria adopted from  {cite:p}`parkes_evaluation_2018`: 
mean framewise displacement > {glue:}`gross_fd` mm, 
above {glue:}`proportion_thresh`% of volumes removed while scrubbing 
with a {glue:}`fd_thresh` mm threshold.

The two tables below are the demographic information of the datasets after
the automatic motion quality control.

```{code-cell}
:tags: [hide-input]
desc = tables.lazy_demographic('ds000228', path_root, **stringent)
desc = desc.style.set_table_attributes('style="font-size: 12px"')

glue('ds000228_scrubbed_desc', desc) 
```

```{code-cell}
:tags: [hide-input]
from fmriprep_denoise.visualization import tables

desc = tables.lazy_demographic('ds000030', path_root, **stringent)
desc = desc.style.set_table_attributes('style="font-size: 12px"')

glue('ds000030_scrubbed_desc', desc) 
```


```{code-cell}
:tags: [hide-input, remove-output]

from statsmodels.stats.weightstats import ttest_ind

for_plotting = {}

datasets = ['ds000228', 'ds000030']
baseline_groups = ['adult', 'CONTROL']
for dataset, baseline_group in zip(datasets, baseline_groups):
    _, data, groups = tables.get_descriptive_data(dataset, path_root, **stringent)
    baseline = data[data['groups'] == baseline_group]
    for group in groups:
        compare = data[data['groups'] == group]
        glue(
            f'{dataset}_{group}_mean_qc',
            compare['mean_framewise_displacement'].mean(),
        )
        glue(
            f'{dataset}_{group}_sd_qc',
            compare['mean_framewise_displacement'].std(),
        )
        glue(
            f'{dataset}_{group}_n_qc',
            compare.shape[0],
        )
        if group != baseline_group:
            t_stats, pval, df = ttest_ind(
                baseline['mean_framewise_displacement'],
                compare['mean_framewise_displacement'],
                usevar='unequal',
            )
            glue(f'{dataset}_t_{group}_qc', t_stats)
            glue(f'{dataset}_p_{group}_qc', pval)
            glue(f'{dataset}_df_{group}_qc', df)
    for_plotting.update({dataset: data})
```

We again checked the difference in mean framewise displacement of each sample and the sub-groups.
In `ds000228`, there was still a significant difference in motion during the scan captured by mean framewise displacement 
between the child 
(M = {glue:text}`ds000228_child_mean_qc:.2f`, SD = {glue:text}`ds000228_child_sd_qc:.2f`, n = {glue:text}`ds000228_child_n_qc:i`)
and adult sample
(M = {glue:text}`ds000228_adult_mean_qc:.2f`, SD = {glue:text}`ds000228_adult_sd_qc:.2f`, n = {glue:text}`ds000228_adult_n_qc:i`,
t({glue:text}`ds000228_df_child_qc:.2f`) = {glue:text}`ds000228_t_child_qc:.2f`, p = {glue:text}`ds000228_p_child_qc:.3f`).
In `ds000030`, the only patient group shows a difference comparing to the control 
(M = {glue:text}`ds000030_CONTROL_mean_qc:.2f`, SD = {glue:text}`ds000030_CONTROL_sd_qc:.2f`, n = {glue:text}`ds000030_CONTROL_n_qc:i`)
is still the schizophrania group 
(M = {glue:text}`ds000030_SCHZ_mean_qc:.2f`, SD = {glue:text}`ds000030_SCHZ_sd_qc:.2f`, n = {glue:text}`ds000030_SCHZ_n_qc:i`;
t({glue:text}`ds000030_df_SCHZ_qc:.2f`) = {glue:text}`ds000030_t_SCHZ_qc:.2f`, p = {glue:text}`ds000030_p_SCHZ_qc:.3f`).
There was no difference between the control and ADHD group
(M = {glue:text}`ds000030_ADHD_mean_qc:.2f`, SD = {glue:text}`ds000030_ADHD_sd:.2f`, n = {glue:text}`ds000030_ADHD_n_qc:i`;
t({glue:text}`ds000030_df_ADHD_qc:.2f`) = {glue:text}`ds000030_t_ADHD_qc:.2f`, p = {glue:text}`ds000030_p_ADHD_qc:.3f`),
or the bipolar group 
(M = {glue:text}`ds000030_BIPOLAR_mean_qc:.2f`, SD = {glue:text}`ds000030_BIPOLAR_sd_qc:.2f`, n = {glue:text}`ds000030_BIPOLAR_n_qc:i`;
t({glue:text}`ds000030_df_BIPOLAR_qc:.2f`) = {glue:text}`ds000030_t_BIPOLAR_qc:.2f`, p = {glue:text}`ds000030_p_BIPOLAR_qc:.3f`).
In conclusion, adult samples has lower mean framewise displacement than a youth sample.

```{code-cell}
:tags: [hide-input, remove-output]

datasets = ['ds000228', 'ds000030']
for dataset in datasets:
    _, data, _ = tables.get_descriptive_data(dataset, path_root, **stringent)
    for_plotting.update({dataset: data})

fig = plt.figure(figsize=(7, 5))
axs = fig.subplots(1, 2, sharey=True)
for dataset, ax in zip(for_plotting, axs):
    df = for_plotting[dataset]
    mean_fd = df['mean_framewise_displacement'].mean()
    sd_fd = df['mean_framewise_displacement'].std()
    df = df.rename(
        columns={
            'mean_framewise_displacement': 'Mean Framewise Displacement (mm)',
            'groups': 'Groups'
        }
    )
    sns.boxplot(
        y='Mean Framewise Displacement (mm)', x='Groups', data=df, ax=ax
    )
    ax.set_title(
        f'{dataset}\nMean\u00B1SD={mean_fd:.2f}\u00B1{sd_fd:.2f}\n$N={df.shape[0]}$'
    )
# fig.suptitle("Mean framewise displacement per sub-sample")

glue('meanFD_cleaned-fig', fig, display=False)
```

```{glue:figure} meanFD_cleaned-fig
:figwidth: 800px
:name: "tbl:meanFD_cleaned-fig"
```

```{code-cell}
:tags: [hide-input, remove-output]
fig, ds_groups = figures.plot_dof_dataset(path_root, **stringent)
glue(f'dof-fig_cleaned', fig, display=False)
for ds, group in ds_groups:
    glue(f'group-order_{ds}_cleaned', group, display=False)
```

As for the loss in temporal degrees of freedom break down by groups, the trend 
did not differ from the full sample, as seen in the two graphs below.

```{glue:figure} dof-fig_cleaned
:figwidth: 800px
:name: "tbl:dof-fig_cleaned"

Loss in temporal degrees of freedom break down by groups after quality control,
after applying the stringent quality control threashold.
From the lightest hue to the darkes, the order of the group in `ds000228` is:
{glue:}`group-order_ds000228_cleaned`
From the lightest hue to the darkes, the order of the group in `ds000030` is:
{glue:}`group-order_ds000030_cleaned`
```

```{code-cell}
:tags: [hide-input, remove-output]
fig = figures.plot_vol_scrubbed_dataset(path_root, **stringent)
glue(f'scrubbing-fig_cleaned', fig, display=False)
```

```{glue:figure} scrubbing-fig_cleaned
:figwidth: 800px
:name: "tbl:scrubbing-fig_cleaned"

Loss in number of volumes in proportion to the full length of the scan after quality control, 
break down by groups in each dataset,
after applying the stringent quality control threashold.
We can see the trend is similar to mean framewise displacement result. 

```
In the next section, we will report the three functional connectivity based metrics and break down the effect on each dataset.
