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
import { useForm, Controller } from 'react-hook-form';
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
} from '@material-ui/core';
import { Header } from '../components/DialogTitle';
import { FormInput } from '../components/FormInput';
import { FormSelect } from '../components/FormSelect';

export interface KFServingFormData {
  name: string;
  modelPath: string;
  predictor: string;
  image?: string;
  port?: number;
  endpoint?: string;
}

interface KFServingDialog {
  open: boolean;
  toggleDialog: Function;
  runInferenceService: Function;
}

export const PREDICTOR_VALUES = [
  { label: 'Tensorflow', value: 'tensorflow' },
  { label: 'PyTorch', value: 'pytorch' },
  { label: 'ONNX', value: 'onnx' },
  { label: 'Triton', value: 'triton' },
  { label: 'SKLearn', value: 'sklearn' },
  { label: 'XGBoost', value: 'xgboost' },
  { label: 'Custom', value: 'custom' },
];

const KFServingDialog: React.FunctionComponent<KFServingDialog> = props => {
  const {
    register,
    handleSubmit,
    errors,
    triggerValidation,
    control,
    watch,
  } = useForm({
    mode: 'onChange',
  });

  const predictorValue = watch('predictor');
  console.log(predictorValue);
  // const allValues = watch();
  // console.log(allValues);

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

  const onSubmit = (data: any) => {
    props.toggleDialog();
    props.runInferenceService(data);
  };

  const onCancel = () => {
    props.toggleDialog();
  };

  return (
    <Dialog open={props.open}>
      <DialogTitle>
        <Header title="Serve" />
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
          name="modelPath"
          label="Model Path"
          defaultValue=""
          error={!!errors?.modelPath}
          helperText={errors.modelPath?.message}
          inputRef={register({ required: 'Required field' })}
        />
        <Controller
          name="predictor"
          control={control}
          defaultValue="" // empty selection
          rules={{ required: 'Required field' }}
          as={<FormSelect label="Predictor Type" values={PREDICTOR_VALUES} />}
        />
        {predictorValue === 'custom' && (
          <React.Fragment>
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
          </React.Fragment>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel} color="primary">
          Cancel
        </Button>
        <Button onClick={handleSubmit(onSubmit)} color="primary">
          Run
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default KFServingDialog;
