import argparse

import pandas as pd

from pathlib import Path
from multiprocessing import Pool

from fmriprep_denoise.data.fmriprep import get_prepro_strategy
from fmriprep_denoise.features.derivatives import (compute_connectome,
                                               check_extraction)
from fmriprep_denoise.features import qcfc, louvain_modularity


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="Generate denoise metric based on denoising strategy for ds000228.",
    )
    parser.add_argument(
        "input_path",
        action="store",
        type=str,
        help="input path for .gz dataset."
    )
    parser.add_argument(
        "output_path",
        action="store",
        type=str,
        help="output path for metrics."
    )
    parser.add_argument(
        "--atlas",
        action="store",
        type=str,
        help="Atlas name (schaefer7networks, mist, difumo, gordon333)"
    )
    parser.add_argument(
        "--dimension",
        action="store",
        help="Number of ROI. See meta data of each atlas to get valid inputs.",
    )
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_args()
    print(vars(args))
    input_gz = Path(args.input_path)
    atlas = args.atlas
    dimension = args.dimension
    output_path = Path(args.output_path) / "metrics"
    output_path.mkdir(exist_ok=True)

    extracted_path = check_extraction(input_gz, extracted_path_root=None)
    dataset = extracted_path.name.split('-')[-1]

    _, strategy_names = get_prepro_strategy(None)

    metric_qcfc, metric_mod = [], []
    for strategy_name in strategy_names:
        print(strategy_name)
        file_pattern = f"atlas-{atlas}_nroi-{dimension}_desc-{strategy_name}"

        connectome, phenotype = compute_connectome(atlas, extracted_path,
                                                   dataset, file_pattern)
        print("\tLoaded connectome...")

        metric = qcfc(phenotype.loc[:, 'mean_framewise_displacement'],
                      connectome,
                      phenotype.loc[:, ['age', 'gender']])
        metric = pd.DataFrame(metric)
        metric.columns = [f'{strategy_name}_{col}' for col in metric.columns]
        metric_qcfc.append(metric)
        print("\tQC-FC...")
        with Pool(30) as pool:
            qs = pool.map(louvain_modularity, connectome.values.tolist())

        modularity = pd.DataFrame(qs,
                                  columns=[strategy_name],
                                  index=connectome.index)
        metric_mod.append(modularity)
        print("\tModularity...")

    metric_qcfc = pd.concat(metric_qcfc, axis=1)
    metric_qcfc.to_csv(
        output_path
        / f"dataset-{dataset}_atlas-{atlas}_nroi-{dimension}_qcfc.tsv",
        sep='\t',
    )
    metric_mod = pd.concat(metric_mod, axis=1)
    metric_mod.to_csv(
        output_path
        / f"dataset-{dataset}_atlas-{atlas}_nroi-{dimension}_modularity.tsv",
        sep='\t',
    )

if __name__ == "__main__":
    main()