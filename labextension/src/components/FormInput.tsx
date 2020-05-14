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
import TextField, { OutlinedTextFieldProps } from '@material-ui/core/TextField';
import { createStyles, makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles(() =>
  createStyles({
    label: {
      color: 'var(--jp-input-border-color)',
      fontSize: 'var(--jp-ui-font-size2)',
    },
    input: {
      color: 'var(--jp-ui-font-color1)',
    },
    textField: {
      width: '100%',
    },
    helperLabel: {
      color: 'var(--jp-info-color0)',
    },
  }),
);

// @ts-ignore
export interface InputBaseProps extends OutlinedTextFieldProps {
  inputIndex?: number;
  readOnly?: boolean;
}

export const FormInput: React.FunctionComponent<InputBaseProps> = props => {
  const classes = useStyles({});

  const {
    className,
    inputIndex,
    readOnly = false,
    InputProps,
    ...rest
  } = props;

  return (
    // @ts-ignore
    <TextField
      {...rest}
      className={classes.textField}
      margin="dense"
      spellCheck={false}
      InputProps={{
        classes: { root: classes.input },
        readOnly: readOnly,
        ...InputProps,
      }}
      InputLabelProps={{
        classes: { root: classes.label },
        // shrink: !!placeholder
      }}
      FormHelperTextProps={{ classes: { root: classes.helperLabel } }}
    />
  );
};
