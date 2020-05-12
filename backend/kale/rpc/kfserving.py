#  Copyright 2020 The Kale Authors
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

from kale.utils import pod_utils
from kale.rpc.katib import _get_k8s_co_client
from kubernetes.client.rest import ApiException
from kale.rpc.errors import RPCUnhandledError

MOUNT_POINT = 0

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
      custom:
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


def create_inference_service(request, cr_args):
    """Create InferenceService."""
    raw_template = RAW_TEMPLATE.format(**cr_args)

    definition_path = "%s.kfserving.yaml" % cr_args['name']
    request.log.info("Saving InferenceService definition at %s" %
                     definition_path)
    with open(definition_path, "w") as yaml_file:
        yaml_file.write(raw_template)

    json_obj = yaml.load(raw_template, Loader=yaml.FullLoader)
    _launch_inference_service(request, json_obj, pod_utils.get_namespace())
    return definition_path


def _launch_inference_service(request, inference_service, namespace):
    k8s_co_client = _get_k8s_co_client(None)

    request.log.info("Launching InferenceService '%s'...",
                     inference_service["metadata"]["name"])
    try:
        k8s_co_client.create_namespaced_custom_object(co_group, co_version,
                                                      namespace, co_plural,
                                                      inference_service)
    except ApiException as e:
        request.log.info("Failed to launch InferenceService")
        raise RPCUnhandledError(message="Failed to launch InferenceService",
                                details=str(e))
    request.log.info("Successfully launched InferenceService")


def get_inference_service(request, name):
    """Get an InferenceService"""
    k8s_co_client = _get_k8s_co_client(None)
    ns = pod_utils.get_namespace()
    try:
        inf = k8s_co_client.get_namespaced_custom_object(co_group, co_version,
                                                         ns, co_plural, name)
        if inf['status'].get('default'):
            return {
                "host": inf['status']['default']['predictor'].get('host')
            }
    except ApiException as e:
        request.log.info("Failed to get InferenceService")
    return None
