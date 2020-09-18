# Copyright 2020 The Kale Authors
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import yaml
import logging

from kale.common import podutils, k8sutils
from kubernetes.client.rest import ApiException
from kale.rpc.errors import RPCUnhandledError

log = logging.getLogger(__name__)


PREDICTORS = [
    "onnx"
    "custom",
    "triton",
    "pytorch",
    "sklearn",
    "xgboost",
    "tensorflow",
]

RAW_TEMPLATE = """\
apiVersion: serving.kubeflow.org/v1alpha2
kind: InferenceService
metadata:
  annotations:
    sidecar.istio.io/inject: "false"
  labels:
    controller-tools.k8s.io: "1.0"
  name: {name}
spec:
  default:
    predictor:
{predictor_template}
"""

PVC_PREDICTOR_TEMPLATE = """\
      {predictor}:
        storageUri: "pvc://{pvc_name}{model_path}"
"""

CUSTOM_PREDICTOR_TEMPLATE = """\
      container:
        image: {image}
        name: kfserving-container
        ports:
          - containerPort: {port}
        env:
          - name: STORAGE_URI
            value: "pvc://{pvc_name}{model_path}"
"""

co_group = "serving.kubeflow.org"
co_version = "v1alpha2"
co_plural = "inferenceservices"


def create_inference_service(name: str,
                             predictor: str,
                             pvc_name: str,
                             model_path: str,
                             image: str = None,
                             port: int = None,
                             submit: bool = True):
    """Create and submit an InferenceService.

    Args:
        name (str): Name of the InferenceService CR
        predictor (str): One of serveutils.PREDICTORS
        pvc_name (str): Name of the PVC which contains the model
        model_path (str): Absolute path to the dump of the model
        image (optional): Image to run the InferenceService
        port (optional): To be used in conjunction with `image`. The port where
            the custom endpoint is exposed.
        submit (bool): Set to False to just create the YAML and not submit the
            CR to the K8s.

    Returns (str): Path to the generated YAML
    """

    if predictor not in PREDICTORS:
        raise ValueError("Invalid predictor: %s. Choose one of %s"
                         % (predictor, PREDICTORS))

    if predictor == "custom":
        if not image:
            raise ValueError("You must specify an image when using a custom"
                             " predictor.")
        if not port:
            raise ValueError("You must specify a port when using a custom"
                             " predictor.")
        _tmpl = CUSTOM_PREDICTOR_TEMPLATE.format(image=image, port=port,
                                                 pvc_name=pvc_name,
                                                 model_path=model_path)
    else:
        _tmpl = PVC_PREDICTOR_TEMPLATE.format(predictor=predictor,
                                              pvc_name=pvc_name,
                                              model_path=model_path)

    raw_template = RAW_TEMPLATE.format(name=name, predictor_template=_tmpl)

    definition_path = "%s.kfserving.yaml" % name
    log.info("Saving InferenceService definition at %s" % definition_path)
    with open(definition_path, "w") as yaml_file:
        yaml_file.write(raw_template)

    if submit:
        json_obj = yaml.load(raw_template, Loader=yaml.FullLoader)
        _submit_inference_service(json_obj, podutils.get_namespace())
    return definition_path


def _submit_inference_service(inference_service, namespace):
    k8s_co_client = k8sutils.get_k8s_co_client()

    name = inference_service["metadata"]["name"]
    log.info("Creating InferenceService '%s'..." % name)
    try:
        k8s_co_client.create_namespaced_custom_object(co_group, co_version,
                                                      namespace, co_plural,
                                                      inference_service)
    except ApiException as e:
        log.info("Failed to launch InferenceService. ApiException: %s" % e)
        raise RPCUnhandledError(message="Failed to launch InferenceService",
                                details=str(e))
    log.info("Successfully created InferenceService: %s" % name)


def get_inference_service(name):
    """Get an InferenceService object."""
    k8s_co_client = k8sutils.get_k8s_co_client()
    ns = podutils.get_namespace()
    return k8s_co_client.get_namespaced_custom_object(co_group, co_version,
                                                      ns, co_plural, name)