/*
 * Copyright 2020 The Kale Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import * as React from 'react';
import { useForm } from 'react-hook-form';
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
} from '@material-ui/core';
import { Header } from '../components/DialogTitle';
import { FormInput } from '../components/FormInput';

interface KFServingDialog {
  open: boolean;
  toggleDialog: Function;
  // runInferenceService: Function;
}

export const KFServingDialog: React.FunctionComponent<KFServingDialog> = props => {
  const { register, handleSubmit, errors, triggerValidation } = useForm({
    mode: 'onChange',
  });

  const onSubmit = (data: any) => {
    // props.runInferenceService(data);
  };

  React.useEffect(() => {
    // Run a validation when the dialog opens on the pre-filled/default values.
    // The delay is needed because otherwise the effect would run too fast,
    // before the form is ready to run the validation.
    if (props.open) {
      setTimeout(() => {
        triggerValidation();
      }, 500);
    }
  }, [props.open]);

  const handleClose = () => {
    props.toggleDialog();
  };

  return (
    <Dialog open={props.open}>
      <DialogTitle>
        <Header title="KFServing" />
      </DialogTitle>
      <DialogContent>
        <FormInput
          variant="outlined"
          name="name"
          label="InferenceService Name"
          defaultValue=""
          error={!!errors?.name}
          helperText={errors.name?.message}
          inputRef={register({
            required: 'Required field',
            pattern: {
              value: /^[a-z]([a-z0-9-]*[a-z0-9])?$/,
              message: 'Must be a valid K8s resource name',
            },
          })}
        />
        <FormInput
          variant="outlined"
          name="image"
          label="Docker Image"
          defaultValue=""
          error={!!errors?.image}
          helperText={errors.image?.message}
          inputRef={register({ required: 'Required field' })}
        />
        <FormInput
          variant="outlined"
          name="port"
          label="Endpoint Port"
          defaultValue={5000}
          error={!!errors?.port}
          helperText={errors.port?.message}
          inputRef={register({
            required: 'Required field',
            pattern: { value: /^[0-9]+$/, message: 'Must be an int' },
          })}
        />
        <FormInput
          variant="outlined"
          name="endpoint"
          label="Service Endpoint"
          defaultValue=""
          error={!!errors?.endpoint}
          helperText={errors.endpoint?.message}
          inputRef={register({ required: 'Required field' })}
        />
        <FormInput
          variant="outlined"
          name="path"
          label="Model Path"
          defaultValue=""
          error={!!errors?.path}
          helperText={errors.path?.message}
          inputRef={register({ required: 'Required field' })}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} color="primary">
          Cancel
        </Button>
        <Button onClick={handleSubmit(onSubmit)} color="primary">
          Run
        </Button>
      </DialogActions>
    </Dialog>
  );
};
