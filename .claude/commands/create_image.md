---
name: Create Image with Google (Optimized)
allowed-tools: Bash, Read, Write
description: Generate image(s) via Google Cloud Vertex AI using optimized direct calls
---

# Create Image with Google Cloud (Optimized)

This command generates image(s) using Google Cloud Vertex AI Imagen via a pre-built tool to avoid Python scaffolding.

## Variables

DROPPED_FILE_PATH: [[FILE_PATH]]
DROPPED_FILE_PATH_ARCHIVE: agentic_drop_zone/generate_images_zone/drop_zone_file_archive/
IMAGE_OUTPUT_DIR: agentic_drop_zone/generate_images_zone/image_output/<date_time>/
VERTEX_AI_TOOL: python tools/vertex_ai_image_generator.py

## Workflow

- First, read `DROPPED_FILE_PATH` to get the image prompts
- Create output directory: `IMAGE_OUTPUT_DIR/<date_time>/` where date_time is current timestamp in YYYY-MM-DD_HH-MM-SS format
- For each image prompt in the file:

## Parallel Image Generation with Error Handling

Create a robust parallel processing script that handles all prompts:

```bash
#!/bin/bash

# Create arrays to track parallel jobs
declare -a pids=()
declare -a prompts=()
declare -a results=()

# Function to generate single image with error handling
generate_image() {
    local prompt="$1"
    local output_dir="$2"
    local index="$3"

    echo "[$index] Starting: $prompt"

    # Generate image and capture result
    if python tools/vertex_ai_image_generator.py \
        "$prompt" \
        --aspect-ratio "16:9" \
        --output-dir "$output_dir" > "/tmp/image_result_$index.json" 2>&1; then
        echo "[$index] ✅ SUCCESS: $prompt"
        results[$index]="SUCCESS"
    else
        echo "[$index] ❌ FAILED: $prompt"
        results[$index]="FAILED"
    fi
}

# Read all prompts from file and start parallel generation
output_dir="IMAGE_OUTPUT_DIR/<date_time>/"
index=0

# FOR EACH PROMPT IN THE DROPPED FILE:
while IFS= read -r line; do
    if [[ "$line" =~ ^[[:space:]]*-[[:space:]]*\"(.+)\"[[:space:]]*$ ]]; then
        prompt="${BASH_REMATCH[1]}"
        prompts[$index]="$prompt"

        # Start generation in background
        generate_image "$prompt" "$output_dir" "$index" &
        pids[$index]=$!

        echo "Started parallel job $index (PID: ${pids[$index]}): ${prompt:0:50}..."
        ((index++))
    fi
done < "DROPPED_FILE_PATH"

total_jobs=$index
echo ""
echo "🚀 Started $total_jobs parallel image generation jobs"
echo "⏳ Waiting for all jobs to complete..."

# Wait for all jobs and track completion
completed=0
failed=0

for i in "${!pids[@]}"; do
    pid=${pids[$i]}
    prompt="${prompts[$i]}"

    echo "⏳ Waiting for job $i (PID: $pid): ${prompt:0:40}..."

    if wait $pid; then
        echo "✅ Job $i completed successfully"
        ((completed++))
    else
        echo "❌ Job $i failed"
        ((failed++))
    fi
done

# Summary report
echo ""
echo "🎯 PARALLEL GENERATION COMPLETE"
echo "📊 Results Summary:"
echo "   ✅ Successful: $completed/$total_jobs images"
echo "   ❌ Failed: $failed/$total_jobs images"
echo "   📁 Output directory: $output_dir"

# Show generated files
echo ""
echo "📋 Generated Images:"
find "$output_dir" -name "*.jpg" -o -name "*.png" | while read -r file; do
    size=$(du -h "$file" | cut -f1)
    basename=$(basename "$file")
    echo "   🖼️  $basename ($size)"
done

# Show any errors
if [ $failed -gt 0 ]; then
    echo ""
    echo "⚠️  Error Details:"
    for i in "${!results[@]}"; do
        if [[ "${results[$i]}" == "FAILED" ]]; then
            echo "   ❌ Job $i: ${prompts[$i]}"
            echo "      Details: $(cat /tmp/image_result_$i.json 2>/dev/null || echo 'No error details')"
        fi
    done
fi
```

- After all images are generated, open the output directory: `open IMAGE_OUTPUT_DIR/<date_time>/`
- Archive the original file: `mkdir -p DROPPED_FILE_PATH_ARCHIVE && mv DROPPED_FILE_PATH DROPPED_FILE_PATH_ARCHIVE/`

## Benefits of This Approach

- ✅ **No Python scaffolding generation** - uses pre-built tool
- ✅ **Faster execution** - direct API calls
- ✅ **Consistent error handling** - standardized responses
- ✅ **Reliable authentication** - centralized service account handling
- ✅ **Clean file organization** - automatic timestamped directories

## Prerequisites

- Google Cloud service account key configured at: `./service-account-key.json`
- Environment variables: `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_REGION`
- Vertex AI Imagen model deployed in your GCP project