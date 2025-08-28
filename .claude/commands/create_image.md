---
name: Create Image
allowed-tools: Bash, mcp__replicate__create_models_predictions, mcp__replicate__get_predictions
description: Generate image(s) via Replicate
---

# Create Image

This command generates image(s) based on the provided prompt using Replicate.

## Variables

DROPPED_FILE_PATH: [[FILE_PATH]]
DROPPED_FILE_PATH_ARCHIVE: agentic_drop_zone/generate_images_zone/drop_zone_file_archive/
IMAGE_OUTPUT_DIR: agentic_drop_zone/generate_images_zone/image_output/<date_time>/
    - This is the directory where all images will be saved
    - The date_time is the current date and time in the format YYYY-MM-DD_HH-MM-SS
MODEL: google/nano-banana
ASPECT_RATIO: 16:9

## Workflow

- First, read `DROPPED_FILE_PATH`.
- Create output directory: `IMAGE_OUTPUT_DIR/<date_time>/`
- IMPORTANT: For every image prompt detailed in the `DROPPED_FILE_PATH` do the following:

<image-loop>
  - Use `mcp__replicate__create_models_predictions` with the MODEL specified above
  - Pass image prompt as the prompt input
  - Use ASPECT_RATIO for the image dimensions
  - Wait for completion by polling `mcp__replicate__get_predictions`
  - Save the executed prompts to `IMAGE_OUTPUT_DIR/<date_time>/image_prompt_<concise_name_based_on_prompt>.txt`
    - Use the exact prompt that was executed in the `mcp__replicate__create_models_predictions` call
  - Download the image: `IMAGE_OUTPUT_DIR/<date_time>/<MODEL_NAME_underscore_separated>_<concise_name_based_on_prompt>.jpg`
  - Display:
    - Generation time
    - File size
    - Full path to saved image
</image-loop>
- After all images are generated, open the output directory: `open IMAGE_OUTPUT_DIR/<date_time>/`
- When you finish generating images, move the `DROPPED_FILE_PATH` into a `DROPPED_FILE_PATH_ARCHIVE` directory