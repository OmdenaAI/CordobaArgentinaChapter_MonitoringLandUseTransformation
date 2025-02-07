import onnx
import numpy as np
import cv2
import matplotlib.pyplot as plt
import onnxruntime as ort

from pre_process import preprocess_image

# Load the ONNX model
model_path = "./models/deeplabv3_landcover_4c.onnx"
model = onnx.load(model_path)

# Display model input and output details
for input_tensor in model.graph.input:
    shape = [dim.dim_value for dim in input_tensor.type.tensor_type.shape.dim]
    print(f"Input Name: {input_tensor.name}, Shape: {shape}")

for output_tensor in model.graph.output:
    shape = [dim.dim_value for dim in output_tensor.type.tensor_type.shape.dim]
    print(f"Output Name: {output_tensor.name}, Shape: {shape}")



# Load ONNX runtime session
ort_session = ort.InferenceSession(model_path)

# Get model input name
input_name = ort_session.get_inputs()[0].name

# Preprocess image
image = preprocess_image("./images/N-33-60-D-c-4-2_56.jpg")

# Run inference
outputs = ort_session.run(None, {input_name: image})

# Extract output (Segmentation Map)
output_mask = outputs[0]  # Shape: (1, 4, 512, 512)


# Convert probabilities to class index (highest probability per pixel)
segmentation_map = np.argmax(output_mask, axis=1)  # Shape: (1, 512, 512)

print(segmentation_map)

# Remove batch dimension
segmentation_map = segmentation_map.squeeze()  # Shape: (512, 512)


# Define class color mapping (BGR format for OpenCV)
CLASS_COLORS = {
    1: (255, 0, 0),    # Building (Blue)
    2: (0, 255, 0),    # Woodland (Green)
    3: (255, 255, 255), # Water (White)
    4: (0, 0, 255),# Road (Red)
    
}

def apply_color_mask(segmentation_map):
    # Create an empty color image (H, W, 3)
    color_mask = np.zeros((segmentation_map.shape[0], segmentation_map.shape[1], 3), dtype=np.uint8)

    # Assign colors based on class labels
    for class_id, color in CLASS_COLORS.items():
        color_mask[segmentation_map == class_id] = color  # Apply color where class matches

    return color_mask

# Apply the color mask
colored_mask = apply_color_mask(segmentation_map)


# Display the segmentation map
plt.imshow(cv2.cvtColor(colored_mask, cv2.COLOR_BGR2RGB))  # Convert BGR to RGB for matplotlib
plt.axis("off")
plt.title("Land Cover Segmentation")
plt.show()
