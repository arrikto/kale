#### katib_parameters.schema.json

The `feasibleSpace` parameter is dependent on the `parameterType`, for example:

If `parameterType` is `int`, then `feasibleSpace` **must** contain both `min`
and `max` and they **must** be of type `int`

If `parameterType` is `categorical`, then `feasibleSpace` **must** contain `list`.

The `required` keyword is not enough to enforce this nested relationship, as it 
can be used just with direct father-child objects (e.g. having `feasibleSpace` be
required in case `parameterType` is `int`).

See here for a solution to achieve the above: https://stackoverflow.com/questions/57141416/jsonschema-required-property-dependent-on-parent-property



#### Additional checks

- all parameters should have different names
- categorical parameters should have NON-empty list of values?
- assert that correct algortihm settings correspond to certain algortihm name. e.g. if name == random, then random-state must be present