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

import kubernetes


def get_k8s_co_client():
    """Get the K8s client to interact with the custom objects API."""
    try:
        kubernetes.config.load_incluster_config()
    except Exception:  # Not in a notebook server
        try:
            kubernetes.config.load_kube_config()
        except Exception:
            raise RuntimeError("Could not load Kubernetes config")

    return kubernetes.client.CustomObjectsApi()
