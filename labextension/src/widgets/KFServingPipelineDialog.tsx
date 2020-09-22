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
import { PREDICTOR_VALUES } from './KFServingDialog';

interface KFServingPipelineDialog {
  open: boolean;
  toggleDialog: Function;
  setKFServingMetadata: Function;
}

const KFServingPipelineDialog: React.FunctionComponent<KFServingPipelineDialog> = props => {
  const {
    register,
    handleSubmit,
    errors,
    triggerValidation,
    control,
  } = useForm({
    mode: 'onChange',
  });

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
    props.setKFServingMetadata(data);
  };

  return (
    <Dialog open={props.open}>
      <DialogTitle>
        <Header title="KFServing" />
      </DialogTitle>
      <DialogContent>
        <FormInput
          variant="outlined"
          name="model"
          label="Model Variable Name"
          defaultValue=""
          error={!!errors?.model}
          helperText={errors.model?.message}
          inputRef={register({ required: 'Required field' })}
        />
        <Controller
          name="predictor"
          control={control}
          defaultValue="" // empty selection
          rules={{ required: 'Required field' }}
          as={<FormSelect label="Predictor" values={PREDICTOR_VALUES} />}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={handleSubmit(onSubmit)} color="primary">
          Ok
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default KFServingPipelineDialog;
