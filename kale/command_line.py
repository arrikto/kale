import argparse
import nbformat as nb

from argparse import RawTextHelpFormatter

from kale.core import Kale
from kale.notebook_gen import generate_notebooks_from_yml


ARGS_DESC = """
KALE: Kubeflow Automated pipeLines Engine\n
\n
KALE is tool to convert JupyterNotebooks into self-contained python scripts
that define execution graph using the KubeflowPipelines Python SDK.\n
\n
The pipeline's steps are defined by the cell(s) of the Notebook. To tell Kale
how to merge multiple cells together and how to link together the steps
of the generated pipeline, you need to tag the cells using a proper
tagging language. More info at github.com/kubeflow-kale/kale.\n
\n
CLI Arguments:\n
\n
Most of the arguments that you see in this help can be embedded in the
input notebook `metadata` section. If the same argument (e.g. `pipeline_name`)
is provided both in the Notebook metadata and from CLI, the CLI parameter
will take precedence.\n
"""

KALE_NOTEBOOK_METADATA_KEY = 'kubeflow_noteobok'
REQUIRED_ARGUMENTS = ['experiment_name', 'pipeline_name', 'docker_image']


def main():
    parser = argparse.ArgumentParser(description=ARGS_DESC, formatter_class=RawTextHelpFormatter)
    parser.add_argument('--nb', type=str, help='Path to source JupyterNotebook', required=True)
    parser.add_argument('--experiment_name', type=str, help='Name of the created experiment')
    parser.add_argument('--pipeline_name', type=str, help='Name of the deployed pipeline')
    parser.add_argument('--pipeline_description', type=str, help='Description of the deployed pipeline')
    parser.add_argument('--docker_image', type=str, help='Docker base image used to build the pipeline steps')
    # important to have default=None, otherwise it would default to False and would always override notebook_metadata
    parser.add_argument('--upload_pipeline', action='store_true')
    parser.add_argument('--run_pipeline', action='store_true')
    parser.add_argument('--kfp_dns', type=str,
                        help='DNS to KFP service. Provide address as <host>:<port>. `/pipeline` will be appended automatically')
    parser.add_argument('--jupyter_args', type=str, help='YAML file with Jupyter parameters as defined by Papermill')
    parser.add_argument('--debug', action='store_true')

    args = parser.parse_args()

    notebook_metadata = nb.read(args.nb, as_version=nb.NO_CONVERT).metadata.get(KALE_NOTEBOOK_METADATA_KEY, dict())
    # convert args to dict removing all None elements, and overwrite keys into notebook_metadata
    metadata_arguments = {**notebook_metadata, **{k: v for k, v in vars(args).items() if v is not None}}
    for r in REQUIRED_ARGUMENTS:
        if r not in metadata_arguments:
            raise ValueError(f"Required argument not found: {r}")

    # if jupyter_args is set, generate first a set of temporary notebooks
    # based on the input yml parameters (via Papermill)
    if 'jupyter_args' in metadata_arguments:
        generated_notebooks = generate_notebooks_from_yml(input_nb_path=args.nb,
                                                          yml_parameters_path=metadata_arguments['jupyter_args'])

        # Run KaleCore over each generated notebook
        for n, params in generated_notebooks:
            Kale(
                source_notebook_path=n,
                experiment_name=metadata_arguments['experiment_name'] + params,
                pipeline_name=metadata_arguments['pipeline_name'] + params,
                pipeline_descr=metadata_arguments['pipeline_description'] + " params" + params,
                docker_image=metadata_arguments['docker_image'],
                upload_pipeline=metadata_arguments['upload_pipeline'],
                run_pipeline=metadata_arguments['run_pipeline'],
                volumes=metadata_arguments['volumes'],
                debug=args.debug
            ).run()
    else:
        Kale(
            source_notebook_path=args.nb,
            experiment_name=metadata_arguments['experiment_name'],
            pipeline_name=metadata_arguments['pipeline_name'],
            pipeline_descr=metadata_arguments['pipeline_description'],
            docker_image=metadata_arguments['docker_image'],
            upload_pipeline=metadata_arguments['upload_pipeline'],
            run_pipeline=metadata_arguments['run_pipeline'],
            volumes=metadata_arguments['volumes'],
            debug=args.debug
        ).run()


KALE_VOLUMES_DESCRIPTION = """
Call kale-volumes to get information about Rok volumes currently mounted on
your Notebook Server.
"""


def kale_volumes():
    """This function handles kale-volumes CLI command"""
    import logging
    import os
    import sys
    import tabulate
    from pathlib import Path
    import json
    from kale.utils import pod_utils

    # Add logger
    # Log to stdout. Set logging level according to --debug flag
    # Log to file ./kale-volumes.log. Logging level == DEBUG
    logger = logging.getLogger("kubeflow-kale")
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s: %(message)s",
        datefmt="%m-%d %H:%M"
    )
    logger.setLevel(logging.DEBUG)

    log_dir_path = Path(".")
    file_handler = logging.FileHandler(
        filename=log_dir_path / 'kale-volumes.log',
        mode='a'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    def list_volumes(args, logger):
        """This function gets invoked by the sub-command 'list'."""
        volumes = pod_utils.list_volumes()

        if args.output == "table":
            headers = ["Mount Path", "Volume Name", "PVC Name", "Volume Size"]
            data = [(path, volume.name,
                     volume.persistent_volume_claim.claim_name, size)
                    for path, volume, size in volumes]
            logger.info(tabulate.tabulate(data, headers=headers))
        else:
            volumes_out = [{"type": "clone",
                            "name": volume.name,
                            "mount_point": path,
                            "size": size,
                            "size_type": "",
                            "snapshot": False}
                           for path, volume, size in volumes]
            print(json.dumps(volumes_out,
                             sort_keys=True,
                             indent=3,
                             separators=(",", ": ")))

    parser = argparse.ArgumentParser(description=KALE_VOLUMES_DESCRIPTION)
    parser.add_argument(
        "--output",
        "-o",
        choices=["table", "json"],
        default="table",
        nargs="?",
        type=str,
        help="Output format - Default: 'table'"
    )
    parser.add_argument('--debug', action='store_true')
    subparsers = parser.add_subparsers(
        dest="subcommand",
        help="kale-volumes sub-commands"
    )

    parser_list = subparsers.add_parser("list",
                                        help="List Rok volumes currently "
                                             "mounted on the Notebook "
                                             "Server")
    parser_list.set_defaults(func=list_volumes)

    args = parser.parse_args()

    if args.debug:
        stream_handler.setLevel(logging.DEBUG)

    if not os.getenv("NB_PREFIX"):
        logger.error("You may run this command only inside a Notebook Server.")
        sys.exit(1)

    args.func(args, logger)


if __name__ == "__main__":
    main()
