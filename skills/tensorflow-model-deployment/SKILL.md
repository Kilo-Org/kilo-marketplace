---
name: tensorflow-model-deployment
description: Deploy and serve TensorFlow models
allowed-tools:
  - Bash
  - Read
metadata:
  category: data
  source:
    repository: 'https://github.com/thebushidocollective/han'
    path: plugins/specialized/tensorflow/skills/tensorflow-model-deployment
    license_path: LICENSE
    commit: 3fc9880ee2be4b1275359bed910dbd1674134448
---

# TensorFlow Model Deployment

Deploy TensorFlow models to production environments using SavedModel format, TensorFlow Lite for mobile and edge devices, quantization techniques, and serving infrastructure. This skill covers model export, optimization, conversion, and deployment strategies.

## SavedModel Export

### Basic SavedModel Export

```python
# Save model to TensorFlow SavedModel format
model.save('path/to/saved_model')

# Load SavedModel
loaded_model = tf.keras.models.load_model('path/to/saved_model')

# Make predictions with loaded model
predictions = loaded_model.predict(test_data)
```

### Create Serving Model

```python
# Create serving model from classifier
serving_model = classifier.create_serving_model()

# Inspect model inputs and outputs
print(f'Model\'s input shape and type: {serving_model.inputs}')
print(f'Model\'s output shape and type: {serving_model.outputs}')

# Save serving model
serving_model.save('model_path')
```

### Export with Signatures

```python
# Define serving signature
@tf.function(input_signature=[tf.TensorSpec(shape=[None, 224, 224, 3], dtype=tf.float32)])
def serve(images):
    return model(images, training=False)

# Save with signature
tf.saved_model.save(
    model,
    'saved_model_dir',
    signatures={'serving_default': serve}
)
```

## TensorFlow Lite Conversion

### Basic TFLite Conversion

```python
# Convert SavedModel to TFLite
converter = tf.lite.TFLiteConverter.from_saved_model('saved_model_dir')
tflite_model = converter.convert()

# Save TFLite model
with open('model.tflite', 'wb') as f:
    f.write(tflite_model)
```

### From Keras Model

```python
# Convert Keras model directly to TFLite
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

# Save to file
import pathlib
tflite_models_dir = pathlib.Path("tflite_models/")
tflite_models_dir.mkdir(exist_ok=True, parents=True)

tflite_model_file = tflite_models_dir / "mnist_model.tflite"
tflite_model_file.write_bytes(tflite_model)
```

### From Concrete Functions

```python
# Convert from concrete function
concrete_function = model.signatures['serving_default']

converter = tf.lite.TFLiteConverter.from_concrete_functions(
    [concrete_function]
)
tflite_model = converter.convert()
```

### Export with Model Maker

```python
# Export trained model to TFLite with metadata
model.export(
    export_dir='output/',
    tflite_filename='model.tflite',
    label_filename='labels.txt',
    vocab_filename='vocab.txt'
)

# Export multiple formats
model.export(
    export_dir='output/',
    export_format=[
        mm.ExportFormat.TFLITE,
        mm.ExportFormat.SAVED_MODEL,
        mm.ExportFormat.LABEL
    ]
)
```

## Model Quantization

### Post-Training Float16 Quantization

```python
from tflite_model_maker.config import QuantizationConfig

# Create float16 quantization config
config = QuantizationConfig.for_float16()

# Export with quantization
model.export(
    export_dir='.',
    tflite_filename='model_fp16.tflite',
    quantization_config=config
)
```

### Dynamic Range Quantization

```python
# Convert with dynamic range quantization
converter = tf.lite.TFLiteConverter.from_saved_model('saved_model_dir')
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

# Save quantized model
with open('model_quantized.tflite', 'wb') as f:
    f.write(tflite_model)
```

### Full Integer Quantization

```python
def representative_dataset():
    """Generate representative dataset for calibration."""
    for i in range(100):
        yield [np.random.rand(1, 224, 224, 3).astype(np.float32)]

# Convert with full integer quantization
converter = tf.lite.TFLiteConverter.from_saved_model('saved_model_dir')
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8

tflite_model = converter.convert()
```

### Debug Quantization

```python
from tensorflow.lite.python import convert

# Create debug model with numeric verification
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = calibration_gen
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]

# Calibrate and quantize with verification
converter._experimental_calibrate_only = True
calibrated = converter.convert()
debug_model = convert.mlir_quantize(calibrated, enable_numeric_verify=True)
```

### Get Quantization Converter

```python
# Apply quantization settings to converter
def get_converter_with_quantization(converter, **kwargs):
    """Apply quantization configuration to converter."""
    config = QuantizationConfig(**kwargs)
    return config.get_converter_with_quantization(converter)

# Use with custom settings
converter = tf.lite.TFLiteConverter.from_keras_model(model)
quantized_converter = get_converter_with_quantization(
    converter,
    optimizations=[tf.lite.Optimize.DEFAULT],
    representative_dataset=representative_dataset
)
tflite_model = quantized_converter.convert()
```

## JAX to TFLite Conversion

### Basic JAX Conversion

```python
from orbax.export import ExportManager
from orbax.export import JaxModule
from orbax.export import ServingConfig
import tensorflow as tf
import jax.numpy as jnp

def model_fn(_, x):
    return jnp.sin(jnp.cos(x))

jax_module = JaxModule({}, model_fn, input_polymorphic_shape='b, ...')

# Option 1: Direct SavedModel conversion
tf.saved_model.save(
    jax_module,
    '/some/directory',
    signatures=jax_module.methods[JaxModule.DEFAULT_METHOD_KEY].get_concrete_function(
        tf.TensorSpec(shape=(None,), dtype=tf.float32, name="input")
    ),
    options=tf.saved_model.SaveOptions(experimental_custom_gradients=True),
)
converter = tf.lite.TFLiteConverter.from_saved_model('/some/directory')
tflite_model = converter.convert()
```

### JAX with Pre/Post Processing

```python
# Option 2: With preprocessing and postprocessing
serving_config = ServingConfig(
    'Serving_default',
    input_signature=[tf.TensorSpec(shape=(None,), dtype=tf.float32, name='input')],
    tf_preprocessor=lambda x: x,
    tf_postprocessor=lambda out: {'output': out}
)
export_mgr = ExportManager(jax_module, [serving_config])
export_mgr.save('/some/directory')

converter = tf.lite.TFLiteConverter.from_saved_model('/some/directory')
tflite_model = converter.convert()
```

### JAX ResNet50 Example

```python
from orbax.export import ExportManager, JaxModule, ServingConfig

# Wrap the model params and function into a JaxModule
jax_module = JaxModule({}, jax_model.apply, trainable=False)

# Specify the serving configuration and export the model
serving_config = ServingConfig(
    "serving_default",
    input_signature=[tf.TensorSpec([480, 640, 3], tf.float32, name="inputs")],
    tf_preprocessor=resnet_image_processor,
    tf_postprocessor=lambda x: tf.argmax(x, axis=-1),
)

export_manager = ExportManager(jax_module, [serving_config])

saved_model_dir = "resnet50_saved_model"
export_manager.save(saved_model_dir)

# Convert to TFLite
converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)
tflite_model = converter.convert()
```

## Model Optimization

### Graph Transformation

```bash
# Build graph transformation tool
bazel build tensorflow/tools/graph_transforms:transform_graph

# Optimize for deployment
bazel-bin/tensorflow/tools/graph_transforms/transform_graph \
--in_graph=tensorflow_inception_graph.pb \
--out_graph=optimized_inception_graph.pb \
--inputs='Mul' \
--outputs='softmax' \
--transforms='
  strip_unused_nodes(type=float, shape="1,299,299,3")
  remove_nodes(op=Identity, op=CheckNumerics)
  fold_constants(ignore_errors=true)
  fold_batch_norms
  fold_old_batch_norms'
```

### Fix Mobile Kernel Errors

```bash
# Optimize for mobile deployment
bazel-bin/tensorflow/tools/graph_transforms/transform_graph \
--in_graph=tensorflow_inception_graph.pb \
--out_graph=optimized_inception_graph.pb \
--inputs='Mul' \
--outputs='softmax' \
--transforms='
  strip_unused_nodes(type=float, shape="1,299,299,3")
  fold_constants(ignore_errors=true)
  fold_batch_norms
  fold_old_batch_norms'
```

## EfficientDet Deployment

### Export SavedModel

```python
def export_saved_model(
    model: tf.keras.Model,
    saved_model_dir: str,
    batch_size: Optional[int] = None,
    pre_mode: Optional[str] = 'infer',
    post_mode: Optional[str] = 'global'
) -> None:
    """Export EfficientDet model to SavedModel format.

    Args:
        model: The EfficientDetNet model used for training
        saved_model_dir: Folder path for saved model
        batch_size: Batch size to be saved in saved_model
        pre_mode: Pre-processing mode ('infer' or None)
        post_mode: Post-processing mode ('global', 'per_class', 'tflite', or None)
    """
    # Implementation exports model with specified configuration
    tf.saved_model.save(model, saved_model_dir)
```

### Complete Export Pipeline

```python
# Export model with all formats
export_saved_model(
    model=my_keras_model,
    saved_model_dir="./saved_model_export",
    batch_size=1,
    pre_mode='infer',
    post_mode='global'
)

# Convert to TFLite
converter = tf.lite.TFLiteConverter.from_saved_model('./saved_model_export')
tflite_model = converter.convert()

# Save TFLite model
with open('efficientdet.tflite', 'wb') as f:
    f.write(tflite_model)
```

## Mobile Deployment

### Deploy to Android

```bash
# Push TFLite model to Android device
adb push mobilenet_quant_v1_224.tflite /data/local/tmp

# Run benchmark on device
adb shell /data/local/tmp/benchmark_model \
  --graph=/data/local/tmp/mobilenet_quant_v1_224.tflite \
  --num_threads=4
```

### TFLite Interpreter Usage

```python
# Load TFLite model and allocate tensors
interpreter = tf.lite.Interpreter(model_path='model.tflite')
interpreter.allocate_tensors()

# Get input and output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Prepare input data
input_shape = input_details[0]['shape']
input_data = np.array(np.random.random_sample(input_shape), dtype=np.float32)

# Run inference
interpreter.set_tensor(input_details[0]['index'], input_data)
interpreter.invoke()

# Get predictions
output_data = interpreter.get_tensor(output_details[0]['index'])
print(output_data)
```

## Distributed Training and Serving

### MirroredStrategy for Multi-GPU

```python
# Create the strategy instance. It will automatically detect all the GPUs.
mirrored_strategy = tf.distribute.MirroredStrategy()

# Create and compile the keras model under strategy.scope()
with mirrored_strategy.scope():
    model = tf.keras.Sequential([tf.keras.layers.Dense(1, input_shape=(1,))])
    model.compile(loss='mse', optimizer='sgd')

# Call model.fit and model.evaluate as before.
dataset = tf.data.Dataset.from_tensors(([1.], [1.])).repeat(100).batch(10)
model.fit(dataset, epochs=2)
model.evaluate(dataset)

# Save distributed model
model.save('distributed_model')
```

### TPU Variable Optimization

```python
# Optimized TPU variable reformatting in MLIR
# Before optimization:
var0 = ...
var1 = ...
tf.while_loop(..., var0, var1) {
    tf_device.replicate([var0, var1] as rvar) {
        compile = tf._TPUCompileMlir()
        tf.TPUExecuteAndUpdateVariablesOp(rvar, compile)
    }
}

# After optimization with state variables:
var0 = ...
var1 = ...
state_var0 = ...
state_var1 = ...
tf.while_loop(..., var0, var1, state_var0, state_var1) {
    tf_device.replicate(
        [var0, var1] as rvar,
        [state_var0, state_var1] as rstate
    ) {
        compile = tf._TPUCompileMlir()
        tf.TPUReshardVariablesOp(rvar, compile, rstate)
        tf.TPUExecuteAndUpdateVariablesOp(rvar, compile)
    }
}
```

## Model Serving with TensorFlow Serving

### Export for TensorFlow Serving

```python
# Export model with version number
export_path = os.path.join('serving_models', 'my_model', '1')
tf.saved_model.save(model, export_path)

# Export multiple versions
for version in [1, 2, 3]:
    export_path = os.path.join('serving_models', 'my_model', str(version))
    tf.saved_model.save(model, export_path)
```

### Docker Deployment

```bash
# Pull TensorFlow Serving image
docker pull tensorflow/serving

# Run TensorFlow Serving container
docker run -p 8501:8501 \
  --mount type=bind,source=/path/to/my_model,target=/models/my_model \
  -e MODEL_NAME=my_model \
  -t tensorflow/serving

# Test REST API
curl -d '{"instances": [[1.0, 2.0, 3.0, 4.0]]}' \
  -X POST http://localhost:8501/v1/models/my_model:predict
```

## Model Validation and Testing

### Validate TFLite Model

```python
# Compare TFLite predictions with original model
def validate_tflite_model(model, tflite_model_path, test_data):
    """Validate TFLite model against original."""
    # Original model predictions
    original_predictions = model.predict(test_data)

    # TFLite model predictions
    interpreter = tf.lite.Interpreter(model_path=tflite_model_path)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    tflite_predictions = []
    for sample in test_data:
        interpreter.set_tensor(input_details[0]['index'], sample[np.newaxis, ...])
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]['index'])
        tflite_predictions.append(output[0])

    tflite_predictions = np.array(tflite_predictions)

    # Compare predictions
    difference = np.abs(original_predictions - tflite_predictions)
    print(f"Mean absolute difference: {np.mean(difference):.6f}")
    print(f"Max absolute difference: {np.max(difference):.6f}")
```

### Model Size Comparison

```python
import os

def compare_model_sizes(saved_model_path, tflite_model_path):
    """Compare sizes of SavedModel and TFLite."""
    # SavedModel size (sum of all files)
    saved_model_size = sum(
        os.path.getsize(os.path.join(dirpath, filename))
        for dirpath, _, filenames in os.walk(saved_model_path)
        for filename in filenames
    )

    # TFLite model size
    tflite_size = os.path.getsize(tflite_model_path)

    print(f"SavedModel size: {saved_model_size / 1e6:.2f} MB")
    print(f"TFLite model size: {tflite_size / 1e6:.2f} MB")
    print(f"Size reduction: {(1 - tflite_size / saved_model_size) * 100:.1f}%")
```

## When to Use This Skill

Use the tensorflow-model-deployment skill when you need to:

- Export trained models for production serving
- Deploy models to mobile devices (iOS, Android)
- Optimize models for edge devices and IoT
- Convert models to TensorFlow Lite format
- Apply post-training quantization for model compression
- Set up TensorFlow Serving infrastructure
- Deploy models with Docker containers
- Create model serving APIs with REST or gRPC
- Optimize inference latency and throughput
- Reduce model size for bandwidth-constrained environments
- Convert JAX or PyTorch models to TensorFlow format
- Implement A/B testing with multiple model versions
- Deploy models to cloud platforms (GCP, AWS, Azure)
- Create on-device ML applications
- Optimize models for specific hardware accelerators

## Best Practices

1. **Always validate converted models** - Compare TFLite predictions with original model to ensure accuracy
2. **Use SavedModel format** - Standard format for production deployment and serving
3. **Apply appropriate quantization** - Float16 for balanced speed/accuracy, INT8 for maximum compression
4. **Include preprocessing in model** - Embed preprocessing in SavedModel for consistent inference
5. **Version your models** - Use version numbers in export paths for model management
6. **Test on target devices** - Validate performance on actual deployment hardware
7. **Monitor model size** - Track model size before and after optimization
8. **Use representative datasets** - Provide calibration data for accurate quantization
9. **Enable GPU delegation** - Use GPU/TPU acceleration on supported devices
10. **Optimize batch sizes** - Tune batch size for throughput vs latency tradeoffs
11. **Cache frequently used models** - Load models once and reuse for multiple predictions
12. **Use TensorFlow Serving** - Leverage built-in serving infrastructure for scalability
13. **Implement model warmup** - Run dummy predictions to initialize serving systems
14. **Monitor inference metrics** - Track latency, throughput, and error rates in production
15. **Use metadata in TFLite** - Include labels and preprocessing info in model metadata

## Common Pitfalls

1. **Not validating converted models** - TFLite conversion can introduce accuracy degradation
2. **Over-aggressive quantization** - INT8 quantization without calibration causes accuracy loss
3. **Missing representative dataset** - Quantization without calibration produces poor results
4. **Ignoring model size** - Large models fail to deploy on memory-constrained devices
5. **Not testing on target hardware** - Performance varies significantly across devices
6. **Hardcoded preprocessing** - Client-side preprocessing causes inconsistencies
7. **Wrong input/output types** - Type mismatches between model and inference code
8. **Not using batch inference** - Single-sample inference is inefficient for high throughput
9. **Missing error handling** - Production systems need robust error handling
10. **Not monitoring model drift** - Model performance degrades over time without monitoring
11. **Incorrect tensor shapes** - Shape mismatches cause runtime errors
12. **Not optimizing for target device** - Generic optimization doesn't leverage device-specific features
13. **Forgetting model versioning** - Difficult to rollback or A/B test without versions
14. **Not using GPU acceleration** - CPU-only inference is much slower on capable devices
15. **Deploying untested models** - Always validate models before production deployment

## Resources

- [SavedModel Format Guide](https://www.tensorflow.org/guide/saved_model)
- [TensorFlow Lite Guide](https://www.tensorflow.org/lite/guide)
- [Post-Training Quantization](https://www.tensorflow.org/lite/performance/post_training_quantization)
- [TensorFlow Serving](https://www.tensorflow.org/tfx/guide/serving)
- [Model Optimization Toolkit](https://www.tensorflow.org/model_optimization)
- [TFLite Android Guide](https://www.tensorflow.org/lite/guide/android)
- [TFLite iOS Guide](https://www.tensorflow.org/lite/guide/ios)
- [Graph Transforms](https://github.com/tensorflow/tensorflow/tree/master/tensorflow/tools/graph_transforms)
- [Model Maker](https://www.tensorflow.org/lite/guide/model_maker)
- [Orbax Export (JAX)](https://github.com/google/orbax/tree/main/export)
